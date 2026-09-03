#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — PreToolUse gate.
 *
 * Corre antes de invocar OpenCode/Antigravity. Sin red. Debe ser rápido
 * (<200 ms) porque es blocking.
 *
 * Política de fallo, deliberadamente asimétrica:
 *   - Antigravity: FALLA CERRADO. Si la policy no carga, se deniega. El cerrojo
 *     de entorno (ECC_ALLOW_ANTIGRAVITY) no depende del YAML, así que un
 *     archivo roto nunca puede abrir esa puerta.
 *   - Todo lo demás: FALLA ABIERTO (exit 0 + aviso en stderr), según la regla
 *     del repo de que un hook no bloquea la sesión por un error propio.
 *
 * Exportado como run(rawInput) para que run-with-flags.js lo cargue sin spawn.
 *
 * SOBRE EL OPT-IN DEL BRIDGE: este gate es el único componente que NO se apaga
 * con ECC_BRIDGE=off, y es deliberado. Sólo reacciona a invocaciones de
 * `open-code.sh` (ver isBridgeInvocation); todo lo demás pasa intacto. Si
 * alguien ejecuta el script del bridge, está usando el bridge para ese comando
 * — y desactivar una comprobación de seguridad justo cuando el usuario invoca
 * la herramienta que protege sería el peor momento posible. Apagar el bridge
 * quita el flujo, no los cerrojos del flujo.
 */

'use strict';

const TAG = '[BridgeGate]';
const BRIDGE_MARKER = 'open-code.sh';

function parsePayload(rawInput) {
  if (!rawInput || typeof rawInput !== 'string') return null;
  try {
    return JSON.parse(rawInput);
  } catch {
    return null;
  }
}

function getCommand(payload) {
  const input = payload && payload.tool_input;
  return input && typeof input.command === 'string' ? input.command : '';
}

/** Sólo opinamos sobre invocaciones al bridge. El resto pasa sin tocar. */
function isBridgeInvocation(command) {
  return command.includes(BRIDGE_MARKER);
}

function extractFlag(command, flag) {
  const re = new RegExp(`${flag}\\s+([^\\s]+)`);
  const m = command.match(re);
  return m ? m[1] : null;
}

function extractSubcommand(command) {
  const m = command.match(new RegExp(`${BRIDGE_MARKER}\\s+([a-z-]+)`));
  return m ? m[1] : null;
}

function deny(reason, detail) {
  return {
    allowed: false,
    decision: 'deny',
    reason,
    detail: detail || null
  };
}

function allow(extra = {}) {
  return { allowed: true, decision: 'proceed', reason: null, ...extra };
}

/**
 * Decide sobre una invocación ya parseada. Puro y testeable.
 * @param {{command:string, task:object}} invocation
 * @param {{env:object, policy:object|null, policyError:Error|null}} ctx
 */
function evaluateInvocation(invocation, ctx) {
  const env = ctx.env || {};
  const { command, task = {} } = invocation;
  const policy = ctx.policy || null;

  const wantsAntigravity =
    task.engine === 'antigravity' ||
    task.task_type === 'scaffold_prototype' ||
    /--engine\s+antigravity/.test(command);

  // --- cerrojo 1: entorno. No depende de la policy, así que sigue vigente
  // aunque el YAML esté roto.
  if (wantsAntigravity) {
    if (String(env.ECC_ALLOW_ANTIGRAVITY || '0') !== '1') {
      return {
        ...deny(
          'antigravity_locked',
          'ECC_ALLOW_ANTIGRAVITY no está a 1; el flag experimental del payload no basta'
        ),
        requested_engine: 'antigravity',
        engine_applied: 'opencode',
        fallback_applied: 'oc_bulk'
      };
    }
    // --- cerrojo 2: flag explícito en la tarea.
    if (task.experimental !== true) {
      return {
        ...deny('antigravity_not_experimental', 'falta experimental=true en la tarea'),
        requested_engine: 'antigravity',
        engine_applied: 'opencode',
        fallback_applied: 'oc_bulk'
      };
    }
  }

  // A partir de aquí necesitamos la policy. Si no cargó y no era Antigravity,
  // fallamos abierto: bloquear la sesión por un YAML roto es peor que dejar
  // pasar una generación que los gates de PostToolUse van a verificar igual.
  if (!policy) {
    return allow({
      degraded: true,
      warning: `policy no disponible (${ctx.policyError ? ctx.policyError.code : 'desconocido'}); gate en modo permisivo`
    });
  }

  const security = policy.security || {};

  // --- auth
  const tokenVars = security.token_env || ['ECC_OPENCODE_TOKEN'];
  const relevantToken = wantsAntigravity ? 'ECC_ANTIGRAVITY_TOKEN' : 'ECC_OPENCODE_TOKEN';
  if (security.require_auth !== false && tokenVars.includes(relevantToken)) {
    if (!env[relevantToken]) {
      return deny('missing_auth', `falta $${relevantToken} en el entorno`);
    }
  }

  // --- allowlist de subcomandos
  const sub = extractSubcommand(command);
  const allowlist = security.command_allowlist || ['generate', 'refactor', 'script', 'scaffold', 'models'];
  if (sub && !allowlist.includes(sub)) {
    return deny('command_not_allowlisted', `subcomando '${sub}' fuera de la allowlist`);
  }

  // --- cost cap
  const estimated = Number(task.estimated_cost_usd);
  const cap = Number(task.cost_cap_usd ?? (policy.defaults || {}).cost_cap_usd);
  if (Number.isFinite(estimated) && Number.isFinite(cap) && estimated > cap) {
    return allow({
      decision: 'proceed_downgraded',
      cost_capped: true,
      estimated_cost_usd: estimated,
      cost_cap_usd: cap,
      confidence_delta: 'negative',
      warning: `coste estimado ${estimated} > cap ${cap}; se degrada al fallback barato`
    });
  }

  return allow();
}

function loadPolicySafely() {
  try {
    const { loadPolicy } = require('./route-task');
    return { policy: loadPolicy(), policyError: null };
  } catch (err) {
    return { policy: null, policyError: err };
  }
}

function run(rawInput) {
  const payload = parsePayload(rawInput);
  if (!payload) return { stdout: rawInput || '', exitCode: 0 };

  const command = getCommand(payload);
  if (!isBridgeInvocation(command)) return { stdout: rawInput, exitCode: 0 };

  const task = payload.ecc_task || {
    task_type: extractFlag(command, '--task-type'),
    experimental: /--experimental(\s|$)/.test(command)
  };

  const { policy, policyError } = loadPolicySafely();
  const verdict = evaluateInvocation({ command, task }, { env: process.env, policy, policyError });

  if (!verdict.allowed) {
    return {
      stderr: `${TAG} denegado (${verdict.reason}): ${verdict.detail || ''}`,
      exitCode: 2
    };
  }

  if (verdict.warning) {
    return { stderr: `${TAG} ${verdict.warning}`, stdout: rawInput, exitCode: 0 };
  }

  return { stdout: rawInput, exitCode: 0 };
}

module.exports = { run, evaluateInvocation, extractSubcommand, extractFlag };
