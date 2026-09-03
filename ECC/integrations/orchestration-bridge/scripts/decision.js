#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — agregación de gates y matriz de decisión.
 *
 * Puro y sin efectos. La matriz vive en model-route.yaml en forma estructurada;
 * aquí se interpreta sin evaluar ninguna expresión: esto decide si algo se
 * mergea, y una condición evaluable es una condición inyectable.
 */

'use strict';

const GATE_VETO_SCORE = 0;

/**
 * ¿Algún gate con `veto: true` falló?
 * El veto es de configuración (model-route.yaml `gates[].veto`), no del payload.
 */
function hasSecurityVeto(gateResults = {}, policy = {}) {
  const vetoGates = (policy.gates || [])
    .filter(g => g.veto === true)
    .map(g => g.id);
  const ids = vetoGates.length > 0 ? vetoGates : ['security'];
  return ids.some(id => gateResults[id] === 'fail');
}

/** ¿Falló algún gate marcado `blocking`? Si sí, no se invoca ningún LLM. */
function hasBlockingFailure(gateResults = {}, policy = {}) {
  const blocking = (policy.gates || [])
    .filter(g => g.blocking === true)
    .map(g => g.id);
  const ids = blocking.length > 0 ? blocking : ['tests', 'security'];
  return ids.some(id => gateResults[id] === 'fail');
}

function countFails(gateResults = {}, checks = []) {
  const gateFails = Object.values(gateResults).filter(v => v === 'fail').length;
  const checkFails = checks.filter(c => c && c.status === 'fail').length;
  return gateFails + checkFails;
}

/**
 * Score agregado.
 *   veto de seguridad        -> 0
 *   corrió validación final  -> score de la final
 *   sólo corrió triage       -> score del triage
 * Los gates deterministas son precondición, no sumandos.
 */
function aggregateScore({ securityVeto, triage, final }) {
  if (securityVeto) return GATE_VETO_SCORE;
  if (final && typeof final.aggregate_score === 'number') return final.aggregate_score;
  if (triage && typeof triage.aggregate_score === 'number') return triage.aggregate_score;
  return GATE_VETO_SCORE;
}

function matchesDecisionRule(rule, ctx) {
  const cond = rule.if || {};
  if (cond.always === true) return true;
  if (cond.security_veto === true && !ctx.securityVeto) return false;
  if (typeof cond.min_score === 'number' && !(ctx.score >= cond.min_score)) return false;
  if (typeof cond.max_fails === 'number' && !(ctx.fails <= cond.max_fails)) return false;
  return true;
}

/**
 * Aplica la matriz de decisión.
 * @returns {{decision, rule_id, reason, human_review_required}}
 */
function decide(ctx, policy = {}) {
  const matrix = Array.isArray(policy.decision_matrix) && policy.decision_matrix.length > 0
    ? policy.decision_matrix
    : [
        { id: 'd1-security-veto', if: { security_veto: true }, then: 'human_review' },
        { id: 'd2-approve', if: { min_score: 0.85, max_fails: 0 }, then: 'approve' },
        { id: 'd3-auto-fix', if: { min_score: 0.7 }, then: 'auto_fix' },
        { id: 'd4-human', if: { always: true }, then: 'human_review' }
      ];

  const rule = matrix.find(r => matchesDecisionRule(r, ctx));
  const decision = rule ? rule.then : 'human_review';

  return {
    decision,
    rule_id: rule ? rule.id : null,
    reason: rule ? rule.reason || null : 'ninguna regla de decisión casó',
    human_review_required: decision === 'human_review'
  };
}

/**
 * Evaluación completa de un artefacto verificado.
 * `triage` y `final` son los veredictos de los modelos (o null si no corrieron).
 */
function evaluate({ gateResults = {}, checks = [], triage = null, final = null }, policy = {}) {
  const securityVeto = hasSecurityVeto(gateResults, policy);
  const blocked = securityVeto || hasBlockingFailure(gateResults, policy);
  const llmInvoked = !blocked && triage !== null;

  const effectiveTriage = blocked ? null : triage;
  const effectiveFinal = blocked ? null : final;

  const score = aggregateScore({
    securityVeto: blocked,
    triage: effectiveTriage,
    final: effectiveFinal
  });
  const fails = countFails(gateResults, checks);

  const outcome = decide({ securityVeto, score, fails }, policy);
  const defaults = policy.defaults || {};

  return {
    security_veto: securityVeto,
    llm_invoked: llmInvoked,
    aggregate_score: score,
    threshold: defaults.score_threshold ?? 0.7,
    auto_approve_threshold: defaults.auto_approve_threshold ?? 0.85,
    fails,
    escalated_to_opus: Boolean(effectiveFinal),
    decision: outcome.decision,
    decision_rule_id: outcome.rule_id,
    reason: outcome.reason,
    human_review_required: outcome.human_review_required
  };
}

module.exports = {
  evaluate,
  decide,
  aggregateScore,
  countFails,
  hasSecurityVeto,
  hasBlockingFailure
};
