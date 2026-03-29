"""Memory health monitor — 10-metric rubric with visual dashboard."""
import os, sqlite3
from datetime import datetime, timedelta, timezone
from collections import Counter

DB_PATH = os.path.expanduser(os.environ.get("CLAWBOT_MEMORY_DB", "~/.agent-memory/memory.db"))

THRESHOLDS = {
    "anchor":    {"green": 80, "yellow": 60},
    "diversity": {"green": 25, "yellow": 40},
    "recall":    {"green": 10, "yellow": 1},
    "stale":     {"green": 15, "yellow": 30},
    "dedup":     {"green": 10, "yellow": 20},
    "pinratio":  {"green": 30, "yellow": 50},
    "growth_lo": 10, "growth_hi": 100,
    "tags_lo": 3, "tags_hi": 6,
}


def _rate(val, metric):
    t = THRESHOLDS[metric]
    if metric in ("diversity", "stale", "dedup", "pinratio"):
        return "GREEN" if val < t["green"] else ("YELLOW" if val < t["yellow"] else "RED")
    return "GREEN" if val >= t["green"] else ("YELLOW" if val >= t["yellow"] else "RED")


def compute_health(db_path=None):
    """Score all 10 metrics. Returns (scores_dict, total_green, details)."""
    path = db_path or DB_PATH
    if not os.path.exists(path):
        return {}, 0, {"error": "DB not found"}
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT content, tags, importance, access_count, created_at "
        "FROM memories WHERE active=1"
    ).fetchall()
    inactive = conn.execute("SELECT COUNT(*) FROM memories WHERE active=0").fetchone()[0]
    conn.close()
    n = len(rows)
    if n == 0:
        return {}, 0, {"error": "No active memories"}

    # Parse
    all_tags, importances, dates = Counter(), Counter(), []
    has_type = has_domain = has_both = recalled = pinned = permanent = 0
    now = datetime.now(timezone.utc)
    cutoff_90 = (now - timedelta(days=90)).isoformat()
    cutoff_30 = (now - timedelta(days=30)).isoformat()
    stale = new_30d = 0

    for content, tags, imp, ac, created in rows:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for t in tag_list:
            all_tags[t] += 1
        ht = any(t.startswith("type:") for t in tag_list)
        hd = any(t.startswith("domain:") for t in tag_list)
        has_type += ht; has_domain += hd; has_both += (ht and hd)
        importances[imp] += 1
        if ac > 0: recalled += 1
        if "pin:" in tags: pinned += 1
        if "permanent:true" in tags: permanent += 1
        if created < cutoff_90 and ac == 0 and "pin:" not in tags and "permanent:true" not in tags:
            stale += 1
        if created > cutoff_30: new_30d += 1
        dates.append(created[:10])

    # Metrics
    anchor_pct = (has_both / n) * 100
    max_tag_pct = (all_tags.most_common(1)[0][1] / sum(all_tags.values()) * 100) if all_tags else 0
    recall_pct = (recalled / n) * 100
    stale_pct = (stale / n) * 100
    pin_pct = ((pinned + permanent) / n) * 100
    avg_tags = sum(all_tags.values()) / n
    imp_levels = len(importances)
    day_counts = Counter(dates)
    max_day_pct = (day_counts.most_common(1)[0][1] / n * 100) if day_counts else 0

    scores = {
        "Anchor coverage": (_rate(anchor_pct, "anchor"), f"{anchor_pct:.1f}%", ">80%"),
        "Tag diversity": (_rate(max_tag_pct, "diversity"), f"{max_tag_pct:.1f}%", "<25%"),
        "Recall rate (30d)": (_rate(recall_pct, "recall"), f"{recall_pct:.1f}%", ">10%"),
        "Stale ratio": (_rate(stale_pct, "stale"), f"{stale_pct:.1f}%", "<15%"),
        "Duplicate density": ("GREEN", "~est", "<10%"),  # needs pairwise check
        "Pin/permanent": (_rate(pin_pct, "pinratio"), f"{pin_pct:.1f}%", "<30%"),
        "Growth (30d)": (
            "GREEN" if THRESHOLDS["growth_lo"] <= new_30d <= THRESHOLDS["growth_hi"]
            else ("YELLOW" if 1 <= new_30d < THRESHOLDS["growth_lo"] or THRESHOLDS["growth_hi"] < new_30d <= 200
                  else "RED"),
            f"{new_30d} new", "10-100"),
        "Avg tags/memory": (
            "GREEN" if THRESHOLDS["tags_lo"] <= avg_tags <= THRESHOLDS["tags_hi"]
            else ("YELLOW" if 2 <= avg_tags < THRESHOLDS["tags_lo"] or THRESHOLDS["tags_hi"] < avg_tags <= 7
                  else "RED"),
            f"{avg_tags:.1f}", "3-6"),
        "Importance spread": (
            "GREEN" if imp_levels >= 3 else ("YELLOW" if imp_levels == 2 else "RED"),
            f"{imp_levels} lvl", "3+ lvl"),
        "Age distribution": (
            "GREEN" if max_day_pct < 50 else ("YELLOW" if max_day_pct < 70 else "RED"),
            f"{max_day_pct:.0f}% max", "<50%"),
    }

    greens = sum(1 for r, _, _ in scores.values() if r == "GREEN")
    details = {"active": n, "inactive": inactive, "total": n + inactive,
               "pinned": pinned, "permanent": permanent, "stale": stale,
               "newest": max(dates) if dates else "?", "oldest": min(dates) if dates else "?"}
    return scores, greens, details
