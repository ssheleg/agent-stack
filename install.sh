#!/usr/bin/env bash
# Install every skill this plugin ships into ~/.claude/skills/.
# Idempotent: rerun to overwrite. Zero dependencies beyond coreutils.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$ROOT/plugins/agent-stack/skills"

if [ ! -d "$SRC_ROOT" ]; then
  echo "error: skill sources missing at $SRC_ROOT" >&2
  exit 1
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
