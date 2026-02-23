# OpenClaw Brain Memory System — Learnings v1

**Implementation Date:** 2026-02-23
**Source:** `plans/progress.md` (Phases 0-7 of Upgrade OpenClaw Brain plan)

---

## Architecture Learnings

### Hook System (before_agent_start)

- Hook discovery path: `~/.openclaw/hooks/<name>/` with `HOOK.md` (YAML frontmatter) + `handler.js` pairs
- 4 bundled hooks exist: session-memory, command-logger, boot-md, soul-evil
- `before_agent_start` hook returns `{ prependContext: "..." }` which gets prepended: `effectivePrompt = ${prependContext}\n\n${prompt}`
- Hook fires on **every conversation turn** — not once per session (that's `agent:bootstrap`)
- `agent:bootstrap` fires once per session — not useful for per-query memory retrieval
- Gateway must be restarted to pick up new/modified hooks
- Restart command: `python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py`
- Hook latency budget: 2s acceptable. Actual measured: **0.13s** (well under budget)
- Memory token budget: 3-5 facts (~200 tokens) per injection

### SKILL.md System

- Skill discovery via `~/.openclaw/workspace/skills/*/SKILL.md`
- 18 active skills (discoverable via SKILL.md glob pattern), 1 disabled (in `_disabled/`)
- Gating via YAML frontmatter: `metadata.openclaw.requires.bins` and `metadata.openclaw.requires.env`
- Plugin API offers `api.registerTool()`, `api.registerHook()`, `api.registerService()` — but hook file deployment (HOOK.md + handler.js) is simpler and doesn't require openclaw.json changes

### Injection Strategy

- Hybrid approach chosen: `before_agent_start` hook (always-on, lightweight, 3-5 facts) + SKILL.md (on-demand deep recall, topic expansion)
- Do NOT modify built-in `memory_search`/`memory_get` — too invasive, requires forking openclaw source, breaks on updates. Our system is additive via hook
- Do NOT use `gateway_model_routing_hook.js` — dormant prototype, not wired into openclaw.json, not loaded by gateway
- Do NOT use static system context files (MEMORY.md) for dynamic recall — can't do per-query retrieval
- `gateway_model_routing_hook.js` is a dormant prototype for session-scoped model override ("think hard" -> GPT-5.2)

### Session Format

- VM uses openclaw v3 session format: `{type: "message", message: {role, content}}`
- v2 format was: `{type: "user", message: {content: "..."}}`
- v3 event types: `session`, `message`, `model_change`, `summary`, `tool_use`, `tool_result`
- v2 event types: `user`, `assistant`, `progress`, `result`, `error`
- Content nesting differs: v3 = `event.message.role` + `event.message.content`, v2 = top-level

### VM File Paths

- Session files: `~/.openclaw/agents/main/sessions/` (actual), NOT `~/.openclaw/logs/sessions/` (expected by skill)
- Fix: symlink `~/.openclaw/logs/sessions` -> `~/.openclaw/agents/main/sessions`
- 1,566 session files (55 MB) on VM — rich source for extraction
- Memory SQLite DB: `~/.claude-memory/memory.db`
- Skill files: `~/.openclaw/workspace/skills/clawbot-memory/`
- Hook files: `~/.openclaw/hooks/clawbot-memory/`
- Venv: `~/.openclaw/workspace/skills/clawbot-memory/.venv/`
- Built-in memory: `~/.openclaw/memory/main.sqlite` + daily journals — separate system, leave untouched

### Existing Context Files

- MEMORY.md: only 3 entries (ClickUp prefs, archive command, folder structure)
- USER.md and IDENTITY.md: empty templates
- SOUL.md: fully populated (BarneyBot persona, 7,281 bytes)

---

## Bugs Found & Fixed

### 1. Session Format v3 Mismatch (Phase 4)

- **Impact:** smart_extractor.py returned 0 candidates from all sessions
- **Root Cause:** Format detection at line ~735 only recognized v2 types (`user`, `assistant`, `progress`) but VM sessions use v3 (`session`, `message`, `model_change`)
- **Fix:** Updated detection to recognize v3 types + created `_parse_openclaw_v3_session()` parser (~180 lines)
- **Lesson:** Always check actual session file format before assuming compatibility. Run a single test extraction first.

### 2. cli/mem.py Path Mismatch (Phase 4)

- **Impact:** 123 extracted facts silently failed to persist — subprocess calls to mem.py returned non-zero but were not caught
- **Root Cause:** `MEM_CLI = os.path.join(SKILL_DIR, "cli", "mem.py")` resolves to `~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py`, but mem.py was only deployed to `~/claude-memory/cli/mem.py`
- **Fix:** Copied mem.py to the expected skill dir location
- **Lesson:** When deploying files, trace the actual import/reference paths in all consuming scripts. Don't assume a file is only referenced from one location.

### 3. handler.js `--format brief` Flag (Phase 6)

- **Impact:** Hook silently failed on every invocation — argparse exit code 2, handler caught and returned empty
- **Root Cause:** handler.js included `--format brief` in the command, but `smart_extractor.py recall` does not support that flag
- **Fix:** Removed `--format brief` from command string. Also removed redundant `<clawbot_memory>` wrapping since output already comes wrapped in `<clawbot_context>` tags
- **Lesson:** Test the exact command that the hook will execute before deploying. Don't assume CLI flags exist without checking argparse definition.

### 4. Azure Content Filter (Phase 4, non-blocking)

- **Impact:** 2 chunks in one session triggered Azure's jailbreak content filter during GPT-5.2 extraction
- **Root Cause:** Session content contained patterns that matched Azure's content safety filters
- **Fix:** Added try/except in `extract_and_tag()` — logs warning and skips chunk
- **Lesson:** Always handle content filter errors in Azure OpenAI pipelines. They're common with real-world conversation data.

### 5. Missing Azure Env Vars (Phase 0)

- **Impact:** All 3 Azure env vars (AZURE_SEARCH_ENDPOINT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_ENDPOINT) were empty on VM
- **Root Cause:** Never set — Azure resources were provisioned but env vars weren't configured
- **Fix:** Set in .bashrc, .profile, /etc/environment, and ~/.config/environment.d/azure-endpoints.conf
- **Lesson:** Set env vars in multiple locations for reliability (interactive shells, non-interactive shells, cron, systemd)

### 6. Missing RBAC Role (Phase 3)

- **Impact:** VM managed identity couldn't access Azure AI Search data plane
- **Root Cause:** MI had no data plane role on the search service
- **Fix:** Assigned Search Index Data Contributor role on oclaw-search resource (in oclaw-rg, not RG_OCLAW2026)
- **Lesson:** Azure resource group matters — AI Search is in `oclaw-rg`, not `RG_OCLAW2026`. Always verify RBAC at data plane level, not just control plane.

---

## Operational Learnings

### Azure

- AI Search lives in `oclaw-rg` resource group, NOT `RG_OCLAW2026` (where the VM is)
- AI Search basic tier: ~$74/mo (flat-rate, no per-query cost)
- GPT-5.2 extraction + recall: ~$10/mo
- Embeddings (3072-dim): ~$0.04/mo
- Total cost: ~$84/month
- Managed Identity auth via DefaultAzureCredential with API key fallback
- Azure endpoints: `oclaw-search.search.windows.net` (Search), `oclaw-openai.openai.azure.com` (OpenAI), `pitchbook-resource.cognitiveservices.azure.com` (Chat)

### Cron Jobs

- Extraction: `15 20 * * *` (4:15 PM ET / 20:15 UTC)
- Sync: `35 20 * * *` (4:35 PM ET / 20:35 UTC — 20 min after extraction)
- Log rotation: `0 3 * * *` (keeps 7 days)
- `session_gc.py` runs daily 8PM UTC, backs up >5MB sessions before truncating — perfect future hook for extract-before-truncate pipeline

### Gateway

- Built-in `memory_search` uses hybrid vector (0.7) + FTS5 (0.3) — but DB is empty (0 chunks, 0 files, FTS-only mode). Our system fills the semantic search gap
- Gateway tailscale mode: config key `tailscale.mode` should be `"off"` (or empty `{}`). Setting it to `"serve"` causes gateway crash
- Gateway restart required after hook/skill file changes

### Extraction Pipeline

- 5-gate pipeline: Noise filter -> Secrets/PII filter -> Confidence filter -> Dedup filter -> Pivot detection
- From 4 sessions (6.97 MB total): 131 candidates -> 93 stored (71% pass rate)
- Session extraction rates vary: c12bc59b (96% stored), 3fedaa0f (57%), 317f68b6 (44%), c20853de (86%)
- SQLite uses SHA-256 content hash for dedup
- Recall uses SQLite keyword matching with priority scoring (decisions/pivots ranked higher)

### Fallback Chain

- Recall path: SQLite keyword search (local, default) — does NOT depend on Azure for per-turn recall
- Azure AI Search used for hybrid (vector + BM25) search — richer results but optional
- If Azure is unreachable: recall degrades to SQLite FTS5 silently
- If both fail: hook returns empty, no impact on conversation

---

## Process Learnings

### What Worked Well

- **Aggressive parallelization** of subagents saved significant time (Phases 0, 2+3 ran concurrently)
- **Orchestrator-only model** — main agent never touched code, only coordinated subagents and updated progress.md
- **Single test extraction first** (c20853de, smallest session) caught the v3 format bug before processing larger sessions
- **Progress.md as source of truth** — easy crash recovery, clear status at any point

### What Could Improve

- **Test the exact CLI command** a hook/script will execute before deploying — would have caught `--format brief` bug immediately
- **Trace all file reference paths** during deployment — would have caught mem.py path mismatch
- **Set env vars in ALL locations** from the start (not just .bashrc) — cron and systemd use different env sources
- **Check RBAC at data plane level** before attempting operations — control plane access != data plane access

### Subagent Patterns

- Subagents that proactively went beyond their scope (e.g., Phase 3 agent creating venv + assigning RBAC) were helpful when the extra work was prerequisite for future phases
- Subagents should always report: files changed, verification command + output, pass/fail, blockers
- Silent failures (mem.py path, --format brief) are the hardest to debug — subagents should check exit codes explicitly

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Memories extracted | 93 |
| Sessions processed | 4 |
| Total session data | 6.97 MB |
| Extraction pass rate | 71% (93/131 candidates) |
| Azure sync time | 1.285s (93 docs) |
| Hook recall latency | 0.132s |
| Hook recall budget | 4s timeout (0.13s actual) |
| Active skills | 18 |
| Active hooks | 5 (4 bundled + 1 custom) |
| Monthly cost | ~$84 |
| Bugs found & fixed | 6 |
| Phases completed | 7 of 8 |
