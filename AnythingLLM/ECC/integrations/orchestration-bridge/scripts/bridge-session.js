#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — ciclo de vida de sesión.
 *
 * Un solo módulo con tres entradas (`init`, `flush`, `close`) en vez de tres
 * archivos que compartirían el 90 % del código. `hookify-config.json` apunta a
 * los envoltorios finos de al lado.
 *
 * Con el bridge apagado los tres son no-ops: ni abren ledger, ni escriben, ni
 * dejan rastro. El harness se comporta como si el bridge no existiera.
 */

'use strict';

const { getBridgeState } = require('./lib/bridge-config');
const ledger = require('./lib/ledger');

function parse(rawInput) {
  try {
    return JSON.parse(rawInput) || {};
  } catch {
    return {};
  }
}

function makeRunId(payload) {
  return payload.session_id || process.env.ECC_RUN_ID || 'unknown';
}

function passthrough(rawInput, note) {
  return note
    ? { stderr: `[Bridge] ${note}`, stdout: rawInput || '', exitCode: 0 }
    : { stdout: rawInput || '', exitCode: 0 };
}

/**
 * SessionStart: comprueba la activación y deja constancia de POR QUÉ el bridge
 * está on/off. Transparencia: el usuario ve en el log si actúa y bajo qué regla.
 */
function init(rawInput, options = {}) {
  const payload = parse(rawInput);
  const state = getBridgeState(options);

  if (!state.enabled) {
    // No se escribe en el ledger: apagado significa apagado, sin efectos.
    return passthrough(rawInput);
  }

  let policyOk = true;
  let policyError = null;
  try {
    require('./route-task').loadPolicy();
  } catch (err) {
    policyOk = false;
    policyError = err.message;
  }

  ledger.append({
    run_id: makeRunId(payload),
    step: 'session',
    event: 'bridge_enabled',
    source: state.source,
    reason: state.reason,
    scope: state.config ? state.config.scope || null : null,
    policy_loaded: policyOk,
    policy_error: policyError
  }, { ledgerPath: options.ledgerPath });

  return passthrough(rawInput, `orchestration bridge ACTIVO (${state.reason})`);
}

/** Stop: vuelca métricas del run. No-op si el bridge está apagado. */
function flush(rawInput, options = {}) {
  const payload = parse(rawInput);
  const state = getBridgeState(options);
  if (!state.enabled) return passthrough(rawInput);

  ledger.append({
    run_id: makeRunId(payload),
    step: 'session',
    event: 'metrics_flush',
    transcript_path: payload.transcript_path || null
  }, { ledgerPath: options.ledgerPath });

  return passthrough(rawInput);
}

/** SessionEnd: cierra el ledger con un resumen agregado del run. */
function close(rawInput, options = {}) {
  const payload = parse(rawInput);
  const state = getBridgeState(options);
  if (!state.enabled) return passthrough(rawInput);

  const runId = makeRunId(payload);
  const ledgerPath = options.ledgerPath || ledger.resolveLedgerPath();
  const entries = ledger.read(ledgerPath).filter(e => e.run_id === runId);
  const decisions = entries.filter(e => e.event === 'final');

  const summary = {
    run_id: runId,
    step: 'session',
    event: 'bridge_closed',
    steps_logged: entries.length,
    decisions: decisions.length,
    approved: decisions.filter(d => d.decision === 'approve').length,
    auto_fixed: decisions.filter(d => d.decision === 'auto_fix').length,
    human_review: decisions.filter(d => d.decision === 'human_review').length
  };

  ledger.append(summary, { ledgerPath });
  return passthrough(rawInput, `bridge cerrado: ${summary.decisions} decisiones, ` +
    `${summary.human_review} a revisión humana`);
}

module.exports = { init, flush, close };
