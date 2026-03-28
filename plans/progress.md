> Process: Follow plans/AGENT-PLAN.md for all task execution.

# Project: Memory Recall Optimizer

**Plan:** `plans/memory-recall-optimizer1.md`
**Dev folder:** `~/Projects/oclaw_brain/oclaw_brain_skill_v1/` (source code) + `~/Projects/openclaw_vm/` (benchmark tools + data)

---

## Gates

### Plan Gate

> **Auto-populated:** `memory-recall-optimizer1` is replaced with the plan filename when this progress.md is created or updated.

- **Read `plans/memory-recall-optimizer1.md` before AND after every step.**
- Before: confirm your approach aligns with the plan's specification.
- After: diff your changes against the plan — if anything deviates, fix the code before moving on.
- The plan file is **read-only** — never modify it from progress.md context.

### Architecture Gate

> **SKIP** — architecture is already documented in the PRD (`MEMORY-CI-LOOP.PRD`) and the plan itself contains the full architecture diagram (Local Test → Compare → Push). No separate `plans/architectural-design.md` needed.

---

## Rules to Follow

> See `plans/AGENT-PLAN.md` for the 5-phase task execution protocol.
> See `plans/workflow/` for detailed workflow rules:
> - `agent-orchestration.md` — sub-agent dispatch, parallelism, domain routing
> - `testing-protocol.md` — TDD, test placement, quality gates
> - `progress-discipline.md` — how to manage this file, recovery
> - `commit-protocol.md` — git workflow, branching, atomic commits
> - `code-gap-handling.md` — adaptive gap resolution: ImportError, API changes, auth failures, unknown blockers

### Core Rules
1. **Read this file FIRST** at the start of every session
2. **Update this file AFTER** completing each step — immediately, not in batch
3. **Never contradict this file** — if it says something is done, don't redo it
4. **Follow AGENT-PLAN.md** for task execution, testing, and commits
5. **Research before guessing** — log findings to `plans/research-log.md`

### Execution Model
- **Strict delegation.** Orchestrator coordinates — subagents do code work.
- **Only the orchestrator updates this file.** Subagents report back; orchestrator records.
- **Use subagents in parallel** when steps have no shared dependencies.

### Testing (After Every Step)
- Follow `plans/AGENT-PLAN.md` Phases 3-4 for all testing after implementation.
- 3 agents, sequential loop: `test-planner` → `test-writer` → `test-runner` (one test at a time).
- A step is not `[x]` until all planned tests pass AND verification passes.

### Step Verification
- **Commit after each phase is completed.** This is your checkpoint.
- **Each step should have a verification command.** A step is not complete until its verify command passes.
- **Mark a step `[x]` only when:** action is done, verification passes, AND tests exist.
- **On ANY error/exception:** Log it in the Exceptions & Learnings section.

### Recovery After Crash
```
1. Read this file → find last completed step
2. Check git log → verify last commit matches
3. Resume from the NEXT uncompleted step
4. If a step was in-progress, re-run it from scratch
```

---

## Import Rules

```
quality/recall/*.py -> smart_extractor + memory_bridge (read recall results, not modify)
quality/recall/*.py -> quality/data/*.json (read/write benchmark data)
handler.js -> smart_extractor.py (invokes via shell, not Python import)
smart_extractor.py -> memory_bridge.py (imports hybrid search)
smart_extractor.py DO NOT import quality/* (benchmark is separate from production)
```

---

## Formatting Rules — How to Structure Phases, Steps, and Substeps

> These rules define how sprint progress sections must be written.
> Follow this structure exactly when filling in the Sprint Progress section.

### Current Status Table

The status table is the **first thing to check** at session start. It shows all phases and their state at a glance.

### Step Format

Each step is an `####` heading under its phase. Include the parallelism tag and agent count.

### Substep Format

Substeps are checkboxes (`- [ ]`) under a step. They are atomic actions.

---

## Current Status

| Phase | Status |
|-------|--------|
| Phase 0 — Architecture | SKIP — documented in MEMORY-CI-LOOP.PRD |
| Round 1 — Baseline Measurement | NOT STARTED |
| Round 2 — RRF Fusion | NOT STARTED |
| Round 3 — Query Quality Bundle | NOT STARTED |
| Round 4 — Embed/Scoring Quality | NOT STARTED |
| Round 5 — Full Benchmark (conditional) | NOT STARTED — only if stop gate not met after Round 4 |
| Round 6 — Deploy to VM | NOT STARTED |

---

## Parallelism Legend

| Tag | Meaning |
|-----|---------|
| `[SEQ]` | Sequential — must complete before next step |
| `[P1-x]` | Parallel group 1 — all P1 steps launch simultaneously |
| `[P2-x]` | Parallel group 2 — all P2 steps launch simultaneously |
| `[GATE]` | Sync point — waits for all prior parallel steps to finish |

---

## Key Learnings

> Carry forward across phases. When you hit a bug, conflict, or blocker that has a resolution, log it here so future phases don't repeat the mistake.

| Type | Description | Resolution |
|------|-------------|------------|
| _(none yet)_ | | |

---

## Exceptions & Learnings

> Runtime errors, unexpected behaviors, and one-off issues encountered during execution. Unlike Key Learnings (which are reusable patterns), this section captures session-specific incidents.

_(Log new issues here as they arise.)_

---

## Sprint Progress

### Phase 0 — Architecture (SKIP)

> **SKIP:** Architecture is documented in `MEMORY-CI-LOOP.PRD` and in the plan itself (`plans/memory-recall-optimizer1.md` — "Architecture: Local Test → Compare → Push" diagram). No separate architecture doc needed.

---

### Round 1 — Baseline Measurement

**Plan:** `plans/memory-recall-optimizer1.md`
**Goal:** Get a number — export memories, build 20 benchmark queries, run recall, judge on 2 dimensions (Relevance + Noise), compute Precision@5 / MRR / weighted score.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Export memory snapshot to JSON fixture |
| Step 2 | 1 | [SEQ] — Generate 20 benchmark queries (10 verbatim + 10 temporal) |
| Step 3 | 1 | [SEQ] — Run baseline recall against local SQLite |
| Step 4 | 1 | [SEQ] — Judge baseline on 2 dimensions (Relevance + Noise) |
| Step 5 | 1 | [SEQ] — Compute Precision@5, MRR, weighted score |

**Total: 5 agent dispatches across 5 steps (sequential — each needs prior step's output).**

---

#### Step 1 — Export Memory Snapshot `[SEQ]` — 1 agent

> **Launch condition:** None (first step).
> **File ownership:** Agent creates `quality/recall/export_snapshot.py` and `quality/data/memory_snapshot.json`.

- [ ] Create `quality/recall/export_snapshot.py` — reads `~/.agent-memory/memory.db`, exports all active memories to JSON
- [ ] Run: `python3 quality/recall/export_snapshot.py --db ~/.agent-memory/memory.db --output quality/data/memory_snapshot.json`
- [ ] Confirm output contains all active memories with id, content, tags, project, importance, access_count, created_at
- [ ] **Verify:** `python3 -c "import json; d=json.load(open('quality/data/memory_snapshot.json')); print(f'{len(d)} memories exported')"` — count > 0

---

#### Step 2 — Generate 20 Benchmark Queries `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete (need snapshot to mine queries from).
> **File ownership:** Agent creates `quality/recall/generate_queries.py` and `quality/data/recall_benchmark.json`.

- [ ] Create `quality/recall/generate_queries.py` — uses GPT-4.1-mini to generate "What question would this memory answer?" per top-10 memory
- [ ] Generate 10 verbatim fact recall queries from top-10 highest-importance memories
- [ ] Generate 10 temporal ordering queries manually: "What did we decide about X?" for decisions with dates
- [ ] Each query includes: id, query, category, expected_memory_ids, expected_keywords, difficulty
- [ ] Save to `quality/data/recall_benchmark.json`
- [ ] **Verify:** `python3 -c "import json; d=json.load(open('quality/data/recall_benchmark.json')); print(f'{len(d)} queries'); assert len(d)==20"` — exactly 20 queries

---

#### Step 3 — Run Baseline Recall `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete (need benchmark queries).
> **File ownership:** Agent creates `quality/recall/run_benchmark.py` and `quality/data/round1-baseline.json`.

- [ ] Create `quality/recall/run_benchmark.py` — runs each query through `cmd_recall()` against local SQLite
- [ ] Run: `python3 quality/recall/run_benchmark.py --benchmark quality/data/recall_benchmark.json --db ~/.agent-memory/memory.db --output quality/data/round1-baseline.json`
- [ ] Output includes: query, recalled memory IDs, recalled content, expected IDs, hit/miss per query
- [ ] **Verify:** `python3 -c "import json; d=json.load(open('quality/data/round1-baseline.json')); print(f'{len(d)} results')"` — 20 results

---

#### Step 4 — Judge Baseline on 2 Dimensions `[SEQ]` — 1 agent

> **Launch condition:** Step 3 complete (need recall results).
> **File ownership:** Agent creates `quality/recall/judge_recall.py` and `quality/data/round1-scores.json`.

- [ ] Create `quality/recall/judge_recall.py` — LLM-as-judge scoring (one criterion per call, CoT before score, temperature=0)
- [ ] Score each of 20 queries on **Relevance** (30% weight) and **Noise** (10% weight) — 40 judge calls total
- [ ] Use GPT-4.1-mini as judge model
- [ ] Run: `python3 quality/recall/judge_recall.py --input quality/data/round1-baseline.json --dimensions relevance,noise --model gpt-4.1-mini --output quality/data/round1-scores.json`
- [ ] Output includes per-query: reasoning, score (1-5), dimension
- [ ] **Verify:** `python3 -c "import json; d=json.load(open('quality/data/round1-scores.json')); print(f'{len(d[\"scores\"])} judge scores')"` — 40 scores

---

#### Step 5 — Compute Metrics `[SEQ]` — 1 agent

> **Launch condition:** Step 4 complete (need judge scores).
> **File ownership:** Agent creates `quality/recall/regression_gate.py`, updates `quality/data/round1-scores.json` with metrics.

- [ ] Create `quality/recall/regression_gate.py` — computes Precision@5, MRR, weighted judge score; compares before/after with thresholds
- [ ] Compute Precision@5 from round1-baseline.json (fraction of expected IDs in top 5)
- [ ] Compute MRR (mean reciprocal rank of first expected ID)
- [ ] Compute weighted judge score (Relevance 30% + Noise 10%)
- [ ] Document baseline numbers in this progress.md
- [ ] **Verify:** `python3 quality/recall/regression_gate.py --baseline quality/data/round1-scores.json` — prints all 3 metrics

#### Success Criteria (Round 1)

1. `quality/data/memory_snapshot.json` exists with all active memories
2. `quality/data/recall_benchmark.json` contains exactly 20 curated queries
3. `quality/data/round1-baseline.json` has recall results for all 20 queries
4. `quality/data/round1-scores.json` has 40 judge scores (20 queries x 2 dimensions)
5. Baseline Precision@5, MRR, and weighted score documented

---

### Round 2 — RRF Fusion

**Plan:** `plans/memory-recall-optimizer1.md`
**Goal:** Replace dedup+priority sort with Reciprocal Rank Fusion (k=10) in `cmd_recall()`. Highest-ROI single code change: +8-10% accuracy, 15 lines, zero API cost.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Implement `rrf_fuse()` in smart_extractor.py |
| Step 2 | 1 | [SEQ] — Re-run benchmark + judge |
| Step 3 | 1 | [SEQ] — Compare Round 1 → Round 2 |

**Total: 3 agent dispatches across 3 steps (sequential).**

---

#### Step 1 — Implement RRF Fusion `[SEQ]` — 1 agent

> **Launch condition:** Round 1 complete (baseline numbers exist).
> **File ownership:** Agent modifies `smart_extractor.py` (`cmd_recall()` + new `rrf_fuse()` function).

- [ ] Add `rrf_fuse(query_results, k=10)` function to `smart_extractor.py`
- [ ] Replace dedup+priority sort block in `cmd_recall()` with RRF fusion call
- [ ] Collect per-query results as separate lists before fusing
- [ ] Use tag priority as tiebreaker in RRF sort
- [ ] **Verify:** `python3 -c "from smart_extractor import rrf_fuse; print('import ok')"` — no import error

---

#### Step 2 — Re-run Benchmark + Judge `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete.
> **File ownership:** Agent writes `quality/data/round2-results.json` and `quality/data/round2-scores.json`.

- [ ] Run: `python3 quality/recall/run_benchmark.py --benchmark quality/data/recall_benchmark.json --db ~/.agent-memory/memory.db --output quality/data/round2-results.json`
- [ ] Run: `python3 quality/recall/judge_recall.py --input quality/data/round2-results.json --dimensions relevance,noise --model gpt-4.1-mini --output quality/data/round2-scores.json`
- [ ] **Verify:** `test -f quality/data/round2-scores.json && echo "scores exist"`

---

#### Step 3 — Compare Round 1 → Round 2 `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete.
> **File ownership:** Agent reads score files, documents deltas in this progress.md.

- [ ] Run: `python3 quality/recall/regression_gate.py --before quality/data/round1-scores.json --after quality/data/round2-scores.json`
- [ ] Document delta for Precision@5, MRR, weighted score (expected: +8-10%)
- [ ] Confirm no regression (delta >= -0.05 on all metrics)
- [ ] **Verify:** Regression gate passes (all metrics above thresholds)

#### Success Criteria (Round 2)

1. `rrf_fuse()` function exists in `smart_extractor.py`
2. `cmd_recall()` uses RRF instead of dedup+priority
3. `quality/data/round2-scores.json` has 40 judge scores
4. Before/after comparison documented with deltas
5. Expected: +8-10% on Precision@5

---

### Round 3 — Query Quality Bundle

**Plan:** `plans/memory-recall-optimizer1.md`
**Goal:** Three improvements to the query side — dynamic topic expansion with few-shot, multi-turn context in hook, trivial turn gate. All modify query construction, not the index.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Dynamic topic expansion + few-shot in smart_extractor.py |
| Step 2 | 1 | [SEQ] — Multi-turn context in handler.js |
| Step 3 | 1 | [SEQ] — Trivial turn gate in handler.js |
| Step 4 | 1 | [SEQ] — Re-run benchmark + judge + compare Round 2 → 3 |

**Total: 4 agent dispatches across 4 steps (sequential — Steps 1-3 modify code, Step 4 benchmarks all changes together).**

---

#### Step 1 — Dynamic Topic Expansion + Few-Shot `[SEQ]` — 1 agent

> **Launch condition:** Round 2 complete.
> **File ownership:** Agent modifies `smart_extractor.py` (`_expand_topic_queries()`).

- [ ] Add `FEW_SHOT_EXAMPLES` constant with 5 domain-specific expansion examples
- [ ] Add LLM fallback in `_expand_topic_queries()` — if no static map match, call GPT-4.1-mini with few-shot prompt
- [ ] Cap expansions at 8 unique queries via `dict.fromkeys()`
- [ ] **Verify:** `python3 -c "from smart_extractor import _expand_topic_queries; r=_expand_topic_queries('tailscale'); print(len(r), 'queries')"` — returns > 1 query

---

#### Step 2 — Multi-Turn Retrieval Context `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete.
> **File ownership:** Agent modifies `handler.js` (message extraction logic).

- [ ] Change hook to pass last 3 messages (any role) instead of only last user message
- [ ] Join messages with ` | ` separator, truncate to 300 chars
- [ ] Preserve last user message as primary query for recall
- [ ] **Verify:** `node -e "const h=require('./handler.js'); console.log('handler loads')"` — no syntax errors

---

#### Step 3 — Trivial Turn Gate `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete.
> **File ownership:** Agent modifies `handler.js` (early return before recall).

- [ ] Add `TRIVIAL_PATTERNS` regex: `ok|okay|sure|thanks|thank you|got it|yes|no|yep|nope|cool|nice|hello|hi|hey`
- [ ] Gate: if `query.length < 25 && TRIVIAL_PATTERNS.test(query.trim())` → return `{}` (no context injection)
- [ ] Place gate before any recall calls
- [ ] **Verify:** `node -e "const p=/^(ok|okay|sure|thanks|thank you|got it|yes|no|yep|nope|cool|nice|hello|hi|hey)\\b/i; console.log(p.test('ok'));"` — returns true

---

#### Step 4 — Re-run Benchmark + Judge + Compare `[SEQ]` — 1 agent

> **Launch condition:** Steps 1-3 complete.
> **File ownership:** Agent writes `quality/data/round3-results.json` and `quality/data/round3-scores.json`.

- [ ] Run: `python3 quality/recall/run_benchmark.py --benchmark quality/data/recall_benchmark.json --db ~/.agent-memory/memory.db --output quality/data/round3-results.json`
- [ ] Run: `python3 quality/recall/judge_recall.py --input quality/data/round3-results.json --dimensions relevance,noise --model gpt-4.1-mini --output quality/data/round3-scores.json`
- [ ] Run: `python3 quality/recall/regression_gate.py --before quality/data/round2-scores.json --after quality/data/round3-scores.json`
- [ ] Document deltas in this progress.md
- [ ] **Verify:** Regression gate passes

#### Success Criteria (Round 3)

1. `_expand_topic_queries()` has LLM fallback with few-shot examples
2. `handler.js` passes last 3 messages for multi-turn context
3. `handler.js` has trivial turn gate that skips recall for ack messages
4. `quality/data/round3-scores.json` has 40 judge scores
5. Before/after comparison documented
6. Topic expansion covers 100% of queries (no "no static match" failures)

---

### Round 4 — Embed/Scoring Quality

**Plan:** `plans/memory-recall-optimizer1.md`
**Goal:** Improve the index side — contextual metadata prefix on embeddings, access_count scoring boost, verify Azure text_weights behavior. Requires Azure re-index at deploy time.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Contextual metadata prefix in memory_bridge.py |
| Step 2 | 1 | [SEQ] — access_count logarithmic boost in scoring profile |
| Step 3 | 1 | [SEQ] — Verify Azure text_weights behavior |
| Step 4 | 1 | [SEQ] — Re-run benchmark + judge + compare Round 3 → 4 |

**Total: 4 agent dispatches across 4 steps (sequential).**

---

#### Step 1 — Contextual Metadata Prefix `[SEQ]` — 1 agent

> **Launch condition:** Round 3 complete.
> **File ownership:** Agent modifies `memory_bridge.py` (document preparation for Azure sync).

- [ ] Add `prepare_embed_content(fact)` function — prepends `[Project: X | Tags: Y | Date: Z]` before fact content
- [ ] Use prefix only for embedding input — display content stays unchanged
- [ ] Call `prepare_embed_content()` in sync pipeline before embedding generation
- [ ] **Verify:** `python3 -c "from memory_bridge import prepare_embed_content; r=prepare_embed_content({'content':'test','project':'oclaw','tags':'type:fact'}); print(r)"` — shows prefixed content

---

#### Step 2 — access_count Scoring Boost `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete.
> **File ownership:** Agent modifies `memory_bridge.py` (`ensure_memory_index()` scoring profile).

- [ ] Add `MagnitudeScoringFunction` for `access_count` field — boost=1.3, logarithmic interpolation, range 0-20
- [ ] Add to existing scoring profile functions list
- [ ] **Verify:** `python3 -c "from memory_bridge import ensure_memory_index; print('scoring profile loads')"` — no import error

---

#### Step 3 — Verify Azure text_weights `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete.
> **File ownership:** No file changes — diagnostic only. Document findings in this progress.md.

- [ ] Run: `az search service show --name oclaw-search --resource-group oclaw-rg --query "semanticSearch" -o tsv`
- [ ] Determine if `text_weights` in scoring profiles survive semantic reranking
- [ ] If dead code: remove `text_weights` from scoring profile definition in `memory_bridge.py`
- [ ] Document decision: text_weights kept or removed
- [ ] **Verify:** Decision documented in Key Learnings table

---

#### Step 4 — Re-run Benchmark + Judge + Compare `[SEQ]` — 1 agent

> **Launch condition:** Steps 1-3 complete.
> **File ownership:** Agent writes `quality/data/round4-results.json` and `quality/data/round4-scores.json`.

- [ ] Run: `python3 quality/recall/run_benchmark.py --benchmark quality/data/recall_benchmark.json --db ~/.agent-memory/memory.db --output quality/data/round4-results.json`
- [ ] Run: `python3 quality/recall/judge_recall.py --input quality/data/round4-results.json --dimensions relevance,noise --model gpt-4.1-mini --output quality/data/round4-scores.json`
- [ ] Run: `python3 quality/recall/regression_gate.py --before quality/data/round3-scores.json --after quality/data/round4-scores.json`
- [ ] Document deltas in this progress.md
- [ ] **Verify:** Regression gate passes

#### Stop Gate After Round 4

```
IF weighted_score >= 3.5 AND precision@5 >= 0.60:
    → Skip to Round 6 (deploy)
ELSE:
    → Continue to Round 5 (expand benchmark for deeper diagnosis)
```

- [ ] Evaluate stop gate conditions
- [ ] Document decision: Round 5 or skip to Round 6

#### Success Criteria (Round 4)

1. `prepare_embed_content()` exists in `memory_bridge.py`
2. `access_count` magnitude scoring function added to scoring profile
3. Azure `text_weights` behavior documented (kept or removed)
4. `quality/data/round4-scores.json` has 40 judge scores
5. Before/after comparison documented
6. Stop gate evaluated — decision documented

---

### Round 5 — Full Benchmark (CONDITIONAL)

> **Only run if:** Stop gate after Round 4 NOT met (`weighted_score < 3.5` OR `precision@5 < 0.60`).
> **Skip if:** Targets met after Round 4.

**Plan:** `plans/memory-recall-optimizer1.md`
**Goal:** Expand to 80 queries + all 6 judge dimensions for comprehensive diagnostic. Identify which query categories and dimensions need further improvement.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — Expand benchmark to 80 queries across 6 categories |
| Step 2 | 1 | [SEQ] — Run recall + judge on all 6 dimensions (GPT-4.1-mini, 480 calls) |
| Step 3 | 1 | [SEQ] — Final validation with Claude Sonnet (cross-family, 480 calls) |
| Step 4 | 1 | [SEQ] — Diagnostic report by category + dimension |

**Total: 4 agent dispatches across 4 steps (sequential).**

---

#### Step 1 — Expand to 80 Queries `[SEQ]` — 1 agent

> **Launch condition:** Stop gate NOT met after Round 4.
> **File ownership:** Agent creates `quality/data/recall_benchmark_full.json`.

- [ ] Generate 16 verbatim fact recall queries
- [ ] Generate 16 temporal ordering queries
- [ ] Generate 12 knowledge update queries (superseded facts)
- [ ] Generate 12 multi-hop synthesis queries (combining 2+ memories)
- [ ] Generate 12 hard negative queries (similar topic, wrong answer)
- [ ] Generate 12 abstention queries (no relevant memory exists)
- [ ] Save to `quality/data/recall_benchmark_full.json`
- [ ] **Verify:** `python3 -c "import json; d=json.load(open('quality/data/recall_benchmark_full.json')); print(f'{len(d)} queries'); assert len(d)==80"` — exactly 80

---

#### Step 2 — Judge on All 6 Dimensions (GPT-4.1-mini) `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete.
> **File ownership:** Agent writes `quality/data/round5-results.json` and `quality/data/round5-scores.json`.

- [ ] Run benchmark with 80 queries
- [ ] Judge on all 6 dimensions: relevance, noise, specificity, freshness, actionability, completeness — 480 calls
- [ ] Run: `python3 quality/recall/judge_recall.py --input quality/data/round5-results.json --dimensions relevance,noise,specificity,freshness,actionability,completeness --model gpt-4.1-mini --output quality/data/round5-scores.json`
- [ ] **Verify:** `python3 -c "import json; d=json.load(open('quality/data/round5-scores.json')); print(f'{len(d[\"scores\"])} judge scores')"` — 480 scores

---

#### Step 3 — Final Validation with Claude Sonnet `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete.
> **File ownership:** Agent writes `quality/data/round5-scores-sonnet.json`.

- [ ] Re-judge all 80 queries x 6 dimensions with Claude Sonnet 4.6 — unbiased cross-family validation
- [ ] Run: `python3 quality/recall/judge_recall.py --input quality/data/round5-results.json --dimensions relevance,noise,specificity,freshness,actionability,completeness --model claude-sonnet-4-6 --output quality/data/round5-scores-sonnet.json`
- [ ] **Verify:** `test -f quality/data/round5-scores-sonnet.json && echo "sonnet scores exist"`

---

#### Step 4 — Diagnostic Report `[SEQ]` — 1 agent

> **Launch condition:** Step 3 complete.
> **File ownership:** Agent documents results in this progress.md.

- [ ] Compute overall weighted score
- [ ] Compute per-category scores (verbatim, temporal, knowledge update, multi-hop, hard negatives, abstention)
- [ ] Compute per-dimension scores (relevance, noise, specificity, freshness, actionability, completeness)
- [ ] Compare GPT-4.1-mini vs Claude Sonnet scores (inter-judge agreement)
- [ ] Document all scores in this progress.md
- [ ] **Verify:** All 6 categories and 6 dimensions have documented scores

#### Success Criteria (Round 5)

1. 80-query benchmark exists with 6 categories
2. 480 GPT-4.1-mini judge scores computed
3. 480 Claude Sonnet judge scores computed (cross-family validation)
4. Per-category + per-dimension diagnostic report documented
5. Inter-judge agreement measured

---

### Round 6 — Deploy to VM

**Plan:** `plans/memory-recall-optimizer1.md`
**Goal:** Ship validated improvements to production (OpenClaw VM). Run Azure benchmark as final check. Restart gateway and smoke test.

#### Max Parallel Agents

| Step | Agents | Description |
|------|--------|-------------|
| Step 1 | 1 | [SEQ] — scp changed files to VM |
| Step 2 | 1 | [SEQ] — Re-index Azure (contextual prefix + scoring profile) |
| Step 3 | 1 | [SEQ] — Run Azure benchmark on VM + compare local vs Azure |
| Step 4 | 1 | [SEQ] — Restart gateway + smoke test |

**Total: 4 agent dispatches across 4 steps (sequential — each depends on prior).**

---

#### Step 1 — Deploy Changed Files `[SEQ]` — 1 agent

> **Launch condition:** Round 4 (or Round 5) complete with targets met.
> **File ownership:** Agent deploys via scp to VM paths.

- [ ] scp `smart_extractor.py` → `oclaw:~/.openclaw/workspace/skills/clawbot-memory/`
- [ ] scp `memory_bridge.py` → `oclaw:~/.openclaw/workspace/skills/clawbot-memory/`
- [ ] scp `handler.js` → `oclaw:~/.openclaw/hooks/clawbot-memory/`
- [ ] scp `quality/` directory → `oclaw:~/.openclaw/workspace/skills/clawbot-memory/quality/`
- [ ] **Verify:** `ssh oclaw "ls -la ~/.openclaw/workspace/skills/clawbot-memory/smart_extractor.py ~/.openclaw/workspace/skills/clawbot-memory/memory_bridge.py ~/.openclaw/hooks/clawbot-memory/handler.js"` — all 3 files exist with recent timestamps

---

#### Step 2 — Re-index Azure `[SEQ]` — 1 agent

> **Launch condition:** Step 1 complete (files deployed).
> **File ownership:** No local file changes — runs on VM.

- [ ] Run: `ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory && source .venv/bin/activate && python3 memory_bridge.py sync --full"`
- [ ] Confirm all memories re-embedded with contextual prefix
- [ ] Confirm scoring profile updated with access_count boost
- [ ] **Verify:** `ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory && source .venv/bin/activate && python3 memory_bridge.py sync --status"` — shows sync complete

---

#### Step 3 — Azure Benchmark + Compare `[SEQ]` — 1 agent

> **Launch condition:** Step 2 complete (Azure re-indexed).
> **File ownership:** Agent creates `quality/recall/compare_backends.py` and `quality/data/round6-azure-results.json`.

- [ ] Run Azure benchmark on VM: `ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory && source .venv/bin/activate && python3 quality/recall/run_benchmark.py --backend azure --benchmark quality/data/recall_benchmark.json --output /tmp/vm-azure-results.json"`
- [ ] Copy results: `scp oclaw:/tmp/vm-azure-results.json quality/data/round6-azure-results.json`
- [ ] Create `quality/recall/compare_backends.py` — compares local vs Azure results
- [ ] Run: `python3 quality/recall/compare_backends.py --local quality/data/round4-results.json --azure quality/data/round6-azure-results.json`
- [ ] Expected: Azure scores higher (hybrid search + semantic reranking > keyword-only)
- [ ] **Verify:** Comparison report shows Azure >= local on weighted score

---

#### Step 4 — Restart Gateway + Smoke Test `[SEQ]` — 1 agent

> **Launch condition:** Step 3 complete (Azure benchmark validated).
> **File ownership:** No file changes — operational verification.

- [ ] Run: `ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"`
- [ ] Wait for gateway to come back up
- [ ] Send a test message through ClawBot and verify `<clawbot_context>` appears with relevant memories
- [ ] Confirm trivial turn gate works — "ok" should not trigger recall
- [ ] **Verify:** `ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"` — shows active (running)

#### Success Criteria (Round 6)

1. All 3 changed files deployed to VM (smart_extractor.py, memory_bridge.py, handler.js)
2. Azure re-indexed with contextual prefix and updated scoring profile
3. Azure benchmark scores >= local benchmark scores
4. Gateway restarted and healthy
5. Smoke test confirms `<clawbot_context>` injection working
6. Trivial turn gate confirmed working (no recall for "ok", "thanks")
