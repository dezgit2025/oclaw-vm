"""
Memory Lifecycle Manager
========================
Handles stale memory cleanup and quarterly review.

Rule: memories >90 days old with access_count=0 and
not pinned/permanent are soft-deleted (active=0).
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.expanduser(os.environ.get("CLAWBOT_MEMORY_DB", "~/.agent-memory/memory.db"))
LOG_DIR = os.path.expanduser("~/.openclaw/logs/memory-lifecycle")


def cleanup_stale_memories(dry_run: bool = False) -> int:
    """Soft-delete memories >90 days old with 0 accesses."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    conn = sqlite3.connect(DB_PATH)

    candidates = conn.execute("""
        SELECT id, content, tags, created_at, access_count
        FROM memories
        WHERE active = 1 AND created_at < ? AND access_count = 0
    """, (cutoff,)).fetchall()

    deleted = []
    for mem_id, content, tags, created_at, _ in candidates:
        if "permanent:true" in tags or "pin:" in tags:
            continue
        if not dry_run:
            conn.execute(
                "UPDATE memories SET active = 0 WHERE id = ?",
                (mem_id,),
            )
        deleted.append((mem_id, content[:80], tags, created_at))

    if not dry_run:
        conn.commit()
    conn.close()

    _log_cleanup(deleted, len(candidates) - len(deleted), dry_run)
    return len(deleted)


def list_permanent() -> list:
    """List all permanent:true memories for quarterly review."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, substr(content, 1, 80), tags
        FROM memories
        WHERE active = 1 AND tags LIKE '%permanent:true%'
    """).fetchall()
    conn.close()
    return rows


def _log_cleanup(deleted, exempt, dry_run):
    """Write cleanup results to log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    prefix = "DRY-RUN " if dry_run else ""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(LOG_DIR, f"{today}-cleanup.log")
    with open(path, "a") as f:
        f.write(f"{prefix}Stale cleanup: {len(deleted)} deleted, "
                f"{exempt} exempt\n")
        for mem_id, content, tags, created_at in deleted:
            f.write(f"  DELETED {mem_id}: {content} "
                    f"(created: {created_at})\n")


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    count = cleanup_stale_memories(dry_run=dry)
    mode = "would delete" if dry else "deleted"
    print(f"Stale cleanup: {mode} {count} memories")
