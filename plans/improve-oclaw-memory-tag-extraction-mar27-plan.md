# Improve OpenClaw Memory Tag Extraction — Pre-Analysis & Phase 0

**Status:** Not started
**Date:** 2026-03-27
**Depends on:** VM running, Tailscale connected, SSH tunnel up
**References:**
- `plans/mem-optimize-v5.md` (master optimization plan)
- `plans/phase00-tag-definition-injection.md` (Phase 0 spec)
- `plans/mem-best-practice.md` (research)
- Source: `/Users/dez/Projects/oclaw_brain/update1/smart_extractor.py`
- TAG_REGISTRY: `/Users/dez/Projects/oclaw_brain/update1/TAG_REGISTRY.md`
- **Next:** `plans/oclaw-memory-improvement-skill-plan.md` (package everything into a reusable skill — build after this plan completes)

---

## Goal

Before implementing Phase 0 (tag definition injection), verify the problem exists with real data, establish a measured baseline, and standardize existing tag formats. Then implement Phase 0, validate improvement, and add a re-tagging phase for existing memories.

**User goals (confirmed):**
- (c) Both — confirm tags are low-quality AND establish a measured baseline
- (a) Standardize existing tag formats first (normalization)
- (b) Re-tag existing memories through improved prompt — as a new phase, after everything works

---

## Findings (Steps 3-4, 2026-03-27)

Steps 3 and 4 revealed critical issues that change the priority order:

### Quantitative (Step 3 — tag distribution)
- 112 active memories, 594 tag usages, 70 unique tags
- Anchor coverage: 96.4% (PASS — target was 80%)
- Tag diversity: PASS (no single tag >25%)
- **importance is flat** — 100% of memories have importance=5
- **access_count is all zeros** — counter never incremented
- **type:context overuse** — 20.5% of type tags
- **domain:infrastructure dominates** — 70.4% of domain tags
- 83% of memories from a single extraction session (2026-02-23)
- `decided:2026-02-23` over-applied to 76 memories (including non-decisions)
- 40 free-form tags outside registry (75 usages)

### Qualitative (Step 4 — Claude-as-judge)
- **Weighted average score: 2.52/5.0**
- 56.3% scored "needs improvement" (2.0-2.9)
- Only 10.7% scored "excellent" (4.0-5.0)
- **#1 problem: ~40 near-duplicate Tailscale watchdog memories** from bulk extraction
- Manually-added memories (mem_95-109) scored 4.0-4.7 — system works well when intentional
- 6 memories have conflicting dual-confidence tags
- 13 missed facts from 2 session transcripts
- `type:fact` is missing from TAG_REGISTRY, forcing `type:context` overuse

### A/B Test Results (Step 8 — 2026-03-28)

Layer-by-layer extraction tested on 3 stratified sessions (18 GPT-5.2 calls per layer, 6 layers total).

| Run | Layer | Weighted Avg | Delta | Consistency |
|-----|-------|-------------|-------|-------------|
| R0 | Baseline | 0.858 | — | — |
| R1 | +Definitions+counts | 0.902 | +5.1% | **3/3** |
| **R2** | **+Few-shot+reasoning** | **0.968** | **+12.8%** | 2/3 |
| R3 | +Strict JSON schema | 0.940 | +9.6% | 2/3 |
| R4 | +Closed vocab | 0.932 | +8.6% | 2/3 |
| R5 | +Keywords | 0.911 | +6.2% | 2/3 |

**Key findings:**
- R2 (+Few-shot) is the clear winner — perfect tag accuracy (3.00/3.00)
- R1 (+Definitions) is the most reliable — only layer with 3/3 consistency
- **More layers = worse** — full stack (R5=0.911) scored lower than R2 alone (0.968)
- Atomicity degrades with richer prompts (0.94 → 0.57)
- Keywords (Layer 5) actually hurt (-2.9% from R4 to R5)

**Decision: Use Layers 1+2 only.** Drop Layers 3-5. Add atomicity instruction. Extract keywords as post-processing, not in prompt.

### Adjusted priority order (data-driven)

| Priority | Action | Why |
|----------|--------|-----|
| **1** | **Dedup cleanup** — delete ~35 duplicate memories | Removes 31% of all memories, biggest quality drag |
| **2** | **Fix tag errors** — remove wrong `decided:` tags, fix dual-confidence | Data integrity |
| **3** | **Registry update** — add `type:fact`, promote free-form tags | Enables better tag specificity |
| **4** | **Tag normalization** — standardize formats | Clean foundation |
| **5** | **Recency boost + access tracking** — scoring profile, access_count | Lifecycle infrastructure |
| **6** | **Pin + permanent tags** — user control | Feature addition |
| **7** | **Phase 0** — tag definition injection | Extraction prompt improvement |

Original plan had Phase 0 at priority #1. Data shows dedup and registry fixes have higher ROI.

---

## Steps

### Step 1: Boot VM + Tailscale

**Actions:**
1. Open Tailscale app on Mac (menu bar) — enable VPN in System Settings
2. Run `tailscale up` from CLI (GUI toggle alone isn't enough)
3. Start VM if needed: `az vm start --name oclaw2026linux --resource-group RG_OCLAW2026`
4. Start SSH tunnel: `./manage-oclaw/create-manage-tunnel-oclaw.py start`

**Verify:**
```bash
ssh oclaw "hostname && uptime"
```

---

### Step 2: Export data to local files

Pull 3 most recent session JSONL files + all current memories to local for offline analysis.

**Actions:**
```bash
# Create local analysis directory
mkdir -p /Users/dez/Projects/openclaw_vm/plans/tag-analysis-mar27

# Find 3 most recent session JSONL files
ssh oclaw "ls -t ~/.openclaw/agents/main/sessions/*.jsonl | head -3"

# Copy them locally (replace SESSION_IDs from above)
scp oclaw:~/.openclaw/agents/main/sessions/SESSION1.jsonl plans/tag-analysis-mar27/
scp oclaw:~/.openclaw/agents/main/sessions/SESSION2.jsonl plans/tag-analysis-mar27/
scp oclaw:~/.openclaw/agents/main/sessions/SESSION3.jsonl plans/tag-analysis-mar27/

# Export all active memories as JSON
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \
  \"SELECT json_object('id', id, 'content', content, 'tags', tags, 'project', project, \
  'confidence', confidence, 'importance', importance, 'created_at', created_at, \
  'updated_at', updated_at) FROM memories WHERE active=1\"" \
  > plans/tag-analysis-mar27/all-memories.jsonl

# Export tag distribution
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \
  \"SELECT tags, COUNT(*) as c FROM memories WHERE active=1 GROUP BY tags ORDER BY c DESC\"" \
  > plans/tag-analysis-mar27/tag-distribution.txt

# Export total count
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \
  \"SELECT COUNT(*) FROM memories WHERE active=1\"" \
  > plans/tag-analysis-mar27/memory-count.txt

# Pull ClawBot persona files (needed for Step 4 ClawBot utility scoring)
scp oclaw:~/.openclaw/SOUL.md plans/tag-analysis-mar27/
scp oclaw:~/.openclaw/USER.md plans/tag-analysis-mar27/
```

**Verify:** All 7 files exist and are non-empty in `plans/tag-analysis-mar27/`.

**IMPORTANT:** Add `plans/tag-analysis-mar27/` to `.gitignore` — session JSONL files contain conversation data.

---

### Step 3: Tag distribution analysis

Analyze `tag-distribution.txt` and `all-memories.jsonl` to answer:

| Question | How to measure |
|----------|---------------|
| What % of memories use `type:context` or `type:insight`? | Count from tag-distribution.txt |
| What % have BOTH `type:` AND `domain:` anchor tags? | Parse tags field in all-memories.jsonl |
| What's the top-10 most used tags? | Rank from tag-distribution.txt |
| Are there near-duplicate tag names? | Word overlap analysis (e.g., `type:tech_stack` vs `type:techstack`) |
| How many free-form (non-registry) tags exist? | Compare tags against TAG_REGISTRY.md |
| What's the tag-per-memory average? | Parse tags field, count commas+1 |

**Output:** Write findings to `plans/tag-analysis-mar27/step3-tag-distribution-report.md`

**Success criteria baseline (from v5 plan):**
- Tag anchor coverage target: >= 80% have both `type:` and `domain:`
- Tag diversity target: No single tag > 25% of total

---

### Step 4: Claude-as-judge — full memory audit (all ~100 memories)

Claude Sonnet scores ALL active memories (not a sample). This gives an independent judge (different model family than GPT-5.2 which extracted them) and avoids sampling bias.

**Note:** An existing `_score_extraction_quality()` function in `smart_extractor.py` scores MISSED/NOISE/QUALITY on a 1-10 scale using GPT-5.2. We skip it here — same model judging its own work introduces bias. Analyze that function separately as a follow-up to understand what it measures and whether to incorporate it later.

#### Approach: Claude-as-judge (option C — tags + facts + missed facts)

For each memory, Claude evaluates the tags AND the fact itself. Then, using the 3 source session JSONL files from Step 2, Claude also flags facts that *should* have been extracted but weren't.

#### Context files to pull from VM first

```bash
# ClawBot's persona — needed for "would ClawBot find this useful?" dimension
scp oclaw:~/.openclaw/SOUL.md plans/tag-analysis-mar27/
scp oclaw:~/.openclaw/USER.md plans/tag-analysis-mar27/
```

#### Rubric (6 dimensions, 1-5 scale)

| Dimension | 1 (Bad) | 3 (OK) | 5 (Great) | Weight |
|-----------|---------|--------|-----------|--------|
| **Tag accuracy** | Tags don't match content at all | Partially correct, 1-2 wrong tags | Every tag correctly describes this content | 20% |
| **Tag specificity** | Vague default (`type:context` when `type:decision` fits) | Reasonable but a tighter tag exists | Most specific applicable tag from registry chosen | 20% |
| **Anchor completeness** | Missing both `type:` and `domain:` anchors | Has one anchor tag | Has both `type:` and `domain:` anchors | 15% |
| **Fact accuracy** | Fact is wrong, hallucinated, or too vague to be useful | Mostly correct but imprecise | Verifiable, specific, correct fact | 20% |
| **Atomicity** | Multiple unrelated facts bundled into one memory | Slight bundling (2 related facts) | One clean discrete fact | 10% |
| **ClawBot utility** | ClawBot would never use this in conversation | Marginally useful in narrow scenarios | Would clearly improve a future ClawBot conversation with user | 15% |

**ClawBot utility dimension** uses SOUL.md (persona, tone, capabilities) and USER.md (user preferences, context) to judge: "If ClawBot recalled this memory while talking to the user, would it help ClawBot give a better response?"

#### Process

1. Load all ~100 memories from `all-memories.jsonl`
2. Load SOUL.md + USER.md for ClawBot utility scoring
3. Load TAG_REGISTRY.md for tag specificity evaluation
4. For each memory: score all 6 dimensions (1-5), compute weighted average, note issues
5. Aggregate: per-dimension averages, distribution histograms, worst-scoring memories
6. Load 3 session JSONL files from Step 2
7. For each session: read the transcript, identify facts that SHOULD have been extracted but weren't (missed signals)
8. Categorize missed facts: decisions, config changes, error patterns, costs, architecture

#### Output

Write to `plans/tag-analysis-mar27/step4-claude-judge-report.md`:

```
## Executive Summary
- Total memories scored: N
- Weighted average score: X.X/5
- Per-dimension averages: [accuracy, specificity, anchors, fact_accuracy, atomicity, clawbot_utility]

## Score Distribution
- 4.0-5.0 (excellent): N memories (N%)
- 3.0-3.9 (acceptable): N memories (N%)
- 2.0-2.9 (needs improvement): N memories (N%)
- 1.0-1.9 (poor): N memories (N%)

## Bottom 10 (worst scoring memories)
| ID | Content (truncated) | Tags | Weighted Score | Primary Issue |

## Tag-Specific Findings
- % using type:context or type:insight (suspected over-use)
- % missing domain: anchor
- Tags that don't appear in TAG_REGISTRY.md
- Tag format inconsistencies found

## Missed Facts (from 3 session transcripts)
| Session | Missed Fact | Expected Tags | Why It Matters |

## Recommendations
- Top 3 tag quality issues to fix
- Whether Phase 0 (tag definition injection) is validated by data
- Suggested tag normalization changes
```

#### Why this works

- **Independent judge:** Claude Sonnet ≠ GPT-5.2 — no self-grading bias
- **Full coverage:** All ~100 memories, not a sample — no sampling error
- **Persona-aware:** SOUL.md + USER.md make the "utility" score grounded in how ClawBot actually works
- **Missed-fact analysis:** Reading source sessions catches extraction gaps, not just tag quality
- **Zero cost:** Runs inside this Claude Code session — no API calls to Azure/OpenAI

---

### Step 4a: Dedup cleanup + tag error fixes (NEW — from Step 4 findings)

**Added 2026-03-27 based on Claude-as-judge findings.**

#### 4a-1: Delete duplicate Tailscale watchdog memories

The 2026-02-23 bulk extraction produced ~40 near-identical memories about the Tailscale chromeos-nissa watchdog cron job. Consolidate to 3-4 canonical memories.

**Actions:**
1. Query all memories with `tailscale` or `watchdog` or `chromeos-nissa` in content
2. Group by semantic similarity — identify the canonical version of each fact
3. Keep 3-4 best versions (highest quality from Step 4 scores), soft-delete the rest
4. Re-sync to Azure

```bash
# Find candidates
ssh oclaw "python3 -c \"
import sqlite3, json
conn = sqlite3.connect('/home/desazure/.claude-memory/memory.db')
rows = conn.execute(\\\"SELECT id, substr(content, 1, 100), tags FROM memories WHERE active=1 AND (content LIKE '%tailscale%' OR content LIKE '%watchdog%' OR content LIKE '%chromeos%')\\\").fetchall()
conn.close()
for r in rows: print(json.dumps({'id':r[0],'content':r[1],'tags':r[2]}))
\""
```

**Verify:** Memory count drops from ~112 to ~75-80.

#### 4a-2: Fix decided: tag misapplication

Remove `decided:2026-02-23` from ~43 memories that are NOT `type:decision` or `type:pivot`.

```bash
# Find non-decisions with decided: tag
ssh oclaw "python3 -c \"
import sqlite3
conn = sqlite3.connect('/home/desazure/.claude-memory/memory.db')
rows = conn.execute(\\\"SELECT id, tags FROM memories WHERE active=1 AND tags LIKE '%decided:%' AND tags NOT LIKE '%type:decision%' AND tags NOT LIKE '%type:pivot%'\\\").fetchall()
conn.close()
for mem_id, tags in rows:
    # Remove decided:YYYY-MM-DD from tags
    new_tags = ', '.join(t.strip() for t in tags.split(',') if not t.strip().startswith('decided:'))
    print(f'{mem_id}|{new_tags}')
\""
```

Apply the tag updates, then sync.

#### 4a-3: Fix dual-confidence-tag bug

6 memories have both `confidence:medium` and `confidence:low`. Keep only one (the lower one, conservative).

#### 4a-4: Add `type:fact` to TAG_REGISTRY.md

`type:fact` is used in 15 memories but is not in the official registry. This forces the extractor to overuse `type:context` as a fallback. Add it:

```markdown
| `type:fact` | A verifiable, objective observation or measurement | "VM has 4 vCPU / 16 GiB RAM" |
```

Also promote other high-usage free-form tags:
- `type:research` (if used 5+ times)
- `domain:ops` (if used 5+ times)
- `domain:career` (if used 5+ times)

**Verify:** Re-run tag distribution — no more free-form tags with 5+ uses.

---

### Step 5: Re-extract 7 sessions with current prompt (--dry-run)

Run the existing `smart_extractor.py` against the 3 session files to see what the current prompt produces *today* (may differ from when they were originally extracted if sessions were extracted weeks ago).

```bash
# On VM — dry-run extracts facts but does NOT store them
ssh oclaw "source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && \
  cd ~/.openclaw/workspace/skills/clawbot-memory && \
  python3 smart_extractor.py extract --session SESSION1_ID --dry-run" \
  > plans/tag-analysis-mar27/session1-current-extraction.json

# Repeat for SESSION2, SESSION3
```

**Output:** 3 JSON files with extracted facts + tags from current prompt.

**Analyze:**
- Compare tags from dry-run vs tags stored in SQLite (are they the same?)
- Count tag types used across all 3 extractions
- Flag any `type:context` or `type:insight` that should be something more specific

---

### Step 5a: Tag format normalization (standardize existing tags)

Based on findings from Steps 3-5, build a normalization map for inconsistent tag formats.

**Actions:**
1. Identify all format inconsistencies (from Step 3 analysis):
   - Casing issues: `type:Tech_Stack` vs `type:tech_stack`
   - Separator issues: `type:techstack` vs `type:tech_stack`
   - Prefix issues: bare `decision` vs `type:decision`
   - Duplicate semantics: same meaning, different spelling
2. Build normalization map (old_tag -> new_tag)
3. Apply normalization to SQLite:
   ```bash
   ssh oclaw "sqlite3 ~/.claude-memory/memory.db \
     \"UPDATE memories SET tags = REPLACE(tags, 'old_tag', 'new_tag') WHERE tags LIKE '%old_tag%'\""
   ```
4. Re-sync to Azure: `ssh oclaw "... memory_bridge.py sync --full"`

**Output:** Write normalization map + changes applied to `plans/tag-analysis-mar27/step5a-normalization-log.md`

**Verify:** Re-run tag distribution query — no more inconsistencies.

---

### Step 5b: Recency boost, access tracking, lifecycle & decay

Four changes to make memories time-aware: scoring profile, access counting, permanent tag, and auto-deletion of stale unused memories.

#### 5b-1: Azure scoring profile (recency boost)

Configure Azure AI Search to weight newer memories higher at search time. No tag changes needed — uses existing `updated_at` and `importance` fields.

**Actions:**

1. **Create staging index** to test without breaking production:
   ```bash
   # Clone index schema to clawbot-memory-store-staging
   # Run memory_bridge.py sync --full against staging
   ```

2. **Add scoring profile** to index definition in `memory_bridge.py`:
   ```python
   ScoringProfile(
       name="memory-relevance",
       text_weights=TextWeights(weights={"content": 1.5, "tags": 1.2}),
       functions=[
           ScoringFunction(
               field_name="importance",
               boost=2.0,
               interpolation="linear",
               magnitude=MagnitudeFunction(
                   boosting_range_start=1,
                   boosting_range_end=10,
               ),
           ),
           ScoringFunction(
               field_name="updated_at",
               boost=2.0,
               interpolation="linear",
               freshness=FreshnessFunction(boosting_duration="P80D"),
           ),
       ],
   )
   ```

3. **Set `scoring_profile="memory-relevance"`** in the search call.

**Parameters chosen:**
- **80-day freshness window** with **2.0x boost** — long enough that last month's architecture decisions still rank, short enough that truly old memories fade
- **importance 2.0x boost** — high-importance memories always rank well regardless of age
- **content 1.5x, tags 1.2x** text weights — content matters most, tags provide secondary signal

**Test on staging:** Run recall benchmark before/after. Promote to production if MRR improves.

**Verify:** `memory_bridge.py sync --full` after deploying to production.

#### 5b-2: Increment access_count on recall

The `access_count` field exists in both SQLite and Azure but is never incremented. Fix this — it's a one-line change that gives us free usage data.

**File:** `smart_extractor.py` — in the `recall` function, after returning results:

```python
# After recall returns memory IDs, increment access_count
for mem_id in recalled_ids:
    conn.execute("UPDATE memories SET access_count = access_count + 1 WHERE id = ?", (mem_id,))
conn.commit()
```

Also update the Azure document on next sync (access_count field is already in the index schema).

**Verify:**
```bash
# Before: check a memory's access_count
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \"SELECT id, access_count FROM memories WHERE active=1 LIMIT 5\""

# Trigger a recall, then check again — count should increment
ssh oclaw "... smart_extractor.py recall 'some query' -k 3"
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \"SELECT id, access_count FROM memories WHERE active=1 ORDER BY access_count DESC LIMIT 5\""
```

#### 5b-3: permanent:true tag (never decay)

Some facts are permanent infrastructure — "VM is in East US 2", "SSH key is oclaw-key-v4.pem". These should never decay or be deleted regardless of age or access count.

**Add to TAG_REGISTRY.md:**
```markdown
### `permanent:` — Exempt from all decay and auto-deletion

| Tag | Definition |
|-----|-----------|
| `permanent:true` | This memory is permanent infrastructure/reference. Never decay, never auto-delete. Subject to manual quarterly review only. |

Rules:
- Can be applied by user ("make this permanent") or by extraction LLM for clearly permanent facts
- Exempt from 90-day stale deletion (Step 5b-4)
- Exempt from quarterly staleness sweep
- User should manually review permanent memories quarterly to confirm they're still accurate
```

**Interaction with pin: tags:**
- `pin:critical` / `pin:important` / `pin:reference` → also exempt from decay (Step 5c)
- `permanent:true` → exempt from decay even WITHOUT a pin tag
- A memory can have both (`pin:critical, permanent:true`) but `permanent:true` alone is sufficient for decay exemption

#### 5b-4: Auto-delete stale unused memories (90-day rule)

Memories older than 90 days with 0 accesses are deleted automatically. This keeps the memory store clean and relevant.

**Rule:**
```
IF created_at < (now - 90 days)
AND access_count == 0
AND "permanent:true" NOT IN tags
AND "pin:" NOT IN tags
THEN → soft delete (active = 0)
```

**Implementation:** Add to a monthly cron job (or piggyback on the existing monthly quality report cron from v5 Phase 7).

**File:** New function in `memory_bridge.py` or standalone `memory_lifecycle.py`:

```python
def cleanup_stale_memories():
    """Delete memories >90 days old with 0 accesses, unless pinned or permanent."""
    cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
    conn = sqlite3.connect(DB_PATH)

    # Find candidates
    candidates = conn.execute("""
        SELECT id, content, tags, created_at, access_count
        FROM memories
        WHERE active = 1
          AND created_at < ?
          AND access_count = 0
    """, (cutoff,)).fetchall()

    deleted = []
    for mem_id, content, tags, created_at, access_count in candidates:
        if "permanent:true" in tags or "pin:" in tags:
            continue  # exempt
        conn.execute("UPDATE memories SET active = 0 WHERE id = ?", (mem_id,))
        deleted.append((mem_id, content[:80], tags, created_at))

    conn.commit()
    conn.close()

    # Log deletions
    log_path = os.path.expanduser("~/.openclaw/logs/memory-lifecycle/")
    os.makedirs(log_path, exist_ok=True)
    with open(f"{log_path}/{datetime.utcnow().strftime('%Y-%m-%d')}-cleanup.log", "w") as f:
        f.write(f"Stale memory cleanup: {len(deleted)} deleted, {len(candidates) - len(deleted)} exempt\n")
        for mem_id, content, tags, created_at in deleted:
            f.write(f"  DELETED {mem_id}: {content} (created: {created_at}, tags: {tags})\n")

    return len(deleted)
```

**Cron (monthly, 1st of each month at 22:00 UTC):**
```bash
0 22 1 * * cd ~/.openclaw/workspace/skills/clawbot-memory && \
  .venv/bin/python3 -c "from memory_lifecycle import cleanup_stale_memories; print(f'Deleted: {cleanup_stale_memories()}')" \
  >> ~/.openclaw/logs/memory-lifecycle/$(date -u +\%Y-\%m-\%d).log 2>&1
```

**Safety:** Soft delete only (`active = 0`). Memories are NOT physically removed from SQLite. They can be recovered by setting `active = 1` if needed. The next `memory_bridge.py sync` will remove them from Azure.

**Verify:**
```bash
# Check what would be deleted (dry-run)
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \"SELECT id, substr(content, 1, 60), tags, created_at, access_count FROM memories WHERE active=1 AND created_at < datetime('now', '-90 days') AND access_count = 0\""
```

#### 5b-5: Quarterly manual review of permanent memories

**Process (quarterly, user-initiated):**

1. List all `permanent:true` memories:
   ```bash
   ssh oclaw "sqlite3 ~/.claude-memory/memory.db \"SELECT id, substr(content, 1, 80), tags FROM memories WHERE active=1 AND tags LIKE '%permanent:true%'\""
   ```
2. For each: "Is this still accurate?"
   - Yes → keep
   - No → update content or remove `permanent:true` tag (let it decay naturally)
   - Obsolete → soft delete
3. Log review results to `~/.openclaw/logs/memory-lifecycle/quarterly-review-YYYY-QN.md`

**Reminder:** Add to user's quarterly checklist or prompt when expense/agentic review topics come up near quarter boundaries (Jan 1, Apr 1, Jul 1, Oct 1).

---

### Step 5c: Pin tag system (user-applied priority tags)

Add a `pin:` tag dimension that the user can apply explicitly. Pinned memories never decay and get boosted in recall.

#### Pin levels

| Tag | Importance override | Boost effect | Decay exempt | When to use |
|-----|-------------------|--------------|-------------|-------------|
| `pin:critical` | importance = 10 | Highest priority in recall | Yes | Permanent load-bearing facts (infra, security, credentials paths) |
| `pin:important` | importance = 9 | High priority | Yes | Key decisions, architecture choices you'll reference often |
| `pin:reference` | importance = 8 | Above average | Yes | Stuff you want to find easily later |

#### User trigger flow

When the user says "pin", "PIN", "important", "tag important", "remember this", or similar during a conversation:

```
USER: "The Tailscale exit node must stay on chromeos-nissa. Pin that."

CLAWBOT (or Claude Code): "Got it. Which pin level?
  1. pin:critical — permanent, highest priority (infrastructure, security)
  2. pin:important — high priority, key decisions
  3. pin:reference — easy to find later

Pick 1-3 (default: 2):"

USER: "1"

SYSTEM: Memory stored with tags: [...existing tags..., pin:critical]
        importance overridden to 10
```

If the user just says "pin it" with no level, default to `pin:important` (level 2).

#### Implementation (3 files to modify)

**1. `mem.py` — CLI support:**
```bash
# Add --pin flag
python3 mem.py add "fact" --pin important
python3 mem.py add "fact" --pin critical

# Pin an existing memory by ID
python3 mem.py pin MEM_ID critical
python3 mem.py unpin MEM_ID
```

Changes:
- Add `--pin` argument to `add` subcommand
- Add `pin` / `unpin` subcommands
- When pinning: append `pin:LEVEL` to tags, override importance
- When unpinning: remove `pin:*` from tags, reset importance to original

**2. `smart_extractor.py` — extraction prompt rule:**

Add to the extraction prompt:
```
PIN DETECTION:
If the user explicitly says "pin", "PIN", "tag important", "remember this permanently",
or "don't forget this" — add pin:important to tags. If they say "critical" or
"this is critical", use pin:critical. If they say "reference" or "for reference",
use pin:reference. Only apply pin: tags when the user EXPLICITLY requests it.
Do NOT auto-pin based on content importance — that's what the importance score is for.
```

**3. `memory_bridge.py` — decay exemption:**

In any future staleness/decay sweep:
```python
def should_decay(memory: dict) -> bool:
    if "pin:" in memory.get("tags", ""):
        return False  # user-pinned, never decay
    return True
```

#### Add `pin:` to TAG_REGISTRY.md

```markdown
### `pin:` — User-applied priority (never auto-assigned by LLM)

| Tag | Definition | Importance Override |
|-----|-----------|-------------------|
| `pin:critical` | Permanent load-bearing fact — infrastructure, security, credentials | 10 |
| `pin:important` | Key decision or reference the user wants prioritized | 9 |
| `pin:reference` | User wants easy retrieval for this fact | 8 |

Rules:
- ONLY applied when user explicitly requests it (says "pin", "important", "remember this")
- NEVER auto-assigned by extraction LLM based on content analysis
- Exempt from all decay/staleness logic
- importance field is overridden to the level shown above
```

#### Verify

```bash
# Test CLI
python3 mem.py add "Test pinned memory" --pin critical -t "type:test"
python3 mem.py search "test pinned" # should return with pin:critical tag, importance=10

# Test unpin
python3 mem.py pin MEM_ID reference  # change level
python3 mem.py unpin MEM_ID          # remove pin

# Test decay exemption
# (verify pinned memories are skipped in staleness sweep)
```

**Output:** Updated `mem.py`, `smart_extractor.py` extraction prompt, `memory_bridge.py` decay logic, `TAG_REGISTRY.md`.

---

### Step 6: Compare — are current tags the best the current prompt can do?

Produce a comparison report:

| Metric | Current (stored) | Re-extracted (Step 5) | Delta |
|--------|-----------------|----------------------|-------|
| Avg tags per memory | ? | ? | |
| % with type: anchor | ? | ? | |
| % with domain: anchor | ? | ? | |
| % with both anchors | ? | ? | |
| Top overused tag | ? | ? | |
| Free-form tag count | ? | ? | |

**Decision point:** If the current prompt already produces decent tags, Phase 0 may have lower ROI than expected. If tags are demonstrably vague/generic, Phase 0 is validated.

**Output:** Write to `plans/tag-analysis-mar27/step6-baseline-comparison.md`

---

### Step 7: Implement extraction prompt improvements (5 layers)

**Research validated (2026-03-28).** Findings from 3 research agents informed this revised step. Each layer is applied cumulatively and A/B tested individually to measure per-layer impact.

#### Layer 1: Phase 0 — definitions + usage counts (T-shirt: S, 30 min)

**Spec:** Follow `plans/phase00-tag-definition-injection.md`:
1. `extract_known_tags()` returns `(name, definition)` tuples
2. New `_get_tag_usage_counts()` helper
3. `tag_ref` builder with definitions + counts
4. Fix callers (`update_tag_registry()`, `store_facts()`)
5. Prompt wording: "PREFER these -- only create new if NONE fit"

#### Layer 2: Few-shot examples + reasoning field (T-shirt: M, 1 hour)

**Source:** Extraction prompt research (Sagepub 2025: +22% accuracy with few-shot).

1. Add `reasoning` field to JSON schema **before** `tags` field — GPT-5.2 fills fields in order, so it commits rationale before picking tags
2. Add 2-3 `<example>` blocks targeting specific failure modes from Claude-judge audit:
   - Example 1: `type:fact` (not `type:context`) for an objective observation
   - Example 2: `type:pattern` vs `type:decision` — stops `decided:` misapplication
   - Example 3: `type:error_pattern` with proper severity tag
3. Place examples in system prompt (cached by API after first call — reduces effective cost)

**Cost:** ~+30-50 tokens per extracted fact (~$0.001 per session)

#### Layer 3: strict: true JSON Schema enforcement (T-shirt: S, 45 min)

**Source:** Extraction prompt research (OpenAI structured outputs docs).

1. Add `response_format` with `strict: true` to the GPT-5.2 extraction call
2. Define full JSON schema: `content` → `reasoning` → `tags` → `importance` → `confidence`
3. Requires Azure OpenAI API version `2024-08-01-preview` or later — verify on VM

**Effect:** Eliminates format bugs entirely — no dual-confidence tags, no `tags:geo-search` anti-patterns, no importance-as-string errors.

#### Layer 4: Closed vocabulary for type: (T-shirt: XS, 15 min)

**Source:** Mem0 research (3-5 categories with descriptions recommendation).

Change prompt wording from:
```
"PREFER these -- only create new if NONE fit"
```
To:
```
"Use ONLY these type: values. Do NOT create new type: tags.
domain: tags may be created if no existing domain fits."
```

Lock `type:` to these 10 values (closed set):
`decision, fact, preference, error_pattern, architecture, pattern, context, research, metric, insight`

Keep `domain:` open (new domains are legitimate as projects evolve).

#### Layer 5: Keyword extraction as separate kw: tags (T-shirt: S, 30 min)

**Source:** Mem0 research (categories vs keywords are separate concerns).

Add to extraction prompt:
```
KEYWORDS: Extract 2-5 content keywords (service names, error codes,
tool names, concepts) as kw: tags. These are separate from classification tags.
Example: kw:tailscale, kw:exit-node, kw:cron
```

**Effect:** Better BM25 retrieval. Keywords are content-specific terms, not classification categories. Follow-up: migrate to a separate `keywords` field in Azure index (schema change, not this phase).

**Deploy all layers:**
```bash
scp smart_extractor.py oclaw:~/.openclaw/workspace/skills/clawbot-memory/
```

**Verify:** Unit tests pass locally before deploy.

---

### Step 8: Layer-by-layer A/B test

**Goal:** Measure per-layer impact so future tuning effort goes to the highest-ROI layers.

#### Test sessions (stratified, 3 total)

| Session | Size | Type |
|---------|------|------|
| session-large-2.jsonl | 1.5MB | Long multi-turn, decisions + config changes |
| session-medium-1.jsonl | 454KB | Typical working session |
| session-small-1.jsonl | 96KB | Short focused interaction |

#### Test runs (6 cumulative, 18 total extractions, ~$0.02)

| Run | Prompt variant | Sessions |
|-----|---------------|----------|
| Run 0 | Baseline (current prompt, no changes) | 3 |
| Run 1 | +Layer 1 (definitions + counts) | 3 |
| Run 2 | +Layer 1+2 (+ few-shot + reasoning) | 3 |
| Run 3 | +Layer 1+2+3 (+ strict JSON schema) | 3 |
| Run 4 | +Layer 1+2+3+4 (+ closed vocabulary) | 3 |
| Run 5 | +Layer 1+2+3+4+5 (+ keyword extraction) | 3 |

All runs use `--dry-run` (no storage). Save output to `plans/tag-analysis-mar27/ab-run-N.json`.

#### Scoring — Research-Informed Rubric (2026-03-28)

**Sources:** LLM-as-judge research (Anthropic eval docs, MT-Bench, G-Eval, RULERS 2026, Hamel Husain, arXiv 2504.14716, arXiv 2503.01747)

**Key structural rules:**
1. **6 isolated judge calls per memory** — one prompt per dimension, not bundled (Anthropic: "grade each dimension with an isolated call")
2. **CoT before score** — output `{"critique": "...", "score": N}`, reasoning first prevents post-hoc rationalization
3. **Blind labels** — variants labeled "Alpha/Beta" not "old/new" to prevent confirmation bias
4. **Swap-and-re-judge** for any pairwise comparisons — run both orderings, treat disagreements as ties

**Rubric (mixed scales — research shows LLMs can't reliably use 5-point without anchors):**

| Dimension | Scale | Weight | Anchor: low | Anchor: mid | Anchor: high |
|-----------|-------|--------|-------------|-------------|--------------|
| Fact accuracy | Binary (0/1) | 20% | Fact is wrong, hallucinated, or unverifiable | — | Fact is correct and verifiable against source |
| Atomicity | Binary (0/1) | 10% | Multiple unrelated facts bundled | — | One discrete fact |
| Tag accuracy | 1-3 | 20% | 1: Tags don't match content | 2: Partially correct, 1-2 wrong tags | 3: Every tag correctly describes content |
| Tag specificity | 1-3 | 20% | 1: Vague default (type:context when type:decision fits) | 2: Reasonable but a tighter tag exists | 3: Most specific applicable tag chosen |
| Anchor completeness | 1-3 | 15% | 1: Missing both type: and domain: | 2: Has one anchor | 3: Has both type: and domain: |
| ClawBot utility | 1-3 | 15% | 1: ClawBot would never use this | 2: Marginally useful in narrow scenarios | 3: Would clearly improve a future conversation |

**Statistical approach (N=18 is a screening budget, not a conclusion budget):**
- Report **directional consistency**: "3/3 sessions improved" is the strongest small-N signal
- Use **Bayesian Beta-Binomial** for binary dimensions (fact accuracy, atomicity)
- Report **raw counts** not percentages (CLT confidence intervals invalid below N≈200, per arXiv 2503.01747)
- **Effect size threshold**: mean difference of 0.5+ points on a 1-3 scale is practically significant (Cohen's d ≈ 0.5)
- Treat this as a **screening pass** — identify top-2 layers for potential deeper follow-up (N≥15 sessions)

**Lift chart:**

| Layer added | Fact acc (0/1) | Atomicity (0/1) | Tag acc (1-3) | Tag spec (1-3) | Anchors (1-3) | Utility (1-3) | Weighted avg | Delta |
|-------------|---------------|----------------|--------------|---------------|--------------|--------------|-------------|-------|
| Baseline | ? | ? | ? | ? | ? | ? | ? | — |
| +Definitions | ? | ? | ? | ? | ? | ? | ? | ? |
| +Few-shot | ? | ? | ? | ? | ? | ? | ? | ? |
| +Strict schema | ? | ? | ? | ? | ? | ? | ? | ? |
| +Closed vocab | ? | ? | ? | ? | ? | ? | ? | ? |
| +Keywords | ? | ? | ? | ? | ? | ? | ? | ? |

**Decision rules:**
- Layers with <5% weighted improvement → consider dropping (reduces prompt complexity)
- Layers with >15% weighted improvement → candidates for deeper tuning next quarter
- If 3/3 sessions show improvement for a layer → high confidence it's real
- If split (2/1 or 1/2) → flag as inconclusive, include in final prompt but monitor

**Output:** Write lift chart + analysis to `plans/tag-analysis-mar27/step8-layer-ab-comparison.md`

---

### Step 9: Re-tag existing memories through improved prompt

**Only after Step 8 validates improvement (cumulative score > 3.5/5).**

**Approach:**
1. Export all 68 active memories from SQLite
2. For each memory, send content to GPT-5.2 with the winning prompt variant from Step 8
3. Ask: "Given this memory content, assign the best tags from the registry"
4. Include `reasoning` field so we can audit tag choices
5. Diff old tags vs new tags — produce review list
6. Human reviews the diff (approve/reject per memory)
7. Apply approved tag updates to SQLite
8. Run `memory_bridge.py sync --full` to push to Azure

**Cost estimate:** ~68 memories x GPT-5.2 = ~$0.05
**Risk:** Low — dry-run first, human reviews before applying.

**Output:**
- Tag diff report: `plans/tag-analysis-mar27/step9-retag-diff.md`
- Update `plans/mem-optimize-v5.md` to note re-tagging complete

---

## Deliverables

| Step | Output file |
|------|-------------|
| 2 | `plans/tag-analysis-mar27/*.jsonl`, `tag-distribution.txt`, `memory-count.txt`, `SOUL.md`, `USER.md` |
| 3 | `plans/tag-analysis-mar27/step3-tag-distribution-report.md` |
| 4 | `plans/tag-analysis-mar27/step4-claude-judge-report.md` |
| 5 | `plans/tag-analysis-mar27/session*-current-extraction.json` |
| 5a | `plans/tag-analysis-mar27/step5a-normalization-log.md` |
| 5b | Updated `memory_bridge.py` (scoring profile + decay exemption), `smart_extractor.py` (access_count increment), `memory_lifecycle.py` (90-day cleanup), `TAG_REGISTRY.md` (permanent:true), monthly cleanup cron, quarterly review process |
| 5c | Updated `mem.py` (--pin flag, pin/unpin commands), `smart_extractor.py` (pin detection prompt), `memory_bridge.py` (decay exemption), `TAG_REGISTRY.md` (pin: dimension) |
| 6 | `plans/tag-analysis-mar27/step6-baseline-comparison.md` |
| 8 | `plans/tag-analysis-mar27/step8-ab-comparison.md` |
| 9 | Update to `plans/mem-optimize-v5.md` |

---

## Decision Gates

| After Step | Decision |
|-----------|----------|
| Step 3 | If anchor coverage is already >80% and no single tag >25%, Phase 0 may be lower priority |
| Step 6 | If current prompt produces good tags, consider skipping Phase 0 and going straight to recall tuning (v5 Phase 2-3) |
| Step 8 | If A/B shows <10% improvement, Phase 0 may not be worth the complexity. If >20% improvement, proceed to Step 9 (re-tagging) |

---

## Follow-Up: Analyze existing _score_extraction_quality()

**Separate from this plan — do after Step 4.**

`smart_extractor.py` already has a `_score_extraction_quality()` function (~line 1981-2037) that uses GPT-5.2 to score extractions on MISSED/NOISE/QUALITY (1-10)/RECOMMENDATIONS.

**Questions to answer:**
1. What exactly does it measure vs what our Claude-as-judge rubric measures?
2. Is it run automatically (cron) or only manually?
3. Could we repurpose it as a second judge (different perspective) alongside Claude?
4. Should we swap GPT-5.2 for a cheaper model (GPT-4.1-mini) for routine scoring?
5. Does it overlap with the v5 Phase 4 (extraction quality scoring) plan?

**Action:** Read the function, document its rubric, compare to our Claude judge rubric, and decide whether to integrate, replace, or leave it as-is.
