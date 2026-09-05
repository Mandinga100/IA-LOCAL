#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { spawnSync } = require('child_process');
const { findProjectRoot, detectFormatter, resolveFormatterBin } = require('../lib/resolve-formatter');

const MAX_STDIN = 1024 * 1024;
const ADAPTIVE_THRESHOLD = 2;

function exec(command, args, cwd) {
  return spawnSync(command, args, {
    cwd: cwd || process.cwd(),
    encoding: 'utf8',
    env: process.env,
    timeout: 15000
  });
}

function log(msg) {
  process.stderr.write(`${msg}\n`);
}

function getAccumFile() {
  const raw = process.env.CLAUDE_SESSION_ID ||
    crypto.createHash('sha1').update(process.cwd()).digest('hex').slice(0, 12);
  const sessionId = raw.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64);
  return path.join(os.tmpdir(), `ecc-edited-${sessionId}.txt`);
}

function getChangedFileCount() {
  try {
    const accumPath = getAccumFile();
    if (!fs.existsSync(accumPath)) return 1;
    const content = fs.readFileSync(accumPath, 'utf8');
    const unique = new Set(content.split('\n').filter(Boolean));
    return unique.size;
  } catch {
    return 1;
  }
}

function isSmallChange() {
  return getChangedFileCount() <= ADAPTIVE_THRESHOLD;
}

function maybeRunQualityGate(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return;
  filePath = path.resolve(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const fix = String(process.env.ECC_QUALITY_GATE_FIX || '').toLowerCase() === 'true';
  const strict = String(process.env.ECC_QUALITY_GATE_STRICT || '').toLowerCase() === 'true';
  const small = isSmallChange();

  if (['.ts', '.tsx', '.js', '.jsx', '.json', '.md'].includes(ext)) {
    const projectRoot = findProjectRoot(path.dirname(filePath));
    const formatter = detectFormatter(projectRoot);

    if (formatter === 'biome') {
      if (['.ts', '.tsx', '.js', '.jsx'].includes(ext) && !small) return;
      const resolved = resolveFormatterBin(projectRoot, 'biome');
      if (!resolved) return;
      const args = [...resolved.prefix, 'check', filePath];
      if (fix) args.push('--write');
      const result = exec(resolved.bin, args, projectRoot);
      if (result.status !== 0 && strict) {
        log(`[QualityGate] Biome check failed for ${filePath}`);
      }
      return;
    }

    if (formatter === 'prettier') {
      const resolved = resolveFormatterBin(projectRoot, 'prettier');
      if (!resolved) return;
      const args = [...resolved.prefix, fix ? '--write' : '--check', filePath];
      const result = exec(resolved.bin, args, projectRoot);
      if (result.status !== 0 && strict) {
        log(`[QualityGate] Prettier check failed for ${filePath}`);
      }
      return;
    }
    return;
  }

  if (ext === '.go') {
    if (fix) {
      const r = exec('gofmt', ['-w', filePath]);
      if (r.status !== 0 && strict) log(`[QualityGate] gofmt failed for ${filePath}`);
    } else if (strict) {
      const r = exec('gofmt', ['-l', filePath]);
      if (r.status !== 0) log(`[QualityGate] gofmt check failed for ${filePath}`);
      else if (r.stdout && r.stdout.trim()) log(`[QualityGate] gofmt check failed for ${filePath}`);
    }
    return;
  }

  if (ext === '.py') {
    const args = ['format'];
    if (!fix) args.push('--check');
    args.push(filePath);
    const r = exec('ruff', args);
    if (r.status !== 0 && strict) log(`[QualityGate] Ruff check failed for ${filePath}`);
  }
}

function run(rawInput) {
  try {
    const input = JSON.parse(rawInput);
    const filePath = String(input.tool_input?.file_path || '');
    const changedCount = getChangedFileCount();

    if (changedCount <= ADAPTIVE_THRESHOLD) {
      log(`[QualityGate] Small change (${changedCount} files) — incremental validation`);
    } else {
      log(`[QualityGate] Multi-file change (${changedCount} files) — full quality gate`);
    }

    maybeRunQualityGate(filePath);
  } catch {
    // Ignore parse errors
  }
  return rawInput;
}

if (require.main === module) {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => {
    if (raw.length < MAX_STDIN) {
      const remaining = MAX_STDIN - raw.length;
      raw += chunk.substring(0, remaining);
    }
  });
  process.stdin.on('end', () => {
    const result = run(raw);
    process.stdout.write(result);
  });
}

module.exports = { run };
