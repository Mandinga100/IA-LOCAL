#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — pipeline de verificación.
 *
 * gates deterministas → triage → (condicional) validación final → decisión.
 *
 * Los clientes se INYECTAN (`runGates`, `triage`, `final`). El pipeline no sabe
 * de red ni de modelos: eso permite probarlo entero con stubs y es la razón de
 * que el flujo se pueda verificar sin gastar una sola llamada a un modelo.
 */

'use strict';

const { routeTask } = require('./route-task');
const { evaluate } = require('./decision');
const ledger = require('./lib/ledger');

/**
 * ¿Toca escalar a validación final? Lo decide la policy, no este código:
 * se enruta la fase `verify/final` y se mira si la regla resultante apunta al
 * modelo de validación. Así r5 se puede reescribir sin tocar el pipeline.
 */
function shouldEscalate(artifact, triage, policy) {
  const route = routeTask({
    phase: 'verify',
    stage: 'final',
    risk_class: triage ? triage.risk_class : undefined,
    touches_paths: artifact.touches_paths || [],
    needs_deep_review: triage ? triage.needs_deep_review === true : false
  }, { policy });

  return { escalate: route.model_key === 'claude_opus', route };
}

/**
 * @param {object} artifact  {run_id, diff, touches_paths, files_touched, task_type, exit_code}
 * @param {object} deps      {policy, runGates, triage, final, ledgerPath}
 * @returns {object} verdict  ecc.bridge.verdict/v1
 */
function verify(artifact, deps) {
  const { policy, runGates, triage: triageFn, final: finalFn, ledgerPath } = deps;
  const runId = artifact.run_id;
  const log = entry => ledger.append({ run_id: runId, ...entry }, { ledgerPath });

  // --- 1. gates deterministas (baratos y fiables; van primero, siempre)
  const gateResults = runGates(artifact);
  const preliminary = evaluate({ gateResults, triage: null, final: null }, policy);

  log({
    step: 'gates',
    event: 'deterministic_gates',
    results: gateResults,
    llm_invoked: false
  });

  // --- 2. si un gate bloqueante o el veto de seguridad falló, no se gasta LLM
  if (preliminary.security_veto || !gateHasPassed(gateResults, policy)) {
    const verdict = buildVerdict(artifact, preliminary, {
      triage: null,
      final: null,
      remedial: preliminary.security_veto
        ? 'resolver el hallazgo de seguridad antes de volver a generar'
        : 'los gates deterministas fallaron; corregir y re-ejecutar'
    });
    log({ step: 'decision', event: 'final', ...summary(verdict) });
    return verdict;
  }

  // --- 3. triage. Sin verificador enchufado no se inventa un veredicto:
  // los gates pasaron, pero nadie ha mirado el diff. Eso lo mira una persona.
  if (typeof triageFn !== 'function') {
    const noVerifier = { ...preliminary, decision: 'human_review', human_review_required: true };
    const verdict = buildVerdict(artifact, noVerifier, {
      triage: null,
      final: null,
      remedial: 'gates verdes pero sin verificador de triage configurado ' +
        '(ECC_BRIDGE_VERIFIER); nadie ha revisado el diff'
    });
    log({ step: 'decision', event: 'final', ...summary(verdict), verifier_missing: true });
    return verdict;
  }

  const triage = triageFn(artifact);
  log({
    step: 'triage',
    event: 'verification',
    engine: 'claude',
    model: triage.model || null,
    risk_class: triage.risk_class,
    needs_deep_review: triage.needs_deep_review === true,
    aggregate_score: triage.aggregate_score,
    checks: triage.checks || []
  });

  // --- 4. validación final, sólo si la policy lo pide
  const { escalate, route } = shouldEscalate(artifact, triage, policy);
  let final = null;

  if (escalate) {
    if (typeof finalFn !== 'function') {
      // Sin verificador final disponible y la policy lo exige: decide un humano.
      const forced = { ...evaluate({ gateResults, triage, final: null }, policy) };
      forced.decision = 'human_review';
      forced.human_review_required = true;
      const verdict = buildVerdict(artifact, forced, {
        triage,
        final: null,
        remedial: 'la policy exige validación final y no hay verificador disponible'
      });
      log({ step: 'decision', event: 'final', ...summary(verdict), escalation_unavailable: true });
      return verdict;
    }

    final = finalFn(artifact, triage);
    log({
      step: 'final',
      event: 'verification',
      engine: 'claude',
      model: final.model || route.model_id,
      rule_id: route.rule_id,
      aggregate_score: final.aggregate_score,
      verdict: final.verdict || null
    });
  }

  // --- 5. decisión
  const result = evaluate({ gateResults, checks: triage.checks || [], triage, final }, policy);
  const verdict = buildVerdict(artifact, result, {
    triage,
    final,
    remedial: remedialFor(result, triage, final)
  });

  log({ step: 'decision', event: 'final', ...summary(verdict) });
  return verdict;
}

function gateHasPassed(gateResults, policy) {
  const { hasBlockingFailure } = require('./decision');
  return !hasBlockingFailure(gateResults, policy);
}

function remedialFor(result, triage, final) {
  if (result.decision === 'approve') return null;
  if (final && final.verdict) return final.verdict;
  const worst = (triage.checks || [])
    .filter(c => c.status !== 'pass')
    .sort((a, b) => (a.score ?? 1) - (b.score ?? 1))[0];
  return worst ? worst.recommendation || `revisar ${worst.name}` : 'revisar el diff';
}

function buildVerdict(artifact, result, { triage, final, remedial }) {
  return {
    schema: 'ecc.bridge.verdict/v1',
    run_id: artifact.run_id,
    artifact_sha256: artifact.artifact_sha256 || null,
    status: result.decision,
    aggregate_score: result.aggregate_score,
    threshold: result.threshold,
    security_veto: result.security_veto,
    llm_invoked: result.llm_invoked,
    escalated_to_opus: Boolean(final),
    models_used: {
      generation: artifact.model || null,
      triage: triage ? triage.model || null : null,
      final: final ? final.model || null : null
    },
    checks: triage ? triage.checks || [] : [],
    remedial_action: result.decision === 'approve' ? null : remedial,
    human_review_required: result.human_review_required
  };
}

function summary(verdict) {
  return {
    aggregate_score: verdict.aggregate_score,
    threshold: verdict.threshold,
    security_veto: verdict.security_veto,
    decision: verdict.status,
    human_review_required: verdict.human_review_required,
    models_used: verdict.models_used
  };
}

module.exports = { verify, shouldEscalate, buildVerdict };
