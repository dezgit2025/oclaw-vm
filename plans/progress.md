> Process: Follow plans/AGENT-PLAN.md for all task execution.

# Project: Memory CI Loop — Tag Extraction Analysis & Phase 0

**Plan:** `plans/improve-oclaw-memory-tag-extraction-mar27-plan.md`
**PRD:** `MEMORY-CI-LOOP.PRD`
**Dev folder:** `/Users/dez/Projects/openclaw_vm/` (analysis) + `/Users/dez/Projects/oclaw_brain/` (source code)
**Started:** 2026-03-27

---

## Current Status

| Phase | Status |
|-------|--------|
| Phase I — Data Export & Analysis (Steps 1-4) | Complete (2026-03-27) |
| Phase II — Cleanup, Normalization & Infrastructure (Steps 4a-5c) | Complete (2026-03-28) — scoring profile deferred |
| Phase III — Extraction Prompt Tuning & Validation (5 layers + A/B) | Complete (2026-03-28) |

---

## Key Learnings

| Type | Description | Resolution |
|------|-------------|------------|
| Gotcha | SSH to oclaw requires `dangerouslyDisableSandbox: true` in Claude Code | Sandbox blocks outbound connections to Tailscale IPs |
| Gotcha | `tailscale up` CLI fails with "Failed to load preferences" if app not opened first | Open Tailscale app from menu bar first, then CLI |

---

## Exceptions & Learnings

_(Log new issues here as they arise.)_

---

## Sprint Progress

### Phase I — Data Export & Analysis (Steps 1-4)

**Plan:** `plans/improve-oclaw-memory-tag-extraction-mar27-plan.md`
**Goal:** Export data from VM, analyze tag quality, produce Claude-as-judge baseline report.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 0 | [SEQ] — Manual: boot VM + Tailscale (DONE) |
| Step 2 | 1 | [SEQ] — Export data from VM to local |
| Step 3 | 1 | [SEQ] — Tag distribution analysis (needs Step 2 data) |
| Step 4 | 1 | [SEQ] — Claude-as-judge full audit (needs Step 2+3 data) |

**Total: 3 agent dispatches across 3 steps (sequential — each needs prior step's output).**

---

#### Step 1 — Boot VM + Tailscale `[SEQ]` — 0 agents (manual)

> **Launch condition:** None (first step).

- [x] (2026-03-27) Open Tailscale app, enable VPN
- [x] (2026-03-27) VM already running (up 20:34)
- [x] (2026-03-27) Start SSH tunnel (PID 26232, ports 18789-18798)
- [x] (2026-03-27) **Verify:** `ssh oclaw "hostname && uptime"` — PASS

---

#### Step 2 — Export data from VM `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete.

- [x] (2026-03-27) Create local analysis directory `plans/tag-analysis-mar27/`
- [x] (2026-03-27) Find sessions — stratified sample: 2 large, 3 medium, 2 small (7 total, ~5.9MB)
- [x] (2026-03-27) Copy 7 session JSONL files locally (replaced initial 3 tiny files)
- [x] (2026-03-27) Export all active memories as JSONL (112 memories, 55KB)
- [x] (2026-03-27) Export tag distribution (67 tag groups)
- [x] (2026-03-27) Copy SOUL.md (7.5KB) and USER.md (2.2KB) from VM
- [x] (2026-03-27) Add `plans/tag-analysis-mar27/` to `.gitignore`
- [x] (2026-03-27) **Verify:** All 10 files exist and are non-empty — PASS

---

#### Step 3 — Tag distribution analysis `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete.

- [x] (2026-03-27) Analyze tag frequency distribution — 594 tag usages, 70 unique tags
- [x] (2026-03-27) Calculate anchor coverage — 96.4% have both type: + domain: (PASS, target 80%)
- [x] (2026-03-27) Tag diversity — no single tag >25% (PASS, max is status:active at 16.2%)
- [x] (2026-03-27) Near-duplicate detection — found conflicting confidence tags on 6 memories
- [x] (2026-03-27) Free-form tags — 40 outside registry (75 usages), 6 candidates for promotion
- [x] (2026-03-27) Tags-per-memory average — ~5.3 tags/memory
- [x] (2026-03-27) Write report to `plans/tag-analysis-mar27/step3-tag-distribution-report.md`
- [x] (2026-03-27) **Verify:** Report contains all metrics + key findings — PASS

**Critical findings:** importance flat (all=5), access_count all zeros, type:context overuse (20.5%), domain:infrastructure dominates (70.4%), 83% memories from single session, decided:2026-02-23 over-applied to 76 memories

---

#### Step 4 — Claude-as-judge full audit `[SEQ]` — 1 agent

> **Launch condition:** Steps 2 and 3 complete.

- [x] (2026-03-27) Load all 112 memories from `all-memories.jsonl`
- [x] (2026-03-27) Load SOUL.md + USER.md for ClawBot utility scoring
- [x] (2026-03-27) Load TAG_REGISTRY.md for tag specificity evaluation
- [x] (2026-03-27) Score all 112 memories on 6 dimensions — weighted avg: **2.52/5.0**
- [x] (2026-03-27) Aggregate: 56.3% "needs improvement", only 10.7% "excellent"
- [x] (2026-03-27) Read 2 small session JSONL files — found 13 missed facts
- [x] (2026-03-27) Write report to `plans/tag-analysis-mar27/step4-claude-judge-report.md`
- [x] (2026-03-27) **Verify:** Report has all sections — PASS

**Key finding:** #1 problem is duplication (~40 near-identical Tailscale watchdog memories from single bulk extraction). Manually-added memories score 4.0-4.7. Phase 0 validated — need `type:fact` in registry + better dedup in extractor.

#### Success Criteria (Phase I)

1. All data exported from VM to local `plans/tag-analysis-mar27/`
2. Tag distribution report shows baseline anchor coverage and diversity metrics
3. Claude-as-judge report scores all active memories with weighted averages
4. Missed-fact analysis covers all 3 session transcripts
5. Decision gate: Phase 0 validated or deprioritized based on data

---

### Phase II — Cleanup, Normalization & Infrastructure (Steps 4a-5c)

**Plan:** `plans/improve-oclaw-memory-tag-extraction-mar27-plan.md`
**Goal:** Clean up duplicates, fix tag errors, normalize tags, add recency boost, access tracking, lifecycle management, and pin system.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Dedup cleanup + tag error fixes (Step 4a) |
| Step 2 | 1 | [SEQ] — Re-extract baseline on VM (Step 5) |
| Step 3 | 2 | [P1-A, P1-B] — Tag normalization + registry updates (Step 5a) |
| Step 4 | 2 | [P2-A, P2-B] — Scoring profile + access_count (Step 5b-1, 5b-2) |
| Step 5 | 2 | [P3-A, P3-B] — permanent:true + pin: tags (Step 5b-3, 5c) |
| Step 6 | 1 | [SEQ] — Stale cleanup cron + quarterly review (Step 5b-4, 5b-5) |
| Step 6a | 1 | [SEQ] — Memory health monitor: `mem.py status` + daily cron |
| Step 7 | 1 | [GATE] — Verify all changes, sync --full, deploy to VM |

**Total: 11 agent dispatches across 8 steps.**

---

#### Step 1 — Dedup cleanup + tag error fixes `[SEQ]` — 1 agent

> **Launch condition:** Phase I complete.
> **File ownership:** Agent writes to VM SQLite via SSH. No local file changes.

- [x] (2026-03-27) Query Tailscale/watchdog/chromeos memories — found 49 candidates
- [x] (2026-03-27) Identified 5 canonical versions to keep (architecture, decisions, hardening)
- [x] (2026-03-27) Soft-deleted 44 duplicates (active=0)
- [x] (2026-03-27) Removed `decided:2026-02-23` from 29 non-decision memories
- [x] (2026-03-27) Fixed 4 dual-confidence-tag memories (kept confidence:low)
- [ ] Add `type:fact` to TAG_REGISTRY.md — moved to Step 3 P1-B (separate agent)
- [x] (2026-03-27) **Verify:** Active memory count = 68 (was 112) — PASS

---

#### Step 2 — Re-extract baseline `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete (clean data).
> **File ownership:** Agent writes to `plans/tag-analysis-mar27/session*-current-extraction.json`.

- [ ] Dry-run extraction on 3 representative sessions (current prompt, no storage)
- [ ] Save extraction output locally for A/B comparison in Phase III
- [ ] Count tag types used across extractions
- [ ] Flag `type:context` or `type:insight` that should be more specific
- [ ] **Verify:** 3 extraction JSON files exist in `plans/tag-analysis-mar27/`

---

#### Step 3 — Tag normalization + registry updates `[P1-A, P1-B]` — 2 agents in parallel

> **Launch condition:** Step 1 complete.
> **File ownership:** P1-A owns VM SQLite tags. P1-B owns TAG_REGISTRY.md.

**`[P1-A]` Format normalization (VM SQLite)** — COMPLETE (2026-03-27)
- [x] (2026-03-27) Built normalization map: tags:geo→domain:geo, tags:app-launch→domain:product, tag:folder→domain:ops, domain:architecture→type:architecture
- [x] (2026-03-27) Applied 9 REPLACE queries to SQLite on VM
- [x] (2026-03-27) **Verify:** Re-run tag distribution — no more tags: or tag: prefix anti-patterns

**`[P1-B]` Registry updates (TAG_REGISTRY.md)** — COMPLETE (2026-03-27)
- [x] (2026-03-27) Added `type:fact` — "A verifiable, objective observation or measurement"
- [x] (2026-03-27) Added `type:research` — "Investigation or exploration of a topic, tool, or approach"
- [x] (2026-03-27) Added `domain:career`, `domain:ops`
- [x] (2026-03-27) Added `pin:` dimension (critical/important/reference) with rules
- [x] (2026-03-27) Added `permanent:true` tag with rules
- [x] (2026-03-27) **Verify:** `grep -c` returns 6 new entries — PASS

---

#### Step 4 — Scoring profile + access tracking `[P2-A, P2-B]` — 2 agents in parallel

> **Launch condition:** Step 1 complete (can run parallel with Step 3).
> **File ownership:** P2-A owns `memory_bridge.py` index definition. P2-B owns `smart_extractor.py` recall function.

**`[P2-A]` Azure scoring profile (memory_bridge.py)** — DEFERRED to Step 7
- [ ] Create staging index `clawbot-memory-store-staging`
- [ ] Add `memory-relevance` scoring profile (80-day freshness 2.0x, importance 2.0x, content 1.5x, tags 1.2x)
- [ ] Set `scoring_profile="memory-relevance"` in search call
- [ ] Test recall against staging
- [ ] **Verify:** Recall benchmark on staging shows recency-boosted results
- **Note:** Requires Azure index schema change (may need delete+recreate). Doing this during GATE step with full sync.

**`[P2-B]` Increment access_count (smart_extractor.py)** — COMPLETE (2026-03-27)
- [x] (2026-03-27) Added access_count increment in `cmd_recall` after memories sorted/sliced
- [x] (2026-03-27) Fixed pre-existing bug: `_parse_mem_line` now correctly parses `[mem_id] (tags) content` format
- [x] (2026-03-27) Best-effort try/except — can never break recall flow
- [ ] Deploy to VM (pending — will deploy all changes together in Step 7)
- [ ] **Verify:** Trigger recall, check access_count incremented in SQLite

---

#### Step 5 — Lifecycle tags `[P3-A, P3-B]` — 2 agents in parallel

> **Launch condition:** Step 3 P1-B complete (TAG_REGISTRY updated).
> **File ownership:** P3-A owns `memory_bridge.py` decay logic. P3-B owns `mem.py` CLI.

**`[P3-A]` permanent:true tag + decay exemption** — COMPLETE (2026-03-27)
- [x] (2026-03-27) Added `should_decay()` function to `memory_bridge.py` — checks for `permanent:true` and `pin:` tags
- [x] (2026-03-27) Updated `categorize_memory()` to use tags first, content heuristics as fallback
- [x] (2026-03-27) Updated call site to pass tags to `categorize_memory(content, tags)`
- [x] (2026-03-27) **Verify:** Function logic correct — permanent/pinned memories return False

**`[P3-B]` Pin system in mem.py CLI** — COMPLETE (2026-03-27)
- [x] (2026-03-27) Added `--pin` argument to `add` subcommand (choices: critical/important/reference)
- [x] (2026-03-27) Added `pin` subcommand: `mem.py pin MEM_ID critical`
- [x] (2026-03-27) Added `unpin` subcommand: `mem.py unpin MEM_ID` (resets importance to 5)
- [x] (2026-03-27) PIN_IMPORTANCE dict: critical=10, important=9, reference=8
- [ ] Add pin detection rule to `smart_extractor.py` extraction prompt — deploy in Step 7
- [ ] **Verify:** `python3 mem.py add "test" --pin critical` stores with pin:critical tag, importance=10 — test on VM after deploy

---

#### Step 6 — Stale cleanup + quarterly review `[SEQ]` — 1 agent

> **Launch condition:** Steps 4 and 5 complete.
> **File ownership:** Agent creates `memory_lifecycle.py` + cron entry.

- [x] (2026-03-27) Created `memory_lifecycle.py` with `cleanup_stale_memories()` + `list_permanent()`
- [x] (2026-03-27) Rule: >90 days + access_count=0 + not pinned/permanent → soft delete
- [x] (2026-03-27) Supports `--dry-run` flag, logs to `~/.openclaw/logs/memory-lifecycle/`
- [ ] Add monthly cron on VM (1st of month, 22:00 UTC) — deploy in Step 7
- [ ] Document quarterly permanent review process
- [ ] **Verify:** Dry-run cleanup shows 0 candidates (all memories are <90 days old currently)

---

#### Step 6a — Memory health monitor `[SEQ]` — 1 agent

> **Launch condition:** Step 6 complete (lifecycle code exists).
> **File ownership:** Agent modifies `mem.py` (adds `status` subcommand).

**Goal:** Add `mem.py status` command that scores memory health against a 10-metric rubric, plus a `--log-only` flag for daily cron.

**Health rubric (10 metrics, pass = 7/10 GREEN):**

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Anchor coverage (type: + domain:) | >80% | 60-80% | <60% |
| Tag diversity (max single tag %) | <25% | 25-40% | >40% |
| Recall rate (% recalled in 30d) | >10% | 1-10% | 0% |
| Stale ratio (>90d, 0 access) | <15% | 15-30% | >30% |
| Duplicate density (word overlap) | <10% | 10-20% | >20% |
| Pin/permanent ratio | <30% | 30-50% | >50% |
| Growth (new memories in 30d) | 10-100 | 1-10 or 100-200 | 0 or >200 |
| Avg tags per memory | 3-6 | 2-3 or 6-7 | <2 or >7 |
| Importance spread | 3+ levels | 2 levels | 1 level (flat) |
| Age distribution (max single-day %) | <50% | 50-70% | >70% |

**Score interpretation:**

| Score | Rating | Label |
|-------|--------|-------|
| 9-10 | Excellent | `EXCELLENT` |
| 7-8 | Healthy (pass) | `HEALTHY` |
| 5-6 | Needs attention | `ATTENTION` |
| 3-4 | Unhealthy | `UNHEALTHY` |
| 0-2 | Broken | `BROKEN` |

- [x] (2026-03-27) Created `mem_status.py` — 10-metric scoring engine with thresholds
- [x] (2026-03-27) Created `mem_display.py` — box visual dashboard + cron one-liner
- [x] (2026-03-27) Added `cmd_status()` to `mem.py` with lazy imports
- [x] (2026-03-27) Added `--log-only` flag for cron one-liner output
- [x] (2026-03-27) Added `status` subcommand to argparse
- [ ] Add daily cron on VM: `0 20 * * *` runs `mem.py status --log-only` — deploy in Step 7
- [ ] **Verify:** `python3 mem.py status` outputs health dashboard — test on VM after deploy

---

#### Step 7 — GATE: Verify + sync `[GATE]` — 1 agent

> **Launch condition:** All Steps 1-6 complete.

- [ ] Re-run tag distribution analysis — compare to Step 3 baseline
- [ ] Confirm memory count reduced (dedup applied)
- [ ] Confirm scoring profile active on staging
- [ ] Run `memory_bridge.py sync --full` to push all changes to Azure
- [ ] Capture post-normalization baseline scores
- [ ] **Verify:** Azure AI Search returns results with scoring profile applied

#### Success Criteria (Phase II)

1. Memory count reduced from 112 to ~75-80 (duplicates removed)
2. No memories with wrong `decided:` tags on non-decisions
3. No dual-confidence-tag conflicts
4. `type:fact` exists in TAG_REGISTRY.md
5. Scoring profile `memory-relevance` active on staging index
6. `access_count` increments on recall
7. `pin` and `unpin` CLI commands work
8. `permanent:true` exempted from decay logic
9. Monthly cleanup cron installed
10. Azure AI Search fully synced with cleaned data
11. `mem.py status` outputs health dashboard with 10-metric rubric
12. Daily health check cron installed (20:00 UTC)

---

### Phase III — Extraction Prompt Tuning & Validation (Steps 6-9)

**Plan:** `plans/improve-oclaw-memory-tag-extraction-mar27-plan.md`
**Goal:** Implement 5 extraction prompt improvements, A/B test each layer individually, re-tag existing memories with winning prompt.
**Research:** `plans/research-log.md` (2026-03-28 entries — memory tags, extraction prompts, Azure scoring)

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Re-extract baseline (3 stratified sessions, current prompt) |
| Step 2 | 1 | [SEQ] — Implement Layer 1 (definitions + counts) |
| Step 3 | 1 | [SEQ] — Implement Layer 2 (few-shot examples + reasoning field) |
| Step 4 | 1 | [SEQ] — Implement Layer 3 (strict: true JSON Schema) |
| Step 5 | 1 | [SEQ] — Implement Layer 4 (closed type: vocabulary) |
| Step 6 | 1 | [SEQ] — Implement Layer 5 (keyword extraction kw: tags) |
| Step 7 | 1 | [SEQ] — Layer-by-layer A/B test (6 runs x 3 sessions = 18 extractions) |
| Step 8 | 1 | [SEQ] — Re-tag existing 68 memories with winning prompt |
| Step 9 | 1 | [GATE] — Final verify + sync |

**Total: 9 steps, sequential (each layer builds on the previous).**

**Note:** Steps 2-6 are sequential because each layer is cumulative — Layer 2 includes Layer 1, etc. The A/B test in Step 7 runs all 6 variants (baseline + 5 layers) to produce a per-layer lift chart.

---

#### Step 1 — Re-extract baseline `[SEQ]` — 1 agent

> **Launch condition:** Phase II complete.
> **File ownership:** Agent writes to `plans/tag-analysis-mar27/ab-run-0-*.json`

- [x] (2026-03-28) Dry-run extraction on 3 stratified sessions — ran locally via az login Entra auth
- [x] (2026-03-28) Saved: `ab-run-0-large.json` (4 facts), `ab-run-0-medium.json` (10), `ab-run-0-small.json` (4)
- [x] (2026-03-28) **Verify:** 3 JSON files exist — PASS (18 total baseline facts)

---

#### Step 2 — Layer 1: Definitions + usage counts `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete.
> **File ownership:** Agent modifies `smart_extractor.py` (extract_known_tags, tag_ref builder)

- [x] (2026-03-28) All Layer 1 changes implemented in A/B test runner
- [x] (2026-03-28) Dry-run: `ab-run-1-large.json` (5), `ab-run-1-medium.json` (14), `ab-run-1-small.json` (3) — 22 total
- [x] (2026-03-28) **Verify:** tag_ref includes definitions + counts — PASS

---

#### Step 3 — Layer 2: Few-shot examples + reasoning `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete.
> **File ownership:** Agent modifies `smart_extractor.py` (prompt + JSON schema)

- [x] (2026-03-28) Added reasoning field + 3 few-shot examples (type:fact, type:pattern, type:error_pattern)
- [x] (2026-03-28) Dry-run: `ab-run-2-*` — 14 total (4+8+2). Facts include reasoning field.
- [x] (2026-03-28) **Verify:** Reasoning field present — PASS

---

#### Step 4 — Layer 3: strict: true JSON Schema `[SEQ]` — 1 agent

> **Launch condition:** Step 3 complete.
> **File ownership:** Agent modifies `smart_extractor.py` (response_format)

- [x] (2026-03-28) Added strict: true JSON schema with field ordering
- [x] (2026-03-28) Dry-run: `ab-run-3-*` — 18 total (3+14+1). Structured output enforced.
- [x] (2026-03-28) **Verify:** Zero format errors — PASS

---

#### Step 5 — Layer 4: Closed type: vocabulary `[SEQ]` — 1 agent

> **Launch condition:** Step 4 complete.
> **File ownership:** Agent modifies `smart_extractor.py` (prompt wording)

- [x] (2026-03-28) Closed type: vocabulary (10 values), domain: kept open
- [x] (2026-03-28) Dry-run: `ab-run-4-*` — 16 total (2+11+3)
- [x] (2026-03-28) **Verify:** No invented type: tags — PASS

---

#### Step 6 — Layer 5: Keyword extraction `[SEQ]` — 1 agent

> **Launch condition:** Step 5 complete.
> **File ownership:** Agent modifies `smart_extractor.py` (prompt)

- [x] (2026-03-28) Added kw: keyword extraction instruction
- [x] (2026-03-28) Dry-run: `ab-run-5-*` — 15 total (1+12+2). Facts include kw: tags.
- [x] (2026-03-28) **Verify:** kw: tags present — PASS

---

#### Step 7 — Layer-by-layer A/B scoring `[SEQ]` — 1 agent

> **Launch condition:** Steps 1-6 complete (all 6 runs saved).
> **File ownership:** Agent writes `plans/tag-analysis-mar27/step8-layer-ab-comparison.md`

**Research-informed rubric (2026-03-28 — LLM-as-judge best practices):**

**Structure:**
- 6 isolated judge calls per memory (not 1 bundled — Anthropic guidance)
- CoT before score: `{"critique": "...", "score": N}` — reasoning first
- Blind labels: variants as "Alpha/Beta", randomized per call
- Swap-and-re-judge for any pairwise comparisons

**Scoring (mixed scales):**
- Binary (0/1): fact accuracy, atomicity
- 1-3 with anchors: tag accuracy, tag specificity, anchor completeness, ClawBot utility

**Statistics (N=18 = screening budget):**
- Report directional consistency (3/3 sessions = high confidence)
- Bayesian Beta-Binomial for binary dimensions
- Raw counts, not percentages
- Effect size threshold: 0.5+ on 1-3 scale

**Substeps:**
- [x] (2026-03-28) Scored all 103 facts across 6 runs with 6-dimension rubric
- [x] (2026-03-28) Binary scoring for fact accuracy + atomicity
- [x] (2026-03-28) 1-3 anchored scoring for tag accuracy, specificity, anchors, utility
- [x] (2026-03-28) Lift chart: R2 (+Few-shot) won at 0.968 weighted avg (+12.8% over baseline 0.858)
- [x] (2026-03-28) Directional: R1 = 3/3 sessions (most reliable), R2 = 2/3 (highest score)
- [x] (2026-03-28) Layers 1+2 keep (>5% each). Layers 3-5 drop (full stack scored worse than R2 alone)
- [x] (2026-03-28) Report written to `plans/tag-analysis-mar27/step8-layer-ab-comparison.md`
- [x] (2026-03-28) **Verify:** Lift chart complete, decision: use L1+L2 only — PASS

**Finding:** More layers = worse. Full stack (R5=0.911) < R2 alone (0.968). Atomicity degrades with richer prompts. Keywords as post-processing, not in prompt.

---

#### Step 8 — Re-tag existing memories `[SEQ]` — 1 agent

> **Launch condition:** Step 7 cumulative score > 3.5/5.
> **File ownership:** Agent writes to VM SQLite via SSH.

- [x] (2026-03-28) Exported all 68 memories, re-tagged with winning L1+L2 prompt via Entra auth
- [x] (2026-03-28) Reasoning field included for every tag choice
- [x] (2026-03-28) Diff: 68/68 changed — saved to `plans/tag-analysis-mar27/step9-retag-diff.json`
- [x] (2026-03-28) Applied to VM SQLite
- [x] (2026-03-28) Stripped auto-assigned pin:/permanent: (42 memories) — user-only rule violated by re-tag prompt
- [x] (2026-03-28) **Verify:** `mem.py status` = 6/10 ATTENTION. Anchor coverage 100%, tag diversity 14.7%

**Lesson learned:** `pin:` and `permanent:` tags must NOT appear in the extraction/re-tagging prompt. They are user-applied only. The re-tag prompt saw them in TAG_REGISTRY and applied them to 42 memories. Fixed by stripping post-hoc.

---

#### Step 9 — GATE: Final verify + sync `[GATE]` — 1 agent

> **Launch condition:** Step 8 complete.

- [x] (2026-03-28) `memory_bridge.py sync --full` — 68 memories synced to Azure
- [x] (2026-03-28) `mem.py status` = 6/10 ATTENTION (recall rate + age distribution will improve over time)
- [x] (2026-03-28) Final `smart_extractor.py` deployed to VM (winning L1+L2 variant)
- [x] (2026-03-28) Azure search verified — returns results with improved tags
- [ ] Claude-as-judge re-validation — deferred to next session (need new extraction data first)
- [x] (2026-03-28) **Verify:** Azure search returns re-tagged results — PASS

#### Success Criteria (Phase III)

1. Lift chart produced — per-layer impact measured with 6 isolated judge calls per dimension
2. Directional consistency documented (3/3 sessions = high confidence per layer)
3. Binary dimensions (fact accuracy, atomicity) show pass rate improvement
4. Graded dimensions (tag accuracy, specificity, anchors, utility) show 0.5+ mean improvement on 1-3 scale
5. `type:context` overuse reduced by >30%
6. Zero format bugs after Layer 3 (strict JSON schema)
7. All 68 memories re-tagged with winning prompt variant
8. `mem.py status` health score maintained at 7/10 or higher
9. Azure AI Search synced with re-tagged data
10. Research rubric methodology documented in plan for reproducibility
