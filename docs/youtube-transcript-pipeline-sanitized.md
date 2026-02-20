# YouTube Transcript Pipeline (Sanitized)

A simple, cookie-free **captions-first** workflow:

1) Pull subtitles (manual + auto) from specific YouTube channels using `yt-dlp` (skip video download)
2) Convert subtitle files to `.srt`
3) Convert `.srt` → cleaned `.txt`
4) Feed `.txt` into your summarizer / embedding / search pipeline

---

## 1) One-shot `yt-dlp` command (captions-first)

Pull English subtitles (manual + auto) for videos on a channel page, skipping short videos and older uploads, and writing files into a structured folder.

```bash
yt-dlp \
  --skip-download \
  --write-subs \
  --write-auto-subs \
  --sub-langs "en.*,en" \
  --convert-subs srt \
  --dateafter 20250101 \
  --match-filters "duration>120" \
  -o "%(channel)s/%(upload_date)s_%(title)s.%(ext)s" \
  "https://www.youtube.com/@Bloomberg/videos"
```

**Notes**
- `--write-subs` = human subtitles (when available)
- `--write-auto-subs` = auto-generated subtitles (fallback)
- `--sub-langs "en.*,en"` grabs English variants
- Output template creates folders like: `Bloomberg/20260214_Title.en.srt`

---

## 2) Batch script: pull subtitles from multiple channels

Create `pull_transcripts.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

CHANNELS=(
  "https://www.youtube.com/@Bloomberg/videos"
  "https://www.youtube.com/@CNBCtelevision/videos"
  "https://www.youtube.com/@WallStreetJournal/videos"
)

for channel in "${CHANNELS[@]}"; do
  yt-dlp \
    --skip-download \
    --write-subs \
    --write-auto-subs \
    --sub-langs "en.*,en" \
    --convert-subs srt \
    --dateafter 20250101 \
    --match-filters "duration>120" \
    --playlist-items "1:20" \
    --sleep-interval 2 \
    --max-sleep-interval 5 \
    -o "transcripts/%(channel)s/%(upload_date)s_%(title)s.%(ext)s" \
    "$channel"
done
```

Run it:

```bash
chmod +x pull_transcripts.sh
./pull_transcripts.sh
```

**What this does**
- Pulls subtitles only (no media) for the first 20 videos per channel page
- Filters: uploaded after `2025-01-01` and duration > 120 seconds
- Throttles requests with randomized sleep between 2–5 seconds
- Writes under `transcripts/<ChannelName>/...`

**Optional hardening (recommended)**
- Safer filenames:
  ```bash
  --restrict-filenames
  ```
- Small test run (first 5 items):
  ```bash
  --playlist-end 5
  ```

---

## 3) Post-processing: Convert `.srt` → cleaned `.txt`

Create `srt_to_text.py`:

```python
import re
from pathlib import Path

TIMESTAMP = re.compile(
    r"^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}.*$",
    re.MULTILINE,
)

def srt_to_text(srt_path: Path) -> str:
    text = srt_path.read_text(encoding="utf-8", errors="ignore")

    # Drop sequence numbers (lines that are only digits)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Drop timestamp lines
    text = re.sub(TIMESTAMP, "", text)

    # Drop simple tags like <i>...</i>
    text = re.sub(r"<[^>]+>", "", text)

    # Collapse whitespace
    return " ".join(text.split())

root = Path("transcripts")
for srt in root.rglob("*.srt"):
    txt_path = srt.with_suffix(".txt")
    txt_path.write_text(srt_to_text(srt), encoding="utf-8")
    print(f"Converted: {txt_path}")
```

Run it:

```bash
python3 srt_to_text.py
```

Output example:
- Input: `transcripts/Bloomberg/20250102_Title.en.srt`
- Output: `transcripts/Bloomberg/20250102_Title.en.txt`

---

## 4) Common failure mode (cookie-free reality)

Some environments still hit YouTube’s bot-gate even for subtitles-only pulls.

If that happens, the most reliable cookie-free fallback is to change the workflow to **“transcript supplied by user”** (paste/upload `.vtt/.srt/.txt`) or use a **transcript provider API**.
