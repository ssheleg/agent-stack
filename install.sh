#!/usr/bin/env bash
# Install the agent-orchestrator skill into ~/.claude/skills/.
# Idempotent: rerun to overwrite. Zero dependencies beyond coreutils.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/plugins/agent-stack/skills/agent-orchestrator"
DEST="${HOME}/.claude/skills/agent-orchestrator"

if [ ! -d "$SRC" ]; then
  echo "error: skill sources missing at $SRC" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"
echo "Installed agent-orchestrator skill -> $DEST"
echo "Restart your agent — skills load at session start."
