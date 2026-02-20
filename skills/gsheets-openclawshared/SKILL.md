---
name: gsheets-openclawshared
description: Read and edit Google Sheets restricted to the OpenClawShared Drive folder.
user-invocable: true
metadata: {"openclaw":{"emoji":"📊"}}
---

# Google Sheets — OpenClawShared only

Hard restriction: only operate on Sheets that live under Drive folder:
- `OpenClawShared` folderId: `1qlthNlyA1bxg-a4pMbC6MTrrXgd7tgV7`

## One-time OAuth

Token file:
- `~/.config/openclaw-gdrive/token-sheets-openclawshared.json`

Enable Google Sheets API (once):
https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=721049927451

Tunnel from your Mac:

```bash
ssh -N -L 18796:127.0.0.1:18796 <your-vm-ssh-host>
```

Run auth on VM:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  {baseDir}/scripts/auth_sheets.py \
  --account desi4k@gmail.com \
  --token ~/.config/openclaw-gdrive/token-sheets-openclawshared.json \
  --port 18796
```

## Read a range

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/read_range.py \
  --token ~/.config/openclaw-gdrive/token-sheets-openclawshared.json \
  --sheet-id <spreadsheetId> \
  --range "Sheet1!A1:D20"
```

## Write a range

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/write_range.py \
  --token ~/.config/openclaw-gdrive/token-sheets-openclawshared.json \
  --sheet-id <spreadsheetId> \
  --range "Sheet1!A1" \
  --values '[["colA","colB"],["1","2"]]'
```

## Append a row

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/append_row.py \
  --token ~/.config/openclaw-gdrive/token-sheets-openclawshared.json \
  --sheet-id <spreadsheetId> \
  --range "Sheet1!A:Z" \
  --row '["2026-02-09","note","123"]'
```
