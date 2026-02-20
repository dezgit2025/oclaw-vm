---
name: gdocs-openclawshared
description: Read and edit Google Docs restricted to the OpenClawShared Drive folder.
user-invocable: true
metadata: {"openclaw":{"emoji":"📝"}}
---

# Google Docs — OpenClawShared only

Hard restriction: only operate on Docs that live under Drive folder:
- `OpenClawShared` folderId: `1qlthNlyA1bxg-a4pMbC6MTrrXgd7tgV7`

## One-time OAuth

Token file:
- `~/.config/openclaw-gdrive/token-docs-openclawshared.json`

Tunnel from your Mac:

```bash
ssh -N -L 18795:127.0.0.1:18795 <your-vm-ssh-host>
```

Run auth on VM:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  {baseDir}/scripts/auth_docs.py \
  --account desi4k@gmail.com \
  --token ~/.config/openclaw-gdrive/token-docs-openclawshared.json \
  --port 18795
```

You may need to enable the Google Docs API in the same Google Cloud project as your OAuth client.

## Read a Doc

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/read_doc.py \
  --token ~/.config/openclaw-gdrive/token-docs-openclawshared.json \
  --doc-id <docId>
```

## Append text to a Doc

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/append_doc.py \
  --token ~/.config/openclaw-gdrive/token-docs-openclawshared.json \
  --doc-id <docId> \
  --text "Hello"
```
