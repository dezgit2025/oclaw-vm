# ClawBot Memory System Deployed (oclaw_brain v1)

**Date:** 2026-02-23
**Impact:** Enhancement — ClawBot gains persistent cross-session memory
**Rollback:** Delete `~/.openclaw/hooks/clawbot-memory/` (hook) + `~/.openclaw/workspace/skills/clawbot-memory/` (skill) + comment out cron entries

---

## What Changed

Deployed the oclaw_brain memory skill to the VM. ClawBot now has two memory injection paths:

1. **`before_agent_start` hook** — fires every conversation turn, injects 3-5 relevant facts from SQLite (~0.13s latency)
2. **SKILL.md deep recall** — on-demand topic search with richer results

93 memories extracted from 4 largest sessions (6.97 MB), synced to Azure AI Search with 3072-dim embeddings.

## Files Deployed

| Location | What |
|----------|------|
| `~/.openclaw/workspace/skills/clawbot-memory/` | 10 Python files (smart_extractor.py, memory_bridge.py, auth_provider.py, oclaw_cli.py, SKILL.md, etc.) |
| `~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py` | SQLite CRUD CLI |
| `~/.openclaw/workspace/skills/clawbot-memory/.venv/` | Python venv (openai, azure-search-documents, azure-identity) |
| `~/.openclaw/hooks/clawbot-memory/HOOK.md` | Hook manifest (YAML frontmatter) |
| `~/.openclaw/hooks/clawbot-memory/handler.js` | Hook handler (74 lines) |
| `~/.claude-memory/memory.db` | SQLite memory store (93 memories) |
| `~/.openclaw/logs/sessions` | Symlink → `~/.openclaw/agents/main/sessions` |

## Environment Changes

Set in `/etc/environment`, `~/.bashrc`, `~/.profile`:
```
AZURE_SEARCH_ENDPOINT=https://oclaw-search.search.windows.net
AZURE_OPENAI_ENDPOINT=https://oclaw-openai.openai.azure.com/
AZURE_OPENAI_CHAT_ENDPOINT=https://pitchbook-resource.cognitiveservices.azure.com/
```

## RBAC Change

Assigned **Search Index Data Contributor** role to VM managed identity (`56afe324-cd9e-4d5d-b7c3-3d5847e5bdc6`) on `oclaw-search` resource in `oclaw-rg`.

## Cron Jobs Added

```
15 20 * * *  — Extract facts from new sessions (smart_extractor.py sweep)
35 20 * * *  — Sync SQLite → Azure AI Search (memory_bridge.py sync)
0 3 * * *   — Log rotation (keep 7 days)
```

## Bugs Found During Deployment

1. **Session format v3 mismatch** — smart_extractor.py only knew v2 format, returned 0 candidates. Added ~180-line v3 parser.
2. **mem.py path mismatch** — MEM_CLI referenced skill dir but mem.py was deployed elsewhere. 123 facts silently lost. Fixed by deploying to both locations.
3. **handler.js `--format brief`** — Flag doesn't exist in smart_extractor.py. Hook silently failed on every invocation. Removed the flag.
4. **Azure content filter** — 2 chunks triggered jailbreak filter during GPT-5.2 extraction. Added try/except to skip.
5. **Missing env vars** — All 3 Azure endpoints were empty on VM. Set in multiple locations.
6. **Missing RBAC** — VM MI lacked data plane access to Azure AI Search. Assigned role.

## Cost

| Component | Monthly |
|-----------|---------|
| Azure AI Search (basic tier, oclaw-rg) | ~$74 |
| GPT-5.2 extraction + recall | ~$10 |
| Embeddings (3072-dim) | ~$0.04 |
| **Total** | **~$84** |

## Verification

- Hook discovered: 5/5 hooks ready (4 bundled + clawbot-memory-recall)
- Recall latency: 0.132s (budget: 4s)
- 18 active skills (clawbot-memory included)
- Azure hybrid search score: 3.6619 for test query
- Phase 8 (24h soak) starts 2026-02-24

## Source

Original code: `/Users/dez/Projects/oclaw_brain/oclaw_brain_skill_v1/` (laptop)
Plan: `plans/upgrade_open_claw_brain.md`
Progress: `plans/progress.md`
Learnings: `plans/memory-learnings-v1.md`
