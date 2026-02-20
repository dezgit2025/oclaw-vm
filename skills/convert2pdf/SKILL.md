---
name: convert2pdf
description: Convert a web page or text/markdown content into a PDF and (optionally) upload it to Google Drive (OpenClawShared). Use when the user says “turn this into a PDF”, “save this page as PDF”, “convert Wayback page to PDF”, or wants a URL → PDF workflow without paywall bypass.
---

# convert2pdf

## Workflow (URL → PDF → Drive)

1) **Fetch readable text**
- Prefer `web_fetch(url, extractMode="markdown")`.
- If the URL is paywalled, do **not** bypass. Suggest Wayback or use user-provided access.

2) **Write the extracted text to a local .md file**
- Save under: `/home/desazure/.openclaw/workspace/exports/convert2pdf/`

3) **Convert markdown/text → PDF**

Run:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  {skill_dir}/scripts/text_to_pdf.py \
  --in /path/to/article.md \
  --out /path/to/article.pdf \
  --title "Optional Title" \
  --source-url "https://..."
```

Notes:
- Uses `fpdf2` + DejaVuSans for Unicode.
- Output is a **text PDF** (not pixel-perfect HTML rendering). Good for reading, archiving, and sharing.

4) **Upload to Google Drive (OpenClawShared)** (optional)

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/upload_file.py \
  --token ~/.config/openclaw-gdrive/token-openclawshared.json \
  --path /path/to/article.pdf
```

5) **Send the Drive link or file id back to the user**

## Naming convention
- `exports/convert2pdf/<slug>-<YYYY-MM-DD>-<source>.pdf`

## Troubleshooting
- If headless Chrome PDF printing hangs or the browser control server is down, use this skill’s text-PDF approach.
- If `fpdf2` throws layout errors, ensure long URLs are wrapped (the script already does this).
