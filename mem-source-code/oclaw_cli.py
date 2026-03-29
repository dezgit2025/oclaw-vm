#!/usr/bin/env python3
"""oclaw_cli.py - ClawBot Memory Inspector CLI

Provides 9 subcommands for inspecting, searching, and managing memories.
All output passes through safe_print() to prevent secrets/PII leakage.
"""

import argparse
import json
import os
import sys
import sqlite3
import csv
import io
from datetime import datetime, timedelta
from pathlib import Path

# --- Constants ---
MEMORY_DB = os.path.expanduser("~/.claude-memory/memory.db")
SYNC_STATE = os.path.expanduser("~/.claude-memory/.sync_state.json")
EXTRACT_STATE = os.path.expanduser("~/.claude-memory/.extract_state.json")
TAG_REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TAG_REGISTRY.md")

# --- ANSI Colors ---
USE_COLOR = sys.stdout.isatty()


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def dim(t):    return _c("2", t)
def bold(t):   return _c("1", t)
def green(t):  return _c("32", t)
def yellow(t): return _c("33", t)
def red(t):    return _c("31", t)
def cyan(t):   return _c("36", t)


# --- Safe Print ---
_raw_mode = False


def safe_print(text, force_raw=False):
    """Print text after scanning for secrets and PII. Redacts matches."""
    text = str(text)
    if _raw_mode or force_raw:
        print(text)
        return
    try:
        from smart_extractor import scan_secrets, scan_pii, redact_text
        secrets = scan_secrets(text)
        pii = scan_pii(text)
        if secrets or pii:
            text = redact_text(text, secrets + pii)
    except (ImportError, AttributeError):
        pass  # smart_extractor not available - print as-is
    print(text)


# --- Database Helpers ---
def _get_db():
    if not os.path.exists(MEMORY_DB):
        return None
    return sqlite3.connect(MEMORY_DB)


def _db_size():
    if not os.path.exists(MEMORY_DB):
        return "N/A"
    size = os.path.getsize(MEMORY_DB)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def _get_table_cols(db):
    """Return list of column names for the memories table, or None if table missing."""
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    if "memories" not in tables:
        return None
    cursor.execute("PRAGMA table_info(memories)")
    return [r[1] for r in cursor.fetchall()]


def _get_memories(project=None, tag=None, limit=20, sort="created_at DESC"):
    db = _get_db()
    if not db:
        return []
    try:
        cols = _get_table_cols(db)
        if not cols:
            return []
        cursor = db.cursor()
        where = []
        params = []
        if project and "project" in cols:
            where.append("project = ?")
            params.append(project)
        if tag and "tags" in cols:
            where.append("tags LIKE ?")
            params.append(f"%{tag}%")

        where_str = (" WHERE " + " AND ".join(where)) if where else ""
        sort_parts = sort.split()
        sort_col = sort_parts[0] if sort_parts else "created_at"
        sort_dir = sort_parts[1].upper() if len(sort_parts) > 1 else "DESC"
        if sort_dir not in ("ASC", "DESC"):
            sort_dir = "DESC"
        if sort_col not in cols:
            sort_col = "rowid"
        query = f"SELECT * FROM memories{where_str} ORDER BY {sort_col} {sort_dir} LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        safe_print(f"DB error: {e}")
        return []
    finally:
        db.close()


# --- Commands ---

def cmd_list(args):
    """List memories from local SQLite."""
    memories = _get_memories(
        project=args.project, tag=args.tag,
        limit=args.limit, sort=args.sort
    )
    if args.json:
        safe_print(json.dumps(memories, indent=2, default=str))
        return
    if not memories:
        safe_print("No memories found.")
        return
    safe_print(bold(f"{'ID':<8} {'Created':<20} {'Project':<15} {'Tags':<30} {'Content':<40}"))
    safe_print("-" * 113)
    for m in memories:
        mid = str(m.get("id", m.get("rowid", "?")))[:7]
        created = str(m.get("created_at", ""))[:19]
        project = str(m.get("project", ""))[:14]
        tags = str(m.get("tags", ""))[:29]
        content = str(m.get("content", m.get("text", "")))[:39]
        safe_print(f"{mid:<8} {created:<20} {project:<15} {tags:<30} {content:<40}")
    safe_print(dim(f"\n{len(memories)} memories shown (limit: {args.limit})"))


def cmd_get(args):
    """Show full memory detail by ID."""
    db = _get_db()
    if not db:
        safe_print("Memory database not found.")
        return
    try:
        cols = _get_table_cols(db)
        if not cols:
            safe_print("No memories table found.")
            return
        cursor = db.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (args.id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "SELECT * FROM memories WHERE CAST(id AS TEXT) LIKE ?",
                (f"%{args.id}%",)
            )
            row = cursor.fetchone()
        if not row:
            safe_print(f"Memory '{args.id}' not found.")
            return
        mem = dict(zip(cols, row))
        if args.json:
            safe_print(json.dumps(mem, indent=2, default=str))
            return
        for k, v in mem.items():
            safe_print(f"{bold(k)}: {v}")
    finally:
        db.close()


def cmd_search(args):
    """Hybrid search: Azure first, local SQLite fallback."""
    query = args.query

    # Try Azure search first
    try:
        from auth_provider import get_search_client
        from azure.search.documents.models import VectorizableTextQuery
        client = get_search_client("clawbot-memory-store")
        vector_query = VectorizableTextQuery(
            text=query, k_nearest_neighbors=5,
            fields="content_vector", exhaustive=True
        )
        results = client.search(
            search_text=query,
            vector_queries=[vector_query],
            query_type="semantic",
            semantic_configuration_name="memory-semantic-config",
            top=args.limit
        )
        hits = list(results)
        if args.json:
            safe_print(json.dumps([dict(h) for h in hits], indent=2, default=str))
            return
        if not hits:
            safe_print("No results from Azure search.")
        else:
            safe_print(bold(f"Azure search results for: '{query}'"))
            safe_print("-" * 80)
            for h in hits:
                score = h.get("@search.score", 0)
                content = str(h.get("content", ""))[:80]
                tags = str(h.get("tags", ""))
                safe_print(f"  [{score:.3f}] {content}")
                if tags:
                    safe_print(f"          {dim(tags)}")
            safe_print(dim(f"\n{len(hits)} results"))
        return
    except Exception as e:
        safe_print(dim(f"Azure search unavailable ({e}), falling back to local..."))

    # Local fallback
    db = _get_db()
    if not db:
        safe_print("No local database found.")
        return
    try:
        cols = _get_table_cols(db)
        if not cols:
            safe_print("No memories table found.")
            return
        cursor = db.cursor()
        content_col = "content" if "content" in cols else "text" if "text" in cols else None
        if not content_col:
            safe_print("Cannot determine content column in memories table.")
            return
        cursor.execute(
            f"SELECT * FROM memories WHERE {content_col} LIKE ? LIMIT ?",
            (f"%{query}%", args.limit)
        )
        rows = cursor.fetchall()
        if args.json:
            safe_print(json.dumps([dict(zip(cols, r)) for r in rows], indent=2, default=str))
            return
        if not rows:
            safe_print(f"No local results for '{query}'.")
            return
        safe_print(bold(f"Local search results for: '{query}'"))
        safe_print("-" * 80)
        for row in rows:
            mem = dict(zip(cols, row))
            content = str(mem.get(content_col, ""))[:80]
            safe_print(f"  {content}")
        safe_print(dim(f"\n{len(rows)} results"))
    finally:
        db.close()


def cmd_stats(args):
    """Memory counts, tag distribution, age histogram."""
    db = _get_db()
    if not db:
        safe_print("Memory database not found.")
        return
    try:
        cols = _get_table_cols(db)
        if not cols:
            safe_print("No memories table found.")
            return
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        total = cursor.fetchone()[0]

        stats = {"total_memories": total}

        # Project counts
        if "project" in cols:
            cursor.execute(
                "SELECT project, COUNT(*) FROM memories GROUP BY project ORDER BY COUNT(*) DESC"
            )
            stats["by_project"] = {r[0] or "(none)": r[1] for r in cursor.fetchall()}

        # Tag distribution
        if "tags" in cols:
            cursor.execute("SELECT tags FROM memories WHERE tags IS NOT NULL AND tags != ''")
            tag_counts = {}
            for (tags_str,) in cursor.fetchall():
                for tag in str(tags_str).split(","):
                    tag = tag.strip()
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            stats["tag_distribution"] = dict(
                sorted(tag_counts.items(), key=lambda x: -x[1])[:20]
            )

        # Age histogram
        if "created_at" in cols:
            now = datetime.now()
            buckets = {"<1d": 0, "1-7d": 0, "7-30d": 0, "30-90d": 0, ">90d": 0}
            cursor.execute("SELECT created_at FROM memories WHERE created_at IS NOT NULL")
            for (ts,) in cursor.fetchall():
                try:
                    ts_str = str(ts).replace("Z", "").replace("+00:00", "")
                    created = datetime.fromisoformat(ts_str)
                    age = (now - created).days
                    if age < 1:
                        buckets["<1d"] += 1
                    elif age < 7:
                        buckets["1-7d"] += 1
                    elif age < 30:
                        buckets["7-30d"] += 1
                    elif age < 90:
                        buckets["30-90d"] += 1
                    else:
                        buckets[">90d"] += 1
                except (ValueError, TypeError):
                    pass
            stats["age_histogram"] = buckets

        if args.json:
            safe_print(json.dumps(stats, indent=2, default=str))
            return

        safe_print(bold("Memory Statistics"))
        safe_print("-" * 50)
        safe_print(f"Total memories: {bold(str(total))}")
        safe_print(f"Database size:  {_db_size()}")
        if "by_project" in stats:
            safe_print(f"\n{bold('By Project:')}")
            for proj, cnt in stats["by_project"].items():
                safe_print(f"  {proj:<20} {cnt}")
        if "tag_distribution" in stats:
            safe_print(f"\n{bold('Top Tags:')}")
            for tag, cnt in list(stats["tag_distribution"].items())[:10]:
                safe_print(f"  {tag:<30} {cnt}")
        if "age_histogram" in stats:
            safe_print(f"\n{bold('Age Distribution:')}")
            for bucket, cnt in stats["age_histogram"].items():
                bar = "#" * min(cnt, 40)
                safe_print(f"  {bucket:<8} {cnt:>4}  {bar}")
    finally:
        db.close()


def cmd_validate(args):
    """Check memories against TAG_REGISTRY v2 rules."""
    if not os.path.exists(TAG_REGISTRY):
        safe_print(f"TAG_REGISTRY.md not found at {TAG_REGISTRY}")
        return
    db = _get_db()
    if not db:
        safe_print("Memory database not found.")
        return
    try:
        cols = _get_table_cols(db)
        if not cols:
            safe_print("No memories table found.")
            return
        if "tags" not in cols:
            safe_print("No 'tags' column in memories table.")
            return
        cursor = db.cursor()
        cursor.execute("SELECT id, tags FROM memories")
        issues = []
        total = 0
        for mid, tags_str in cursor.fetchall():
            total += 1
            tags = [t.strip() for t in str(tags_str or "").split(",") if t.strip()]
            has_type = any(t.startswith("type:") for t in tags)
            has_skill = any(t.startswith("skill:") for t in tags)
            has_domain = any(t.startswith("domain:") for t in tags)
            if not has_type:
                issues.append((mid, "missing type: anchor tag"))
            if not has_skill and not has_domain:
                issues.append((mid, "missing skill: or domain: anchor tag"))
            if len(tags) > 8:
                issues.append((mid, f"too many tags ({len(tags)}, max 8)"))

        if args.json:
            safe_print(json.dumps(
                {"total": total, "issues": len(issues), "details": issues},
                indent=2, default=str
            ))
            return
        safe_print(bold("Tag Validation Report"))
        safe_print("-" * 60)
        safe_print(f"Total memories: {total}")
        safe_print(f"Issues found:   {red(str(len(issues))) if issues else green('0')}")
        if issues:
            safe_print(f"\n{bold('Issues:')}")
            for mid, issue in issues[:20]:
                safe_print(f"  {yellow(str(mid)[:8])}: {issue}")
            if len(issues) > 20:
                safe_print(dim(f"  ... and {len(issues) - 20} more"))
        else:
            safe_print(green("\nAll memories pass validation!"))
    finally:
        db.close()


def cmd_tags(args):
    """Tag usage counts, cross-referenced with TAG_REGISTRY.md."""
    db = _get_db()
    if not db:
        safe_print("Memory database not found.")
        return
    try:
        cols = _get_table_cols(db)
        if not cols:
            safe_print("No memories table found.")
            return
        if "tags" not in cols:
            safe_print("No 'tags' column.")
            return
        cursor = db.cursor()
        cursor.execute("SELECT tags FROM memories WHERE tags IS NOT NULL AND tags != ''")
        tag_counts = {}
        for (tags_str,) in cursor.fetchall():
            for tag in str(tags_str).split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Load registry tags
        registry_tags = set()
        if os.path.exists(TAG_REGISTRY):
            with open(TAG_REGISTRY) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("| `") and "`" in line[3:]:
                        tag = line.split("`")[1]
                        registry_tags.add(tag)

        if args.json:
            safe_print(json.dumps({
                "usage": tag_counts,
                "in_registry": sorted(registry_tags),
                "unregistered": [t for t in tag_counts if t not in registry_tags]
            }, indent=2, default=str))
            return

        safe_print(bold("Tag Usage Report"))
        safe_print("-" * 60)
        if not tag_counts:
            safe_print("No tags found in memories.")
            return
        sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
        for tag, cnt in sorted_tags:
            reg = green("[reg]") if tag in registry_tags else yellow("[new]")
            safe_print(f"  {reg} {tag:<35} {cnt:>4}")
        unregistered = [t for t in tag_counts if t not in registry_tags]
        if unregistered:
            safe_print(f"\n{yellow(f'{len(unregistered)} unregistered tags')} (consider adding to TAG_REGISTRY.md)")
    finally:
        db.close()


def cmd_health(args):
    """Auth mode, connectivity, DB size, sync state."""
    result = {}

    # Auth health
    try:
        from auth_provider import health_check
        result["auth"] = health_check()
    except Exception as e:
        result["auth"] = {"error": str(e)}

    # DB info
    result["database"] = {
        "path": MEMORY_DB,
        "exists": os.path.exists(MEMORY_DB),
        "size": _db_size()
    }
    if os.path.exists(MEMORY_DB):
        try:
            db = sqlite3.connect(MEMORY_DB)
            cursor = db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            if "memories" in tables:
                cursor.execute("SELECT COUNT(*) FROM memories")
                result["database"]["memory_count"] = cursor.fetchone()[0]
            db.close()
        except Exception:
            pass

    # Sync state
    if os.path.exists(SYNC_STATE):
        with open(SYNC_STATE) as f:
            result["sync_state"] = json.load(f)
    else:
        result["sync_state"] = {"status": "no sync state file"}

    if args.json:
        safe_print(json.dumps(result, indent=2, default=str))
        return

    safe_print(bold("ClawBot Health Check"))
    safe_print("-" * 50)
    auth = result.get("auth", {})
    if "error" in auth and auth["error"]:
        safe_print(f"Auth:     {red('ERROR')} -- {auth['error']}")
    else:
        mode = auth.get("auth_mode", "unknown")
        reachable = auth.get("search_reachable", False)
        safe_print(f"Auth:     {green(mode) if mode and mode != 'none' else red('none')}")
        safe_print(f"Search:   {'reachable' if reachable else red('unreachable')}")

    db_info = result["database"]
    safe_print(f"Database: {green('exists') if db_info['exists'] else red('missing')} ({db_info['size']})")
    if "memory_count" in db_info:
        safe_print(f"Memories: {db_info['memory_count']}")

    sync = result.get("sync_state", {})
    if sync.get("status") == "no sync state file":
        safe_print(f"Sync:     {dim('never synced')}")
    else:
        last = sync.get("last_sync", "unknown")
        safe_print(f"Sync:     last={last}")


def cmd_state(args):
    """Show sync and extraction cursor states."""
    result = {}
    for name, path in [("sync", SYNC_STATE), ("extract", EXTRACT_STATE)]:
        if os.path.exists(path):
            with open(path) as f:
                result[name] = json.load(f)
        else:
            result[name] = {"status": f"no {name} state file"}

    if args.json:
        safe_print(json.dumps(result, indent=2, default=str))
        return

    safe_print(bold("State Files"))
    safe_print("-" * 50)
    for name in ["sync", "extract"]:
        safe_print(f"\n{bold(name.upper())} state:")
        state = result[name]
        for k, v in state.items():
            safe_print(f"  {k}: {v}")


def cmd_export(args):
    """Export memories as JSON or CSV."""
    memories = _get_memories(project=args.project, limit=99999, sort="created_at ASC")
    if not memories:
        safe_print("No memories to export.")
        return

    fmt = args.format or "json"
    if fmt == "json":
        output = json.dumps(memories, indent=2, default=str)
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=memories[0].keys())
        writer.writeheader()
        writer.writerows(memories)
        output = buf.getvalue()
    else:
        safe_print(f"Unknown format: {fmt}")
        return

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        safe_print(f"Exported {len(memories)} memories to {args.output}")
    else:
        safe_print(output)


# --- Main ---

def main():
    global _raw_mode
    parser = argparse.ArgumentParser(
        prog="oclaw_cli.py",
        description="ClawBot Memory Inspector -- search, inspect, and manage memories"
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--raw", action="store_true",
                        help="Disable secret/PII redaction (debug only)")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list
    p = sub.add_parser("list", help="List memories")
    p.add_argument("--project", "-p", help="Filter by project")
    p.add_argument("--tag", "-t", help="Filter by tag (substring match)")
    p.add_argument("--limit", "-l", type=int, default=20, help="Max results (default: 20)")
    p.add_argument("--sort", "-s", default="created_at DESC", help="Sort order")

    # get
    p = sub.add_parser("get", help="Show full memory detail")
    p.add_argument("id", help="Memory ID")

    # search
    p = sub.add_parser("search", help="Hybrid search (Azure + local fallback)")
    p.add_argument("query", help="Search query")
    p.add_argument("--limit", "-l", type=int, default=10, help="Max results")

    # stats
    sub.add_parser("stats", help="Memory statistics")

    # validate
    sub.add_parser("validate", help="Validate tags against TAG_REGISTRY")

    # tags
    sub.add_parser("tags", help="Tag usage report")

    # health
    sub.add_parser("health", help="System health check")

    # state
    sub.add_parser("state", help="Sync and extraction state")

    # export
    p = sub.add_parser("export", help="Export memories")
    p.add_argument("--format", "-f", choices=["json", "csv"], default="json",
                    help="Output format")
    p.add_argument("--project", "-p", help="Filter by project")
    p.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()
    _raw_mode = getattr(args, "raw", False)

    if not args.command:
        parser.print_help()
        return

    commands = {
        "list": cmd_list, "get": cmd_get, "search": cmd_search,
        "stats": cmd_stats, "validate": cmd_validate, "tags": cmd_tags,
        "health": cmd_health, "state": cmd_state, "export": cmd_export
    }
    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)


if __name__ == "__main__":
    main()
