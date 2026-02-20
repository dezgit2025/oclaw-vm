#!/usr/bin/env bash
set -euo pipefail

# Convert a local UTF-8 text/markdown file to a text-based PDF and upload it to
# Google Drive (OpenClawShared).
#
# Usage:
#   convert2pdf_to_drive.sh --in /path/to/article.md --out /path/to/out.pdf \
#     [--title "..."] [--source-url "https://..."]
#
# Notes:
# - This does NOT fetch URLs or bypass paywalls.
# - Pair with an OpenClaw `web_fetch` step (or Wayback) to create the input .md.

IN=""
OUT=""
TITLE=""
SOURCE_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in)
      IN="$2"; shift 2;;
    --out)
      OUT="$2"; shift 2;;
    --title)
      TITLE="$2"; shift 2;;
    --source-url)
      SOURCE_URL="$2"; shift 2;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$IN" || -z "$OUT" ]]; then
  echo "Missing required args. Usage: $0 --in file.md --out file.pdf [--title ...] [--source-url ...]" >&2
  exit 2
fi

PY=/home/desazure/.openclaw/workspace/.venv-gmail/bin/python
TEXT2PDF=/home/desazure/.openclaw/workspace/skills/convert2pdf/scripts/text_to_pdf.py
UPLOAD=/home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/upload_file.py
TOKEN=/home/desazure/.config/openclaw-gdrive/token-openclawshared.json

mkdir -p "$(dirname "$OUT")"

ARGS=("$TEXT2PDF" --in "$IN" --out "$OUT")
if [[ -n "$TITLE" ]]; then ARGS+=(--title "$TITLE"); fi
if [[ -n "$SOURCE_URL" ]]; then ARGS+=(--source-url "$SOURCE_URL"); fi

$PY "${ARGS[@]}"

$PY "$UPLOAD" --token "$TOKEN" --path "$OUT"
