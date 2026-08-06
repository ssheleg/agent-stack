#!/usr/bin/env node
/*
 * agent-stack installer CLI.
 *
 * Installs the agent-orchestrator skill into ~/.claude/skills/agent-orchestrator
 * (same layout as install.sh). Idempotent: an existing install is skipped unless
 * --force. Zero dependencies.
 *
 * For other agents (Cursor, Codex, 70+) use: npx skills add ssheleg/agent-stack
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = path.resolve(__dirname, '..');
const REPO = 'ssheleg/agent-stack';

function usage() {
  console.log(`agent-stack installer

Usage:
  npx @ssheleg/agent-stack [--force]   install the agent-orchestrator skill
                                       into ~/.claude (skip existing unless --force)
  npx @ssheleg/agent-stack --help

Other install paths:
  Claude Code plugin:  /plugin marketplace add ${REPO}
                       /plugin install agent-stack@agent-stack
  Any agent (70+):     npx skills add ${REPO}`);
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function installOne(label, src, dest, isDir, force) {
  if (fs.existsSync(dest) && !force) {
    console.log(`skip: ${label} already installed at ${dest} (rerun with --force to overwrite)`);
    return;
  }
  fs.rmSync(dest, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  if (isDir) copyDir(src, dest);
  else fs.copyFileSync(src, dest);
  console.log(`Installed ${label} -> ${dest}`);
}

function main(argv) {
  const args = argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    usage();
    return 0;
  }
  const force = args.includes('--force');
  const unknown = args.filter((a) => a !== '--force');
  if (unknown.length) {
    console.error(`unknown argument(s): ${unknown.join(' ')}`);
    usage();
    return 2;
  }

  const skillSrc = path.join(ROOT, 'plugins/agent-stack/skills/agent-orchestrator');
  if (!fs.existsSync(skillSrc)) {
    console.error(`error: skill sources missing at ${skillSrc} — corrupted package?`);
    return 1;
  }

  const home = os.homedir();
  installOne(
    'agent-orchestrator skill',
    skillSrc,
    path.join(home, '.claude', 'skills', 'agent-orchestrator'),
    true,
    force
  );
  return 0;
}

process.exit(main(process.argv));
