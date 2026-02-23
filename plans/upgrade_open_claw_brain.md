# Upgrade OpenClaw Brain — Wire Memory into Live Gateway

**Goal:** Wire the oclaw_brain memory skill into the running OpenClaw gateway on `oclaw2026linux` so ClawBot gains persistent cross-session memory with minimal blast radius and easy rollback.

**Approach:** Hybrid injection — `before_agent_start` plugin hook for always-on lightweight recall + SKILL.md for on-demand deep recall. Extraction via cron. Rollback = delete hook + skill dir + remove cron lines.

---

## Critical Findings (from research)

| Finding | Impact |
|---------|--------|
| Session path mismatch: skill expects `~/.openclaw/logs/sessions/`, actual is `~/.openclaw/agents/main/sessions/` | **Must fix** — symlink or patch |
| `~/claude-memory/` does not exist on VM | **Must create** — skill stores DB + state here |
| 1,566 session files (55 MB) on VM | Rich source for initial load |
| Existing memory: `~/.openclaw/memory/main.sqlite` (empty, FTS-only) + daily markdown journals (14 files) | Separate system — leave untouched |
| Azure resources (oclaw-search, oclaw-openai, pitchbook-resource) already provisioned | No new Azure setup needed |
| Gateway has `before_agent_start` plugin hook | **Using this** — deterministic pre-turn memory injection |
| Gateway has SKILL.md discovery (`~/.openclaw/workspace/skills/*/SKILL.md`) | **Using this** — on-demand deep recall |
| `gateway_model_routing_hook.js` exists but is **dormant** (not wired into config) | Prototype code, not relevant |
| Built-in `memory_search`/`memory_get` tools exist but DB is empty (0 chunks, 0 files) | Leave as-is, our system is additive |
| `MEMORY.md` has only 3 entries, `USER.md` and `IDENTITY.md` are empty templates | Our brain skill fills the semantic search gap |
| Skill gating: requires `python3` on PATH + `AZURE_SEARCH_ENDPOINT` env var | Must verify both on VM |
| Only 15 test memories in Azure from Phase I convologs | **Clear and reload** with real sessions |
| Hook system: workspace hooks at `~/.openclaw/hooks/`, managed at `~/.openclaw/hooks/` | Hook deployment path confirmed |
| Plugin `before_agent_start` returns `{ prependContext: "..." }` to inject before prompt | Exact interface confirmed |
| `agent:bootstrap` hook can mutate bootstrap files (MEMORY.md, SOUL.md, etc.) | Available but not using (per-session, not per-turn) |

---

## Architecture: How It Wires In

### ASCII Flow: Injection Decision Tree

```
     Which injection path fires?

     ┌─────────────────────────────────────────────────────────────┐
     │                   EVERY TURN (automatic)                    │
     │                                                             │
     │   before_agent_start hook fires                             │
     │     │                                                       │
     │     ├─ Extract keywords from user message                   │
     │     ├─ Query Azure AI Search (2s timeout)                   │
     │     │   ├─ SUCCESS: top 3-5 facts → prependContext          │
     │     │   └─ TIMEOUT/ERROR: query local SQLite fallback       │
     │     │       ├─ SUCCESS: top 3-5 facts → prependContext      │
     │     │       └─ ERROR: skip gracefully (no memory this turn) │
     │     └─ Return { prependContext: "<clawbot_memory>..." }     │
     │                                                             │
     │   Cost: ~2s latency, ~200 tokens prepended                  │
     └─────────────────────────────────────────────────────────────┘

     ┌─────────────────────────────────────────────────────────────┐
     │              ON-DEMAND (agent chooses via SKILL.md)          │
     │                                                             │
     │   Agent reads SKILL.md → decides deep recall needed         │
     │     │                                                       │
     │     ├─ Runs: python3 smart_extractor.py recall <topic> -k 5 │
     │     ├─ Topic expansion via GPT-5.2                          │
     │     ├─ Full hybrid search (Azure + local)                   │
     │     └─ Returns detailed <clawbot_context> with tags/dates   │
     │                                                             │
     │   Cost: ~5s latency, ~500 tokens, 1 tool call               │
     └─────────────────────────────────────────────────────────────┘
```

### ASCII Flow: Full Turn with Memory (Telegram → Response)

```
    User sends message to ClawBot via Telegram
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  OpenClaw Gateway receives message   │
    │  Routes to agent runtime             │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  BEFORE_AGENT_START HOOK             │  ◄── NEW: memory_recall_hook.js
    │                                      │
    │  1. Parse user message keywords      │
    │  2. Query Azure AI Search (2s max)   │
    │     ├─ vector + BM25 + semantic      │
    │     └─ Fallback: local SQLite        │
    │  3. Format top 3-5 results           │
    │  4. Return:                          │
    │     { prependContext:                │
    │       "<clawbot_memory>             │
    │        [1] VM uses D4s_v3...        │
    │        [2] Decided GPT-5.2...       │
    │       </clawbot_memory>" }          │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Agent runtime builds the turn       │
    │                                      │
    │  System prompt =                     │
    │    prependContext (memory facts)      │  ◄── injected by hook
    │    + SOUL.md, USER.md, MEMORY.md     │
    │    + Skills list (incl. clawbot-mem) │
    │    + Tool policy                     │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  LLM call (GPT-5.2 via Copilot)     │
    │                                      │
    │  Agent sees memory facts at top of   │
    │  context. May also choose to run     │
    │  deep recall via SKILL.md tool:      │
    │                                      │
    │  python3 smart_extractor.py recall   │
    │    "detailed topic" -k 5             │
    │                                      │
    │  (Only if agent decides it needs     │
    │   more context beyond the 3-5 auto-  │
    │   injected facts)                    │
    └──────────┬───────────────────────────┘
               │
               ▼
    Assistant response → Gateway → Telegram
```

### ASCII Flow: Extraction (When facts are captured)

```
                        ┌─────────────────────────────┐
                        │   OpenClaw Gateway (18789)   │
                        │   ClawBot agent sessions     │
                        └──────────┬──────────────────┘
                                   │ appends messages
                                   ▼
                 ~/.openclaw/agents/main/sessions/
                 ├── c12bc59b-....jsonl  (3.7 MB, active)
                 ├── 317f68b6-....jsonl  (1.5 MB)
                 ├── ... (1,566 files, 55 MB total)
                                   │
                    ┌──────────────┘
                    │  CRON: 2x daily (noon + midnight UTC)
                    ▼
        ┌───────────────────────────────┐
        │   smart_extractor.py sweep    │
        │                               │
        │  1. Check .extract_state.json │
        │     (skip already-processed)  │
        │  2. Parse new session JSONL   │
        │  3. Prioritize content:       │
        │     thinking > user > assist  │
        │  4. Chunk if >14K chars       │
        │  5. Send to GPT-5.2 (Azure)   │
        │     "Extract facts + tags"    │
        │  6. 5-Gate Pipeline:          │
        │     ├─ Noise (score <0.3)     │
        │     ├─ Secrets (30+ patterns) │
        │     ├─ Confidence (<0.4)      │
        │     ├─ Dedup (60% overlap)    │
        │     └─ Pivot detection        │
        │  7. Store via mem.py add      │
        └──────────┬────────────────────┘
                   │
                   ▼
        ~/.claude-memory/memory.db     ◄── SOURCE OF TRUTH (SQLite)
                   │
                   │  CRON: daily 2 AM UTC
                   ▼
        ┌──────────────────────────────┐
        │   memory_bridge.py sync      │
        │                              │
        │  1. Read new memories since  │
        │     last cursor              │
        │  2. Generate 3072-dim embeds │
        │     (text-embedding-3-large) │
        │  3. Upload to Azure AI Search│
        │  4. Sync deletions           │
        │  5. Update .sync_state.json  │
        └──────────┬───────────────────┘
                   │
                   ▼
        Azure AI Search: clawbot-memory-store
        (hybrid: vector + BM25 + semantic ranking)
```

### ASCII Flow: Weekly Self-Optimization

```
        CRON: Sunday midnight UTC
                   │
                   ▼
        ┌──────────────────────────────────────┐
        │  weekly_review_agent.py               │
        │                                      │
        │  OBSERVE: Read last 7 days sessions  │
        │     ↓                                │
        │  ANALYZE: GPT-5.2 identifies         │
        │     - Token waste patterns           │
        │     - Error clusters                 │
        │     - Skill efficiency rankings      │
        │     ↓                                │
        │  IMPROVE: Rewrite SKILL.md files     │
        │     - Remove redundant examples      │
        │     - Tighten language               │
        │     - Target 15-30% token savings    │
        │     ↓                                │
        │  VERIFY: Quality checks              │
        │     - No token regression            │
        │     - Backup originals (timestamped) │
        │     ↓                                │
        │  STORE: Upload learnings to Azure    │
        │     clawbot-learning-store index     │
        └──────────────────────────────────────┘
```

---

## Injection Point Analysis

### Why Hybrid (Hook + SKILL.md) is Best

| Criterion | Hook Only | SKILL.md Only | Hybrid (Recommended) |
|-----------|-----------|---------------|----------------------|
| Reliability | Always fires | Agent may skip recall | Always-on + deep on-demand |
| Latency | ~2s (lightweight query) | ~5s (topic expansion + search) | 2s base + 5s optional |
| Token cost | ~200 tokens/turn | ~500 tokens when invoked | 200 base + 500 optional |
| Complexity | Need JS hook file | Python skill only | Both, but simple |
| Blast radius | Hook file + config | Skill dir only | Slightly larger, still easy rollback |
| Agent awareness | Hidden (context just appears) | Explicit (agent reads tool result) | Both paths available |
| Fallback | Azure → SQLite → skip | Azure → SQLite → skip | Same, two layers |

### Injection Points Evaluated (Best → Worst)

| # | Injection Point | Verdict | Reason |
|---|----------------|---------|--------|
| 1 | **`before_agent_start` hook** | **USE** — always-on lightweight recall | Deterministic, pre-prompt, ~2s, hidden from agent |
| 2 | **SKILL.md deep recall** | **USE** — on-demand deep recall | Agent-driven, topic expansion, full search |
| 3 | System context files (MEMORY.md) | **Skip** — static, not dynamic | Can't do per-query retrieval |
| 4 | `agent:bootstrap` hook | **Skip** — per-session only | Fires once at session start, not per-turn |
| 5 | `gateway_model_routing_hook.js` | **Skip** — dormant, not wired | Prototype, not connected to gateway |
| 6 | Modify `memory_search`/`memory_get` | **Skip** — too invasive | Would require forking openclaw source |

---

## Answers to Your Questions

### Q1: Should we clear AI Search memory and start fresh?

**YES.** The current 15 memories are test data extracted from local convologs (laptop Claude Code sessions), not from real ClawBot VM sessions. They'll pollute search results. Clear both indexes and reload from real VM sessions.

### Q2: Should we do an initial load of last 4 session files?

**YES.** The 4 most recent active sessions contain the freshest institutional knowledge:

| Session | Size | Modified | Why Include |
|---------|------|----------|-------------|
| `c12bc59b` | 3.7 MB | Feb 23 | Current active session — richest context |
| `317f68b6` | 1.5 MB | Feb 23 | Recent work |
| `3fedaa0f` | 1.0 MB | Feb 21 | Recent decisions |
| `c20853de` | 770 KB | Feb 22 | Recent operational work |

Total: ~7 MB of sessions → expect 30-60 high-quality memories after 5-gate filtering.

### Q3: Do we need mem CLI in ClawBot?

**YES, but not as a tool ClawBot calls directly.** The `mem.py` CLI is the storage layer that `smart_extractor.py` calls via subprocess to persist facts to SQLite. ClawBot never calls it — ClawBot uses `smart_extractor.py recall` which internally queries via `memory_bridge.py` (hybrid search). The mem CLI is infrastructure, not a user-facing tool.

### Q4: Should we modify `memory_search`/`memory_get` to grab from Azure AI Search?

**NO.** The built-in memory tools are tightly coupled to openclaw's SQLite + FTS5 backend. Modifying them would require forking the openclaw source — high blast radius, breaks on updates. Instead, we inject via the `before_agent_start` hook which runs **before** the built-in memory tools and adds our Azure-backed facts as `prependContext`. The built-in memory system continues to work independently (it searches MEMORY.md + daily journals). Our system is **additive**, not a replacement.

### Q5: Should we inject via the gateway_model_routing_hook.js?

**NO.** That file is dormant prototype code — not wired into `openclaw.json`, not loaded by the gateway. The proper injection point is the `before_agent_start` plugin hook, which is a supported gateway feature with a clean API (`{ prependContext: "..." }`).

---

## My Suggestions & Questions

### Suggestions (All Approved ✓)

1. **Use `before_agent_start` hook for always-on recall** — deploy `memory_recall_hook.js` to `~/.openclaw/hooks/clawbot-memory/`. Every turn: extract keywords → query Azure (2s timeout) → fallback SQLite → prepend top 3-5 facts. Agent sees facts automatically without needing to "decide" to recall. **→ APPROVED**

2. **Keep SKILL.md for deep recall** — when agent needs thorough search with topic expansion (e.g., "tell me everything about the pricing decision"), it runs `smart_extractor.py recall` via the skill. This is the explicit, agent-driven path. **→ APPROVED**

3. **Use symlink for session path** (not code patch): `ln -s ~/.openclaw/agents/main/sessions ~/.openclaw/logs/sessions` — zero code changes, easy to understand, reversible. **→ APPROVED**

4. **Don't touch the existing memory system** (`~/.openclaw/memory/main.sqlite` + daily journals). These are openclaw's built-in memory. Our brain skill is additive — it provides deeper semantic search on top. No conflicts. **→ APPROVED**

5. **Start with extraction + hook injection for 24 hours** before enabling the SKILL.md deep recall. Verify the hook injects good context before giving agent the deep recall tool. **→ APPROVED**

6. **Add a log rotation cron** for the brain skill logs (extract.log, sync.log, review.log) — keep 7 days, same pattern as existing watchdog logs. **→ APPROVED**

7. **Skip `session_telemetry.py` for v1** — it requires wrapping the agentic loop (invasive). The extraction sweep reads session JSONL directly — no telemetry wrapper needed. **→ APPROVED**

8. **Skip `weekly_review_agent.py` for week 1** — let extraction + sync stabilize first, then enable the self-optimization loop. Less blast radius. **→ APPROVED**

### Questions (All Answered)

1. **Hook latency budget** — the `before_agent_start` hook adds ~2s per turn (Azure query). **→ 2s is acceptable**

2. **Memory token budget** — how many facts should the hook inject per turn? **→ 3-5 facts (~200 tokens) confirmed**

3. **Injection path preference** — hook (always-on) vs SKILL.md (on-demand) vs both? **→ Hook (always-on) confirmed as primary path**

---

## Implementation Phases

### Phase 0: Pre-Flight Checks (read-only, no changes)
- [ ] **0.1** Verify tunnel is up
- [ ] **0.2** Verify `az login` is active on VM (for Entra ID auth)
- [ ] **0.3** Verify env vars set on VM: `AZURE_SEARCH_ENDPOINT`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_ENDPOINT`
- [ ] **0.4** Verify `python3` on PATH and version
- [ ] **0.5** Check gateway tailscale mode (config shows `"serve"`, CLAUDE.md says `"off"`)
- [ ] **0.6** Verify Azure indexes exist: `clawbot-memory-store`, `clawbot-learning-store`

### Phase 1: Prepare VM Directory Structure (low risk, reversible)
- [ ] **1.1** Create `~/claude-memory/` directory tree: `cli/`, `logs/`
- [ ] **1.2** Create session path symlink: `~/.openclaw/logs/sessions` → `~/.openclaw/agents/main/sessions`
- [ ] **1.3** Verify symlink resolves correctly

### Phase 2: Deploy Skill + Hook Files (reversible — delete directories to rollback)
- [ ] **2.1** Copy skill files to VM at `~/.openclaw/workspace/skills/clawbot-memory/`
- [ ] **2.2** Copy `cli/mem.py` to `~/claude-memory/cli/mem.py`
- [ ] **2.3** Create `memory_recall_hook.js` — the `before_agent_start` hook
- [ ] **2.4** Deploy hook to `~/.openclaw/hooks/clawbot-memory/` (HOOK.md + handler.js)
- [ ] **2.5** Install Python dependencies in a venv on VM
- [ ] **2.6** Set env vars in `~/.zshrc` if not already present
- [ ] **2.7** Verify skill gating: `python3` + `AZURE_SEARCH_ENDPOINT`

### Phase 3: Clear & Initialize Azure (reversible — indexes can be recreated)
- [ ] **3.1** Clear `clawbot-memory-store` index (delete all documents)
- [ ] **3.2** Clear `clawbot-learning-store` index (delete all documents)
- [ ] **3.3** Verify indexes are empty
- [ ] **3.4** Run `auth_provider.py` health check

### Phase 4: Initial Load — Extract from Last 4 Sessions
- [ ] **4.1** Run extraction on session `c12bc59b` (3.7 MB, most recent)
- [ ] **4.2** Run extraction on session `317f68b6` (1.5 MB)
- [ ] **4.3** Run extraction on session `3fedaa0f` (1.0 MB)
- [ ] **4.4** Run extraction on session `c20853de` (770 KB)
- [ ] **4.5** Verify: `mem.py search "Azure"` returns results
- [ ] **4.6** Verify: `oclaw_cli.py stats` shows memory counts
- [ ] **4.7** Run `memory_bridge.py sync --full` to push to Azure
- [ ] **4.8** Verify: Azure hybrid search returns results

### Phase 5: Enable Cron Jobs (reversible — comment out to disable)
- [ ] **5.1** Add extraction cron: `15 20 * * *` (4:15 PM ET / 20:15 UTC)
- [ ] **5.2** Add sync cron: `0 2 * * *` (2 AM UTC)
- [ ] **5.3** Add log rotation cron (keep 7 days)
- [ ] **5.4** Verify cron jobs listed in `crontab -l`

### Phase 6: Enable Injection — Hook First (reversible — delete hook dir)
- [ ] **6.1** Verify hook is discovered by gateway (check startup logs)
- [ ] **6.2** Test: send ClawBot a message, verify hook fires and injects memory context
- [ ] **6.3** Monitor gateway logs for hook errors
- [ ] **6.4** Verify fallback: if Azure is slow, hook falls back to local SQLite

### Phase 7: Enable SKILL.md Deep Recall (reversible — remove skill dir)
- [ ] **7.1** Verify SKILL.md has recall directive for ClawBot
- [ ] **7.2** Verify gateway discovers the skill: `openclaw skills list | grep memory`
- [ ] **7.3** Test: ask ClawBot "what do you remember about [specific topic]", verify deep recall runs
- [ ] **7.4** Monitor gateway logs for skill execution errors

### Phase 8: 24-Hour Soak & Enable Weekly Review
- [ ] **8.1** After 24h: check extraction logs, verify no errors
- [ ] **8.2** After 24h: check sync logs, verify Azure has new memories
- [ ] **8.3** After 24h: verify hook has been injecting context (check gateway logs)
- [ ] **8.4** Enable weekly review cron: `0 0 * * 0` (Sunday midnight)
- [ ] **8.5** Run `weekly_review_agent.py --dry-run` to preview

---

## Hook Implementation: `memory_recall_hook.js`

### Hook Structure (deployed to `~/.openclaw/hooks/clawbot-memory/`)

```
~/.openclaw/hooks/clawbot-memory/
├── HOOK.md          # Hook metadata (name, events, requirements)
└── handler.js       # Hook implementation
```

### HOOK.md

```yaml
---
name: clawbot-memory-recall
description: Injects relevant memories from Azure AI Search before each agent turn
events:
  - before_agent_start
requirements:
  env:
    - AZURE_SEARCH_ENDPOINT
  bins:
    - python3
---

# ClawBot Memory Recall Hook

Queries Azure AI Search (with SQLite fallback) on every turn.
Prepends top 3-5 relevant facts as `<clawbot_memory>` context.
Graceful degradation: Azure timeout → local SQLite → skip.
```

### handler.js (Pseudocode — will be implemented in Phase 2.3)

```javascript
// before_agent_start hook
// Receives: { prompt, messages }
// Returns:  { prependContext: "<clawbot_memory>...</clawbot_memory>" }

module.exports = async function(event, ctx) {
  const userMessage = extractLastUserMessage(event.messages);
  if (!userMessage) return;

  try {
    // 1. Try Azure AI Search (2s timeout)
    const facts = await queryAzureSearch(userMessage, { timeout: 2000, topK: 5 });
    if (facts.length > 0) {
      return { prependContext: formatMemoryContext(facts) };
    }
  } catch (err) {
    // 2. Fallback: local SQLite
    try {
      const localFacts = await queryLocalSQLite(userMessage, { topK: 5 });
      if (localFacts.length > 0) {
        return { prependContext: formatMemoryContext(localFacts) };
      }
    } catch (localErr) {
      // 3. Graceful skip — no memory this turn
      console.warn('[clawbot-memory] Both Azure and local search failed, skipping');
    }
  }
};

function formatMemoryContext(facts) {
  const lines = facts.map((f, i) =>
    `[${i+1}] ${f.text} [${f.type}, ${f.domain}${f.date ? ', ' + f.date : ''}]`
  );
  return `<clawbot_memory>\n${lines.join('\n')}\n</clawbot_memory>`;
}
```

---

## Cron Jobs (Final State)

```cron
# === ClawBot Brain (Memory Skill) ===

# Extraction sweep — daily 4:15 PM ET (20:15 UTC)
15 20 * * * cd ~/.openclaw/workspace/skills/clawbot-memory && ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/python3 smart_extractor.py sweep >> ~/claude-memory/logs/extract.log 2>&1

# Azure sync — daily 4:35 PM ET (20:35 UTC) — 20 min after extraction
35 20 * * * cd ~/.openclaw/workspace/skills/clawbot-memory && ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/python3 memory_bridge.py sync >> ~/claude-memory/logs/sync.log 2>&1

# Weekly review — Sunday midnight UTC (enable after 24h soak)
# 0 0 * * 0 cd ~/.openclaw/workspace/skills/clawbot-memory && ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/python3 weekly_review_agent.py >> ~/claude-memory/logs/review.log 2>&1

# Log rotation — daily 3 AM UTC (keep 7 days)
0 3 * * * find ~/claude-memory/logs/ -name "*.log" -mtime +7 -delete 2>/dev/null
```

---

## Rollback Procedure

**If anything goes wrong, execute in order:**

```bash
# 1. Remove cron jobs (stops all automated processing)
ssh oclaw "crontab -l | grep -v 'clawbot-memory' | grep -v 'claude-memory' | crontab -"

# 2. Remove hook directory (gateway stops loading it on next turn)
ssh oclaw "rm -rf ~/.openclaw/hooks/clawbot-memory"

# 3. Remove skill directory (gateway stops discovering it on next reload)
ssh oclaw "rm -rf ~/.openclaw/workspace/skills/clawbot-memory"

# 4. Remove session symlink (clean up)
ssh oclaw "rm -f ~/.openclaw/logs/sessions"

# 5. Data is preserved (no destruction):
#    - ~/claude-memory/memory.db still has all extracted memories
#    - Azure indexes still have synced data
#    - Session JSONL files are untouched (read-only access)
#    - Gateway config unchanged (no openclaw.json edits)
#    - Built-in memory system unchanged
```

**Total rollback time: ~30 seconds. Zero data loss. No gateway restart needed.**

---

## File Manifest (What Gets Deployed to VM)

```
~/.openclaw/hooks/clawbot-memory/              # NEW: Hook for always-on recall
├── HOOK.md                     # Hook metadata (name, events, requirements)
└── handler.js                  # before_agent_start implementation

~/.openclaw/workspace/skills/clawbot-memory/   # Skill for deep recall + extraction
├── SKILL.md                    # Skill definition (gateway reads this)
├── smart_extractor.py          # Extraction pipeline + recall command
├── memory_bridge.py            # SQLite → Azure sync
├── auth_provider.py            # Azure auth provider
├── oclaw_cli.py                # Inspector CLI
├── TAG_REGISTRY.md             # Tag taxonomy
├── .venv/                      # Python venv (azure-*, openai packages)
└── (weekly_review_agent.py)    # Deployed but cron disabled until Phase 8

~/claude-memory/
├── cli/
│   └── mem.py                  # SQLite CRUD
├── logs/
│   ├── extract.log             # Extraction sweep output
│   ├── sync.log                # Azure sync output
│   └── review.log              # Weekly review output
├── memory.db                   # Created by mem.py on first run
├── .extract_state.json         # Created by smart_extractor on first run
└── .sync_state.json            # Created by memory_bridge on first run

~/.openclaw/logs/
└── sessions -> ../agents/main/sessions/   # SYMLINK (new)
```

---

## Dependencies & Parallel Groups

```
Phase 0: Pre-flight (read-only)           {all parallel}
Phase 1: VM dirs + symlink                 {sequential}
Phase 2: Deploy skill + hook files         {after Phase 1}
Phase 3: Clear Azure                       {parallel with Phase 2}
Phase 4: Initial load (4 sessions)         {after Phase 2 + 3}
Phase 5: Enable cron                       {after Phase 4}
Phase 6: Enable hook injection             {after Phase 5}
Phase 7: Enable SKILL.md deep recall       {after Phase 6, verify hook works first}
Phase 8: 24h soak + weekly review          {after Phase 7, next day}
```

**Estimated time: Phases 0-7 in ~1.5 hours. Phase 8 after 24h soak.**
