#!/usr/bin/env bash
set -euo pipefail

URL=${1:-}
if [[ -z "$URL" ]]; then
  echo "Usage: $0 <instagram-public-url>" >&2
  exit 2
fi

# Local staging
OUTDIR="/home/desazure/.openclaw/workspace/instagram/out"
mkdir -p "$OUTDIR"

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
# Try to pull a stable ID from URL (fallback to 'instagram')
ID=$(python3 - "$URL" <<'PY'
import re,sys
u=sys.argv[1]
# handle /reel/<id>/ and /p/<id>/
m=re.search(r"instagram\.com/(?:reel|p)/([^/?#]+)", u)
print(m.group(1) if m else "instagram")
PY
)

BASENAME="${STAMP}_${ID}"
OUTTEMPLATE="$OUTDIR/${BASENAME}.%(ext)s"

echo "[info] url=$URL"
echo "[info] outdir=$OUTDIR"

# Download best available video only (public)
# --no-playlist prevents profile/page expansion
# --restrict-filenames avoids weird characters
# --write-info-json keeps metadata for indexing
yt-dlp \
  --no-playlist \
  --restrict-filenames \
  --no-progress \
  --write-info-json \
  -f "bv*+ba/b" \
  -o "$OUTTEMPLATE" \
  "$URL"

# Find the produced mp4 (or mkv/webm if mp4 isn't available)
FILE=$(ls -1 "$OUTDIR/${BASENAME}."* 2>/dev/null | grep -E '\.(mp4|mkv|webm)$' | head -n 1 || true)
if [[ -z "$FILE" ]]; then
  echo "[error] download succeeded but could not find output media for base=$BASENAME" >&2
  ls -la "$OUTDIR" | tail -n 50 >&2 || true
  exit 3
fi

echo "[ok] downloaded=$FILE"

# Upload to OpenClawShared Drive folder
PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
UPLOADER="/home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/upload_file.py"
TOKEN="$HOME/.config/openclaw-gdrive/token-openclawshared.json"

if [[ ! -f "$TOKEN" ]]; then
  echo "[error] missing Drive token: $TOKEN" >&2
  exit 4
fi

$PY "$UPLOADER" --token "$TOKEN" --path "$FILE"
