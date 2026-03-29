#!/usr/bin/env python3
"""Export active memories from SQLite to a JSON fixture for benchmarking."""

import argparse
import json
import os
import sqlite3
import sys


def export_memories(db_path: str, output_path: str) -> int:
    """Read all active memories from the DB and write to JSON.

    Returns the number of memories exported.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, content, tags, project, importance, access_count, created_at "
        "FROM memories WHERE active = 1 ORDER BY created_at"
    ).fetchall()
    conn.close()

    memories = [dict(r) for r in rows]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(memories, f, indent=2)

    return len(memories)


def main():
    parser = argparse.ArgumentParser(description="Export active memories to JSON fixture")
    parser.add_argument("--db", required=True, help="Path to memory.db")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    count = export_memories(args.db, args.output)
    print(f"Exported {count} memories to {args.output}")


if __name__ == "__main__":
    main()
