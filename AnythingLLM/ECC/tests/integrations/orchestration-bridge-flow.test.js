/**
 * End-to-end del orchestration bridge, sin llamar a ningun modelo.
 *
 * Run with: node tests/integrations/orchestration-bridge-flow.test.js
 *
 * Cubre las dos mitades del contrato:
 *   1. OPT-IN: apagado por defecto, el harness se comporta como si el bridge
 *      no existiera (ni ledger, ni efectos, ni salida).
 *   2. FLUJO: activado, recorre gates -> triage -> final -> decision y deja
 *      la traza completa en el ledger.
 *
 * Los clientes de verificacion se inyectan como stubs; el pipeline nunca ve
 * una red. Es el motivo de que verify() reciba runGates/triage/final.
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const BRIDGE = path.resolve(__dirname, '../../integrations/orchestration-bridge');
const { loadPolicy } = require(path.join(BRIDGE, 'scripts/route-task'));
const { verify } = require(path.join(BRIDGE, 'scripts/verify-pipeline'));
const { getBridgeState } = require(path.join(BRIDGE, 'scripts/lib/bridge-config'));
const bridgeSession = require(path.join(BRIDGE, 'scripts/bridge-session'));
const postVerify = require(path.join(BRIDGE, 'scripts/post-opencode-verify'));
const { handleFailure } = require(path.join(BRIDGE, 'scripts/post-opencode-failure'));
const ledgerLib = require(path.join(BRIDGE, 'scripts/lib/ledger'));

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    return true;
  } catch (err) {
    console.log(`  ✗ ${name}`);
    console.log(`    Error: ${err.message}`);
    return false;
  }
}

// --- entorno temporal -------------------------------------------------------

function makeWorkspace(bridgeJson) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ecc-bridge-'));
  if (bridgeJson !== undefined) {
    fs.mkdirSync(path.join(dir, '.claude'), { recursive: true });
    fs.writeFileSync(
      path.join(dir, '.claude', 'bridge.json'),
      typeof bridgeJson === 'string' ? bridgeJson : JSON.stringify(bridgeJson),
      'utf8'
    );
  }
  return dir;
}

// --- stubs de verificacion --------------------------------------------------

const GREEN_GATES = () => ({ lint: 'pass', tests: 'pass', security: 'pass', markdown: 'warn' });
const VETO_GATES = () => ({ lint: 'pass', tests: 'pass', security: 'fail' });

const stubTriage = overrides => () => ({
  model: 'claude-sonnet-5',
  aggregate_score: 0.88,
  risk_class: 'medium',
  needs_deep_review: false,
  checks: [
    { name: 'style_conventions', status: 'pass', score: 0.94, recommendation: null },
    { name: 'test_coverage_delta', status: 'warn', score: 0.72, recommendation: 'añadir test' }
  ],
  ...overrides
});

const stubFinal = overrides => () => ({
  model: 'claude-opus-4-8',
  aggregate_score: 0.64,
  verdict: 'cobertura insuficiente del path de fallo',
  ...overrides
});

const ARTIFACT = {
  run_id: 'flow-test-1',
  task_type: 'bulk_codegen',
  model: 'oc-bulk-stub',
  files_touched: 11,
  touches_paths: ['src/lib/parse.js'],
  artifact_sha256: 'deadbeef',
  exit_code: 0,
  success: true
};

function runTests() {
  console.log('\n=== Testing orchestration-bridge flow (opt-in + e2e) ===\n');

  let passed = 0;
  let failed = 0;
  const check = (name, fn) => { if (test(name, fn)) passed++; else failed++; };
  const policy = loadPolicy(path.join(BRIDGE, 'model-route.yaml'));

  // ======================================================================
  console.log('Opt-in (default OFF):');

  check('sin .claude/bridge.json el bridge esta apagado', () => {
    const cwd = makeWorkspace(undefined);
    const state = getBridgeState({ cwd, env: {} });
    assert.strictEqual(state.enabled, false);
    assert.strictEqual(state.source, 'default');
    assert.ok(state.reason.includes('opt-in'));
  });

  check('bridge.json con enabled:false sigue apagado', () => {
    const cwd = makeWorkspace({ enabled: false });
    assert.strictEqual(getBridgeState({ cwd, env: {} }).enabled, false);
  });

  check('bridge.json con enabled:true lo activa', () => {
    const cwd = makeWorkspace({ enabled: true });
    const state = getBridgeState({ cwd, env: {} });
    assert.strictEqual(state.enabled, true);
    assert.strictEqual(state.source, 'project');
  });

  check('ECC_BRIDGE=off gana sobre un proyecto que lo activo', () => {
    const cwd = makeWorkspace({ enabled: true });
    const state = getBridgeState({ cwd, env: { ECC_BRIDGE: 'off' } });
    assert.strictEqual(state.enabled, false);
    assert.strictEqual(state.source, 'env');
  });

  check('ECC_BRIDGE=on activa sin tocar el proyecto', () => {
    const cwd = makeWorkspace(undefined);
    assert.strictEqual(getBridgeState({ cwd, env: { ECC_BRIDGE: 'on' } }).enabled, true);
  });

  check('un bridge.json corrupto NO activa el bridge', () => {
    const cwd = makeWorkspace('{ esto no es json');
    const state = getBridgeState({ cwd, env: {} });
    assert.strictEqual(state.enabled, false, 'un archivo roto nunca debe activar nada');
    assert.ok(state.reason.includes('ilegible'));
  });

  check('scope acota por tarea: fuera de scope, apagado', () => {
    const cwd = makeWorkspace({ enabled: true, scope: ['src/**'] });
    const dentro = getBridgeState({ cwd, env: {}, task: { touches_paths: ['src/a.js'] } });
    const fuera = getBridgeState({ cwd, env: {}, task: { touches_paths: ['docs/x.md'] } });
    assert.strictEqual(dentro.enabled, true);
    assert.strictEqual(fuera.enabled, false);
    assert.strictEqual(fuera.source, 'scope');
  });

  check('el scope del proyecto acota incluso con ECC_BRIDGE=on', () => {
    const cwd = makeWorkspace({ enabled: true, scope: ['src/**'] });
    const state = getBridgeState({
      cwd, env: { ECC_BRIDGE: 'on' }, task: { touches_paths: ['docs/x.md'] }
    });
    assert.strictEqual(state.enabled, false, 'un override de sesion no debe saltarse el scope');
  });

  // ======================================================================
  console.log('\nApagado = sin efectos:');

  check('SessionStart apagado no escribe ledger ni emite salida', () => {
    const cwd = makeWorkspace(undefined);
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const out = bridgeSession.init(JSON.stringify({ session_id: 's1' }), { cwd, env: {}, ledgerPath });
    assert.strictEqual(fs.existsSync(ledgerPath), false, 'apagado no debe crear el ledger');
    assert.strictEqual(out.exitCode, 0);
    assert.ok(!out.stderr, 'apagado no debe hablar');
  });

  check('SessionEnd y flush apagados tampoco escriben', () => {
    const cwd = makeWorkspace({ enabled: false });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    bridgeSession.flush(JSON.stringify({ session_id: 's1' }), { cwd, env: {}, ledgerPath });
    bridgeSession.close(JSON.stringify({ session_id: 's1' }), { cwd, env: {}, ledgerPath });
    assert.strictEqual(fs.existsSync(ledgerPath), false);
  });

  check('PostToolUse apagado devuelve el stdin intacto', () => {
    const cwd = makeWorkspace(undefined);
    const prev = process.cwd();
    process.chdir(cwd);
    try {
      const raw = JSON.stringify({ tool_response: { exit_code: 0, artifact: ARTIFACT } });
      const out = postVerify.run(raw);
      assert.strictEqual(out.stdout, raw, 'debe pasar de largo sin tocar el payload');
      assert.strictEqual(out.exitCode, 0);
      assert.ok(!out.stderr);
    } finally {
      process.chdir(prev);
    }
  });

  // ======================================================================
  console.log('\nFlujo completo (activado, clientes stub):');

  check('camino feliz: gates verdes + triage alto -> approve, sin Opus', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const verdict = verify(ARTIFACT, {
      policy, ledgerPath, runGates: GREEN_GATES, triage: stubTriage(), final: stubFinal()
    });

    assert.strictEqual(verdict.status, 'approve');
    assert.strictEqual(verdict.aggregate_score, 0.88);
    assert.strictEqual(verdict.escalated_to_opus, false, 'un cambio rutinario no paga Opus');
    assert.strictEqual(verdict.human_review_required, false);
    assert.strictEqual(verdict.models_used.final, null);

    const entries = ledgerLib.read(ledgerPath);
    const steps = entries.map(e => e.step);
    assert.deepStrictEqual(steps, ['gates', 'triage', 'decision'], `traza inesperada: ${steps}`);
    assert.strictEqual(entries[entries.length - 1].decision, 'approve');
  });

  check('veto de seguridad: corta antes del LLM y manda a humano', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    let triageCalled = false;

    const verdict = verify(ARTIFACT, {
      policy, ledgerPath, runGates: VETO_GATES,
      triage: () => { triageCalled = true; return stubTriage()(); },
      final: stubFinal()
    });

    assert.strictEqual(triageCalled, false, 'el veto debe cortar ANTES de gastar tokens');
    assert.strictEqual(verdict.status, 'human_review');
    assert.strictEqual(verdict.aggregate_score, 0);
    assert.strictEqual(verdict.security_veto, true);
    assert.ok(verdict.remedial_action.includes('seguridad'));

    const steps = ledgerLib.read(ledgerPath).map(e => e.step);
    assert.deepStrictEqual(steps, ['gates', 'decision'], 'no debe haber paso de triage');
  });

  check('critico: escala a Opus y el score bajo manda a humano', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const critical = { ...ARTIFACT, touches_paths: ['scripts/hooks/pre-bash-dispatcher.js'] };

    const verdict = verify(critical, {
      policy, ledgerPath, runGates: GREEN_GATES,
      triage: stubTriage({ risk_class: 'critical', needs_deep_review: true, aggregate_score: 0.79 }),
      final: stubFinal()
    });

    assert.strictEqual(verdict.escalated_to_opus, true);
    assert.strictEqual(verdict.models_used.final, 'claude-opus-4-8');
    assert.strictEqual(verdict.aggregate_score, 0.64, 'manda el score de la validacion final');
    assert.strictEqual(verdict.status, 'human_review');

    const steps = ledgerLib.read(ledgerPath).map(e => e.step);
    assert.deepStrictEqual(steps, ['gates', 'triage', 'final', 'decision']);
  });

  check('sin verificador enchufado NO se aprueba: va a humano', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const verdict = verify(ARTIFACT, {
      policy, ledgerPath, runGates: GREEN_GATES, triage: null, final: null
    });

    assert.strictEqual(verdict.status, 'human_review');
    assert.strictEqual(verdict.human_review_required, true);
    assert.ok(
      verdict.remedial_action.includes('ECC_BRIDGE_VERIFIER'),
      'debe decir que falta el adaptador, no inventarse un veredicto'
    );
  });

  check('la policy exige Opus pero no hay verificador final -> humano', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const critical = { ...ARTIFACT, touches_paths: ['scripts/hooks/x.js'] };
    const verdict = verify(critical, {
      policy, ledgerPath, runGates: GREEN_GATES,
      triage: stubTriage({ risk_class: 'critical', needs_deep_review: true }), final: null
    });
    assert.strictEqual(verdict.status, 'human_review');
    assert.strictEqual(verdict.escalated_to_opus, false);
  });

  // ======================================================================
  console.log('\nFallo de generacion y cierre:');

  check('con reintentos disponibles, reintenta', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const outcome = handleFailure(
      { run_id: 'f1', task_type: 'bulk_codegen', exit_code: 1, retries_used: 0, error: 'boom' },
      { policy, ledgerPath }
    );
    assert.strictEqual(outcome.decision, 'retry');
    assert.strictEqual(outcome.retries_used, 1);
    assert.ok(outcome.instruction.includes('boom'), 'el reintento debe llevar el error concreto');
  });

  check('agotados los reintentos, escala en vez de repetir', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    const outcome = handleFailure(
      { run_id: 'f2', task_type: 'db_migration', exit_code: 1, retries_used: 1 },
      { policy, ledgerPath }
    );
    assert.strictEqual(outcome.decision, 'escalate');
    assert.strictEqual(outcome.escalated_to, 'claude-sonnet-5');
  });

  check('SessionEnd agrega las decisiones del run', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    verify(ARTIFACT, { policy, ledgerPath, runGates: GREEN_GATES, triage: stubTriage() });
    verify({ ...ARTIFACT, run_id: 'flow-test-1' }, {
      policy, ledgerPath, runGates: VETO_GATES, triage: stubTriage()
    });

    bridgeSession.close(JSON.stringify({ session_id: 'flow-test-1' }), { cwd, env: {}, ledgerPath });

    const last = ledgerLib.read(ledgerPath).pop();
    assert.strictEqual(last.event, 'bridge_closed');
    assert.strictEqual(last.decisions, 2);
    assert.strictEqual(last.approved, 1);
    assert.strictEqual(last.human_review, 1);
  });

  check('el ledger redacta credenciales', () => {
    const cwd = makeWorkspace({ enabled: true });
    const ledgerPath = path.join(cwd, 'ledger.jsonl');
    ledgerLib.append(
      { run_id: 'r', nested: { authorization: 'Bearer abc', api_key: 'k' }, safe: 'ok' },
      { ledgerPath }
    );
    const raw = fs.readFileSync(ledgerPath, 'utf8');
    assert.ok(!raw.includes('Bearer abc'), 'el token no puede llegar al disco');
    assert.ok(raw.includes('[redacted]'));
    assert.ok(raw.includes('ok'), 'lo que no es secreto se conserva');
  });

  // Formato exacto que parsea tests/run-all.js (/Passed:\s*(\d+)/).
  console.log(`\nResults: Passed: ${passed}, Failed: ${failed}\n`);
  return failed === 0;
}

if (require.main === module) {
  process.exit(runTests() ? 0 : 1);
}

module.exports = { runTests };
