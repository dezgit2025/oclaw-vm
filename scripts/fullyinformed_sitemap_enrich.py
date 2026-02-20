#!/usr/bin/env python3
"""Sitemap-first crawl: collect URLs from WordPress sitemap index, then fetch each URL
and extract title + description.

Outputs:
- progress/fullyinformed_urls.csv
- progress/fullyinformed_urls.jsonl

Politeness:
- sequential requests
- delay between requests

Usage:
  python3 scripts/fullyinformed_sitemap_enrich.py \
    --base-sitemap https://www.fullyinformed.com/wp-sitemap.xml \
    --include posts,pages \
    --delay 2.0 \
    --limit 0

"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable, Optional

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
}

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class PageMeta:
    url: str
    title: str = ""
    description: str = ""
    status: int = 0
    error: str = ""


def http_get(url: str, timeout: int = 30) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            data = resp.read()
            headers = dict(resp.headers)
            return status, data, headers
    except urllib.error.HTTPError as e:
        data = e.read() if hasattr(e, "read") else b""
        return int(e.code), data, dict(getattr(e, "headers", {}) or {})


def parse_sitemap_index(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    locs = []
    for sm in root.findall("sm:sitemap", NS):
        loc = sm.findtext("sm:loc", default="", namespaces=NS).strip()
        if loc:
            locs.append(loc)
    return locs


def parse_urlset(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    locs = []
    for url in root.findall("sm:url", NS):
        loc = url.findtext("sm:loc", default="", namespaces=NS).strip()
        if loc:
            locs.append(loc)
    return locs


def which_sitemap_kind(url: str) -> str:
    # WP default patterns: wp-sitemap-posts-post-1.xml, wp-sitemap-posts-page-1.xml,
    # wp-sitemap-taxonomies-category-1.xml, etc.
    m = re.search(r"/wp-sitemap-(posts|taxonomies)-([a-zA-Z0-9_-]+)-\d+\.xml$", url)
    if not m:
        return "other"
    group, kind = m.group(1), m.group(2)
    if group == "posts":
        if kind.startswith("post"):
            return "posts"
        if kind.startswith("page"):
            return "pages"
        return f"posts:{kind}"
    if group == "taxonomies":
        return f"taxonomies:{kind}"
    return "other"


def extract_title(html: str) -> str:
    # Prefer OG title if present
    for pat in [
        r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']\s*/?>',
        r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:title["\']\s*/?>',
    ]:
        m = re.search(pat, html, flags=re.I)
        if m:
            return html_unescape(m.group(1)).strip()

    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    if m:
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        return html_unescape(t)
    return ""


def extract_description(html: str) -> str:
    # Prefer meta description, then OG description
    for pat in [
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']\s*/?>',
        r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']\s*/?>',
        r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']\s*/?>',
        r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:description["\']\s*/?>',
    ]:
        m = re.search(pat, html, flags=re.I)
        if m:
            return html_unescape(m.group(1)).strip()
    return ""


def html_unescape(s: str) -> str:
    # minimal unescape for common entities
    s = s.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    s = s.replace("&lt;", "<").replace("&gt;", ">")
    return s


def extract_snippet(html: str, max_len: int = 220) -> str:
    # Remove scripts/styles
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.I | re.S)
    # Prefer paragraph inside main WP content container if present
    m = re.search(r"class=\"[^\"]*(entry-content|post-content|content-area)[^\"]*\"[^>]*>(.*?)</(div|section|article)>", html, flags=re.I | re.S)
    scope = m.group(2) if m else html
    m2 = re.search(r"<p\b[^>]*>(.*?)</p>", scope, flags=re.I | re.S)
    chunk = m2.group(1) if m2 else scope
    # Strip tags
    chunk = re.sub(r"<[^>]+>", " ", chunk)
    chunk = html_unescape(chunk)
    chunk = re.sub(r"\s+", " ", chunk).strip()
    # Drop boilerplate-y starts
    chunk = re.sub(r"^(Skip to content|Menu|Search)\s+", "", chunk, flags=re.I)
    if re.search(r"Select to view all results\.?", chunk, flags=re.I):
        return ""
    return chunk[:max_len]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-sitemap", required=True)
    ap.add_argument(
        "--include",
        default="posts",
        help="Comma-separated sitemap types to include: posts,pages,taxonomies. Default: posts",
    )
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    ap.add_argument("--out-csv", default="progress/fullyinformed_urls.csv")
    ap.add_argument("--out-jsonl", default="progress/fullyinformed_urls.jsonl")
    args = ap.parse_args()

    include = {x.strip().lower() for x in args.include.split(",") if x.strip()}

    print(f"Fetching sitemap index: {args.base_sitemap}", flush=True)
    st, data, _ = http_get(args.base_sitemap)
    if st >= 400:
        print(f"ERROR: sitemap index fetch failed: HTTP {st}")
        return 2

    sitemap_urls = parse_sitemap_index(data)
    if not sitemap_urls:
        # Sometimes base sitemap is a urlset itself
        try:
            urls = parse_urlset(data)
            sitemap_urls = []
        except Exception:
            urls = []
        if urls:
            sitemap_urls = []
            all_urls = urls
        else:
            print("ERROR: no sitemaps found in index")
            return 2
    else:
        all_urls: list[str] = []

        for sm_url in sitemap_urls:
            kind = which_sitemap_kind(sm_url)
            kind_bucket = kind.split(":", 1)[0]
            if kind_bucket.startswith("taxonomies"):
                if "taxonomies" not in include:
                    continue
            else:
                # posts / pages / other
                if kind_bucket not in include:
                    continue
            print(f"Fetching sitemap: {sm_url} (kind={kind})", flush=True)
            st2, data2, _ = http_get(sm_url)
            if st2 >= 400:
                print(f"  WARN: sitemap fetch failed HTTP {st2}: {sm_url}")
                continue
            try:
                urls = parse_urlset(data2)
            except Exception as e:
                print(f"  WARN: parse failed: {sm_url}: {e}")
                continue
            all_urls.extend(urls)
            time.sleep(max(0.0, args.delay))

    # De-dupe preserving order
    seen = set()
    urls_unique = []
    for u in all_urls:
        if u in seen:
            continue
        seen.add(u)
        urls_unique.append(u)

    print(f"Total URLs from sitemaps (unique): {len(urls_unique)}", flush=True)

    # Prepare output
    import os

    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)

    with open(args.out_csv, "w", newline="", encoding="utf-8") as fcsv, open(
        args.out_jsonl, "w", encoding="utf-8"
    ) as fjsonl:
        w = csv.DictWriter(
            fcsv,
            fieldnames=["url", "status", "title", "description", "error"],
        )
        w.writeheader()

        for i, url in enumerate(urls_unique, start=1):
            if args.limit and i > args.limit:
                break

            meta = PageMeta(url=url)
            st3, body, headers = http_get(url)
            meta.status = st3
            if st3 >= 400:
                meta.error = f"HTTP {st3}"
            else:
                ctype = (headers.get("Content-Type") or "").lower()
                # best-effort decode
                enc = "utf-8"
                m = re.search(r"charset=([a-zA-Z0-9_-]+)", ctype)
                if m:
                    enc = m.group(1)
                try:
                    html = body.decode(enc, errors="ignore")
                except Exception:
                    html = body.decode("utf-8", errors="ignore")

                meta.title = extract_title(html)
                meta.description = extract_description(html)
                if not meta.description:
                    meta.description = extract_snippet(html)

            w.writerow(
                {
                    "url": meta.url,
                    "status": meta.status,
                    "title": meta.title,
                    "description": meta.description,
                    "error": meta.error,
                }
            )
            fjsonl.write(json.dumps(meta.__dict__, ensure_ascii=False) + "\n")

            if i % 25 == 0:
                print(f"Processed {i}/{len(urls_unique)}", flush=True)

            time.sleep(max(0.0, args.delay))

    print(f"Wrote: {args.out_csv}", flush=True)
    print(f"Wrote: {args.out_jsonl}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
