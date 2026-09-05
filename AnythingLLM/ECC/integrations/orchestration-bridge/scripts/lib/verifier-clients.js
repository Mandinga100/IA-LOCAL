#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — clientes del pipeline de verificación.
 *
 *   runGates : REAL. Ejecuta los comandos de `gates` de model-route.yaml.
 *   triage   : ADAPTADOR. Este repo no trae cliente LLM; hay que enchufar uno.
 *   final    : ADAPTADOR. Igual.
 *
 * Sin adaptador, `triage`/`final` son null y el pipeline manda a revisión
 * humana. Es deliberado: preferimos un "no sé, míralo tú" honesto a un
 * veredicto inventado. Un verificador que aprueba sin haber verificado es
 * peor que no tener verificador.
 *
 * Para enchufar uno:
 *   ECC_BRIDGE_VERIFIER=/ruta/a/mi-adaptador.js
 * exportando { triage(artifact) -> {model, aggregate_score, risk_class,
 * needs_deep_review, checks[]} } y { final(artifact, triage) -> {model,
 * aggregate_score, verdict} }.
 */

'use strict';

const path = require('path');
const { spawnSync } = require('child_process');

const GATE_TIMEOUT_MS = 120000;

/** Ejecuta un gate y traduce el código de salida a pass/fail. */
function runGate(gate, cwd) {
  if (!gate.cmd || typeof gate.cmd !== 'string') return 'skip';
  const parts = gate.cmd.split(/\s+/);
  const result = spawnSync(parts[0], parts.slice(1), {
    cwd,
    encoding: 'utf8',
    timeout: GATE_TIMEOUT_MS,
    shell: process.platform === 'win32'
  });
  if (result.error) return 'skip';
  if (result.status === 0) return 'pass';
  return gate.blocking === true || gate.veto === true ? 'fail' : 'warn';
}

function makeGateRunner(policy, options = {}) {
  const cwd = options.cwd || process.cwd();
  const gates = policy.gates || [];
  return function runGates() {
    const results = {};
    for (const gate of gates) {
      results[gate.id] = runGate(gate, cwd);
    }
    return results;
  };
}

function loadAdapter(env = process.env) {
  const target = env.ECC_BRIDGE_VERIFIER;
  if (!target) return null;
  try {
    return require(path.resolve(target));
  } catch (err) {
    process.stderr.write(
      `[BridgeVerify] adaptador de verificación no cargable (${err.message}); ` +
      'el pipeline mandará a revisión humana\n'
    );
    return null;
  }
}

function makeClients(policy, options = {}) {
  const env = options.env || process.env;
  const adapter = options.adapter || loadAdapter(env);

  return {
    runGates: options.runGates || makeGateRunner(policy, options),
    triage: adapter && typeof adapter.triage === 'function' ? adapter.triage : null,
    final: adapter && typeof adapter.final === 'function' ? adapter.final : null,
    adapter_present: Boolean(adapter)
  };
}

module.exports = { makeClients, makeGateRunner, loadAdapter };
