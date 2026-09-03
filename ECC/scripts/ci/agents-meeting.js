#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');

const AGENTS_DIR = path.join(__dirname, '../../agents');
const COMMANDS_DIR = path.join(__dirname, '../../commands');

function extractFrontmatter(content) {
  const fm = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) return {};
  const data = {};
  fm[1].split('\n').forEach(l => {
    const m = l.match(/^(\w+):\s*(.+)$/);
    if (m) data[m[1]] = m[2].replace(/^['"]|['"]$/g, '');
  });
  return data;
}

function bodyOnly(content) {
  return content.replace(/^---[\s\S]*?\n---\n*/, '').trim();
}

// === LOAD AGENTS ===
const files = fs.readdirSync(AGENTS_DIR).filter(f => f.endsWith('.md')).sort();
const agents = files.map(f => {
  const content = fs.readFileSync(path.join(AGENTS_DIR, f), 'utf8');
  const fm = extractFrontmatter(content);
  const body = bodyOnly(content);
  return {
    file: f,
    name: fm.name || path.basename(f, '.md'),
    model: fm.model || 'MISSING',
    tools: fm.tools || 'MISSING',
    description: fm.description || 'MISSING',
    bodyLines: body.split('\n').length,
    totalLines: content.split('\n').length
  };
});

console.log('# ECC Agents Meeting Report\n');

// === 1. MODEL DISTRIBUTION ===
console.log('## 1. Model Distribution\n');
const modelCounts = {};
agents.forEach(a => { modelCounts[a.model] = (modelCounts[a.model] || 0) + 1; });
Object.entries(modelCounts).sort().forEach(([m, c]) => {
  console.log(`  ${m}: ${c} agents (${Math.round(c/agents.length*100)}%)`);
});
console.log('');

// === 2. TOOL PATTERNS ===
console.log('## 2. Tool Patterns\n');
const toolSets = {};
const toolAgents = {};
agents.forEach(a => {
  const key = a.tools;
  toolSets[key] = (toolSets[key] || 0) + 1;
  if (!toolAgents[key]) toolAgents[key] = [];
  toolAgents[key].push(a.name);
});
Object.entries(toolSets)
  .sort((a, b) => b[1] - a[1])
  .forEach(([t, c]) => {
    const pct = Math.round(c / agents.length * 100);
    console.log(`  [${c} agents, ${pct}%] ${t}`);
    if (c <= 3) {
      toolAgents[t].forEach(n => console.log(`    - ${n}`));
    }
  });
console.log('');

// === 3. BODY SIZE ANALYSIS ===
console.log('## 3. Body Size Analysis\n');
const sizes = agents.map(a => a.bodyLines).sort((a, b) => a - b);
const total = sizes.reduce((a, b) => a + b, 0);
console.log(`  Total: ${agents.length} agents`);
console.log(`  Total body lines: ${total}`);
console.log(`  Min: ${sizes[0]} lines`);
console.log(`  Max: ${sizes[sizes.length - 1]} lines`);
console.log(`  Median: ${sizes[Math.floor(sizes.length / 2)]} lines`);
console.log(`  Average: ${Math.round(total / sizes.length)} lines`);
console.log('');

// Small agents
console.log('### Small agents (< 15 body lines)\n');
const small = agents.filter(a => a.bodyLines < 15).sort((a, b) => a.bodyLines - b.bodyLines);
if (small.length === 0) console.log('  None\n');
else small.forEach(a => console.log(`  ${a.file}: ${a.bodyLines} lines, ${a.model}, ${a.description.slice(0, 50)}`));
console.log('');

// Large agents
console.log('### Large agents (> 250 body lines)\n');
const large = agents.filter(a => a.bodyLines > 250).sort((a, b) => b.bodyLines - a.bodyLines);
if (large.length === 0) console.log('  None\n');
else large.forEach(a => console.log(`  ${a.file}: ${a.bodyLines} lines, ${a.model}, ${a.description.slice(0, 50)}`));
console.log('');

// === 4. CROSS-REFERENCES (commands -> agents) ===
console.log('## 4. Command Cross-References\n');
const commands = fs.readdirSync(COMMANDS_DIR).filter(f => f.endsWith('.md'));
const agentNames = new Set(agents.map(a => a.name));
const refdByCommands = new Set();
const cmdRefs = {};
commands.forEach(f => {
  const content = fs.readFileSync(path.join(COMMANDS_DIR, f), 'utf8');
  const body = bodyOnly(content);
  const refs = [...body.matchAll(/agents\/([a-z][-a-z0-9]*)\.md/g)].map(m => m[1]);
  refs.forEach(r => {
    refdByCommands.add(r);
    if (!cmdRefs[r]) cmdRefs[r] = [];
    cmdRefs[r].push(f);
  });
});

const refdByAgents = new Set();
agents.forEach(a => {
  const content = fs.readFileSync(path.join(AGENTS_DIR, a.file), 'utf8');
  const body = bodyOnly(content);
  const refs = [...body.matchAll(/agents\/([a-z][-a-z0-9]*)\.md/g)].map(m => m[1]);
  refs.forEach(r => refdByAgents.add(r));
});

const referenced = new Set([...refdByCommands, ...refdByAgents]);
const orphans = [...agentNames].filter(a => !referenced.has(a)).sort();

console.log(`  Agents referenced by commands: ${refdByCommands.size}/${agents.length}`);
console.log(`  Agents referenced by other agents (only): ${[...refdByAgents].filter(a => !refdByCommands.has(a)).length}`);
console.log(`  Fully orphan agents: ${orphans.length}/${agents.length}\n`);

if (orphans.length > 0) {
  console.log('### Orphan agents (no command or agent references them)\n');
  orphans.forEach(a => {
    const info = agents.find(x => x.name === a);
    const refsInBody = info ? (cmdRefs[a] || []).length : 0;
    console.log(`  ${a} (${info ? info.model : '?'}, ${info ? info.bodyLines : '?'} lines, ${info ? info.description.slice(0, 40) : '?'})`);
  });
  console.log('');
}

console.log('### Top-referenced agents (by commands)\n');
const sortedRefs = Object.entries(cmdRefs).sort((a, b) => b[1].length - a[1].length);
sortedRefs.forEach(([agent, cmds]) => {
  console.log(`  ${agent}: ${cmds.length} commands -> ${cmds.join(', ')}`);
});
console.log('');

// === 5. FRONTMATTER INTEGRITY ===
console.log('## 5. Frontmatter Integrity\n');
const errors = [];
agents.forEach(a => {
  const content = fs.readFileSync(path.join(AGENTS_DIR, a.file), 'utf8');
  if (!content.startsWith('---')) errors.push(`${a.file}: missing frontmatter`);
  if (a.model === 'MISSING') errors.push(`${a.file}: missing model`);
  if (a.tools === 'MISSING') errors.push(`${a.file}: missing tools`);
  if (a.name !== path.basename(a.file, '.md')) errors.push(`${a.file}: name mismatch (frontmatter="${a.name}" !== filename)`);
});
if (errors.length === 0) console.log('  All 67 agents have valid frontmatter with name, model, and tools.\n');
else errors.forEach(e => console.log(`  ERROR: ${e}`)); console.log('');

// === 6. SUMMARY ===
console.log('## Summary\n');
const opusCount = modelCounts['opus'] || 0;
const sonnetCount = modelCounts['sonnet'] || 0;
const haikuCount = modelCounts['haiku'] || 0;
console.log(`  Total agents: ${agents.length}`);
console.log(`  Opus (strategy/architecture): ${opusCount}`);
console.log(`  Sonnet (operational/review): ${sonnetCount}`);
console.log(`  Haiku (lightweight): ${haikuCount}`);
console.log(`  Unique tool patterns: ${Object.keys(toolSets).length}`);
console.log(`  Orphan rate: ${Math.round(orphans.length/agents.length*100)}% (${orphans.length}/${agents.length})`);
console.log(`  Frontmatter errors: ${errors.length}`);
