#!/usr/bin/env bash
set -euo pipefail

# captions-first transcript puller (cookie-free)
# - manual subs when available
# - auto subs otherwise
# - no media downloads

CHANNELS=(
  "https://www.youtube.com/@Bloomberg/videos"
  "https://www.youtube.com/@CNBCtelevision/videos"
  "https://www.youtube.com/@WallStreetJournal/videos"
)

# Filters
DATEAFTER=${DATEAFTER:-20250101}
MIN_DURATION=${MIN_DURATION:-120}
PLAYLIST_ITEMS=${PLAYLIST_ITEMS:-1:20}

# Throttling
SLEEP_INTERVAL=${SLEEP_INTERVAL:-2}
MAX_SLEEP_INTERVAL=${MAX_SLEEP_INTERVAL:-5}

# Output root (relative to this script)
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
OUTROOT=${OUTROOT:-"$SCRIPT_DIR/../transcripts"}
mkdir -p "$OUTROOT"

# yt-dlp options (tweak as needed)
COMMON_OPTS=(
  --skip-download
  --write-subs
  --write-auto-subs
  --sub-langs "en.*,en"
  --sub-format vtt
  --convert-subs srt
  --dateafter "$DATEAFTER"
  --match-filters "duration>$MIN_DURATION"
  --playlist-items "$PLAYLIST_ITEMS"
  --sleep-interval "$SLEEP_INTERVAL"
  --max-sleep-interval "$MAX_SLEEP_INTERVAL"
  --restrict-filenames
  --no-overwrites
)

# Avoid re-processing the same videos across runs
ARCHIVE_FILE=${ARCHIVE_FILE:-"$OUTROOT/.yt-dlp-archive.txt"}
COMMON_OPTS+=( --download-archive "$ARCHIVE_FILE" )

# Logging
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG_DIR=${LOG_DIR:-"$OUTROOT/_logs"}
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/run-$STAMP.log"

echo "[info] outroot=$OUTROOT" | tee -a "$LOG"
echo "[info] archive=$ARCHIVE_FILE" | tee -a "$LOG"
echo "[info] dateafter=$DATEAFTER min_duration=$MIN_DURATION playlist_items=$PLAYLIST_ITEMS" | tee -a "$LOG"

for channel in "${CHANNELS[@]}"; do
  echo "[info] channel=$channel" | tee -a "$LOG"

  # Output template under OUTROOT
  TEMPLATE="$OUTROOT/%(channel)s/%(upload_date)s_%(title)s.%(ext)s"

  # Run and continue to next channel on failure (don’t kill the whole batch)
  set +e
  yt-dlp "${COMMON_OPTS[@]}" -o "$TEMPLATE" "$channel" >>"$LOG" 2>&1
  RC=$?
  set -e

  if [[ $RC -ne 0 ]]; then
    echo "[warn] yt-dlp failed rc=$RC for channel=$channel (see $LOG)" | tee -a "$LOG"
  else
    echo "[ok] finished channel=$channel" | tee -a "$LOG"
  fi

done

echo "[done] log=$LOG" | tee -a "$LOG"
