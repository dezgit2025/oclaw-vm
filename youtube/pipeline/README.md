# YouTube Transcript Downloader (captions-first, cookie-free)

This is a **captions-first** pipeline using `yt-dlp`:

1. Fetch subtitles (manual + auto) for a set of channel video feeds (no media download)
2. Convert subtitles to `.srt`
3. Convert `.srt` → cleaned `.txt`

## Prereqs
- `yt-dlp` installed and on PATH
- `python3` available

Quick check:

```bash
yt-dlp --version
python3 --version
```

## Configuration
Edit channels in `pull_transcripts.sh`.

Defaults:
- Output directory: `../transcripts/`
- Date filter: after `2025-01-01`
- Duration filter: > 120 seconds
- Per-channel limit: first 20 videos

## Run

```bash
cd /home/desazure/.openclaw/workspace/youtube/pipeline
chmod +x pull_transcripts.sh
./pull_transcripts.sh

python3 srt_to_text.py
```

## Notes / failure modes
Some environments hit YouTube bot-gate even for subtitles-only downloads. If that happens consistently:
- switch to “user provides transcript” (paste/upload `.vtt/.srt/.txt`)
- or use a transcript provider API
