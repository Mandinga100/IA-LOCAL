#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — activación (opt-in).
 *
 * El bridge es una capacidad OPCIONAL del harness. Por defecto está APAGADO:
 * si nadie lo activa, todos sus hooks pasan de largo y la sesión se comporta
 * exactamente igual que sin el bridge instalado.
 *
 * Precedencia, de más fuerte a más débil:
 *   1. ECC_BRIDGE=on|off        — override de sesión; gana siempre
 *   2. .claude/bridge.json      — opt-in del proyecto {enabled, scope, ...}
 *   3. apagado                  — default
 *
 * `scope` acota además POR TAREA: si está presente, la tarea sólo entra en el
 * bridge cuando alguna de sus rutas casa. Fuera del scope, apagado.
 *
 * Todo devuelve un motivo legible: el usuario tiene que poder saber por qué el
 * bridge actuó o dejó de actuar sin leer el código.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const CONFIG_RELATIVE = path.join('.claude', 'bridge.json');
const ON = new Set(['1', 'on', 'true', 'yes', 'enabled']);
const OFF = new Set(['0', 'off', 'false', 'no', 'disabled']);

function readProjectConfig(cwd) {
  const file = path.join(cwd, CONFIG_RELATIVE);
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
    return { config: parsed && typeof parsed === 'object' ? parsed : null, file };
  } catch (err) {
    if (err.code === 'ENOENT') return { config: null, file };
    // Un bridge.json corrupto NO activa el bridge: el default sigue siendo off.
    return { config: null, file, error: err };
  }
}

function inScope(scope, touchedPaths) {
  if (!Array.isArray(scope) || scope.length === 0) return true;
  if (!Array.isArray(touchedPaths) || touchedPaths.length === 0) return false;
  const { matchesAnyGlob } = require('../route-task');
  return matchesAnyGlob(touchedPaths, scope);
}

/**
 * @param {{cwd?:string, env?:object, task?:object}} options
 * @returns {{enabled:boolean, source:string, reason:string, config:object|null}}
 */
function getBridgeState(options = {}) {
  const env = options.env || process.env;
  const cwd = options.cwd || process.cwd();
  const task = options.task || null;

  const raw = String(env.ECC_BRIDGE ?? '').trim().toLowerCase();
  if (OFF.has(raw)) {
    return { enabled: false, source: 'env', reason: 'ECC_BRIDGE=off', config: null };
  }

  const { config, file, error } = readProjectConfig(cwd);

  if (ON.has(raw)) {
    // El override de sesión activa, pero el scope del proyecto sigue acotando.
    if (config && task && !inScope(config.scope, task.touches_paths)) {
      return {
        enabled: false,
        source: 'scope',
        reason: `ECC_BRIDGE=on pero la tarea queda fuera de scope en ${CONFIG_RELATIVE}`,
        config
      };
    }
    return { enabled: true, source: 'env', reason: 'ECC_BRIDGE=on', config };
  }

  if (error) {
    return {
      enabled: false,
      source: 'default',
      reason: `${CONFIG_RELATIVE} ilegible (${error.message}); el bridge sigue apagado`,
      config: null
    };
  }

  if (!config) {
    return {
      enabled: false,
      source: 'default',
      reason: `sin ${CONFIG_RELATIVE}; el bridge es opt-in y está apagado`,
      config: null
    };
  }

  if (config.enabled !== true) {
    return {
      enabled: false,
      source: 'project',
      reason: `${file} tiene enabled != true`,
      config
    };
  }

  if (task && !inScope(config.scope, task.touches_paths)) {
    return {
      enabled: false,
      source: 'scope',
      reason: 'la tarea queda fuera del scope declarado en bridge.json',
      config
    };
  }

  return { enabled: true, source: 'project', reason: `activado en ${file}`, config };
}

function isBridgeEnabled(options) {
  return getBridgeState(options).enabled;
}

/**
 * Envoltorio para hooks: si el bridge está apagado, devuelve el passthrough
 * que el harness espera (stdin intacto, exit 0) y no ejecuta nada más.
 */
function withBridgeEnabled(rawInput, options, handler) {
  const state = getBridgeState(options);
  if (!state.enabled) {
    return { stdout: rawInput || '', exitCode: 0, _bridge: { skipped: true, ...state } };
  }
  return handler(state);
}

module.exports = {
  getBridgeState,
  isBridgeEnabled,
  withBridgeEnabled,
  inScope,
  CONFIG_RELATIVE
};
