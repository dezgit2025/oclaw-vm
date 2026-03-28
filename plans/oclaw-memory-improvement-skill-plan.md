# OpenClaw Memory Improvement Skill — Plan

**Status:** Planned (build after `improve-oclaw-memory-tag-extraction-mar27-plan.md` completes)
**Date:** 2026-03-27
**Depends on:** Completion of tag extraction improvement plan (Steps 1-9)
**Deploys to:** Both targets (see below)

---

## What is this?

A **dual-target** memory quality tool that runs against EITHER memory system — ClawBot on the VM or Claude Code on the Mac. Same tooling, same rubric, same lifecycle rules, different targets. Instead of manually running scripts and cron jobs, the user (or ClawBot) can invoke memory health checks, tag audits, recall benchmarks, pin/unpin, and lifecycle management through one interface.

**This skill is the operational layer on top of the memory storage/recall layer.** It handles quality, lifecycle, and optimization — not extraction or recall.

---

## Dual-Target Architecture

The two memory systems share identical architecture (SQLite + Azure AI Search) but live in different places:

| | ClawBot (VM) | Claude Code (Mac) |
|--|-------------|-------------------|
| **SQLite DB** | `~/.claude-memory/memory.db` | `~/.agent-memory/memory.db` |
| **Azure AI Search index** | `clawbot-memory-store` | `agent-code-memory` |
| **Azure resource group** | `oclaw-rg` | `oclaw-rg` (same) |
| **Extraction model** | GPT-5.2 (via `smart_extractor.py`) | GPT-5.2 (via hooks) |
| **Recall hook** | `before_agent_start` (OpenClaw gateway) | `UserPromptSubmit` (Claude Code) |
| **Sync mechanism** | `memory_bridge.py` cron on VM | `mem.py add` auto-triggers async sync |
| **Deploy path** | `~/.openclaw/workspace/skills/memory-improvement/` | `~/.agent-memory/tools/memory-improvement/` (or Claude Code skill) |
| **Invoked by** | ClawBot conversation or VM cron | Claude Code session or Mac cron |

### Target selection

Every command takes a `--target` flag:

```bash
# Run against ClawBot memory (VM)
python3 cli.py health --target clawbot

# Run against Claude Code memory (Mac)
python3 cli.py health --target claude-code

# Auto-detect based on hostname/environment
python3 cli.py health
```

Auto-detection logic:
1. If `OPENCLAW_WORKSPACE` env var exists → `clawbot`
2. If `~/.agent-memory/memory.db` exists and hostname is Mac → `claude-code`
3. If `~/.claude-memory/memory.db` exists → `clawbot`
4. Else → error, must specify `--target`

### Config per target

```python
# config.py
TARGETS = {
    "clawbot": {
        "db_path": "~/.claude-memory/memory.db",
        "azure_index": "clawbot-memory-store",
        "tag_registry": "~/.openclaw/workspace/skills/clawbot-memory/TAG_REGISTRY.md",
        "persona_files": {
            "soul": "~/.openclaw/SOUL.md",
            "user": "~/.openclaw/USER.md",
        },
        "session_dir": "~/.openclaw/agents/main/sessions/",
        "log_dir": "~/.openclaw/logs/memory-improvement/",
    },
    "claude-code": {
        "db_path": "~/.agent-memory/memory.db",
        "azure_index": "agent-code-memory",
        "tag_registry": None,  # Claude Code memory uses auto-memory, no TAG_REGISTRY
        "persona_files": None,  # No SOUL.md — skip ClawBot utility dimension
        "session_dir": None,  # Session files not accessible from Mac for missed-fact analysis
        "log_dir": "~/.agent-memory/logs/memory-improvement/",
    },
}
```

### What works on both targets

| Feature | ClawBot | Claude Code | Notes |
|---------|---------|-------------|-------|
| Tag distribution analysis | Yes | Yes | Both have tags field in SQLite |
| Tag normalization | Yes | Yes | Same logic, different DB path |
| Pin system | Yes | Yes | Same `pin:` tags |
| `permanent:true` | Yes | Yes | Same tag |
| Access tracking | Yes | Yes | Both have `access_count` field |
| 90-day stale cleanup | Yes | Yes | Same rule |
| Recency boost (scoring profile) | Yes | Yes | Different Azure indexes, same profile config |
| Monthly health report | Yes | Yes | Same report format |
| Claude-as-judge scoring | Yes | Yes | Reads from either DB |
| ClawBot utility dimension | Yes | **No** | No SOUL.md/USER.md on Mac — skip this dimension, reweight others |
| Missed-fact analysis | Yes | **No** | Session JSONL files not accessible from Mac side |
| Quarterly permanent review | Yes | Yes | Same process |

### Claude Code: adjusted rubric (5 dimensions)

When running against Claude Code memory (no persona files), the ClawBot utility dimension is dropped and weights redistribute:

| Dimension | ClawBot weight | Claude Code weight |
|-----------|---------------|-------------------|
| Tag accuracy | 20% | 25% |
| Tag specificity | 20% | 25% |
| Anchor completeness | 15% | 15% |
| Fact accuracy | 20% | 20% |
| Atomicity | 10% | 15% |
| ClawBot utility | 15% | **N/A** |

### Why Claude Code will probably get better results

Claude Code's `~/.agent-memory/` system:
- Has the same SQLite schema + Azure AI Search backend
- Runs in the same Claude Sonnet/Opus context (richer reasoning)
- Benefits from the same scoring profile, pin system, and lifecycle rules
- Claude Code sessions are longer and more technical → richer extraction source material
- The quality tooling developed for ClawBot transfers directly

---

## Research & Decisions (from Mar 27 session)

These decisions were made during the planning session and should be baked into the skill:

### Tag System

| Decision | Detail |
|----------|--------|
| Tag definition injection | Phase 0 — enrich extraction prompt with tag definitions + usage counts |
| Tag normalization | Standardize existing tag formats (casing, prefixes, duplicates) |
| `pin:` dimension | 3 levels: `pin:critical` (importance=10), `pin:important` (importance=9), `pin:reference` (importance=8). User-applied only. Never decay. |
| `permanent:true` tag | Infrastructure facts that never decay. Quarterly manual review. |
| No date tags on every memory | Use `created_at`/`updated_at` timestamps instead. Keep `decided:YYYY-MM-DD` for decisions only. |

### Scoring & Recall

| Decision | Detail |
|----------|--------|
| Azure scoring profile | `memory-relevance`: 80-day freshness (2.0x boost), importance (2.0x boost), content (1.5x weight), tags (1.2x weight) |
| Access tracking | Increment `access_count` on every recall. Used for stale detection. |

### Lifecycle & Decay

| Decision | Detail |
|----------|--------|
| 90-day auto-delete | Memories >90 days old with `access_count == 0` and not pinned/permanent → soft delete |
| Quarterly review | User manually reviews `permanent:true` memories each quarter |
| Soft decay | Scoring profile handles recency — old memories rank lower but aren't deleted unless unused |

### Quality Evaluation

| Decision | Detail |
|----------|--------|
| Claude-as-judge | Claude Sonnet scores all memories (independent judge, different model family than GPT-5.2 extractor) |
| 6-dimension rubric | Tag accuracy (20%), tag specificity (20%), anchor completeness (15%), fact accuracy (20%), atomicity (10%), ClawBot utility (15%) |
| ClawBot utility dimension | Uses SOUL.md + USER.md to judge "would ClawBot find this useful?" |
| Missed-fact analysis | Read source session transcripts, flag facts that should have been extracted |
| Existing `_score_extraction_quality()` | GPT-5.2 self-scoring function exists — analyze separately, don't use as primary judge |

---

## Skill Structure

```
memory-improvement/
  SKILL.md                      # Skill definition (YAML frontmatter + instructions)
  __init__.py
  config.py                     # Thresholds, boost params, decay rules, paths

  # --- Quality Analysis ---
  quality/
    __init__.py
    tag_distribution.py         # Tag frequency, anchor coverage, drift detection
    tag_normalization.py        # Build + apply normalization map
    score_memories.py           # LLM-as-judge scoring (calls Azure OpenAI)
    missed_fact_analysis.py     # Compare sessions to extracted memories

  # --- Lifecycle ---
  lifecycle/
    __init__.py
    access_tracker.py           # Increment access_count on recall
    stale_cleanup.py            # 90-day auto-delete (soft)
    permanent_review.py         # List permanent memories for quarterly review

  # --- Pin System ---
  pin/
    __init__.py
    pin_memory.py               # Add/change/remove pin tags
    list_pinned.py              # Show all pinned memories with levels

  # --- Reporting ---
  reporting/
    __init__.py
    health_report.py            # Monthly health report (tag stats, recall quality, lifecycle)
    baseline_snapshot.py        # Capture current state for before/after comparison

  # --- CLI ---
  cli.py                        # Unified CLI: health | tags | pin | lifecycle | report
```

22 Python files. Each under 80 lines per project rules.

---

## SKILL.md Definition

```yaml
---
name: memory-improvement
description: "Dual-target memory quality: tag optimization, lifecycle, pin system, health reports. Works on ClawBot (VM) and Claude Code (Mac)."
version: 1.0.0
enabled: true
gating:
  - command: python3 --version
    expect: "Python 3"
tools:
  - name: memory_health
    description: "Run a full memory health check — tag quality, stale detection. Use --target clawbot|claude-code"
  - name: memory_pin
    description: "Pin or unpin a memory. Usage: memory_pin <memory_id> <level> (critical/important/reference/unpin)"
  - name: memory_tags
    description: "Analyze tag distribution, anchor coverage, and normalization candidates"
  - name: memory_lifecycle
    description: Show stale memories, run cleanup (dry-run or apply), list permanent memories for review
---
```

---

## CLI Commands

```bash
# --target auto-detects, or specify: --target clawbot | --target claude-code

# Health check (runs tag analysis + stale detection + summary)
python3 cli.py health                              # auto-detect target
python3 cli.py health --target clawbot             # explicitly target ClawBot (VM)
python3 cli.py health --target claude-code         # explicitly target Claude Code (Mac)

# Tag analysis
python3 cli.py tags                                # Full tag distribution report
python3 cli.py tags --normalize --dry-run          # Show normalization candidates
python3 cli.py tags --normalize --apply            # Apply normalization

# Pin system
python3 cli.py pin MEM_ID critical                 # Pin a memory
python3 cli.py pin MEM_ID important                # Change pin level
python3 cli.py unpin MEM_ID                        # Remove pin
python3 cli.py pinned                              # List all pinned memories

# Lifecycle
python3 cli.py lifecycle                           # Show stale candidates (>90 days, 0 access)
python3 cli.py lifecycle --cleanup                 # Soft-delete stale memories
python3 cli.py lifecycle --permanent               # List permanent memories for quarterly review

# Reporting
python3 cli.py report                              # Generate monthly health report
python3 cli.py baseline                            # Capture baseline snapshot for A/B comparison

# Quality scoring
python3 cli.py score --sample 10                   # Score 10 random memories
python3 cli.py score --all                         # Score all memories
python3 cli.py score --session SESSION_ID          # Missed-fact analysis (clawbot only)

# Cross-target comparison
python3 cli.py compare                             # Side-by-side health of both targets
```

---

## How ClawBot uses it

### Automatic (cron-driven)

| Schedule | Command | What |
|----------|---------|------|
| 1st of month, 21:00 UTC | `cli.py report` | Monthly health report |
| 1st of month, 22:00 UTC | `cli.py lifecycle --cleanup` | Auto-delete stale memories |
| 1st of Jan/Apr/Jul/Oct | `cli.py lifecycle --permanent` | Quarterly review reminder |

### User-triggered (via conversation)

| User says | ClawBot does |
|-----------|-------------|
| "Pin that" / "tag important" | Prompts for level (critical/important/reference), applies `pin:` tag |
| "Memory health" / "how's the memory?" | Runs `cli.py health`, reports summary |
| "Show stale memories" | Runs `cli.py lifecycle`, reports candidates |
| "Review permanent memories" | Runs `cli.py lifecycle --permanent`, walks through each |
| "Tag report" | Runs `cli.py tags`, reports distribution and issues |

### Hook integration

The existing `before_agent_start` hook in `clawbot-memory` handles recall. This skill adds:

- **Post-recall hook** (or inline in `smart_extractor.py recall`): increment `access_count` for every recalled memory
- **No new hooks needed** — lifecycle and quality run on cron or user request

---

## Relationship to existing plans

| Plan | Relationship |
|------|-------------|
| `improve-oclaw-memory-tag-extraction-mar27-plan.md` | **Prerequisite** — Steps 1-9 build and validate all the components. This skill packages them. |
| `mem-optimize-v5.md` | **Supersedes Phases 1, 4, 5, 7** — tag analysis, extraction scoring, dedup, monthly report are all in this skill |
| `phase00-tag-definition-injection.md` | **Prerequisite** — Phase 0 changes `smart_extractor.py` before this skill is built |
| `clawbot-memory` (existing skill) | **Complement** — that skill handles extraction/storage/recall. This skill handles quality/lifecycle/optimization. |

---

## Build order

### Phase A: Core + ClawBot target (VM)

1. Complete `improve-oclaw-memory-tag-extraction-mar27-plan.md` Steps 1-9
2. Package validated components into skill directory structure
3. Write `config.py` with dual-target config (TARGETS dict, auto-detection logic)
4. Write `cli.py` as unified entry point with `--target` flag
5. Move/adapt quality analysis scripts from tag-analysis work
6. Implement pin system (`pin/`)
7. Implement lifecycle management (`lifecycle/`)
8. Write SKILL.md with tool definitions
9. Test all CLI commands with `--target clawbot` on VM
10. Wire VM cron jobs (monthly health, monthly cleanup, quarterly review)
11. Deploy to VM: `scp -r memory-improvement/ oclaw:~/.openclaw/workspace/skills/`
12. Restart gateway: `ssh oclaw "python3 ~/.openclaw/workspace/ops/watchdog/restart_gateway.py"`
13. Verify skill discovery: `ssh oclaw "openclaw skills list"`

### Phase B: Claude Code target (Mac) — DEFERRED until Phase A complete

**Do not start until ClawBot (Phase A) is fully deployed and validated.**

14. Verify `~/.agent-memory/memory.db` schema matches expected fields (id, content, tags, importance, access_count, created_at, updated_at, active)
15. Confirm Azure index name for Claude Code memory (`agent-code-memory` or check `AZURE_SEARCH_INDEX` env var)
16. Deploy to Mac: `cp -r memory-improvement/ ~/.agent-memory/tools/memory-improvement/`
17. Test all CLI commands with `--target claude-code`
18. Optionally create Claude Code skill at `~/.claude/skills/memory-improvement/SKILL.md` so it's invocable as a slash command
19. Wire Mac cron jobs (optional — or run on-demand from Claude Code sessions)

#### Claude Code tuning considerations (different context than ClawBot)

Claude Code is a dev tool, not a conversational partner. The memory quality rules need different emphasis:

| Dimension | ClawBot tuning | Claude Code tuning |
|-----------|---------------|-------------------|
| **What's a "good" memory** | User preferences, startup context, business decisions | Code patterns, project architecture, debugging fixes, workflow preferences |
| **Tag taxonomy emphasis** | `type:preference`, `type:decision`, `domain:product` | `type:fix`, `type:architecture`, `type:correction`, `domain:infra` |
| **Decay sensitivity** | Preferences are long-lived; project context shifts fast | Fixes are permanent; workarounds expire when code changes |
| **Pin usage** | "Our pricing model is X" → `pin:critical` | "This repo uses go.mod not venvs" → `pin:reference` |
| **Recall trigger** | Persona-based ("what does the user like?") | Task-based ("how did we fix this before?") |
| **Biggest quality risk** | Extracting opinions as facts | Extracting stale code patterns that no longer apply |
| **Judge rubric** | 6 dimensions (includes ClawBot utility via SOUL.md) | 5 dimensions (drop ClawBot utility, add "code relevance") |
| **Staleness signal** | 90 days + 0 access → delete | May need shorter window — code context changes faster. Or tie to git history (file still exists?) |

**Config changes for Claude Code target:**
- Adjust scoring rubric weights in `config.py` TARGETS dict
- Consider a "code relevance" dimension instead of "ClawBot utility"
- Shorter freshness window? (60 days instead of 80 for code-context memories)
- Different TAG_REGISTRY — Claude Code memory may need its own tag taxonomy tuned for dev workflows
- Session JSONL files live at `~/.claude/projects/<encoded-path>/<session-uuid>.jsonl` — missed-fact analysis IS possible on Mac (unlike what we assumed earlier)

**These details will be refined when we start Phase B.** The config architecture supports it — just add/adjust the `claude-code` entry in `TARGETS`.

### Phase C: Cross-target + docs

20. Implement `cli.py compare` — side-by-side health report of both targets
21. Test compare command
22. Update OPEN-CLAW-SKILL-INDEX.md with new skill entry (#29)
23. Update `openclaw_vm/CLAUDE.md` — add memory-improvement skill to ClawBot Memory System section
24. Update `~/.claude/CLAUDE.md` — add memory-improvement reference to Agent Memory System section
25. Archive research decisions from Mar 27 session into skill docs

---

## Deployment summary

| Target | Deploy path | Invoked by | Cron |
|--------|------------|-----------|------|
| ClawBot (VM) | `~/.openclaw/workspace/skills/memory-improvement/` | ClawBot conversation, VM cron, SSH manual | Monthly health + cleanup, quarterly review |
| Claude Code (Mac) | `~/.agent-memory/tools/memory-improvement/` | Claude Code session, Mac cron (optional) | On-demand (or optional monthly Mac cron) |
| Both | Same codebase, different `--target` | `cli.py compare` | N/A |

**Source of truth:** Single codebase in `~/Projects/oclaw_brain/memory-improvement/` (or wherever the skill source lives). Deploy via `scp` to VM, `cp` to Mac. Changes go to source first, then deploy to both.

---

## Documentation to produce

After the skill is built, create:

1. **Skill README** — `memory-improvement/README.md` with usage examples for both targets
2. **Update `openclaw_vm/CLAUDE.md`** — add memory-improvement skill to the ClawBot Memory System section
3. **Update `~/.claude/CLAUDE.md`** — add memory-improvement to Agent Memory System section (Claude Code side)
4. **Update OPEN-CLAW-SKILL-INDEX.md** — register skill #29
5. **Decision log** — archive all research decisions from this session into the skill's own docs
6. **Claude Code skill definition** — `~/.claude/skills/memory-improvement/SKILL.md` for slash command access

This documentation is the "research doc" from the planning session, now living inside the skill itself as operational reference.
