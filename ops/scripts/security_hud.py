#!/usr/bin/env python3
"""Extract a compact 'Security HUD' block from latest security scan reports.

Reads:
- logs/security-scan-latest.md (Tier 1)
- logs/security-deepdive-latest.md (Tier 2, optional)

Outputs markdown to stdout, suitable for pasting into the nightly carryover.

Design goals:
- Zero secrets; only reads local markdown reports.
- Robust to missing files.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/home/desazure/.openclaw/workspace")
T1 = ROOT / "logs/security-scan-latest.md"
T2 = ROOT / "logs/security-deepdive-latest.md"


def _extract_dashboard_and_lines(p: Path, max_bullets: int = 6):
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")

    # Find first 'Dashboard:' line
    dash = None
    m = re.search(r"^\*\*Dashboard:\*\*\s*`([^`]+)`\s*$", text, flags=re.M)
    if m:
        dash = m.group(1).strip()

    # Extract the Executive Summary bullet lines (top section)
    # Heuristic: lines after '## ✅ Executive Summary' until the next '## ' heading.
    summary_lines: list[str] = []
    m2 = re.search(r"^##\s+✅\s+Executive Summary.*?$", text, flags=re.M)
    if m2:
        start = m2.end()
        tail = text[start:]
        # stop at next heading
        stop = re.search(r"^##\s+", tail, flags=re.M)
        block = tail[: stop.start()] if stop else tail
        for line in block.splitlines():
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("**Dashboard:**"):
                continue
            if line.lstrip().startswith("-"):
                summary_lines.append(line.strip())

    return {
        "path": str(p),
        "dashboard": dash,
        "bullets": summary_lines[:max_bullets],
    }


def main():
    t1 = _extract_dashboard_and_lines(T1)
    t2 = _extract_dashboard_and_lines(T2)

    out: list[str] = []
    out.append("## 🛡️ Security HUD")

    if not t1:
        out.append("- Tier 1: 🟡 No report found (`logs/security-scan-latest.md` missing)")
    else:
        dash = f"`{t1['dashboard']}`" if t1.get("dashboard") else "(no dashboard line found)"
        out.append(f"- Tier 1 (daily scan): {dash}")
        for b in t1["bullets"]:
            out.append(f"  {b}")

    if not t2:
        out.append("- Tier 2 (deep dive): 🟡 Not run / no report present")
    else:
        dash = f"`{t2['dashboard']}`" if t2.get("dashboard") else "(no dashboard line found)"
        out.append(f"- Tier 2 (deep dive): {dash}")
        for b in t2["bullets"]:
            out.append(f"  {b}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
