#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const args = process.argv.slice(2);
const binary = path.join(__dirname, 'agent-native');

function run(cmd, cmdArgs) {
  const result = spawnSync(cmd, cmdArgs, { stdio: 'inherit' });
  process.exit(result.status ?? 1);
}

if (fs.existsSync(binary)) {
  fs.chmodSync(binary, 0o755);
  run(binary, args);
} else {
  const python = process.env.PYTHON || 'python3';
  run(python, ['-m', 'agent.cli', ...args]);
}
