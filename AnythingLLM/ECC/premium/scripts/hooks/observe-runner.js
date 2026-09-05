#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

const OBSERVE_RELATIVE_PATH = path.join('skills', 'continuous-learning-v2', 'hooks', 'observe.sh');
const DEFAULT_TIMEOUT_MS = 9000;
const TASK_METRICS_PREFIX = 'ecc-task-metrics-';

function getPluginRoot(options) {
  options = options || {};
  if (options.pluginRoot && String(options.pluginRoot).trim()) return String(options.pluginRoot).trim();
  if (process.env.CLAUDE_PLUGIN_ROOT && process.env.CLAUDE_PLUGIN_ROOT.trim()) return process.env.CLAUDE_PLUGIN_ROOT.trim();
  if (process.env.ECC_PLUGIN_ROOT && process.env.ECC_PLUGIN_ROOT.trim()) return process.env.ECC_PLUGIN_ROOT.trim();
  return path.resolve(__dirname, '..', '..');
}

function resolveTarget(rootDir, relPath) {
  var resolvedRoot = path.resolve(rootDir);
  var resolvedTarget = path.resolve(rootDir, relPath);
  if (resolvedTarget !== resolvedRoot && !resolvedTarget.startsWith(resolvedRoot + path.sep)) {
    throw new Error('Path traversal rejected: ' + relPath);
  }
  return resolvedTarget;
}

function toShellPath(filePath) {
  var normalized = String(filePath || '');
  if (process.platform !== 'win32') return normalized;
  return normalized.replace(/^([A-Za-z]):[\\/]/, function(_, driveLetter) {
    return '/' + driveLetter.toLowerCase() + '/';
  }).replace(/\\/g, '/');
}

function findShellBinary() {
  var candidates = [];
  if (process.env.BASH && process.env.BASH.trim()) candidates.push(process.env.BASH.trim());
  if (process.platform === 'win32') candidates.push('bash.exe', 'bash', 'sh');
  else candidates.push('bash', 'sh');
  for (var i = 0; i < candidates.length; i++) {
    var probe = spawnSync(candidates[i], ['-c', ':'], { stdio: 'ignore', windowsHide: true });
    if (!probe.error) return candidates[i];
  }
  return null;
}

function getPhaseFromHookId(hookId) {
  var prefix = String(hookId || process.env.ECC_HOOK_ID || '').split(':')[0];
  return prefix === 'pre' || prefix === 'post' ? prefix : null;
}

function getTimeoutMs() {
  var parsed = Number.parseInt(process.env.ECC_OBSERVE_RUNNER_TIMEOUT_MS || '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_TIMEOUT_MS;
}

function combineStderr(stderr, message) {
  var prefix = typeof stderr === 'string' && stderr.length > 0
    ? (stderr.endsWith('\n') ? stderr : stderr + '\n')
    : '';
  return prefix + message + '\n';
}

function sanitizeSessionId(sessionId) {
  if (!sessionId || typeof sessionId !== 'string') return null;
  var cleaned = sessionId.replace(/[^a-zA-Z0-9_-]/g, '_');
  return cleaned.length > 0 ? cleaned : null;
}

function isEfficientSession(sessionId) {
  if (!sessionId) return true;
  var metricsPath = path.join(os.tmpdir(), TASK_METRICS_PREFIX + sessionId + '.json');
  try {
    var metrics = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
    var agentsCount = (metrics.agents_invoked && metrics.agents_invoked.length) || 0;
    var compactCount = metrics.compaction_count || 0;
    var reAnalysis = metrics.re_analysis_count || 0;
    if (agentsCount > 5 && (metrics.files_modified_count || 0) <= 2) return false;
    if (compactCount > 3) return false;
    if (reAnalysis > 2) return false;
    return true;
  } catch (e) {
    return true;
  }
}

function run(raw, options) {
  options = options || {};
  var input = typeof raw === 'string' ? raw : String(raw || '');
  var phase = getPhaseFromHookId(options.hookId);
  if (!phase) {
    return { stderr: '[Hook] observe runner received an unsupported hook id; skipping observation', exitCode: 0 };
  }

  // Premium filter: skip learning if session is over-orchestrated
  var rawSessionId = process.env.CLAUDE_SESSION_ID || process.env.ECC_SESSION_ID || '';
  var sessionId = sanitizeSessionId(rawSessionId);
  if (sessionId && !isEfficientSession(sessionId)) {
    return { stderr: '[Premium Observe] Session excluded — over-orchestration detected; skipping continuous learning', exitCode: 0 };
  }

  var pluginRoot = getPluginRoot(options);
  var observePath;
  try {
    observePath = resolveTarget(pluginRoot, OBSERVE_RELATIVE_PATH);
  } catch (error) {
    return { stderr: '[Hook] observe runner path resolution failed: ' + error.message, exitCode: 0 };
  }

  if (!fs.existsSync(observePath)) {
    return { stderr: '[Hook] observe script not found: ' + observePath, exitCode: 0 };
  }

  var shell = findShellBinary();
  if (!shell) {
    return { stderr: '[Hook] shell runtime unavailable; skipping continuous-learning observation', exitCode: 0 };
  }

  var result = spawnSync(shell, [toShellPath(observePath), phase], {
    input: input,
    encoding: 'utf8',
    env: Object.assign({}, process.env, { CLAUDE_PLUGIN_ROOT: pluginRoot, ECC_PLUGIN_ROOT: pluginRoot }),
    cwd: process.cwd(),
    timeout: getTimeoutMs(),
    windowsHide: true
  });

  var output = { exitCode: Number.isInteger(result.status) ? result.status : 0 };
  if (typeof result.stdout === 'string' && result.stdout.length > 0) output.stdout = result.stdout;
  if (typeof result.stderr === 'string' && result.stderr.length > 0) output.stderr = result.stderr;
  if (result.error || result.signal || result.status === null) {
    var reason = result.error
      ? result.error.message
      : result.signal
        ? 'terminated by signal ' + result.signal
        : 'missing exit status';
    output.stderr = combineStderr(output.stderr, '[Hook] observe runner failed: ' + reason);
    output.exitCode = 0;
  }
  return output;
}

function emitHookResult(raw, output) {
  if (output && typeof output === 'object') {
    if (output.stderr) {
      process.stderr.write(String(output.stderr).endsWith('\n') ? String(output.stderr) : String(output.stderr) + '\n');
    }
    if (Object.prototype.hasOwnProperty.call(output, 'stdout')) {
      process.stdout.write(String(output.stdout || ''));
    } else if (!Number.isInteger(output.exitCode) || output.exitCode === 0) {
      process.stdout.write(raw);
    }
    return Number.isInteger(output.exitCode) ? output.exitCode : 0;
  }
  process.stdout.write(raw);
  return 0;
}

if (require.main === module) {
  var raw = '';
  try { raw = fs.readFileSync(0, 'utf8'); } catch (e) { raw = ''; }
  var output = run(raw, { hookId: process.argv[2] || process.env.ECC_HOOK_ID });
  process.exit(emitHookResult(raw, output));
}

module.exports = { OBSERVE_RELATIVE_PATH, findShellBinary, getPhaseFromHookId, run, toShellPath };
