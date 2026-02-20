#!/usr/bin/env python3
"""Convert UTF-8 text/markdown into a simple readable PDF.

This produces a *text PDF* (not HTML-rendered). It is designed to be robust
in headless/server environments.

Dependencies:
- fpdf2 (installed in the workspace .venv-gmail)
- DejaVuSans font present at /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf

Usage:
  text_to_pdf.py --in article.md --out article.pdf [--title "..."] [--source-url "..."]
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from fpdf import FPDF

DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def slug_safe(s: str) -> str:
    return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in s).strip("_")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input .txt/.md file (UTF-8)")
    ap.add_argument("--out", dest="out", required=True, help="Output .pdf path")
    ap.add_argument("--title", default=None)
    ap.add_argument("--source-url", default=None)
    ap.add_argument("--font", default=DEFAULT_FONT)
    ap.add_argument("--font-size", type=int, default=11)
    ap.add_argument("--wrap-width", type=int, default=110, help="Approx character wrap width")
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    text = inp.read_text(encoding="utf-8", errors="replace")

    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Unicode-capable font
    pdf.add_font("DejaVu", "", args.font)
    pdf.set_font("DejaVu", size=args.font_size)

    epw = pdf.epw  # effective page width

    def write_line(line: str) -> None:
        # Wrap long tokens (URLs) too
        for wline in textwrap.wrap(
            line,
            width=args.wrap_width,
            break_long_words=True,
            break_on_hyphens=False,
        ):
            pdf.multi_cell(epw, 5, wline)

    # Optional header
    if args.title:
        pdf.set_font("DejaVu", size=args.font_size + 3)
        write_line(args.title)
        pdf.ln(2)
        pdf.set_font("DejaVu", size=args.font_size)

    if args.source_url:
        write_line(f"Source: {args.source_url}")
        pdf.ln(2)

    # Body
    for line in text.splitlines():
        if not line.strip():
            pdf.ln(4)
        else:
            write_line(line)

    pdf.output(str(out))


if __name__ == "__main__":
    main()
