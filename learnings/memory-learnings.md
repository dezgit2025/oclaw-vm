# Memory System Fixes & Learnings — 2026-02-25

## Session Summary

This session diagnosed and fixed critical issues in the ClawBot memory system: duplicate memories, inconsistent project naming, missing dedup at the `mem.py add` entry point, and investigated API 500 errors.

---

## 1. Root Cause Analysis: Why Duplicates Exist

### Investigation

Discovered **massive duplication** across the memory system — same facts stored 3-4 times with slightly different wording. Example: the git regex fix appeared in 4 separate memories.

### Root Causes Identified

```
┌─────────────────────────────────────────────────────────────┐
│                    DUPLICATE ENTRY PATHS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RC1: mem.py add has ZERO dedup                             │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐            │
│  │ User says│ ──> │ mem.py   │ ──> │ SQLite   │            │
│  │"remember"│     │ add      │     │ INSERT OR│            │
│  └──────────┘     │ (no check│     │ REPLACE  │            │
│                   │  at all) │     │ (hash    │            │
│                   └──────────┘     │  only)   │            │
│                                    └──────────┘            │
│  SHA-256 hash only catches EXACT text match.               │
│  "Fixed regex X" vs "Fixed the regex X" = 2 entries.       │
│                                                             │
│  RC2: _is_likely_duplicate() scoped to single project       │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │smart_extractor│ ──> │ mem.py search │                    │
│  │calls dedup   │     │ -p PROJECT   │ <-- only checks     │
│  │with -p flag  │     │ (misses cross│     same project    │
│  └──────────────┘     │  project)    │                     │
│                       └──────────────┘                     │
│  Same fact in "oclaw-brain" won't match "oclaw_brain".     │
│                                                             │
│  RC3: Inconsistent project detection                        │
│  ┌──────────────────────────────────────────────┐          │
│  │ Session in ~/Projects/openclaw_vm/            │          │
│  │   detect_project() → "openclaw_vm"            │          │
│  │                                               │          │
│  │ Session in ~/Projects/oclaw_brain/            │          │
│  │   detect_project() → "oclaw_brain"            │          │
│  │                                               │          │
│  │ Different session →  "oclaw-brain" (hyphen)   │          │
│  │                                               │          │
│  │ Result: 3 "projects" for same system          │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  RC4: No dedup on manual mem.py add                         │
│  When user or ClawBot manually runs mem.py add,             │
│  there is ZERO dedup — no fuzzy match, no search.           │
│  Just hash-and-insert.                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Impact

| Project | Before Fix | Dupes Found |
|---------|-----------|-------------|
| `oclaw-brain` | 41 memories | ~20 duplicates |
| `oclaw_brain` | 25 memories | Entire project is a dupe namespace |
| `oclaw-vm` / `openclaw_vm` | 2 memories (split) | 1 namespace dupe |
| `_global` / `global` | 3 memories (split) | 1 namespace dupe |
| `logicapp-cli` / `logicflow-cli` | 34 memories (split) | 7 namespace dupes |

---

## 2. Fix: Fuzzy Word Overlap Dedup in mem.py

### What Changed

Added `_word_overlap()` and `_find_duplicate()` to `mem.py` `cmd_add()`. Every `add` now scans ALL active memories (cross-project) before inserting.

### Flow: Before vs After

```
BEFORE (no dedup):
┌──────────┐     ┌─────────────┐     ┌─────────┐
│ mem.py   │ ──> │ make_id()   │ ──> │ INSERT  │
│ add "X"  │     │ SHA-256     │     │ OR      │
│          │     │ hash        │     │ REPLACE │
└──────────┘     └─────────────┘     └─────────┘
Only blocks EXACT same text + same project.


AFTER (fuzzy dedup):
┌──────────┐     ┌──────────────────┐     ┌──────────────┐
│ mem.py   │ ──> │ _find_duplicate()│     │ DUPE BLOCKED │
│ add "X"  │     │ scan ALL active  │ ──> │ >60% overlap │
│          │     │ memories (cross- │     │ shows match  │
│          │     │ project)         │     │ + existing   │
│          │     └────────┬─────────┘     └──────────────┘
│          │              │ no dupe
│          │              v
│          │     ┌─────────────┐     ┌─────────┐
│          │     │ make_id()   │ ──> │ INSERT  │
│          │     │ SHA-256     │     │ OR      │
│          │     │ hash        │     │ REPLACE │
│          │     └─────────────┘     └─────────┘
│          │
│ --force  │ ──> skip dedup, insert directly
└──────────┘
```

### Algorithm

```python
def _word_overlap(a, b):
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    overlap = len(wa & wb)
    return overlap / min(len(wa), len(wb))  # <-- KEY: uses min()
```

**Why `min()` not `max()`:**
- A short new fact like "Tailscale enable disable on Mac" (5 words)
- Existing long fact: "Tailscale on Mac: Enable: 1) Open app... disable... reboot..." (40 words)
- With `max()`: 4 shared / 40 = 0.10 = **miss** (below 0.6)
- With `min()`: 4 shared / 5 = 0.80 = **caught** (above 0.6)

`min()` means: "if most of the shorter text's words appear in the longer text, it's a dupe." This catches subset dupes where someone writes a shorter version of an existing fact.

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Cross-project scan (no `-p` filter) | Prevents the exact bug that caused most dupes |
| 60% threshold | Matches `smart_extractor.py` for consistency |
| `--force` flag to bypass | Sometimes you intentionally want overlapping memories |
| No LLM (pure Python) | Zero cost, instant, no API dependency |

### Test Results

```bash
# Blocked — 80% overlap with existing Tailscale memory
$ mem.py add "Tailscale on Mac: Enable by opening Tailscale app, enable VPN" -p oclaw-vm
DUPE BLOCKED: >60% word overlap with [mem_b250df15c0ae9a5e] (project: oclaw-vm)
  Existing: Tailscale on Mac: Enable: 1) Open Tailscale app, enable VPN...
  Use --force to override

# Cross-project catch — openclaw_vm normalized to oclaw-vm, still caught
$ mem.py add "Tailscale on Mac enable disable instructions" -p openclaw_vm
DUPE BLOCKED: >60% word overlap with [mem_b250df15c0ae9a5e] (project: oclaw-vm)

# Force bypass works
$ mem.py add "same thing" -p oclaw-vm --force
Stored: mem_abc123...
```

---

## 3. Fix: Project Name Normalization

### What Changed

Added `PROJECT_ALIASES` map and `normalize_project()` function to `mem.py`. Applied to `add`, `search`, and `list` commands.

### Alias Map

```python
PROJECT_ALIASES = {
    "openclaw_vm": "oclaw-vm",      # underscore variant
    "openclaw-vm": "oclaw-vm",      # hyphen variant
    "oclaw_vm":    "oclaw-vm",      # short underscore
    "oclaw_brain": "oclaw-brain",   # underscore variant
    "logicflow-cli": "logicapp-cli",# renamed project
    "logicflow_cli": "logicapp-cli",# underscore variant
    "global":      "_global",       # missing underscore
}
```

### Flow

```
┌───────────────┐     ┌──────────────────┐     ┌─────────────┐
│ mem.py add    │     │ normalize_project │     │ Canonical   │
│ -p openclaw_vm│ ──> │ ("openclaw_vm")  │ ──> │ "oclaw-vm"  │
│               │     │                  │     │             │
│ mem.py search │     │ Checks alias map │     │ Used for    │
│ -p oclaw_vm   │ ──> │ ("oclaw_vm")    │ ──> │ all DB ops  │
│               │     │                  │     │             │
│ mem.py add    │     │ No alias found   │     │ "my-project"│
│ -p my-project │ ──> │ returns as-is   │ ──> │ (passthrough)│
└───────────────┘     └──────────────────┘     └─────────────┘
```

### What This Prevents

```
BEFORE:
  Session A (cwd: ~/Projects/openclaw_vm/) → stores as "openclaw_vm"
  Session B (cwd: ~/Projects/oclaw_brain/) → stores as "oclaw_brain"
  Session C (different detection) → stores as "oclaw-brain"
  Result: 3 projects, dedup can't find matches across them

AFTER:
  Session A → normalize("openclaw_vm") → "oclaw-vm"
  Session B → normalize("oclaw_brain") → "oclaw-brain"
  Session C → normalize("oclaw-brain") → "oclaw-brain" (passthrough)
  Result: 2 projects (correct), dedup works within each
  Plus: cross-project dedup catches overlap between them
```

---

## 4. Deployment Locations

### Files Updated

```
LOCAL (Mac):
  /Users/dez/Projects/oclaw_brain/oclaw_brain_skill_v1/cli/mem.py
    DB_PATH: ~/.agent-memory/memory.db
    Used by: Claude Code on laptop (via hooks + manual)

VM (oclaw2026linux) — TWO copies required:
  ~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py
    DB_PATH: ~/.claude-memory/memory.db
    Used by: smart_extractor.py, ClawBot skills

  ~/claude-memory/cli/mem.py
    DB_PATH: ~/.claude-memory/memory.db
    Used by: smart_extractor.py (references this path)
```

### Deployment Flow

```
┌─────────────────────────────┐
│ Edit local source file      │
│ /Users/dez/Projects/        │
│ oclaw_brain/.../cli/mem.py  │
└──────────┬──────────────────┘
           │
           ├──> Local (already correct DB_PATH)
           │
           ├──> sed 's|agent-memory|claude-memory|'
           │    │
           │    ├──> scp → VM skill dir
           │    │    ~/.openclaw/.../cli/mem.py
           │    │
           │    └──> scp → VM cli dir
           │         ~/claude-memory/cli/mem.py
           │
           └──> Test on both sides
```

---

## 5. API 500 Error Investigation

### Summary

Anthropic API 500 errors on 2026-02-25 confirmed as platform-wide outage, NOT caused by our hooks.

### Evidence

```
Debug Log Analysis:
┌─────────────────────────────────────────────────────┐
│ f4c1e03d-583a-457c-8b09-dfd09c1501f6.txt            │
│                                                     │
│ 16:15:34 Hook fires: UserPromptSubmit               │
│ 16:15:34 Found 1 hook matcher ← memory recall hook  │
│ 16:15:34 Matched 1 unique hook                      │
│ 16:15:44 Hook completes (no errors)                 │
│                                                     │
│ ... (no api_error or 500 in hook vicinity) ...      │
│                                                     │
│ API 500 occurs LATER, during Anthropic API call     │
│ Completely independent of hook execution            │
└─────────────────────────────────────────────────────┘

External Confirmation:
  - status.claude.com: "elevated error rates across Opus 4.6 and Sonnet 4.6"
  - GitHub #28624: dozens of users, "basically unusable"
  - GitHub #28614: "500 on every prompt, Claude Max unusable"
```

### Edge Case to Monitor

```
Context Capacity Risk:
┌──────────────────────────────────────────────────────┐
│                                                      │
│  200k token context window                           │
│  ┌──────────────────────────────────────────────┐   │
│  │ System prompt (5.2k)                         │   │
│  │ System tools (16k)                           │   │
│  │ CLAUDE.md + memory files (6.1k)              │   │
│  │ Hook-injected memories (~500 tokens/turn)    │   │
│  │ Conversation messages (growing...)           │   │
│  │                                              │   │
│  │ At ~90% (180k): API silently 500s            │   │
│  │ NOT a graceful "context too large" error     │   │
│  │                                              │   │
│  │ Mitigation: run /compact before ~85%         │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  GitHub issue #15126 documents this behavior         │
└──────────────────────────────────────────────────────┘
```

### Monitor Script

Created `manage-oclaw/api-error-monitor.sh` to scan Claude Code debug logs for 500 errors and check for hook correlation.

```bash
./manage-oclaw/api-error-monitor.sh 24   # scan last 24 hours
```

---

## 6. Dedup Layers — Current vs Planned

```
CURRENT (deployed 2026-02-25):
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Layer 1: SHA-256 exact hash (mem.py INSERT OR REPLACE) │
│  ├── Catches: exact same text + same project            │
│  └── Misses: any rewording, different project           │
│                                                         │
│  Layer 2: Word overlap 60% (mem.py _find_duplicate)     │
│  ├── Catches: similar wording, cross-project    [NEW]   │
│  └── Misses: semantic dupes with different words        │
│                                                         │
│  Layer 3: Word overlap 60% (smart_extractor gate 4)     │
│  ├── Catches: extraction-time dupes, same project       │
│  └── Misses: cross-project (still uses -p filter)       │
│                                                         │
│  Layer 4: Project normalization (mem.py aliases)  [NEW] │
│  ├── Catches: openclaw_vm/oclaw_vm/oclaw-vm splits      │
│  └── Misses: new unknown variants                       │
│                                                         │
└─────────────────────────────────────────────────────────┘

PLANNED (next week):
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Layer 5: Weekly LLM dedup sweep (GPT-4.1-mini)        │
│  ├── Catches: semantic dupes ("enable Tailscale"        │
│  │   vs "turn on Tailscale VPN")                        │
│  ├── Merges: keeps best version, combines tags          │
│  ├── Cost: ~$0.002/day                                  │
│  └── Script: dedup_sweep.py (to be built)               │
│                                                         │
│  Layer 6: Cosine similarity at Azure sync               │
│  ├── smart_extractor.py line 18 mentions this           │
│  │   "Semantic dedup: >0.92 cosine sim"                 │
│  ├── NOT yet implemented                                │
│  └── Would catch dupes at sync time using embeddings    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Remaining Work

### Manual Cleanup Needed

The fixes prevent future dupes but ~30+ existing duplicates remain across:
- `oclaw-brain`: ~20 content dupes (same fix stored 3-4x)
- `oclaw_brain`: 25 memories need moving to `oclaw-brain`
- `openclaw_vm`: 1 memory needs moving to `oclaw-vm`
- `global`: 1 memory needs moving to `_global`
- `logicflow-cli`: 7 memories need moving to `logicapp-cli`
- 2 junk test entries to delete

### smart_extractor.py Gap

`_is_likely_duplicate()` still passes `-p project` to `mem.py search`, which limits dedup to same-project only. Since `mem.py add` now has cross-project dedup, this is a safety net gap but not critical — the `add` layer catches it.

### Weekly LLM Dedup

Build `dedup_sweep.py`:
1. Pull all active memories
2. Batch into groups of 5-10 by topic
3. Send to GPT-4.1-mini: "Which of these are duplicates? Return merge groups."
4. For each group: keep best version, combine tags, delete rest
5. Log all actions
6. Wire into weekly cron (Sunday midnight UTC)

Estimated effort: 2-3 hours. Stored in memory as `status:exploring`.

---

## 8. Key Takeaways

1. **Dedup must be cross-project** — project name inconsistency is the #1 source of dupes
2. **`min()` not `max()` for word overlap** — short new facts must match against longer existing ones
3. **Every entry point needs dedup** — `mem.py add` was a blind spot for months
4. **Normalization is a band-aid** — the real fix is consistent project detection in `detect_project()`
5. **API 500s are transient** — always check `status.anthropic.com` before blaming hooks
6. **Word overlap is good enough for prevention** — LLM dedup is better for retroactive cleanup
