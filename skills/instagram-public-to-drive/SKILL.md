---
name: instagram-public-to-drive
description: Download PUBLIC Instagram reels/posts via yt-dlp and upload the video to Google Drive (OpenClawShared folder). Use when the user gives an Instagram URL and wants the MP4 saved into Drive.
user-invocable: true
---

# Instagram (public) → Google Drive (OpenClawShared)

Use this skill when the user provides an Instagram **public** post/reel URL and wants the video saved into Google Drive (OpenClawShared).

## Safety / constraints
- Public URLs only. No login/cookies handling in this skill.
- Output is uploaded to the **OpenClawShared** Drive folder only.

## Paths
- Script: `scripts/ig_public_to_drive.sh`
- Local staging dir: `/home/desazure/.openclaw/workspace/instagram/out/`
- Drive uploader: uses `gdrive-openclawshared` token `~/.config/openclaw-gdrive/token-openclawshared.json`

## Run

```bash
/home/desazure/.openclaw/workspace/skills/instagram-public-to-drive/scripts/ig_public_to_drive.sh \
  "https://www.instagram.com/reel/<id>/"
```

Output prints the local file path and the Drive file id.

## Notes
- IG frequently rate-limits / bot-gates downloaders. If it fails, retry later or use a different network/IP.
- File naming is deterministic: `instagram/out/<timestamp>_<id>.mp4`.
