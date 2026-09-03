#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — resolución de ruta de modelo.
 *
 * Puro: sin red, sin escritura. Lee model-route.yaml y devuelve la regla que
 * casa con el contexto de la tarea. Se usa desde pre-opencode-gate.js y desde
 * open-code.sh (via CLI).
 *
 * CLI:
 *   node route-task.js --task-type bulk_codegen [--field model_id]
 *   node route-task.js --task-type refactor --json
 */

'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_POLICY = path.join(__dirname, '..', 'model-route.yaml');

/**
 * js-yaml no está en `dependencies` — llega transitivo y puede desaparecer al
 * podar el árbol. Cargarlo perezosamente y con error explícito evita que un
 * hook reviente con un MODULE_NOT_FOUND opaco.
 */
function loadYaml(source, file) {
  let yaml;
  try {
    yaml = require('js-yaml');
  } catch {
    const err = new Error(
      'js-yaml no disponible: añádelo a dependencies de package.json'
    );
    err.code = 'ECC_NO_YAML';
    throw err;
  }
  try {
    return yaml.load(source);
  } catch (cause) {
    const err = new Error(`model-route.yaml ilegible (${file}): ${cause.message}`);
    err.code = 'ECC_BAD_POLICY';
    throw err;
  }
}

function loadPolicy(policyPath = process.env.ECC_BRIDGE_POLICY || DEFAULT_POLICY) {
  const resolved = path.resolve(policyPath);
  const raw = fs.readFileSync(resolved, 'utf8');
  const policy = loadYaml(raw, resolved);
  if (!policy || !Array.isArray(policy.rules) || policy.rules.length === 0) {
    const err = new Error(`model-route.yaml sin reglas: ${resolved}`);
    err.code = 'ECC_BAD_POLICY';
    throw err;
  }
  return policy;
}

/** Expande `${VAR}` contra el entorno. Sin var definida devuelve el literal. */
function expandEnv(value, env = process.env) {
  if (typeof value !== 'string') return value;
  return value.replace(/\$\{([A-Z0-9_]+)\}/g, (literal, name) =>
    env[name] ? env[name] : literal
  );
}

/** Glob mínimo: `**` cruza separadores, `*` no. Sin clases ni alternancias. */
function globToRegExp(glob) {
  const escapeLiteral = ch => ch.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  const source = String(glob);
  let body = '';

  // Tokenizado en vez de sustitución con centinela: un placeholder puede
  // colisionar con el propio contenido del glob.
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i];
    if (ch === '*') {
      if (source[i + 1] === '*') {
        body += '.*';
        i += 1;
      } else {
        body += '[^/]*';
      }
    } else if (ch === '?') {
      body += '[^/]';
    } else {
      body += escapeLiteral(ch);
    }
  }

  return new RegExp(`^${body}$`);
}

function matchesAnyGlob(candidatePaths, globs) {
  if (!Array.isArray(candidatePaths) || !Array.isArray(globs)) return false;
  const patterns = globs.map(globToRegExp);
  return candidatePaths.some(p => {
    const normalized = String(p).split(path.sep).join('/');
    return patterns.some(re => re.test(normalized));
  });
}

/** Compara `'>= 5'`, `'< 10'`, `'== 3'` o un número suelto contra un valor. */
function matchesNumeric(actual, expression) {
  if (typeof expression === 'number') return Number(actual) === expression;
  const m = String(expression).trim().match(/^(>=|<=|==|>|<)?\s*(-?\d+(?:\.\d+)?)$/);
  if (!m) return false;
  const [, op = '==', rawBound] = m;
  const bound = Number(rawBound);
  const value = Number(actual);
  if (!Number.isFinite(value)) return false;
  switch (op) {
    case '>=': return value >= bound;
    case '<=': return value <= bound;
    case '>': return value > bound;
    case '<': return value < bound;
    default: return value === bound;
  }
}

function matchesScalar(actual, expected) {
  if (Array.isArray(expected)) return expected.includes(actual);
  return actual === expected;
}

/**
 * Evalúa el bloque `when` de una regla contra el contexto de la tarea.
 * Las claves de `when` son AND entre sí; `any_of` es OR interno.
 */
function matchesWhen(when, task, env = process.env) {
  if (!when || typeof when !== 'object') return false;
  if (when.always === true) return true;

  for (const [key, expected] of Object.entries(when)) {
    if (key === 'always') continue;

    if (key === 'any_of') {
      const alternatives = Object.entries(expected || {});
      const anyMatched = alternatives.some(([altKey, altExpected]) =>
        matchesWhen({ [altKey]: altExpected }, task, env)
      );
      if (!anyMatched) return false;
      continue;
    }

    if (key.startsWith('env.')) {
      if (String(env[key.slice(4)] ?? '') !== String(expected)) return false;
      continue;
    }

    if (key === 'touches_paths') {
      if (!matchesAnyGlob(task.touches_paths, expected)) return false;
      continue;
    }

    if (key === 'triage_says') {
      // `triage_says: needs_deep_review` <- task.needs_deep_review === true
      if (task[expected] !== true) return false;
      continue;
    }

    if (key === 'files_touched') {
      if (!matchesNumeric(task.files_touched, expected)) return false;
      continue;
    }

    if (!matchesScalar(task[key], expected)) return false;
  }

  return true;
}

/**
 * Resuelve la ruta para una tarea.
 * @returns {{rule_id, engine, model_key, model_id, model_verified, fallback,
 *            fallback_model_id, max_retries, timeout_s, cost_cap_usd,
 *            requires_flag, sandbox, write_scope, why}}
 */
function routeTask(task = {}, options = {}) {
  const policy = options.policy || loadPolicy(options.policyPath);
  const env = options.env || process.env;
  const defaults = policy.defaults || {};
  const models = policy.models || {};

  const rule = policy.rules.find(r => matchesWhen(r.when, task, env));
  if (!rule) {
    const err = new Error('ninguna regla casó y falta la regla de cierre r8-default');
    err.code = 'ECC_NO_RULE';
    throw err;
  }

  const model = models[rule.use] || {};
  const fallbackKey = rule.fallback || null;
  const fallbackModel = fallbackKey ? models[fallbackKey] : null;

  return {
    rule_id: rule.id,
    engine: model.engine || 'unknown',
    model_key: rule.use,
    model_id: expandEnv(model.id, env),
    model_verified: model.verified === true,
    fallback: fallbackKey,
    fallback_model_id: fallbackModel ? expandEnv(fallbackModel.id, env) : null,
    max_retries: rule.max_retries ?? defaults.max_retries ?? 1,
    timeout_s: rule.timeout_s ?? defaults.timeout_s ?? 300,
    cost_cap_usd: rule.cost_cap_usd ?? defaults.cost_cap_usd ?? 0.5,
    requires_flag: model.requires_flag || null,
    sandbox: rule.sandbox === true,
    write_scope: rule.write_scope || null,
    on_fallback_exhausted: rule.on_fallback_exhausted || 'human_review',
    why: rule.why || null
  };
}

// --- CLI --------------------------------------------------------------------

function parseArgv(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2).replace(/-/g, '_');
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function main(argv) {
  const args = parseArgv(argv);
  const task = {
    task_type: args.task_type,
    phase: args.phase,
    stage: args.stage,
    risk_class: args.risk_class,
    files_touched: args.files_touched ? Number(args.files_touched) : 0,
    experimental: args.experimental === true || args.experimental === 'true',
    touches_paths: args.touches_paths ? String(args.touches_paths).split(',') : []
  };

  const route = routeTask(task, { policyPath: args.policy });

  if (args.json) {
    process.stdout.write(`${JSON.stringify(route, null, 2)}\n`);
  } else if (args.field) {
    process.stdout.write(`${route[args.field] ?? ''}\n`);
  } else {
    process.stdout.write(`${route.model_id}\n`);
  }
}

if (require.main === module) {
  try {
    main(process.argv.slice(2));
  } catch (err) {
    process.stderr.write(`[RouteTask] ${err.message}\n`);
    process.exit(1);
  }
}

module.exports = {
  loadPolicy,
  routeTask,
  matchesWhen,
  matchesNumeric,
  matchesAnyGlob,
  globToRegExp,
  expandEnv
};
