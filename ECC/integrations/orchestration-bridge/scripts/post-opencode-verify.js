#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — PostToolUse.
 *
 * Recoge el artefacto de OpenCode y lo pasa por el pipeline de verificación.
 * Si el bridge no está activado, pasa de largo sin hacer nada.
 *
 * Detecta el fallo por su cuenta (`exit_code` / `tool_response.success`): no
 * depende de que el runtime emita PostToolUseFailure, porque hoy no lo emite.
 */

'use strict';

const TAG = '[BridgeVerify]';
const { withBridgeEnabled } = require('./lib/bridge-config');

function parsePayload(rawInput) {
  try {
    return JSON.parse(rawInput);
  } catch {
    return null;
  }
}

function extractArtifact(payload) {
  const response = payload.tool_response || {};
  const artifact = response.artifact || payload.ecc_artifact || null;
  if (!artifact) return null;
  return {
    run_id: artifact.run_id || payload.session_id || 'unknown',
    task_type: artifact.task_type || null,
    model: artifact.model || null,
    files_touched: artifact.files_touched || 0,
    touches_paths: artifact.touches_paths || [],
    artifact_sha256: artifact.artifact_sha256 || null,
    diff: artifact.diff || '',
    exit_code: Number(response.exit_code ?? artifact.exit_code ?? 0),
    success: response.success !== false
  };
}

/** Fallo de generación: no hay nada que verificar, lo gestiona la rama de retry. */
function isFailure(artifact) {
  return artifact.exit_code !== 0 || artifact.success === false;
}

function run(rawInput) {
  const payload = parsePayload(rawInput);
  if (!payload) return { stdout: rawInput || '', exitCode: 0 };

  const artifact = extractArtifact(payload);
  if (!artifact) return { stdout: rawInput, exitCode: 0 };

  return withBridgeEnabled(rawInput, { task: artifact }, () => {
    if (isFailure(artifact)) {
      const { handleFailure } = require('./post-opencode-failure');
      const outcome = handleFailure(artifact);
      return {
        stderr: `${TAG} generación fallida (exit ${artifact.exit_code}) -> ${outcome.decision}`,
        stdout: rawInput,
        exitCode: 0
      };
    }

    const { loadPolicy } = require('./route-task');
    const { verify } = require('./verify-pipeline');
    const { makeClients } = require('./lib/verifier-clients');

    let verdict;
    try {
      const policy = loadPolicy();
      const clients = makeClients(policy);
      verdict = verify(artifact, { policy, ...clients });
    } catch (err) {
      // Error propio del bridge: no bloquea la sesión, pero se dice en voz alta.
      return {
        stderr: `${TAG} pipeline no ejecutado (${err.message}); sin veredicto`,
        stdout: rawInput,
        exitCode: 0
      };
    }

    const line = `${TAG} ${verdict.status} score=${verdict.aggregate_score}` +
      (verdict.human_review_required ? ' -> revisión humana' : '');

    return { stderr: line, stdout: rawInput, exitCode: 0 };
  });
}

module.exports = { run, extractArtifact, isFailure };
