"""Display functions for memory health dashboard."""
from datetime import datetime, timezone


ICONS = {"GREEN": "\u2705", "YELLOW": "\U0001f7e1", "RED": "\U0001f534"}
LABELS = {
    (9, 10): "EXCELLENT", (7, 8): "HEALTHY",
    (5, 6): "ATTENTION", (3, 4): "UNHEALTHY", (0, 2): "BROKEN",
}


def _label(greens):
    for (lo, hi), label in LABELS.items():
        if lo <= greens <= hi:
            return label
    return "UNKNOWN"


def display_dashboard(scores, greens, details):
    """Print the box-visual health dashboard."""
    label = _label(greens)
    bar = "\u2588" * (greens * 2) + "\u2591" * ((10 - greens) * 2)
    print(f"\u2554{'=' * 44}\u2557")
    print(f"\u2551  MEMORY HEALTH: {greens}/10 {ICONS.get(('GREEN' if greens >= 7 else 'YELLOW' if greens >= 5 else 'RED'), '')}  {label:>16}  \u2551")
    print(f"\u2551  {bar}  \u2551")
    print(f"\u2560{'=' * 44}\u2563")
    for name, (rating, value, target) in scores.items():
        icon = ICONS.get(rating, "?")
        print(f"\u2551  {name:<22}{value:>8}  {icon} {target:<8}\u2551")
    print(f"\u2560{'=' * 44}\u2563")
    d = details
    print(f"\u2551  Active: {d['active']:<5} Inactive: {d['inactive']:<5} Total: {d['total']:<5}\u2551")
    print(f"\u2551  Pinned: {d['pinned']:<5} Permanent: {d['permanent']:<14}  \u2551")
    print(f"\u2551  Newest: {d['newest']}  Oldest: {d['oldest']}    \u2551")
    print(f"\u255a{'=' * 44}\u255d")


def display_log_line(scores, greens, details):
    """Print one-liner for cron log."""
    label = _label(greens)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    parts = [f"health:{greens}/10:{label}", f"active:{details['active']}"]
    for name, (rating, value, _) in scores.items():
        if name in ("Recall rate (30d)", "Growth (30d)", "Stale ratio"):
            key = name.split("(")[0].strip().lower().replace(" ", "_")
            parts.append(f"{key}:{value}({rating})")
    print(f"{ts} | {' '.join(parts)}")
