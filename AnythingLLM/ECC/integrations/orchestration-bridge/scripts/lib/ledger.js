#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — escritura del ledger de auditoría.
 *
 * Una línea JSON por evento. Nunca lanza: un fallo de escritura no puede
 * tumbar un hook (regla del repo: exit 0 ante error propio).
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const SECRET_KEY = /(token|secret|password|authorization|_key$|apikey)/i;
const REDACTED = '[redacted]';

function resolveLedgerPath(env = process.env) {
  const raw = env.ECC_BRIDGE_LEDGER || path.join('~', '.claude', 'metrics', 'run-ledger.jsonl');
  return raw.startsWith('~') ? path.join(os.homedir(), raw.slice(1)) : path.resolve(raw);
}

/** Redacta claves sensibles en profundidad antes de que toquen el disco. */
function redact(value) {
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === 'object') {
    const out = {};
    for (const [key, inner] of Object.entries(value)) {
      out[key] = SECRET_KEY.test(key) ? REDACTED : redact(inner);
    }
    return out;
  }
  return value;
}

function append(entry, options = {}) {
  const env = options.env || process.env;
  const file = options.ledgerPath || resolveLedgerPath(env);
  const record = redact({ ts: options.ts || new Date().toISOString(), ...entry });

  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.appendFileSync(file, `${JSON.stringify(record)}\n`, 'utf8');
    return { written: true, file, record };
  } catch (err) {
    return { written: false, file, record, error: err.message };
  }
}

function read(ledgerPath) {
  try {
    return fs
      .readFileSync(ledgerPath, 'utf8')
      .split('\n')
      .filter(Boolean)
      .map(line => JSON.parse(line));
  } catch {
    return [];
  }
}

module.exports = { append, read, redact, resolveLedgerPath };
