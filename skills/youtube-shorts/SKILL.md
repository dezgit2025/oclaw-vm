---
name: youtube-shorts
description: Download YouTube Shorts (youtube.com/shorts/… or youtu.be/…) to MP4 using yt-dlp. Use when the user wants to save a Short locally, upload it to Google Drive (OpenClawShared), or attach it to a Gmail draft.
---

# YouTube Shorts downloader

## Quick start

Download one YouTube Short to a local folder:

```bash
/home/desazure/.openclaw/workspace/skills/youtube-shorts/scripts/download_short.sh \
  --url "https://www.youtube.com/shorts/<id>"
```

Download + upload to Google Drive (OpenClawShared):

```bash
/home/desazure/.openclaw/workspace/skills/youtube-shorts/scripts/download_short.sh \
  --url "https://www.youtube.com/shorts/<id>" \
  --upload-drive
```

Download + create Gmail draft with the MP4 attached (defaults to **desi4k@gmail.com**):

```bash
/home/desazure/.openclaw/workspace/skills/youtube-shorts/scripts/download_short.sh \
  --url "https://www.youtube.com/shorts/<id>" \
  --gmail-draft
```

Or specify a different recipient:

```bash
/home/desazure/.openclaw/workspace/skills/youtube-shorts/scripts/download_short.sh \
  --url "https://www.youtube.com/shorts/<id>" \
  --gmail-draft-to "someone@example.com"
```

## Notes / behavior

- Cookie-free by default (portable). Some Shorts may fail due to YouTube bot-gates.
- Saves logs next to the output so failures are debuggable.
- If Drive upload fails due to OAuth, it will keep the local file and print the error.

## Files

- Entrypoint: `scripts/download_short.sh`
- Implementation: `scripts/download_short.py`
