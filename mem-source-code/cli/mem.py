#!/usr/bin/env python3
"""Minimal mem CLI for ClawBot memory system."""
import argparse, hashlib, os, sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.expanduser(os.environ.get("CLAWBOT_MEMORY_DB", "~/.agent-memory/memory.db"))

PROJECT_ALIASES = {
    "openclaw_vm": "oclaw-vm",
    "openclaw-vm": "oclaw-vm",
    "oclaw_vm": "oclaw-vm",
    "oclaw_brain": "oclaw-brain",
    "logicflow-cli": "logicapp-cli",
    "logicflow_cli": "logicapp-cli",
    "global": "_global",
}

def normalize_project(name):
    return PROJECT_ALIASES.get(name, name)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY, content TEXT NOT NULL, project TEXT DEFAULT 'general',
        tags TEXT DEFAULT '', importance INTEGER DEFAULT 5, access_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL, active INTEGER DEFAULT 1)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_active ON memories(active)")
    conn.commit()
    return conn

def make_id(content, project):
    return f"mem_{hashlib.sha256(f'{content}:{project}'.encode()).hexdigest()[:16]}"

def _word_overlap(a, b):
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    overlap = len(wa & wb)
    return overlap / min(len(wa), len(wb))

def _find_duplicate(conn, fact, threshold=0.6):
    rows = conn.execute(
        "SELECT id, content, project FROM memories WHERE active=1"
    ).fetchall()
    for mid, content, project in rows:
        if _word_overlap(fact, content) > threshold:
            return mid, content, project
    return None

PIN_IMPORTANCE = {"critical": 10, "important": 9, "reference": 8}

def cmd_add(args):
    conn = init_db()
    project = normalize_project(args.project or "general")
    force = getattr(args, 'force', False)
    if not force:
        dupe = _find_duplicate(conn, args.fact)
        if dupe:
            print(f"DUPE BLOCKED: >60% word overlap with [{dupe[0]}] (project: {dupe[2]})")
            print(f"  Existing: {dupe[1][:150]}")
            print(f"  Use --force to override")
            conn.close()
            return
    now = datetime.now(timezone.utc).isoformat()
    mid = make_id(args.fact, project)
    tags = args.tags or ""
    importance = 5
    pin = getattr(args, 'pin', None)
    if pin:
        tags = f"{tags}, pin:{pin}".strip(", ")
        importance = PIN_IMPORTANCE[pin]
    conn.execute("INSERT OR REPLACE INTO memories (id,content,project,tags,importance,access_count,created_at,updated_at,active) VALUES (?,?,?,?,?,0,?,?,1)",
        (mid, args.fact, project, tags, importance, now, now))
    conn.commit(); conn.close()
    msg = f"Stored: {mid}"
    if pin:
        msg += f" [pin:{pin}, importance={importance}]"
    print(msg)

def cmd_pin(args):
    conn = init_db()
    mid, level = args.mem_id, args.level
    row = conn.execute("SELECT tags FROM memories WHERE id=? AND active=1", (mid,)).fetchone()
    if not row:
        print(f"Memory {mid} not found"); conn.close(); return
    parts = [t.strip() for t in row[0].split(",") if t.strip() and not t.strip().startswith("pin:")]
    parts.append(f"pin:{level}")
    new_tags = ", ".join(parts)
    importance = PIN_IMPORTANCE[level]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE memories SET tags=?, importance=?, updated_at=? WHERE id=?",
        (new_tags, importance, now, mid))
    conn.commit(); conn.close()
    print(f"Pinned {mid} as pin:{level} (importance={importance})")

def cmd_unpin(args):
    conn = init_db()
    mid = args.mem_id
    row = conn.execute("SELECT tags FROM memories WHERE id=? AND active=1", (mid,)).fetchone()
    if not row:
        print(f"Memory {mid} not found"); conn.close(); return
    parts = [t.strip() for t in row[0].split(",") if t.strip() and not t.strip().startswith("pin:")]
    new_tags = ", ".join(parts)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE memories SET tags=?, importance=5, updated_at=? WHERE id=?",
        (new_tags, now, mid))
    conn.commit(); conn.close()
    print(f"Unpinned {mid} (importance reset to 5)")

def cmd_search(args):
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    query = args.query.lower().split(); k = args.k or 5
    project = normalize_project(args.project) if args.project else None
    sql = "SELECT * FROM memories WHERE active=1"
    params = []
    if project:
        sql += " AND project=?"
        params.append(project)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    scored = []
    for row in rows:
        content = row["content"].lower()
        score = sum(1 for w in query if w in content)
        if score > 0: scored.append((score, dict(row)))
    scored.sort(key=lambda x: -x[0])
    for score, mem in scored[:k]:
        print(f"[{mem['id']}] ({mem['tags']}) {mem['content']}")
    conn.close()

def cmd_status(args):
    from mem_status import compute_health
    from mem_display import display_dashboard, display_log_line
    scores, greens, details = compute_health()
    if "error" in details:
        print(f"Error: {details['error']}"); return
    if getattr(args, 'log_only', False):
        display_log_line(scores, greens, details)
    else:
        display_dashboard(scores, greens, details)

def cmd_list(args):
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    project = normalize_project(args.project) if args.project else None
    if project:
        rows = conn.execute("SELECT * FROM memories WHERE active=1 AND project=? ORDER BY created_at DESC", (project,)).fetchall()
        for r in rows:
            print(f"[{r['id']}] ({r['tags']}) {r['content']}")
        print(f"\n{len(rows)} memories in project '{project}'")
    else:
        rows = conn.execute("SELECT project, COUNT(*) as cnt FROM memories WHERE active=1 GROUP BY project ORDER BY cnt DESC").fetchall()
        for r in rows:
            print(f"{r['project']}: {r['cnt']} memories")
    conn.close()

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    a = sub.add_parser("add"); a.add_argument("fact"); a.add_argument("-t","--tags",default=""); a.add_argument("-p","--project",default="general"); a.add_argument("--force",action="store_true",help="Skip dedup check"); a.add_argument("--pin",choices=["critical","important","reference"],help="Pin level")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-k",type=int,default=5); s.add_argument("-p","--project",default=None)
    l = sub.add_parser("list"); l.add_argument("-p","--project",default=None)
    pn = sub.add_parser("pin"); pn.add_argument("mem_id"); pn.add_argument("level",choices=["critical","important","reference"])
    un = sub.add_parser("unpin"); un.add_argument("mem_id")
    st = sub.add_parser("status"); st.add_argument("--log-only",action="store_true",help="One-liner for cron")
    args = p.parse_args()
    if args.command == "add": cmd_add(args)
    elif args.command == "search": cmd_search(args)
    elif args.command == "list": cmd_list(args)
    elif args.command == "pin": cmd_pin(args)
    elif args.command == "unpin": cmd_unpin(args)
    elif args.command == "status": cmd_status(args)
    else: p.print_help()

if __name__ == "__main__": main()
