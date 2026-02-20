Subject: ForexFactory “Equity Millipede” acquisition playbook (Apify → Drive → OpenClaw)

This email captures the working instructions + lessons learned from getting ForexFactory thread content (Cloudflare-protected) into a usable format for synthesis.

## What worked (the breakthrough)
- Apify Playwright run that **saves real rendered HTML** (not empty shells) produced ZIPs containing `html-*` files with post content (`edit########` / `post_message_########`).
- The resulting ZIP (example: “records (6).zip”) is directly usable for parsing + summarization.

## Why we needed Apify
- Direct server-side fetches from the VM fail:
  - `web_fetch` → **403 “Just a moment…”** (Cloudflare)
- Local OpenClaw browser automation was unavailable at the time:
  - `browser(...)` → timed out reaching browser control service

## Apify run settings (recommended baseline)
Use these as defaults for the forum crawl:
- Concurrency: **1**
- Delay: **3–8s** between requests
- Proxy: **Residential**
- HTML transformer: avoid Readability if it strips content; prefer **none/raw** for forums
- Save linked files content-types: include **`text/html`**

### Include / exclude URL patterns (reduce noise + blocks)
Include (keep tight):
- `https://www.forexfactory.com/thread/245149-building-an-equity-millipede*`
- `https://www.forexfactory.com/thread/245149-building-an-equity-millipede?page=*`

Exclude (important):
- `*reply*`
- `*quote=*`
- `*goto=*`
- `*login*`, `*register*` (optional)

## Scaling strategy: chunked crawls + overlap (prevents “too large” + edge misses)
Goal: up to ~373 pages without producing an unmanageably large export.

Recommended approach:
- Run multiple crawls with **max ~50 pages per run**
- Use **~10 pages overlap** between runs to protect against:
  - missed “next page” discovery
  - occasional blocked/failed pages
  - export gaps

Suggested start pages (50 pages/run, 10-page overlap):
- 1, 41, 81, 121, 161, 201, 241, 281, 321, 361

Naming convention (so merging is easy):
- `ff_p001.zip`, `ff_p041.zip`, …

## Transport to the agent
- Email is unreliable for the agent to “verify receipt” (agent can’t read inbox). Prefer:
  - Upload ZIPs to Google Drive
  - Share as “Anyone with link: Viewer”
  - Send the **direct file link**:
    - `https://drive.google.com/file/d/<FILE_ID>/view?usp=sharing`

## Parsing/merge notes (for later)
- Each HTML snapshot contains stable identifiers:
  - `edit########` and/or `post_message_########`
- Overlap can be de-duped by those IDs.

## Security note
- Be careful exporting/sharing anything that includes cookies/session snapshots.
- Avoid publicly posting sensitive items like `cf_clearance`.
