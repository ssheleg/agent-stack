#!/usr/bin/env node
/*
 * agent-stack installer CLI.
 *
 * Installs every skill this plugin ships into ~/.claude/skills/<name>
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
const PLUGIN = 'agent-stack';

// Exit codes are the contract: 0 installed or skipped, 1 corrupted package,
// 2 usage error, 3 refused — the plugin channel owns this agent (--force overrides).
const EXIT_PLUGIN_PRESENT = 3;

/**
 * The plugin spec (`<name>@<marketplace>`) installed for `name` in this home,
 * or null.
 *
 * `installed_plugins.json` is the record of what is actually installed. The
 * `plugins/marketplaces/<name>` directory under-reports: a marketplace added
 * from a local `directory` source has no dir there at all, and plugin names
 * differ from marketplace names, so a check keyed on it stays green while the
 * shadow lands. Absence and corruption both read as "no plugin": the fresh
 * HOME is the common case, and an installer that crashes on a parse error
 * refuses the machines that need it most.
 */
function installedPluginSpec(home, name) {
  try {
    const raw = fs.readFileSync(
      path.join(home, '.claude', 'plugins', 'installed_plugins.json'), 'utf8');
    const parsed = JSON.parse(raw);
    const plugins =
      parsed && typeof parsed === 'object' &&
      parsed.plugins && typeof parsed.plugins === 'object'
        ? parsed.plugins
        : parsed;
    if (!plugins || typeof plugins !== 'object') return null;
    for (const spec of Object.keys(plugins)) {
      if (spec === name) return `${name}@${name}`;
      if (spec.startsWith(name + '@')) return spec;
    }
  } catch {
    // missing or corrupt = no plugin — fail open on absence, never crash
  }
  return null;
}

function usage() {
  console.log(`agent-stack installer

Usage:
  npx @ssheleg/agent-stack [--force]   install every skill this plugin ships
                                       into ~/.claude (skip existing unless --force)
  npx @ssheleg/agent-stack --help

Exit codes:
  0 installed or skipped   2 usage error
  1 corrupted package      3 refused: the agent-stack PLUGIN is installed in
                             this home — plain copies would shadow it (pass
                             --force to write them anyway)

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

  const skillRoot = path.join(ROOT, 'plugins/agent-stack/skills');
  if (!fs.existsSync(skillRoot)) {
    console.error(`error: skill sources missing at ${skillRoot} — corrupted package?`);
    return 1;
  }

  // Iterate rather than name one skill: a skill added to the plugin must not
  // require an installer change to reach anybody.
  const names = fs
    .readdirSync(skillRoot, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort();
  if (!names.length) {
    console.error(`error: no skills found under ${skillRoot} — corrupted package?`);
    return 1;
  }

  const home = os.homedir();

  // One channel per agent. A plain ~/.claude/skills/<name> beside the installed
  // agent-stack plugin is two listings of the same skill per skill this pack
  // ships, and the stale copy wins — the exact shadow make-skill's distribution
  // canon forbids (§ "The installer must refuse the shadow it documents").
  // Refuse rather than create it, and refuse LOUDLY: a presence check keyed on
  // the marketplaces/ dir alone that exits 0 is the fail-open class — a
  // directory-sourced marketplace has no dir there, plugin names differ from
  // marketplace names, and exit 0 reads as success to every script above it.
  // Reproduced live 2026-08-29: a bare `npx @ssheleg/telegram-dev` shipped
  // three shadows past exactly this hole while the plugin was enabled. Only the
  // ~/.claude write is gated — no other agent has plugins.
  const spec = installedPluginSpec(home, PLUGIN);
  const marketplace = path.join(home, '.claude', 'plugins', 'marketplaces', PLUGIN);
  const viaMarketplaceDir = !spec && fs.existsSync(marketplace);
  if ((spec || viaMarketplaceDir) && !force) {
    const found = spec
      ? `installed as the Claude Code plugin ${spec}\n` +
        '         (declared in ~/.claude/plugins/installed_plugins.json)'
      : `registered as a Claude Code marketplace\n         (${marketplace})`;
    console.error(
      `refused: agent-stack is already ${found}.\n` +
      `         Plain copies in ~/.claude/skills/ (${names.join(', ')})\n` +
      '         would shadow the plugin and serve this frozen version forever.\n' +
      '         Update the plugin channel instead:\n' +
      '           claude plugin marketplace update agent-stack\n' +
      `           claude plugin update ${spec || 'agent-stack@agent-stack'}\n` +
      '         Family launcher (updates every member, prunes shadow copies):\n' +
      '           npx --yes sshlg-skills@latest update\n' +
      '         Pass --force to write the plain copies anyway — a deliberate choice\n' +
      '         to run two channels, where the stale one wins.'
    );
    return EXIT_PLUGIN_PRESENT;
  }

  for (const name of names) {
    installOne(
      `${name} skill`,
      path.join(skillRoot, name),
      path.join(home, '.claude', 'skills', name),
      true,
      force
    );
  }
  // The last line says how the next version arrives — "Installed" is not a
  // complete sentence. Auto-update is off on purpose: this member composes
  // with its family, and per-marketplace autoUpdate moves each member on its
  // own clock, into combinations nobody tested together.
  console.log(
    '\nUpdates: rerun `npx @ssheleg/agent-stack@latest --force`, or refresh the\n' +
    'whole family with `npx --yes sshlg-skills@latest update` (every channel,\n' +
    'and it prunes plain copies that would shadow a plugin).'
  );
  return 0;
}

process.exit(main(process.argv));
