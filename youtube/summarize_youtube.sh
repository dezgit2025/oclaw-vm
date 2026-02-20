#!/usr/bin/env bash
set -euo pipefail

URL=${1:-}
if [[ -z "$URL" ]]; then
  echo "Usage: $0 <youtube-url>" >&2
  exit 2
fi

COOKIES=${YTDL_COOKIES:-/home/desazure/.openclaw/workspace/youtube/cookies_youtube.txt}
OUTDIR=${OUTDIR:-/home/desazure/.openclaw/workspace/youtube/out}
mkdir -p "$OUTDIR"

VID=$(python3 - "$URL" <<'PY'
import re,sys,urllib.parse
url=sys.argv[1]
q=urllib.parse.urlparse(url)
qs=urllib.parse.parse_qs(q.query)
vid=(qs.get('v') or [''])[0]
if not vid:
  m=re.search(r"youtu\.be/([^?&/]+)", url)
  vid=m.group(1) if m else ''
print(vid)
PY
)

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BASE="$OUTDIR/${VID:-video}-$STAMP"

echo "[info] url=$URL"
echo "[info] cookies=$COOKIES"
echo "[info] out_base=$BASE"

# Captions-first: prefer human captions, then auto.
# We include deno runtime (installed via brew dependency) to satisfy yt-dlp JS runtime requirements.
set +e
yt-dlp \
  --cookies "$COOKIES" \
  --js-runtimes deno \
  --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "en.*,en" \
  --sub-format "vtt" \
  -o "$BASE.%(ext)s" \
  "$URL" \
  >"$BASE.ytdl.stdout.txt" \
  2>"$BASE.ytdl.stderr.txt"
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  echo "[error] yt-dlp failed (rc=$RC)." >&2
  echo "Most common cause: YouTube bot-gate / invalid cookies." >&2
  echo "See: $BASE.ytdl.stderr.txt" >&2
  echo "Next steps:" >&2
  echo "  1) Export fresh YouTube cookies in Netscape cookies.txt format (while logged in)." >&2
  echo "  2) Replace $COOKIES with the new file and re-run." >&2
  echo "  3) Or paste the transcript here and I can summarize immediately." >&2
  exit $RC
fi

# Find a .vtt (manual or auto) and extract plain text.
VTT=$(ls -1 "$OUTDIR"/*.vtt 2>/dev/null | grep -F "${VID:-video}-$STAMP" | head -n 1 || true)
if [[ -z "$VTT" ]]; then
  # fallback: any vtt that matches the base
  VTT=$(ls -1 "$BASE"*.vtt 2>/dev/null | head -n 1 || true)
fi

if [[ -z "$VTT" ]]; then
  echo "[error] No .vtt subtitles were written." >&2
  echo "Check stdout/stderr: $BASE.ytdl.*.txt" >&2
  exit 3
fi

echo "[info] vtt=$VTT"

TXT="$BASE.captions.txt"
python3 - "$VTT" "$TXT" <<'PY'
import re,sys
vtt=sys.argv[1]
out=sys.argv[2]
lines=[]
for line in open(vtt,'r',encoding='utf-8',errors='ignore'):
  line=line.strip('\n')
  # drop headers, timestamps, cues
  if not line.strip():
    continue
  if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
    continue
  if re.match(r"^\d\d:\d\d:\d\d\.\d\d\d\s+-->\s+\d\d:\d\d:\d\d\.\d\d\d", line):
    continue
  if re.match(r"^\d\d:\d\d\.\d\d\d\s+-->\s+\d\d:\d\d\.\d\d\d", line):
    continue
  if line.isdigit():
    continue
  # remove simple markup
  line=re.sub(r"<[^>]+>", "", line)
  line=line.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
  lines.append(line.strip())
text='\n'.join(lines)
# light de-dupe of repeated consecutive lines
out_lines=[]
prev=None
for ln in text.splitlines():
  if ln==prev:
    continue
  out_lines.append(ln)
  prev=ln
open(out,'w',encoding='utf-8').write('\n'.join(out_lines).strip()+"\n")
PY

echo "[ok] captions_text=$TXT"
wc -l "$TXT" | sed 's/^/[info] /'
