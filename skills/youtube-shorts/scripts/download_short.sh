#!/usr/bin/env bash
set -euo pipefail

# Wrapper for download_short.py
# Example:
#   download_short.sh --url "https://www.youtube.com/shorts/<id>" --upload-drive

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"

exec "$PY" "$SCRIPT_DIR/download_short.py" "$@"
