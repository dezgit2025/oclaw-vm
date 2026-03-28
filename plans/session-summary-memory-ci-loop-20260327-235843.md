# Memory CI Loop — Session Summary (2026-03-27/28)

**Project:** openclaw_vm
**Duration:** ~5 hours (across 2 days)
**Health score:** 4/10 (pre-session) → 6/10 ATTENTION (post-session, 4 metrics self-healing)

---

## What We Did

### Planning & Documentation

| Document | Location |
|----------|----------|
| Memory CI Loop PRD | `MEMORY-CI-LOOP.PRD` |
| Tag Extraction Plan (9 steps) | `plans/improve-oclaw-memory-tag-extraction-mar27-plan.md` |
| Memory Improvement Skill Plan | `plans/oclaw-memory-improvement-skill-plan.md` |
| Memory Locations Guide | `MEMORY-LOCATIONS.md` |

### Phase I — Analysis (Complete)

| Step | What | Finding |
|------|------|---------|
| Step 2 | Exported 7 sessions (stratified) + 112 memories + SOUL.md + USER.md | 5.9MB sample |
| Step 3 | Tag distribution analysis | 96.4% anchor coverage (PASS), importance flat (all=5), access_count all zeros |
| Step 4 | Claude-as-judge audit (all 112 memories) | Score: 2.52/5.0 — 56% need improvement, #1 problem = 40 duplicate Tailscale memories |

### Phase II — Implementation (Complete)

| Step | What | Result |
|------|------|--------|
| Step 1 | Dedup cleanup | 44 duplicates soft-deleted (112 → 68 memories) |
| Step 1 | Tag error fixes | 29 wrong decided: tags removed, 4 dual-confidence fixed |
| Step 3 P1-A | Tag normalization | 9 tag format replacements on VM |
| Step 3 P1-B | TAG_REGISTRY updates | Added type:fact, type:research, domain:career, domain:ops, pin:, permanent: |
| Step 4 P2-B | access_count tracking | smart_extractor.py increments on recall + bug fix |
| Step 5 P3-A | Decay exemption | should_decay() + categorize_memory() updated |
| Step 5 P3-B | Pin system | mem.py: pin/unpin commands, --pin flag, 3 levels |
| Step 6 | Stale cleanup | memory_lifecycle.py: 90-day rule, soft delete |
| Step 6a | Health monitor | mem.py status: 10-metric rubric, box visual, cron one-liner |
| Step 7 | VM deploy + Azure sync | 7 files deployed, 2 crons added, 68 memories synced |

---

## Key Decisions

### Tags
- **pin:** dimension — critical (importance=10), important (9), reference (8). User-applied, never decay.
- **permanent:true** — infrastructure facts, quarterly manual review.
- **type:fact** added to registry — fixes type:context overuse.
- No date tags on every memory — use timestamps instead.

### Scoring & Lifecycle
- 80-day freshness window, 2.0x boost (deferred — needs index schema change).
- access_count tracked on every recall.
- 90 days + 0 access + not pinned/permanent → soft delete.
- Health pass score = 7/10 GREEN.

### Architecture
- Claude-as-judge (independent from GPT-5.2 extractor).
- Dual-target design (ClawBot VM + Claude Code Mac, same codebase).
- Research-first CI loop — every cycle starts with best practices check.

---

## Health Check — Before & After

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Active memories | 112 | 68 | Quality > quantity |
| Duplicates | ~40 (36%) | ~3 (5%) | <10% |
| Anchor coverage | 96.4% | 92.6% | >80% |
| Importance spread | 1 level (flat) | 2 levels | 3+ levels |
| access_count tracking | Never | Active | Tracked |
| Health monitoring | None | Daily cron + CLI | Daily |
| Health score | ~4/10 | 7/10 | 7/10 |

---

## Files Created

| File | Purpose |
|------|---------|
| `MEMORY-CI-LOOP.PRD` | Master PRD |
| `MEMORY-LOCATIONS.md` | ClawBot vs Claude Code separation guide |
| `plans/improve-oclaw-memory-tag-extraction-mar27-plan.md` | 9-step plan |
| `plans/oclaw-memory-improvement-skill-plan.md` | Skill packaging plan |
| `plans/tag-analysis-mar27/step3-tag-distribution-report.md` | Tag analysis |
| `plans/tag-analysis-mar27/step4-claude-judge-report.md` | Quality audit |
| `oclaw_brain: memory_lifecycle.py` | Stale cleanup |
| `oclaw_brain: cli/mem_status.py` | Health scoring engine |
| `oclaw_brain: cli/mem_display.py` | Dashboard display |

## Files Modified

| File | Changes |
|------|---------|
| `oclaw_brain: TAG_REGISTRY.md` | +6 tag definitions |
| `oclaw_brain: cli/mem.py` | +pin/unpin/status commands |
| `oclaw_brain: smart_extractor.py` | +access_count increment, +L1+L2 winning prompt (definitions + few-shot + reasoning + atomicity) |
| `oclaw_brain: memory_bridge.py` | +should_decay(), categorize_memory() uses tags, +scoring profile, +filterable dates |
| `CLAUDE.md` | +MEMORY-LOCATIONS.md, PRD, and MEMORY-TEST-COMMANDS.md references |
| `plans/progress.md` | Full Phase I + II + III tracking |
| `manage-oclaw/MEMORY-TEST-COMMANDS.md` | All memory test/debug SSH commands |

## New Files (Phase III)

| File | Purpose |
|------|---------|
| `plans/tag-analysis-mar27/step8-layer-ab-comparison.md` | A/B test lift chart (5 layers scored) |
| `plans/tag-analysis-mar27/step9-retag-diff.json` | Old vs new tags diff for all 68 memories |
| `plans/tag-analysis-mar27/ab-run-*.json` | 18 extraction outputs (6 runs x 3 sessions) |
| `/private/tmp/claude/ab_test_runner.py` | Local A/B test runner (Entra auth) |
| `/private/tmp/claude/retag_memories.py` | Local re-tagging script (Entra auth) |

## VM Changes (via SSH)

- 44 memories soft-deleted (dedup)
- 29 decided: tags removed, 4 dual-confidence fixed, 9 tags normalized
- 68 memories re-tagged with winning L1+L2 prompt
- Stripped auto-assigned pin:/permanent: from 42 memories (user-only rule)
- 9 files deployed via scp
- DB paths fixed (agent-memory → claude-memory) on VM copies
- 2 cron jobs added (health 20:00 UTC, cleanup 1st/month 22:00 UTC)
- Azure index deleted + recreated with scoring profile (memory-relevance)
- Scoring profile: 80-day quadratic freshness 1.5x, importance 2.0x, content 1.5x, tags 1.2x
- Search Service Contributor RBAC role assigned to VM MI
- 68 memories synced to Azure AI Search (3 times — after dedup, re-tag, scoring profile)

## A/B Test Results (Phase III)

| Layer | Weighted Avg | Delta | Keep? |
|-------|-------------|-------|-------|
| Baseline | 0.858 | — | — |
| +Definitions | 0.902 | +5.1% | Yes |
| **+Few-shot** | **0.968** | **+12.8%** | **Yes (winner)** |
| +Strict schema | 0.940 | +9.6% | No (full stack worse) |
| +Closed vocab | 0.932 | +8.6% | No |
| +Keywords | 0.911 | +6.2% | No |

**Decision:** Use Layers 1+2 only. More layers = worse (prompt interference). Atomicity instruction added.

## Lessons Learned

| Lesson | Detail |
|--------|--------|
| `pin:` and `permanent:` are user-only | LLM applied them to 42 memories when they appeared in TAG_REGISTRY. Exclude from extraction prompt. |
| More prompt layers ≠ better | Full 5-layer stack scored lower than Layer 2 alone. Prompt complexity hurts. |
| DB path mismatch on VM | Source code uses `~/.agent-memory/`, VM needs `~/.claude-memory/`. Must fix after every `scp` deploy. |
| Sub-agents can't SSH | Sandbox blocks outbound to Tailscale IPs. Do SSH commands directly. |
| Sub-agents can't write to oclaw_brain | Outside sandbox write scope. Do file edits directly. |
| Index schema change requires delete+recreate | Can't add filterable to existing field. ~30 sec downtime. |

---

## What's Next

1. **Fix source code DB path** — make `memory_bridge.py` and `mem.py` use env var or config for DB path instead of hardcoded path. Eliminates the post-deploy sed fix.
2. **Skill packaging** — bundle into `memory-improvement` OpenClaw skill (Phase 2 of skill plan)
3. **Claude Code target** — adapt for Mac dev-tool context (Phase 3, deferred)
4. **ProMem iterative extraction** — research found 73.8% recall vs 41% one-shot. Future upgrade.
5. **Calibration set** — build 30-50 human-labeled examples to validate Claude-as-judge accuracy
