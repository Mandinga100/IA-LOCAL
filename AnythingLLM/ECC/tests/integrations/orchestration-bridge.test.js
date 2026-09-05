/**
 * Tests for integrations/orchestration-bridge
 *
 * Run with: node tests/integrations/orchestration-bridge.test.js
 *
 * Los casos 1-4 de test-cases.json son deterministas: routing, gate y matriz
 * de decision son codigo puro y no llaman a ningun modelo. El caso 5 usa
 * stubs de triage/final en lugar de un cliente LLM real.
 */

const assert = require('assert');
const path = require('path');
const fs = require('fs');

const BRIDGE = path.resolve(__dirname, '../../integrations/orchestration-bridge');
const { loadPolicy, routeTask, matchesNumeric, matchesAnyGlob } = require(
  path.join(BRIDGE, 'scripts/route-task')
);
const { evaluate } = require(path.join(BRIDGE, 'scripts/decision'));
const { evaluateInvocation, extractSubcommand } = require(
  path.join(BRIDGE, 'scripts/pre-opencode-gate')
);

const cases = JSON.parse(
  fs.readFileSync(path.join(BRIDGE, 'test-cases.json'), 'utf8')
).cases;

const byId = id => {
  const found = cases.find(c => c.id === id);
  assert.ok(found, `caso ${id} ausente de test-cases.json`);
  return found;
};

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

function runTests() {
  console.log('\n=== Testing orchestration-bridge ===\n');

  let passed = 0;
  let failed = 0;
  const check = (name, fn) => { if (test(name, fn)) passed++; else failed++; };

  const policy = loadPolicy(path.join(BRIDGE, 'model-route.yaml'));

  // --- policy integrity ----------------------------------------------------
  console.log('Policy:');

  check('model-route.yaml carga con reglas y gates', () => {
    assert.ok(policy.rules.length >= 6, 'el brief pide al menos 6 reglas');
    assert.ok(policy.gates.length > 0);
    assert.ok(Array.isArray(policy.decision_matrix));
  });

  check('la ultima regla es la de cierre (always)', () => {
    const last = policy.rules[policy.rules.length - 1];
    assert.strictEqual(last.when.always, true, 'sin regla de cierre routeTask puede lanzar');
  });

  check('la matriz de decision no contiene expresiones evaluables', () => {
    for (const rule of policy.decision_matrix) {
      assert.strictEqual(
        typeof rule.if, 'object',
        `${rule.id}: 'if' debe ser estructurado, no un string a evaluar`
      );
    }
  });

  check('todo modelo de claude declarado esta marcado verified', () => {
    for (const [key, model] of Object.entries(policy.models)) {
      if (model.engine === 'claude') {
        assert.strictEqual(model.verified, true, `${key} deberia estar verificado`);
      }
    }
  });

  // --- helpers -------------------------------------------------------------
  console.log('\nHelpers:');

  check('matchesNumeric entiende >=, <, == y numero suelto', () => {
    assert.strictEqual(matchesNumeric(5, '>= 5'), true);
    assert.strictEqual(matchesNumeric(4, '>= 5'), false);
    assert.strictEqual(matchesNumeric(3, '< 10'), true);
    assert.strictEqual(matchesNumeric(3, 3), true);
    assert.strictEqual(matchesNumeric('nope', '>= 1'), false);
  });

  check('matchesAnyGlob: ** cruza separadores, * no', () => {
    assert.strictEqual(matchesAnyGlob(['scripts/hooks/x.js'], ['scripts/hooks/**']), true);
    assert.strictEqual(matchesAnyGlob(['src/a/b.js'], ['src/*.js']), false);
    assert.strictEqual(matchesAnyGlob(['src/b.js'], ['src/*.js']), true);
    assert.strictEqual(matchesAnyGlob(['docs/readme.md'], ['scripts/hooks/**']), false);
  });

  check('extractSubcommand saca el verbo de la invocacion', () => {
    assert.strictEqual(
      extractSubcommand('integrations/orchestration-bridge/open-code.sh generate --task-type x'),
      'generate'
    );
  });

  // --- tc1 -----------------------------------------------------------------
  console.log('\ntc1 — bulk limpio aprueba sin Opus:');
  const tc1 = byId('tc1-bulk-approve');

  check('tc1 routing casa r1-bulk-codegen sobre opencode', () => {
    const route = routeTask(
      { task_type: 'bulk_codegen', files_touched: tc1.input.tool_response.artifact.files_touched },
      { policy }
    );
    assert.strictEqual(route.rule_id, tc1.expected.rule_id);
    assert.strictEqual(route.engine, tc1.expected.engine);
  });

  check('tc1 decision = approve, sin escalada ni revision humana', () => {
    const result = evaluate({
      gateResults: tc1.input.gate_results,
      triage: tc1.input.triage_stub,
      final: null
    }, policy);
    assert.strictEqual(result.aggregate_score, tc1.expected.aggregate_score);
    assert.strictEqual(result.decision, tc1.expected.decision);
    assert.strictEqual(result.escalated_to_opus, tc1.expected.escalated_to_opus);
    assert.strictEqual(result.human_review_required, tc1.expected.human_review_required);
  });

  // --- tc2 -----------------------------------------------------------------
  console.log('\ntc2 — veto de seguridad:');
  const tc2 = byId('tc2-security-veto');

  check('tc2 el veto manda a humano y no invoca LLM', () => {
    const result = evaluate({ gateResults: tc2.input.gate_results, triage: null }, policy);
    assert.strictEqual(result.security_veto, tc2.expected.security_veto);
    assert.strictEqual(result.llm_invoked, tc2.expected.llm_invoked);
    assert.strictEqual(result.aggregate_score, tc2.expected.aggregate_score);
    assert.strictEqual(result.decision, tc2.expected.decision);
  });

  check('tc2 el veto gana aunque el triage hubiera puntuado alto', () => {
    const result = evaluate({
      gateResults: tc2.input.gate_results,
      triage: { aggregate_score: 0.99 }
    }, policy);
    assert.strictEqual(result.decision, 'human_review');
    assert.strictEqual(result.aggregate_score, 0);
    assert.strictEqual(result.llm_invoked, false);
  });

  // --- tc3 -----------------------------------------------------------------
  console.log('\ntc3 — Antigravity denegado por defecto:');
  const tc3 = byId('tc3-antigravity-denied-by-default');

  check('tc3 experimental=true no basta sin ECC_ALLOW_ANTIGRAVITY=1', () => {
    const verdict = evaluateInvocation(
      { command: 'open-code.sh scaffold', task: tc3.input.task },
      { env: { ECC_ALLOW_ANTIGRAVITY: '0' }, policy }
    );
    assert.strictEqual(verdict.decision, tc3.expected.gate_decision);
    assert.strictEqual(verdict.requested_engine, tc3.expected.requested_engine);
    assert.strictEqual(verdict.engine_applied, tc3.expected.engine_applied);
    assert.ok(
      verdict.detail.includes(tc3.expected.reason_contains),
      'el motivo debe nombrar la variable que falta'
    );
  });

  check('tc3 el cerrojo aguanta con la policy rota (falla cerrado)', () => {
    const verdict = evaluateInvocation(
      { command: 'open-code.sh scaffold', task: { task_type: 'scaffold_prototype', experimental: true } },
      { env: { ECC_ALLOW_ANTIGRAVITY: '0' }, policy: null, policyError: new Error('roto') }
    );
    assert.strictEqual(verdict.allowed, false, 'un YAML roto no puede abrir Antigravity');
  });

  check('tc3 con ambos cerrojos abiertos, procede', () => {
    const verdict = evaluateInvocation(
      { command: 'open-code.sh scaffold', task: { task_type: 'scaffold_prototype', experimental: true } },
      { env: { ECC_ALLOW_ANTIGRAVITY: '1', ECC_ANTIGRAVITY_TOKEN: 'x' }, policy }
    );
    assert.strictEqual(verdict.allowed, true);
  });

  check('tc3 una policy rota falla ABIERTO para lo que no es Antigravity', () => {
    const verdict = evaluateInvocation(
      { command: 'open-code.sh generate --task-type bulk_codegen', task: { task_type: 'bulk_codegen' } },
      { env: {}, policy: null, policyError: new Error('roto') }
    );
    assert.strictEqual(verdict.allowed, true, 'un hook no bloquea la sesion por error propio');
    assert.strictEqual(verdict.degraded, true);
  });

  // --- tc4 -----------------------------------------------------------------
  console.log('\ntc4 — cost cap:');
  const tc4 = byId('tc4-cost-cap-downgrade');

  check('tc4 sobre el cap degrada y registra la perdida de confianza', () => {
    const verdict = evaluateInvocation(
      {
        command: 'open-code.sh generate --task-type bulk_codegen',
        task: {
          task_type: 'bulk_codegen',
          estimated_cost_usd: tc4.input.task.estimated_cost_usd,
          cost_cap_usd: tc4.input.policy_cost_cap_usd
        }
      },
      { env: { ECC_OPENCODE_TOKEN: 'x' }, policy }
    );
    assert.strictEqual(verdict.decision, tc4.expected.gate_decision);
    assert.strictEqual(verdict.cost_capped, tc4.expected.cost_capped);
    assert.strictEqual(verdict.confidence_delta, tc4.expected.confidence_delta);
    for (const field of tc4.expected.ledger_fields_present) {
      assert.ok(field in verdict, `falta ${field} en el veredicto`);
    }
  });

  check('tc4 bajo el cap procede sin degradar', () => {
    const verdict = evaluateInvocation(
      {
        command: 'open-code.sh generate --task-type bulk_codegen',
        task: { task_type: 'bulk_codegen', estimated_cost_usd: 0.11, cost_cap_usd: 0.3 }
      },
      { env: { ECC_OPENCODE_TOKEN: 'x' }, policy }
    );
    assert.strictEqual(verdict.decision, 'proceed');
    assert.ok(!verdict.cost_capped);
  });

  check('sin token la generacion se deniega', () => {
    const verdict = evaluateInvocation(
      { command: 'open-code.sh generate --task-type bulk_codegen', task: { task_type: 'bulk_codegen' } },
      { env: {}, policy }
    );
    assert.strictEqual(verdict.allowed, false);
    assert.strictEqual(verdict.reason, 'missing_auth');
  });

  check('un subcomando fuera de la allowlist se deniega', () => {
    const verdict = evaluateInvocation(
      { command: 'open-code.sh exfiltrate --task-type bulk_codegen', task: { task_type: 'bulk_codegen' } },
      { env: { ECC_OPENCODE_TOKEN: 'x' }, policy }
    );
    assert.strictEqual(verdict.allowed, false);
    assert.strictEqual(verdict.reason, 'command_not_allowlisted');
  });

  // --- tc5 -----------------------------------------------------------------
  console.log('\ntc5 — critico escala a Opus (con stubs):');
  const tc5 = byId('tc5-critical-escalates-to-opus');

  check('tc5 un cambio en scripts/hooks/ casa r5-validacion-final-critica', () => {
    const route = routeTask({
      phase: 'verify',
      stage: 'final',
      touches_paths: tc5.input.tool_response.artifact.touches_paths
    }, { policy });
    assert.strictEqual(route.rule_id, tc5.expected.escalation_rule_id);
    assert.strictEqual(route.model_id, tc5.expected.final_model);
  });

  check('tc5 r5 no tiene fallback de modelo: agotado -> humano', () => {
    const route = routeTask({
      phase: 'verify', stage: 'final', risk_class: 'critical'
    }, { policy });
    assert.strictEqual(route.fallback, tc5.expected.fallback_used);
    assert.strictEqual(route.on_fallback_exhausted, 'human_review');
  });

  check('tc5 score final 0.64 -> human_review pese a gates verdes', () => {
    const result = evaluate({
      gateResults: tc5.input.gate_results,
      triage: tc5.input.triage_stub,
      final: tc5.input.final_stub
    }, policy);
    assert.strictEqual(result.aggregate_score, tc5.expected.aggregate_score);
    assert.strictEqual(result.escalated_to_opus, tc5.expected.escalated_to_opus);
    assert.strictEqual(result.decision, tc5.expected.decision);
    assert.strictEqual(result.human_review_required, true);
  });

  check('el umbral 0.70 es frontera dura', () => {
    const justUnder = evaluate({ gateResults: { tests: 'pass', security: 'pass' }, triage: { aggregate_score: 0.699 } }, policy);
    const justOver = evaluate({ gateResults: { tests: 'pass', security: 'pass' }, triage: { aggregate_score: 0.70 } }, policy);
    assert.strictEqual(justUnder.decision, 'human_review');
    assert.strictEqual(justOver.decision, 'auto_fix');
  });

  // --- resumen -------------------------------------------------------------
  // Formato exacto que parsea tests/run-all.js (/Passed:\s*(\d+)/).
  console.log(`\nResults: Passed: ${passed}, Failed: ${failed}\n`);
  return failed === 0;
}

if (require.main === module) {
  process.exit(runTests() ? 0 : 1);
}

module.exports = { runTests };
