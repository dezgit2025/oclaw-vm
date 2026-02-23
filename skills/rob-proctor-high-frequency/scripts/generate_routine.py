#!/usr/bin/env python3
"""Rob Proctor — 3-minute high-frequency morning routine generator.

- Picks 3 random affirmations from affirmations.md
- Outputs a concise routine (breath + affirmations + gratitude + one win)

Safe: local only, no network, no secrets.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
AFF_PATH = HERE / "affirmations.md"


def load_affirmations() -> list[str]:
    if not AFF_PATH.exists():
        raise SystemExit(f"Missing affirmations file: {AFF_PATH}")
    lines = []
    for raw in AFF_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- "):
            s = line[2:].strip()
            if s:
                lines.append(s)
    if len(lines) < 3:
        raise SystemExit("Need at least 3 affirmations in affirmations.md")
    return lines


def main() -> None:
    affs = load_affirmations()
    picks = random.sample(affs, k=3)

    print("Rob Proctor — 3-minute High Frequency Routine\n")
    print("0:00–1:00  Breath")
    print("- 6 slow breaths: inhale 4s (nose), exhale 6s (mouth)")
    print("- On each exhale: think ‘Release.’\n")

    print("1:00–2:00  Affirmations (say these 3)")
    for a in picks:
        # keep clean
        a = re.sub(r"\s+", " ", a).strip()
        print(f"- {a}")
    print()

    print("2:00–3:00  Gratitude + One Win")
    print("- Gratitude (1 sentence): I’m grateful for ______ because ______.")
    print("- Today’s win (1 sentence): ______.")
    print("- First step (<5 min): ______.")
    print("\nClosing")
    print("- Thank you, God for my abundance, wealth, and health.")


if __name__ == "__main__":
    main()
