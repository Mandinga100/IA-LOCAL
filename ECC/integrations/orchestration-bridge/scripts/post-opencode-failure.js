#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — política de reintentos.
 *
 * Registrado en PostToolUseFailure por compatibilidad futura, pero la ruta
 * real de entrada es `post-opencode-verify.js`, que detecta el fallo por su
 * cuenta. Ambas llaman a `handleFailure`.
 *
 * La política no reintenta a ciegas: si se agotan los intentos, escala a un
 * modelo de diagnóstico en vez de repetir el mismo prompt con otra semilla.
 */

'use strict';

const TAG = '[BridgeRetry]';
const { withBridgeEnabled } = require('./lib/bridge-config');
const ledger = require('./lib/ledger');

function handleFailure(artifact, options = {}) {
  const { routeTask, loadPolicy } = require('./route-task');

  let route;
  try {
    const policy = options.policy || loadPolicy();
    route = routeTask({ task_type: artifact.task_type }, { policy });
  } catch {
    route = { max_retries: 0, fallback: null, on_fallback_exhausted: 'human_review' };
  }

  const used = Number(artifact.retries_used || 0);
  const outcome = used < route.max_retries
    ? {
        decision: 'retry',
        retries_used: used + 1,
        instruction: `re-ejecutar con el error concreto en el prompt: ${artifact.error || 'sin detalle'}`
      }
    : {
        decision: route.fallback ? 'escalate' : route.on_fallback_exhausted,
        escalated_to: route.fallback_model_id || null,
        reason: 'reintentos agotados; reintentar sin contexto nuevo sólo quema cuota'
      };

  ledger.append({
    run_id: artifact.run_id,
    step: 'generate',
    event: 'artifact_failed',
    engine: 'opencode',
    model: artifact.model || null,
    exit_code: artifact.exit_code,
    error: artifact.error || null,
    retries_used: used,
    max_retries: route.max_retries,
    ...outcome
  }, { ledgerPath: options.ledgerPath });

  return outcome;
}

function run(rawInput) {
  let payload;
  try {
    payload = JSON.parse(rawInput);
  } catch {
    return { stdout: rawInput || '', exitCode: 0 };
  }

  const artifact = (payload.tool_response && payload.tool_response.artifact) ||
    payload.ecc_artifact;
  if (!artifact) return { stdout: rawInput, exitCode: 0 };

  return withBridgeEnabled(rawInput, { task: artifact }, () => {
    const outcome = handleFailure(artifact);
    return { stderr: `${TAG} ${outcome.decision}`, stdout: rawInput, exitCode: 0 };
  });
}

module.exports = { run, handleFailure };
