#!/usr/bin/env python3
"""Headless URL fetcher (no JavaScript execution).

This script performs plain HTTP GET requests and extracts readable text from HTML.
It does *not* execute JavaScript (like a browser with JS disabled), but note:
- It does NOT bypass paywalls, login walls, or anti-bot protections.
- Sites like Bloomberg often require JS/cookies and may return 403/robot checks.

Dependencies:
  pip install requests beautifulsoup4

Usage:
  headless_fetch_nojs.py https://example.com
  headless_fetch_nojs.py -f urls.txt -o out.txt
  headless_fetch_nojs.py https://example.com --raw
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def fetch_url(url: str, timeout: int = 15, user_agent: Optional[str] = None) -> requests.Response:
    """Fetch a URL via HTTP GET; no JS is executed."""
    url = normalize_url(url)
    headers = {
        "User-Agent": user_agent or DEFAULT_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    session = requests.Session()
    # No cookies carried over (fresh session, incognito-like)
    session.cookies.clear()

    resp = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp


def extract_text(html: str, include_links: bool = False) -> str:
    """Parse HTML and extract readable text."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style/noscript
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    if include_links:
        for a in soup.find_all("a", href=True):
            label = a.get_text(strip=True)
            href = a.get("href")
            a.string = f"{label} [{href}]" if label else f"[{href}]"

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch URLs with plain HTTP (no JavaScript execution) and output text or raw HTML."
    )
    parser.add_argument("urls", nargs="*", help="URLs to fetch")
    parser.add_argument("-f", "--file", help="File with URLs (one per line)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("-r", "--raw", action="store_true", help="Output raw HTML instead of text")
    parser.add_argument("-l", "--links", action="store_true", help="Include links in extracted text")
    parser.add_argument("-t", "--timeout", type=int, default=15, help="Request timeout (seconds)")
    parser.add_argument("--headers", action="store_true", help="Print response headers")
    parser.add_argument("--user-agent", default=None, help="Override the User-Agent")

    args = parser.parse_args()

    urls = list(args.urls or [])
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            urls.extend(
                line.strip()
                for line in f
                if line.strip() and not line.lstrip().startswith("#")
            )

    if not urls:
        parser.print_help()
        sys.exit(1)

    out_fh = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout

    for url in urls:
        try:
            print("=" * 60, file=out_fh)
            print(f"URL: {url}", file=out_fh)
            print("=" * 60, file=out_fh)

            resp = fetch_url(url, timeout=args.timeout, user_agent=args.user_agent)

            print(f"Status: {resp.status_code} | Size: {len(resp.content)} bytes", file=out_fh)

            if args.headers:
                for k, v in resp.headers.items():
                    print(f"{k}: {v}", file=out_fh)

            print("-" * 60, file=out_fh)

            if args.raw:
                print(resp.text, file=out_fh)
            else:
                print(extract_text(resp.text, include_links=args.links), file=out_fh)

        except requests.RequestException as e:
            print(f"ERROR fetching {url}: {e}", file=out_fh)

    if args.output:
        out_fh.close()
        print(f"Output saved to {args.output}")


if __name__ == "__main__":
    main()
