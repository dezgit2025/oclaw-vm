---
name: gdrive-openclawshared
description: Google Drive tool restricted to the OpenClawShared folder (list/upload/download within that folder only).
user-invocable: true
metadata: {"openclaw":{"emoji":"🗂️"}}
---

# Google Drive — OpenClawShared only

This skill interacts with Google Drive **only inside** the folder:

- Name: `OpenClawShared`
- folderId: `1qlthNlyA1bxg-a4pMbC6MTrrXgd7tgV7`

## Safety rails

These scripts **refuse** to operate on files not under the allowed folder.

## One-time OAuth setup

This uses a separate token file:

- `~/.config/openclaw-gdrive/token-openclawshared.json`

Run auth (headless-friendly via SSH tunnel):

1) On your Mac:

```bash
ssh -N -L 18794:127.0.0.1:18794 <your-vm-ssh-host>
```

2) On the VM:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  {baseDir}/scripts/auth.py \
  --account desi4k@gmail.com \
  --token ~/.config/openclaw-gdrive/token-openclawshared.json \
  --port 18794
```

Open the printed URL in your Mac browser and approve.

## Commands

List files in folder:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/list_files.py \
  --token ~/.config/openclaw-gdrive/token-openclawshared.json
```

Upload a local file into the folder:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/upload_file.py \
  --token ~/.config/openclaw-gdrive/token-openclawshared.json \
  --path /path/to/file
```

Download a file (must be in allowed folder):

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/download_file.py \
  --token ~/.config/openclaw-gdrive/token-openclawshared.json \
  --file-id <id> \
  --out /tmp/out.bin
```
