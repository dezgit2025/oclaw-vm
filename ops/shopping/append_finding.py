#!/usr/bin/env python3

"""Append a single row to ShoppingWatchlist -> Findings tab.

Usage:
  python3 append_finding.py --sheet-id <id> --token <token> --row-json '<json array>'

Row must match Findings header columns.
"""

from __future__ import annotations

import argparse
import json
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--row-json", required=True)
    args = ap.parse_args()

    row = json.loads(args.row_json)

    script = "/home/desazure/.openclaw/workspace/skills/gsheets-openclawshared/scripts/append_row.py"
    py = "/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"

    subprocess.run(
        [
            py,
            script,
            "--token",
            args.token,
            "--sheet-id",
            args.sheet_id,
            "--range",
            "Findings!A:Q",
            "--row",
            json.dumps(row),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
