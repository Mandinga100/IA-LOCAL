#!/usr/bin/env node
'use strict';
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '../..');
const IGNORE_DIRS = new Set(['node_modules', '.git']);

function findMarkdownFiles(dir, files = []) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
  catch { return files; }
  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (!IGNORE_DIRS.has(entry.name)) {
        findMarkdownFiles(path.join(dir, entry.name), files);
      }
    } else if (entry.name.endsWith('.md')) {
      files.push(path.join(dir, entry.name));
    }
  }
  return files;
}

const files = findMarkdownFiles(ROOT);
if (files.length === 0) {
  console.log('No markdown files found');
  process.exit(0);
}

const result = spawnSync('markdownlint', files, {
  cwd: ROOT,
  encoding: 'utf8',
  shell: true,
  stdio: 'inherit',
});

process.exit(result.status ?? 1);
