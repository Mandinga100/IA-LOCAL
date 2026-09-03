#!/usr/bin/env node
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { sanitizeSessionId, readBridge, writeBridgeAtomic } = require('../lib/session-bridge');
const { getClaudeDir } = require('../lib/utils');

const MAX_STDIN = 1024 * 1024;
const MAX_FILES_TRACKED = 200;
const RECENT_TOOLS_SIZE = 5;
const HASH_INPUT_LIMIT = 2048;
const WARNING_CACHE_PREFIX = 'ecc-metrics-cost-warnings-';
const TASK_METRICS_PREFIX = 'ecc-task-metrics-';
const RE_ANALYSIS_WINDOW_MS = 120000;

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function stableStringify(value, depth) {
  depth = depth || 0;
  if (depth > 4) return '[depth-limit]';
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) {
    return `[${value.map(function(item) { return stableStringify(item, depth + 1); }).join(',')}]`;
  }
  return '{' + Object.keys(value).sort().map(function(key) {
    return JSON.stringify(key) + ':' + stableStringify(value[key], depth + 1);
  }).join(',') + '}';
}

function hashToolCall(toolName, toolInput) {
  var name = String(toolName || '');
  var key = '';
  if (name === 'Bash') {
    key = String(toolInput && toolInput.command || '').slice(0, 160);
  } else if (/^(Edit|MultiEdit|Write|NotebookEdit)$/.test(name)) {
    key = crypto.createHash('sha256').update(stableStringify({
      file_path: toolInput && toolInput.file_path,
      old_string: toolInput && toolInput.old_string,
      new_string: toolInput && toolInput.new_string,
      content: toolInput && toolInput.content,
      edits: toolInput && toolInput.edits
    })).digest('hex');
  } else if (toolInput && toolInput.file_path) {
    key = String(toolInput.file_path);
  } else {
    key = stableStringify(toolInput || {}).slice(0, HASH_INPUT_LIMIT);
  }
  return crypto.createHash('sha256').update(name + ':' + key).digest('hex').slice(0, 8);
}

function extractFilePaths(toolName, toolInput) {
  var paths = [];
  if (!toolInput || typeof toolInput !== 'object') return paths;
  var fp = toolInput.file_path;
  if (fp && typeof fp === 'string') paths.push(fp);
  var edits = toolInput.edits;
  if (Array.isArray(edits)) {
    for (var i = 0; i < edits.length; i++) {
      var edit = edits[i];
      if (edit && edit.file_path && typeof edit.file_path === 'string') {
        paths.push(edit.file_path);
      }
    }
  }
  return paths;
}

function getCostWarningCachePath(costsPath) {
  var hash = crypto.createHash('sha256').update(costsPath).digest('hex').slice(0, 16);
  return path.join(os.tmpdir(), WARNING_CACHE_PREFIX + hash + '.json');
}

function readCostWarningCache(cachePath) {
  try {
    var parsed = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
  } catch (e) {
    return {};
  }
}

function writeCostWarningIfChanged(kind, costsPath, signature, message) {
  var cachePath = getCostWarningCachePath(costsPath);
  var cache = readCostWarningCache(cachePath);
  if (cache[kind] === signature) return;
  process.stderr.write(message);
  try {
    var next = {};
    var keys = Object.keys(cache);
    for (var i = 0; i < keys.length; i++) next[keys[i]] = cache[keys[i]];
    next[kind] = signature;
    var tmp = cachePath + '.' + process.pid + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(next), 'utf8');
    fs.renameSync(tmp, cachePath);
  } catch (e) {}
}

function readSessionCost(sessionId) {
  var costsPath = path.join('metrics', 'costs.jsonl');
  try {
    costsPath = path.join(getClaudeDir(), 'metrics', 'costs.jsonl');
    var content = fs.readFileSync(costsPath, 'utf8');
    var lines = content.split('\n').filter(Boolean);
    var totalCost = 0, totalIn = 0, totalOut = 0, malformed = 0;
    var malformedHasher = crypto.createHash('sha256');
    for (var i = 0; i < lines.length; i++) {
      try {
        var row = JSON.parse(lines[i]);
        if (row.session_id === sessionId) {
          totalCost = toNumber(row.estimated_cost_usd);
          totalIn = toNumber(row.input_tokens);
          totalOut = toNumber(row.output_tokens);
        }
      } catch (e) {
        malformed += 1;
        malformedHasher.update(lines[i]).update('\0');
      }
    }
    if (malformed > 0) {
      writeCostWarningIfChanged('malformed', costsPath,
        malformed + ':' + malformedHasher.digest('hex').slice(0, 16),
        '[ecc-metrics-bridge] skipped ' + malformed + ' malformed line(s) in ' + costsPath + '\n');
    }
    return { totalCost: totalCost, totalIn: totalIn, totalOut: totalOut };
  } catch (err) {
    if (err && err.code !== 'ENOENT') {
      writeCostWarningIfChanged('read-error', costsPath,
        (err.code || err.name || 'error') + ':' + (err.message || String(err)),
        '[ecc-metrics-bridge] failing open after ' + (err.name || 'error') + ' reading ' + costsPath + ': ' + (err.message || String(err)) + '\n');
    }
    return { totalCost: 0, totalIn: 0, totalOut: 0 };
  }
}

function updateTaskMetrics(sessionId, toolName, toolInput, filePaths) {
  var metricsPath = path.join(os.tmpdir(), TASK_METRICS_PREFIX + sessionId + '.json');
  var metrics = {};
  try {
    metrics = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
  } catch (e) {
    metrics = {
      session_id: sessionId,
      task_count: 1,
      current_task_id: 1,
      first_decision_time_ms: null,
      tokens_before_first_action: null,
      agents_invoked: [],
      compaction_count: 0,
      file_read_history: [],
      re_analysis_count: 0,
      last_read_timestamp: null,
      task_start: Date.now()
    };
  }

  var now = Date.now();

  if (!metrics.first_decision_time_ms && toolName) {
    metrics.first_decision_time_ms = now - (metrics.task_start || now);
  }

  if (/^(planner|architect|code-reviewer|.*-reviewer|.*-resolver)$/i.test(toolName)) {
    if (metrics.agents_invoked.indexOf(toolName) === -1) {
      metrics.agents_invoked.push(toolName);
    }
  }

  if (toolName === 'Bash' && toolInput && toolInput.command) {
    var cmd = String(toolInput.command);
    if (/compact/i.test(cmd)) {
      metrics.compaction_count = (metrics.compaction_count || 0) + 1;
    }
  }

  // Detect re-analysis: same file read/write within window
  for (var i = 0; i < filePaths.length; i++) {
    var fp = filePaths[i];
    if (!fp) continue;
    var prev = metrics.file_read_history || [];
    var found = false;
    for (var j = 0; j < prev.length; j++) {
      if (prev[j].path === fp && (now - prev[j].timestamp) < RE_ANALYSIS_WINDOW_MS) {
        found = true;
        break;
      }
    }
    if (found) {
      metrics.re_analysis_count = (metrics.re_analysis_count || 0) + 1;
    }
    prev.push({ path: fp, timestamp: now });
    if (prev.length > 100) prev.shift();
    metrics.file_read_history = prev;
  }

  try {
    var tmp = metricsPath + '.' + process.pid + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(metrics), 'utf8');
    fs.renameSync(tmp, metricsPath);
  } catch (e) {}
}

function run(rawInput) {
  try {
    var input = rawInput.trim() ? JSON.parse(rawInput) : {};
    var toolName = String(input.tool_name || '');
    var toolInput = input.tool_input || {};
    var sessionId = sanitizeSessionId(input.session_id) ||
      sanitizeSessionId(process.env.ECC_SESSION_ID) ||
      sanitizeSessionId(process.env.CLAUDE_SESSION_ID);
    if (!sessionId) return rawInput;

    var now = new Date().toISOString();
    var bridge = readBridge(sessionId) || {
      session_id: sessionId,
      total_cost_usd: 0,
      total_input_tokens: 0,
      total_output_tokens: 0,
      tool_count: 0,
      files_modified_count: 0,
      files_modified: [],
      recent_tools: [],
      first_timestamp: now,
      last_timestamp: now,
      context_remaining_pct: null,
      task_agents_invoked: [],
      task_compaction_count: 0,
      task_re_analysis_count: 0
    };

    bridge.tool_count = (bridge.tool_count || 0) + 1;
    bridge.last_timestamp = now;
    if (!bridge.first_timestamp) bridge.first_timestamp = now;

    var isWriteOp = /^(Write|Edit|MultiEdit)$/i.test(toolName);
    var filePaths = isWriteOp ? extractFilePaths(toolName, toolInput) : [];
    if (isWriteOp) {
      var existing = new Set(bridge.files_modified || []);
      for (var k = 0; k < filePaths.length; k++) {
        var p = filePaths[k];
        if (existing.size < MAX_FILES_TRACKED && !existing.has(p)) {
          existing.add(p);
        }
      }
      bridge.files_modified = [];
      var iter = existing.values();
      for (var x = iter.next(); !x.done; x = iter.next()) {
        bridge.files_modified.push(x.value);
      }
      bridge.files_modified_count = existing.size;
    }

    var recent = bridge.recent_tools || [];
    recent.push({ tool: toolName, hash: hashToolCall(toolName, toolInput) });
    if (recent.length > RECENT_TOOLS_SIZE) recent.shift();
    bridge.recent_tools = recent;

    var costs = readSessionCost(sessionId);
    bridge.total_cost_usd = Math.round(costs.totalCost * 1e6) / 1e6;
    bridge.total_input_tokens = costs.totalIn;
    bridge.total_output_tokens = costs.totalOut;

    // Premium: per-task KPIs on the bridge
    updateTaskMetrics(sessionId, toolName, toolInput,
      isWriteOp ? filePaths : extractFilePaths(toolName, toolInput));

    writeBridgeAtomic(sessionId, bridge);
  } catch (e) {}

  return rawInput;
}

if (require.main === module) {
  var data = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', function(chunk) {
    if (data.length < MAX_STDIN) data += chunk.substring(0, MAX_STDIN - data.length);
  });
  process.stdin.on('end', function() {
    process.stdout.write(run(data));
    process.exit(0);
  });
}

module.exports = { run, hashToolCall, extractFilePaths, readSessionCost, stableStringify };
