# ClawBot — "Add to AI Search" Instruction Guide

When a user says **"add to AI search"**, **"add to AI search memory"**, **"sync to AI search"**, or **"save to AI search"**, you MUST run TWO commands in sequence — not just one.

---

## Step 1: Store the memory locally

```bash
source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
cd ~/.openclaw/workspace/skills/clawbot-memory/cli && \
python3 mem.py add "THE FACT HERE" \
  -t "type:decision,domain:infrastructure" \
  -p PROJECT_NAME
```

This writes to SQLite (`~/.claude-memory/memory.db`). By itself, the memory is **local only** — it will NOT appear in AI Search until synced.

---

## Step 2: Sync to Azure AI Search (REQUIRED for "add to AI search")

```bash
source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
cd ~/.openclaw/workspace/skills/clawbot-memory && \
python3 memory_bridge.py sync
```

This pushes all unsynced memories from SQLite to Azure AI Search with 3072-dim embeddings. Without this step, the memory only exists locally and will not be recalled by the hook.

---

## When to run each step

| User says | Step 1 (mem.py add) | Step 2 (memory_bridge.py sync) |
|-----------|:---:|:---:|
| "remember this" / "save this" | YES | NO — daily cron handles it |
| "add to AI search" / "sync to AI search" | YES | **YES — run immediately** |
| "add to AI search memory" | YES | **YES — run immediately** |
| "save to memory and sync" | YES | **YES — run immediately** |

---

## Combined one-liner

For convenience, run both as a single chain:

```bash
source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
cd ~/.openclaw/workspace/skills/clawbot-memory && \
python3 cli/mem.py add "THE FACT" -t "type:decision,domain:product" -p PROJECT && \
python3 memory_bridge.py sync
```

---

## What happens if you skip Step 2

- Memory sits in SQLite only
- Daily cron at 20:35 UTC will eventually sync it (up to 24h delay)
- The recall hook queries Azure AI Search, NOT SQLite — so the memory is invisible until synced
- User expects immediate availability when they say "add to AI search"

---

## Confirm to the user

After both steps succeed, tell the user:
1. The memory ID (from `mem.py add` output)
2. The tags used
3. That it was synced to Azure AI Search immediately

Example response:
> Stored and synced to AI Search: `mem_abc123` with tags `type:decision,domain:product,priority:important` (project: hingex)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `memory_bridge.py sync` fails | Check `AZURE_SEARCH_ENDPOINT` env var is set. Run `echo $AZURE_SEARCH_ENDPOINT` |
| "No module named azure.search" | Activate the venv first: `source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate` |
| Sync says "0 memories to sync" | Memory was already synced, or `mem.py add` failed silently — check the add output |
| "consecutive_failures: N" | Azure may be unreachable. Check `python3 memory_bridge.py status` |
