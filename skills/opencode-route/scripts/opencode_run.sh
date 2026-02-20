#!/usr/bin/env bash
set -euo pipefail

PROMPT=${1:-}
if [[ -z "$PROMPT" ]]; then
  echo "Usage: opencode_run.sh \"<task prompt>\"" >&2
  exit 2
fi

# Default projects folder (user preference)
PROJECTS_DIR="${HOME}/Projects"
mkdir -p "$PROJECTS_DIR"

# Create a new subfolder for new coding work
TS=$(date -u +%Y%m%d-%H%M%S)
SLUG=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g' | cut -c1-40)
DIR="$PROJECTS_DIR/opencode-${TS}-${SLUG}"
mkdir -p "$DIR"

cd "$DIR"

# Initialize git repo for tooling that expects it
if [[ ! -d .git ]]; then
  git init -q
fi

echo "[opencode-route] workdir: $DIR" >&2

# Run OpenCode (interactive)
# Optional: set OPENCODE_MODEL to override, e.g. "github-copilot/gpt-5.2".
if [[ -n "${OPENCODE_MODEL:-}" ]]; then
  exec opencode run --model "$OPENCODE_MODEL" "$PROMPT"
fi

exec opencode run "$PROMPT"
