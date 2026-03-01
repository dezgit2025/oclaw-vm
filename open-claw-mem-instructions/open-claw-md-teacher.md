# ClawBot Memory System — Operator Guide

You (ClawBot) have a persistent memory system backed by **SQLite (local)** and **Azure AI Search (cloud)**. This document teaches you how to use it.

---

## Your Memory Architecture

```
User says "remember X"
    ↓
mem.py add → SQLite (source of truth)
    ↓ (auto-sync daily, or immediate on demand)
memory_bridge.py sync → Azure AI Search (3072-dim embeddings, hybrid search)
    ↓
before_agent_start hook → recalls relevant memories every turn
```

**You already recall memories automatically** via the `clawbot-memory-recall` hook. This doc is about **storing** new memories on demand.

---

## Trigger Phrases — When to Store a Memory

When the user says ANY of these, you MUST store a memory:

| User Says | Action |
|-----------|--------|
| "remember this" / "remember that" | Store the fact they just described |
| "add to memory" / "save to memory" | Store with specified content |
| "add to AI search" / "add to AI search memory" | Store + immediate sync to Azure |
| "this is important" / "mark important" | Store with `priority:important` tag |
| "global memory" / "tag global" / "mark global" | Store with `scope:global` tag |
| "never forget" / "always remember" | Store with `priority:critical` tag |
| "remember for [project]" | Store with `-p PROJECT_NAME` |

---

## How to Store a Memory

### Command

```bash
source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
cd ~/.openclaw/workspace/skills/clawbot-memory/cli && \
python3 mem.py add "THE FACT GOES HERE" \
  -t "type:decision,domain:infrastructure,priority:important" \
  -p PROJECT_NAME
```

### Immediate Azure Sync (when user says "add to AI search")

After `mem.py add`, also run:

```bash
source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
cd ~/.openclaw/workspace/skills/clawbot-memory && \
python3 memory_bridge.py sync
```

This pushes the new memory to Azure AI Search immediately instead of waiting for the daily cron.

---

## Tag System

### Required Tags (always assign these)

| Dimension | Options | Notes |
|-----------|---------|-------|
| `type:` | fact, decision, error, pattern, insight, preference, fix, architecture, context | Pick the best match |
| `domain:` | infrastructure, product, ai, auth, data, backend, frontend, mobile, users, ops | Pick the best match |

### Priority Tags (when user specifies importance)

| Tag | When to Use |
|-----|-------------|
| `priority:critical` | User says "never forget", "always remember", "critical" |
| `priority:important` | User says "important", "mark important" |
| `priority:normal` | Default — don't add this tag, just omit priority |

### Scope Tags

| Tag | When to Use |
|-----|-------------|
| `scope:global` | User says "global", applies across all projects |
| `scope:project` | Default — specific to current project (omit tag) |

### Status Tags

| Tag | When to Use |
|-----|-------------|
| `status:active` | Current and relevant (default) |
| `status:superseded` | Replaced by a newer decision |
| `status:exploring` | Still being evaluated |

### Temporal Tags (for decisions)

Always add `decided:YYYY-MM-DD` when storing a decision.

### Examples

```bash
# User: "remember that Tailscale conflicts with Azure VPN, mark it important"
python3 mem.py add "Tailscale on Mac conflicts with MS Azure VPN client. Must disable one before using the other. Fix: tailscale down before Azure VPN, tailscale up after." \
  -t "type:fix,domain:infrastructure,priority:important,status:active,decided:2026-02-25" \
  -p openclaw_vm

# User: "add to AI search memory: we use claude-opus-4.6 not copilot-opus, global"
python3 mem.py add "Gateway model ID is claude-opus-4.6, NOT copilot-opus-4.6. Use: openclaw models list --all | grep github-copilot to verify." \
  -t "type:fact,domain:ai,scope:global,priority:important,status:active" \
  -p openclaw_vm
# THEN also run: python3 memory_bridge.py sync
```

---

## How to Search / Recall Memories

```bash
# Hybrid search (Azure + local fallback)
source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
cd ~/.openclaw/workspace/skills/clawbot-memory && \
python3 smart_extractor.py recall "topic here" -k 5

# Local SQLite search
cd cli && python3 mem.py search "query" -k 5

# Full inspector CLI
python3 oclaw_cli.py search "query"
python3 oclaw_cli.py list
python3 oclaw_cli.py stats
python3 oclaw_cli.py tags
python3 oclaw_cli.py health
```

---

## How to Check System Health

```bash
# Memory count + extraction stats
python3 smart_extractor.py status

# Azure sync state
python3 memory_bridge.py status

# Full health check (auth, connectivity, index)
python3 oclaw_cli.py health

# Hook status
openclaw hooks list
```

---

## File Locations (on VM)

| File | Path | Purpose |
|------|------|---------|
| mem.py CLI | `~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py` | Add/search memories |
| smart_extractor.py | `~/.openclaw/workspace/skills/clawbot-memory/smart_extractor.py` | Extract from sessions, recall |
| memory_bridge.py | `~/.openclaw/workspace/skills/clawbot-memory/memory_bridge.py` | Sync SQLite → Azure |
| oclaw_cli.py | `~/.openclaw/workspace/skills/clawbot-memory/oclaw_cli.py` | Inspector CLI (9 subcommands) |
| SQLite DB | `~/.claude-memory/memory.db` | Local source of truth |
| Hook | `~/.openclaw/hooks/clawbot-memory/HOOK.md` + `handler.js` | Auto-recall every turn |
| Tag registry | `~/.openclaw/workspace/skills/clawbot-memory/TAG_REGISTRY.md` | Full tag taxonomy |
| Venv | `~/.openclaw/workspace/skills/clawbot-memory/.venv/` | Python dependencies |

---

## Rules

1. **Always activate the venv** before running any memory command
2. **Always use `-p PROJECT_NAME`** to scope memories to a project
3. **Never store secrets** — no API keys, tokens, passwords, or PII
4. **Check for duplicates** before adding — run `mem.py search "similar query"` first
5. **When user says "add to AI search"** — run `mem.py add` THEN `memory_bridge.py sync`
6. **When user says just "remember"** — `mem.py add` is sufficient (daily sync handles Azure)
7. **Confirm storage** — always tell the user the memory ID and tags used
8. **Suggest tags** — if the user doesn't specify tags, suggest appropriate ones before storing

---

## Quick Reference Card

| User Intent | Command Chain |
|-------------|---------------|
| "Remember X" | `mem.py add "X" -t "..." -p PROJECT` |
| "Add to AI search: X" | `mem.py add` → `memory_bridge.py sync` |
| "What do you remember about X?" | `smart_extractor.py recall "X" -k 5` |
| "How many memories?" | `smart_extractor.py status` |
| "Is memory healthy?" | `oclaw_cli.py health` |
| "Show all memories" | `oclaw_cli.py list` |
| "Search memories for X" | `oclaw_cli.py search "X"` |
