#!/usr/bin/env bash
# Install every skill this plugin ships into ~/.claude/skills/.
# Idempotent: rerun to overwrite. Zero dependencies beyond coreutils.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$ROOT/plugins/agent-stack/skills"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
elif [[ -n "${1:-}" ]]; then
  echo "usage: $0 [--force]" >&2
  exit 2
fi

if [ ! -d "$SRC_ROOT" ]; then
  echo "error: skill sources missing at $SRC_ROOT" >&2
  exit 1
fi

# One channel per agent: plain copies beside an installed plugin are two
# listings of the same skill — one per skill this pack ships — and the stale
# one wins. Refuse rather than create that, and refuse loudly: a presence
# check keyed on the marketplaces/ dir alone that exits 0 is the fail-open
# class — a directory-sourced marketplace has no dir there, plugin names
# differ from marketplace names, and an exit 0 reads as success to every
# script above it. installed_plugins.json is the record of what is installed;
# a missing or unparsable one reads as "no plugin".
INSTALLED_JSON="${HOME}/.claude/plugins/installed_plugins.json"
MARKETPLACE="${HOME}/.claude/plugins/marketplaces/agent-stack"
SPEC=""
if [[ -f "$INSTALLED_JSON" ]]; then
  SPEC="$(sed -n 's/.*"\(agent-stack@[^"]*\)".*/\1/p' "$INSTALLED_JSON" 2>/dev/null | head -n 1)" || true
fi
if [[ ( -n "$SPEC" || -e "$MARKETPLACE" ) && "$FORCE" -eq 0 ]]; then
  {
    if [[ -n "$SPEC" ]]; then
      echo "refused: agent-stack is already installed as the Claude Code plugin $SPEC"
      echo "         (declared in ~/.claude/plugins/installed_plugins.json)."
    else
      echo "refused: agent-stack is already registered as a Claude Code marketplace"
      echo "         ($MARKETPLACE)."
    fi
    echo "         Plain copies in ~/.claude/skills would shadow the plugin and serve"
    echo "         this frozen version forever. Update the plugin channel instead:"
    echo "           claude plugin marketplace update agent-stack"
    echo "           claude plugin update ${SPEC:-agent-stack@agent-stack}"
    echo "         Family launcher: npx --yes sshlg-skills@latest update"
    echo "         Pass --force to write the plain copies anyway."
  } >&2
  exit 3
fi

# Iterate rather than name one skill: a skill added to the plugin must not
# require an installer change to reach anybody.
for SRC in "$SRC_ROOT"/*/; do
  NAME="$(basename "$SRC")"
  DEST="${HOME}/.claude/skills/${NAME}"
  mkdir -p "$(dirname "$DEST")"
  rm -rf "$DEST"
  cp -R "${SRC%/}" "$DEST"
  echo "Installed ${NAME} skill -> $DEST"
done
echo "Restart your agent — skills load at session start."
# The last line says how the next version arrives.
echo "Updates: git pull && ./install.sh --force, or npx --yes sshlg-skills@latest update"
