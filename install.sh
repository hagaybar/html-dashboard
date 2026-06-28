#!/usr/bin/env bash
# install.sh — install the html-dashboard skill + /dashboard command into
# ~/.claude from this cloned repo. Idempotent: re-running re-points the
# symlinks; any pre-existing real file is backed up to <name>.bak.<epoch> first.
#
#   ./install.sh            # symlink (git pull then updates the live skill)
#   COPY=1 ./install.sh     # copy instead of symlink
#   CLAUDE_DIR=/path ./install.sh   # install into a non-default config dir
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/commands"

place() {
  local src="$1" dest="$2"
  if [ -L "$dest" ]; then
    rm "$dest"
  elif [ -e "$dest" ]; then
    mv "$dest" "$dest.bak.$(date +%s)"
    echo "backed up existing $dest"
  fi
  if [ "${COPY:-0}" = "1" ]; then
    cp -r "$src" "$dest"; echo "copied $dest <- $src"
  else
    ln -s "$src" "$dest"; echo "linked $dest -> $src"
  fi
}

place "$REPO_DIR" "$CLAUDE_DIR/skills/html-dashboard"
place "$REPO_DIR/commands/dashboard.md" "$CLAUDE_DIR/commands/dashboard.md"
echo "done. Restart Claude Code to pick up the skill and /dashboard command."
