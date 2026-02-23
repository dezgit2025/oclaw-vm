# Memory System Phase II — Update, Edit, Delete Support

**Date:** 2026-02-23
**Status:** Planned (not started)
**Depends on:** Phase I memory system (deployed 2026-02-23)
**Source code:** `/Users/dez/Projects/oclaw_brain/oclaw_brain_skill_v1/`

---

## Problem Statement

The Phase I memory system is **create-read-soft-delete only**. Once a fact is stored, it cannot be edited, corrected, superseded, or deleted via any CLI command. This is a known gap flagged in the Phase I planning doc (`create-oclaw-memory-phaseI.md`, lines 298-312):

> "Problem: `mem` CLI doesn't support tag updates, so superseded memories can't be marked."

The `smart_extractor.py` pivot detection (line 515) also has a TODO waiting on this:

> "TODO: When mem CLI supports tag updates, auto-mark superseded memories"

---

## Current State (Phase I)

| Operation | Supported | Mechanism |
|-----------|-----------|-----------|
| **Create** | Yes | `mem.py add`, auto-extraction via `smart_extractor.py sweep` |
| **Read/Search** | Yes | `mem.py search` (local), `oclaw_cli.py search/list/get` (hybrid Azure+local), hook recall |
| **Update/Edit** | **No** | Not implemented anywhere |
| **Soft-Delete** | Internal only | `active=0` flag in SQLite, no CLI command |
| **Hard-Delete** | **No** | Not implemented |

### Current CLI Commands

**`mem.py`** (64 lines, `/oclaw_brain_skill_v1/cli/mem.py`):
```bash
mem.py add "fact" -p project -t tags      # CREATE
mem.py search "query" -k 5 -p project     # READ (local keyword)
```

**`oclaw_cli.py`** (350+ lines, `/oclaw_brain_skill_v1/oclaw_cli.py`):
```bash
oclaw_cli list                             # READ (browse)
oclaw_cli get <id>                         # READ (detail)
oclaw_cli search "query"                   # READ (hybrid Azure + local)
oclaw_cli stats                            # READ (analytics)
oclaw_cli tags                             # READ (tag distribution)
oclaw_cli validate                         # READ (validation)
oclaw_cli health                           # READ (system status)
oclaw_cli state                            # READ (sync cursor state)
oclaw_cli export --format json|csv         # READ (bulk export)
```

### Current SQLite Schema

Table `memories` in `~/.claude-memory/memory.db`:
- `id` — SHA-256 hash of `content:project` (content-addressable)
- `content` — fact text
- `project` — project name
- `tags` — comma-separated tags
- `active` — 1 (live) or 0 (soft-deleted)
- `created_at` — timestamp
- `updated_at` — timestamp

### Current Data Flow

```
Session logs
    ↓
smart_extractor.py sweep (LLM extraction + 5-gate filter)
    ↓
mem.py add → SQLite (active=1)
    ↓
memory_bridge.py sync → Azure AI Search (3072-dim embeddings)
    ↓
hook recall / SKILL.md search ← ClawBot reads

     ╳ No backward path to UPDATE or DELETE after creation
```

---

## Phase II Requirements

### 1. `mem.py` CLI — New Subcommands

Add to `cli/mem.py`:

```bash
# Edit memory content
mem.py edit <id> --content "corrected fact text"

# Tag management
mem.py tag <id> --add "status:superseded"
mem.py tag <id> --remove "old-tag"

# Soft-delete (mark inactive, keep in DB)
mem.py delete <id>

# Restore soft-deleted memory
mem.py restore <id>

# Mark one memory as superseding another
mem.py supersede <old_id> --by <new_id>
# Equivalent to: tag old_id --add "status:superseded,superseded_by:<new_id>"
#                + tag new_id --add "supersedes:<old_id>"
```

**Implementation notes:**
- `edit` must update `updated_at` timestamp (triggers sync on next `memory_bridge.py sync`)
- `edit` changes content but keeps the same `id` — do NOT rehash (breaks references)
- `delete` sets `active=0` and updates `updated_at`
- `restore` sets `active=1` and updates `updated_at`
- `supersede` is a convenience wrapper around `tag` — links two memories bidirectionally

### 2. `oclaw_cli.py` — New Commands

```bash
# List soft-deleted memories
oclaw_cli deleted

# Show supersession chain for a memory
oclaw_cli history <id>

# Bulk operations
oclaw_cli purge --older-than 90d --tag "status:superseded"
# (hard-deletes from SQLite + Azure — requires --confirm flag)
```

### 3. `memory_bridge.py` — Sync Updates + Deletes to Azure

Current sync only pushes **new** memories (created since last cursor). Phase II needs:

- **Update sync:** Detect memories where `updated_at > last_sync_cursor` AND `active=1` — re-upload to Azure with updated content/tags/embeddings
- **Delete sync:** Already partially implemented — `read_deleted_since()` (line 245) finds `active=0` records, `AzureSearchBridge.delete_memories()` (line 169) removes from Azure. Need to wire the CLI soft-delete to trigger this on next sync cycle.
- **Version field:** Add `version INTEGER DEFAULT 1` to schema — increment on each edit. Useful for conflict detection if concurrent edits ever happen.

### 4. `smart_extractor.py` — Pivot Detection Hookup

Currently at line 515, pivot detection logs a warning but cannot act. With `mem.py tag` support:

```python
# After detecting a pivot (contradictory fact):
subprocess.run(["python3", "cli/mem.py", "supersede", old_memory_id, "--by", new_memory_id])
```

This auto-marks outdated facts during daily extraction sweeps.

### 5. Schema Migration

Add to `memory.db`:

```sql
-- Version tracking
ALTER TABLE memories ADD COLUMN version INTEGER DEFAULT 1;

-- Edit history (new table)
CREATE TABLE IF NOT EXISTS memory_edits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    field_changed TEXT NOT NULL,       -- 'content', 'tags', 'active'
    old_value TEXT,
    new_value TEXT,
    changed_at TEXT DEFAULT (datetime('now')),
    changed_by TEXT DEFAULT 'cli',     -- 'cli', 'extractor', 'manual'
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- Index for efficient history lookups
CREATE INDEX IF NOT EXISTS idx_edits_memory ON memory_edits(memory_id);
```

**Migration strategy:** Run `ALTER TABLE` on existing DB — SQLite supports `ADD COLUMN` without rebuild. Create `memory_edits` table fresh.

---

## Files to Modify

| File | Changes |
|------|---------|
| `cli/mem.py` | Add `edit`, `tag`, `delete`, `restore`, `supersede` subcommands |
| `oclaw_cli.py` | Add `deleted`, `history`, `purge` commands |
| `memory_bridge.py` | Update sync to handle edits + deletes, add version tracking |
| `smart_extractor.py` | Wire pivot detection to `mem.py supersede` (line ~515) |
| `schema.sql` (new) | Migration script for `version` column + `memory_edits` table |

Files that should NOT change:
- `handler.js` (hook) — read-only recall path, unaffected
- `HOOK.md` — no change needed
- `auth_provider.py` — Azure auth, unrelated

---

## Azure AI Search Impact

- **No index schema change needed** — content/tags fields already exist, updates replace documents by ID
- **Cost impact:** Negligible — updates use same API calls as creates
- **Deletion:** Already supported via `AzureSearchBridge.delete_memories()` — just needs CLI trigger

---

## Risk & Rollback

| Risk | Mitigation |
|------|------------|
| Accidental deletion of good memories | Soft-delete by default, `purge` requires `--confirm`, edit history table tracks all changes |
| Content-addressable ID breaks on edit | Do NOT rehash ID on content edit — keep original ID |
| Azure sync conflicts | Version field prevents stale overwrites |
| Schema migration on existing DB | `ALTER TABLE ADD COLUMN` is safe in SQLite, non-destructive |

**Rollback:** Phase II is additive. Existing create/read paths are untouched. If anything breaks, the old `mem.py add` / `mem.py search` still work. Delete the new subcommands and drop the `memory_edits` table.

---

## Testing Checklist

- [ ] `mem.py edit` updates content and `updated_at`, preserves `id`
- [ ] `mem.py tag --add/--remove` modifies tags correctly
- [ ] `mem.py delete` sets `active=0`, memory no longer appears in search
- [ ] `mem.py restore` sets `active=1`, memory reappears in search
- [ ] `mem.py supersede` links two memories bidirectionally via tags
- [ ] `memory_bridge.py sync` pushes edited memories to Azure
- [ ] `memory_bridge.py sync` deletes soft-deleted memories from Azure
- [ ] `smart_extractor.py` pivot detection auto-supersedes contradictory facts
- [ ] `memory_edits` table logs all changes with timestamps
- [ ] `oclaw_cli deleted` shows only inactive memories
- [ ] `oclaw_cli history <id>` shows edit trail
- [ ] `oclaw_cli purge` requires `--confirm` and respects `--older-than`

---

## Priority

Medium. The system works well for Phase I (create + recall). Update/delete becomes important as:
1. Memory count grows and stale facts pollute recall results
2. User corrections need to propagate (e.g., "that's wrong, the model ID is actually X")
3. Pivot detection needs to auto-retire outdated facts instead of just logging warnings
