# Memory Extraction from AI Agent Session Files: Best Practices

**Research Date:** March 6, 2026 | **Coverage:** December 2025 - March 2026

---

## Table of Contents

1. [Claude Code Session JSONL Format](#1-claude-code-session-jsonl-format)
2. [Claude Code Memory & Compaction Internals](#2-claude-code-memory--compaction-internals)
3. [Anthropic Memory Tool API](#3-anthropic-memory-tool-api)
4. [Session-to-Memory Extraction Pipelines](#4-session-to-memory-extraction-pipelines)
5. [LLM-Based Fact Extraction Systems](#5-llm-based-fact-extraction-systems)
6. [Deduplication & Contradiction Resolution](#6-deduplication--contradiction-resolution)
7. [Memory Schemas](#7-memory-schemas)
8. [Incremental vs Batch Extraction](#8-incremental-vs-batch-extraction)
9. [Embedding & Retrieval](#9-embedding--retrieval)
10. [Graph-Based Memory Systems](#10-graph-based-memory-systems)
11. [Academic Papers (Dec 2025 - Mar 2026)](#11-academic-papers-dec-2025---mar-2026)
12. [Commercial Platform Comparison](#12-commercial-platform-comparison)
13. [Recommendations for oclaw_brain](#13-recommendations-for-oclaw_brain)

---

## 1. Claude Code Session JSONL Format

### 1.1 Storage Locations

| Path | Purpose |
|------|---------|
| `~/.claude/projects/<encoded-path>/<session-uuid>.jsonl` | Full session transcripts |
| `~/.claude/history.jsonl` | Global session index for `/resume` picker |
| `~/.claude/projects/<encoded-path>/sessions-index.json` | Per-project session metadata |
| `~/.claude/projects/<encoded-path>/memory/MEMORY.md` | Auto-memory index file |

Project paths use dash-encoding: `/Users/dez/Projects/openclaw_vm` becomes `-Users-dez-Projects-openclaw-vm`. Log retention: 30 days default, configurable via `logRetentionDays`.

### 1.2 Message Types (7 Distinct Types)

| Type | Purpose |
|------|---------|
| `progress` | Hook execution, streaming progress, sub-agent status (most frequent) |
| `assistant` | Claude responses (text, thinking, tool calls) |
| `user` | User prompts and tool results |
| `file-history-snapshot` | Git/file state checkpoint |
| `system` | Compaction boundaries, turn duration, local commands |
| `queue-operation` | Sub-agent task enqueue/dequeue/complete |
| `last-prompt` | Final prompt marker at session end |

### 1.3 Common Envelope Fields (All Messages)

```
parentUuid           -- UUID of parent message (null for first or after compact)
uuid                 -- unique message ID
sessionId            -- session UUID (matches filename)
timestamp            -- ISO-8601 string
type                 -- one of the 7 types above
cwd                  -- absolute working directory path
version              -- Claude Code version string (e.g., "2.1.69")
gitBranch            -- current git branch name
isSidechain          -- boolean; true for branched/alternate conversation paths
userType             -- "external" (human user) or other agent types
```

The `parentUuid` field creates a linked-list chain through the conversation, allowing reconstruction including branches.

### 1.4 User Message Schema

**Standard prompt:**
```json
{
  "type": "user",
  "message": { "role": "user", "content": "the prompt text" },
  "parentUuid": null,
  "uuid": "...",
  "permissionMode": "default"
}
```

**Tool result:**
```json
{
  "type": "user",
  "message": { "role": "user", "content": [{ "type": "tool_result", "tool_use_id": "toolu_...", "content": "..." }] },
  "toolUseResult": { ... },
  "sourceToolAssistantUUID": "assistant-msg-uuid"
}
```

**Compact summary (after compaction):**
```json
{
  "type": "user",
  "isCompactSummary": true,
  "isVisibleInTranscriptOnly": true,
  "message": { "role": "user", "content": "This session is being continued from a previous conversation..." }
}
```

### 1.5 Assistant Message Content Blocks

Three types inside `message.content[]`:

| Block | Fields | Notes |
|-------|--------|-------|
| `thinking` | `thinking`, `signature` | Signature is cryptographic verification token |
| `text` | `text` | The visible response text |
| `tool_use` | `id`, `name`, `input`, `caller` | Tool invocation |

### 1.6 Token Usage Fields

Every assistant message carries:
```json
{
  "usage": {
    "input_tokens": 3,
    "output_tokens": 9,
    "cache_creation_input_tokens": 14075,
    "cache_read_input_tokens": 5621,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 14075
    },
    "service_tier": "standard",
    "inference_geo": "not_available"
  }
}
```

### 1.7 System Message Subtypes

- `compact_boundary` -- marks where compaction occurred (includes `compactMetadata.trigger`, `compactMetadata.preTokens`, `logicalParentUuid`)
- `turn_duration` -- performance telemetry (`durationMs`)
- `local_command` -- slash commands like `/compact`, `/model`

### 1.8 Queue Operation Messages (Sub-agents)

```json
{
  "type": "queue-operation",
  "operation": "enqueue",
  "content": "<task-notification><task-id>...</task-id><status>completed</status><result>...</result></task-notification>"
}
```

---

## 2. Claude Code Memory & Compaction Internals

### 2.1 Two Memory Systems

**A. CLAUDE.md (Manual)** -- Three-tier hierarchy, re-read at session start and after compaction:

| Level | Path | Scope |
|-------|------|-------|
| Global | `~/.claude/CLAUDE.md` | All projects |
| Project (shared) | `<project-root>/CLAUDE.md` | Per-project (committed) |
| Project (local) | `<project-root>/.claude/CLAUDE.md` | Per-project (gitignored) |

**B. Auto Memory (MEMORY.md)** -- Claude's self-written notes:

| Path | Purpose |
|------|---------|
| `~/.claude/projects/<encoded-path>/memory/MEMORY.md` | Index (first 200 lines auto-loaded) |
| `~/.claude/projects/<encoded-path>/memory/<topic>.md` | Topic files (loaded on demand) |

Categories saved: build commands, debugging insights, architecture notes, code style preferences, workflow habits, error patterns, key decisions.

### 2.2 Compaction Process

1. **PreCompact hook fires** (if configured) -- receives `session_id` + `transcript_path`
2. **`compact_boundary` system message** appended to JSONL
3. **Full conversation summarized** via structured prompt
4. **Compact summary user message** appended after boundary
5. **Future API requests** use only summary + post-compact messages
6. **Original JSONL preserved** -- compaction never deletes lines

### 2.3 Three-Layer Compaction Design

| Layer | Trigger | Action |
|-------|---------|--------|
| Microcompaction | Early, transparent | Strips bulky tool outputs no longer referenced |
| Auto-compaction | ~95% context window (~120K-190K tokens) | Full structured summary, resets context |
| Manual (`/compact [hint]`) | User-initiated | Summary biased toward focus hint |

### 2.4 Compaction Summary Prompt Structure

The summarization prompt produces:
1. **Primary Request and Intent** -- all user requests in detail
2. **Files and Code Sections** -- specific files examined/modified/created with code snippets
3. **Errors and Fixes** -- all errors and resolutions, with attention to user feedback
4. **All User Messages** -- verbatim listing (critical for preserving feedback/corrections)
5. **Pending Tasks and Current Work** -- what was in progress

### 2.5 Memory-Related System Prompts

| Prompt File | Tokens | Purpose |
|-------------|--------|---------|
| `agent-prompt-memory-selection.md` | 156 | Selects relevant stored memories for query |
| `agent-prompt-session-memory-update-instructions.md` | 756 | How to update session memory files |
| `data-session-memory-template.md` | 292 | Template for new memory entries |
| `agent-prompt-conversation-summarization.md` | -- | Full compact summary generation |
| `agent-prompt-recent-message-summarization.md` | -- | Micro-compaction summaries |

Source: [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)

### 2.6 Hook System for Memory

Relevant hooks: `SessionStart`, `Stop`, `PreCompact`, `SessionEnd`, `SubagentStop`

All receive `session_id` + `transcript_path` pointing to the JSONL file. Four hook types: command, HTTP, prompt, agent.

---

## 3. Anthropic Memory Tool API

**Type:** `memory_20250818` (Beta header: `context-management-2025-06-27`)

Client-side tool -- Claude makes tool calls, your app executes locally. Six operations:

| Command | Purpose |
|---------|---------|
| `view` | Read memory files from `/memories` directory |
| `create` | Create new memory files |
| `str_replace` | Surgical edits to existing memory content |
| `insert` | Add content at specific location |
| `delete` | Remove memory files |
| `rename` | Rename memory files |

Reference implementation: `anthropic-sdk-python/examples/memory/basic.py`

Pairs with server-side compaction. The auto-injected system prompt tells Claude to always check memory first and assume potential interruption.

---

## 4. Session-to-Memory Extraction Pipelines

### 4.1 OpenAmnesia (Feb 2026)
[github.com/vincentkoc/openamnesia](https://github.com/vincentkoc/openamnesia)

Pipeline: Raw JSONL -> Schema normalization (Stable Event IR) -> Segmentation into "moments" (intent->actions->outcomes->artifacts) -> Deterministic time/project grouping -> Dedup retries/tool spam -> Memory extraction from clustered moments.

**Key insight:** Hardest part is normalization across heterogeneous agent JSONL schemas.

### 4.2 CASS - Coding Agent Session Search (Jan 2026)
[github.com/Dicklesworthstone/coding_agent_session_search](https://github.com/Dicklesworthstone/coding_agent_session_search)

Three-layer cognitive architecture:
1. **Episodic Memory** -- raw session logs from all agents
2. **Working Memory (Diary)** -- structured session summaries with typed events
3. **Procedural Memory (Playbook)** -- distilled rules with confidence tracking

Cross-agent transfer learning, confidence decay, anti-pattern learning, "trauma guard" safety.

### 4.3 QMD Sessions (Mar 3, 2026)
[williambelk.com/blog/qmd-sessions-claude-code-memory-with-qmd-20260303](https://www.williambelk.com/blog/qmd-sessions-claude-code-memory-with-qmd-20260303/)

Reads every session JSONL, extracts messages, outputs organized markdown. Three search modes: `search` (BM25), `vsearch` (vector), `query` (hybrid FTS + vector + query expansion + LLM re-ranking).

### 4.4 Ghost (2026)
[github.com/notkurt/ghost](https://github.com/notkurt/ghost)

Records sessions non-blockingly as markdown, attaches to commits via git notes, indexes into QMD for semantic search.

### 4.5 severity1/claude-code-auto-memory
Hooks: SessionStart, UserPromptSubmit, PostToolUse, Stop. **Cursor-based reading** (only processes new content). Chunks at 6,000 chars for Haiku processing. Sends chunks + existing memories as context (dedup at extraction time). Returns typed JSON with decay lifespans:
- **Permanent:** architecture, decisions, patterns, gotchas
- **7-day decay:** progress
- **30-day decay:** context

### 4.6 thedotmack/claude-mem
AI-compressed observations with progressive compression layers. Recent work stays detailed, older work gets summarized. SQLite3 backend on port 37777.

### 4.7 Other Notable Tools

| Tool | URL | Approach |
|------|-----|----------|
| Severance | [github.com/blas0/Severance](https://github.com/blas0/Severance) | Embeddings + annotations + summarized notes + knowledge graphs via hooks |
| Mnemon | [github.com/mnemon-dev/mnemon](https://github.com/mnemon-dev/mnemon) | LLM-supervised memory with graph-based recall, single binary |
| mnemo | [pkg.go.dev/github.com/Pilan-AI/mnemo](https://pkg.go.dev/github.com/Pilan-AI/mnemo) | Go binary indexing sessions from 12+ tools into SQLite with FTS5 |
| Total Recall | [github.com/radu2lupu/total-recall](https://github.com/radu2lupu/total-recall) | Cross-session semantic memory via QMD |
| engram | [github.com/Gentleman-Programming/engram](https://github.com/Gentleman-Programming/engram) | Agent proactively calls `mem_save` after significant work |

---

## 5. LLM-Based Fact Extraction Systems

### 5.1 LangMem SDK (LangChain)
[langchain-ai.github.io/langmem](https://langchain-ai.github.io/langmem/)

```python
from langmem import create_memory_manager
manager = create_memory_manager("anthropic:claude-3-5-sonnet-latest")
memories = await manager([messages])
```

Structured extraction with Pydantic schemas (e.g., `Fact(subject, predicate, object)`). Background memory manager runs async. Prompt optimizer uses trajectories to refine system prompts. **Limitation:** No knowledge graph -- flat KV with vector search.

### 5.2 Mem0
[mem0.ai](https://mem0.ai) | [docs.mem0.ai](https://docs.mem0.ai)

Two-phase extraction (Extract + Update): Entity extraction -> Relationship generation (triplets) -> Conflict detection -> Graph merging. 26% relative uplift over OpenAI memory on LOCOMO benchmark. Graph-enhanced `Mem0g` reaches 68.4%.

### 5.3 ChatGPT Memory (Reverse-Engineered, Dec 2025)
[manthanguptaa.in/posts/chatgpt_memory](https://manthanguptaa.in/posts/chatgpt_memory/)

4-layer system (no vector DB, no RAG):
1. Session metadata
2. Saved facts via `bio` tool (LLM accepts messages + existing facts, returns updates)
3. Conversation summaries (~15 lightweight summaries)
4. Current conversation sliding window

**Key insight:** All saved facts injected into EVERY prompt. No retrieval step.

### 5.4 Gemini Memory
[shloked.com/writing/gemini-memory](https://www.shloked.com/writing/gemini-memory)

Compressed `user_context` document with typed factual bullets. Each includes a **rationale**: `"Statement: The user is Shlok. (Rationale: User explicitly stated on June 18, 2025...)"`. Doubles memory size but adds provenance.

### 5.5 Claude.ai Memory (Official)
- Conversations processed in daily synthesis cycles (~24 hours)
- Explicit "remember this" takes effect immediately
- Memory encrypted at rest, tied to conversations
- Project-specific siloed memory spaces
- As of March 2, 2026: free for all users, with import from ChatGPT/Gemini/Grok

### 5.6 SimpleMem (Jan 2026)
[arxiv.org/abs/2601.02553](https://arxiv.org/abs/2601.02553) | [github.com/aiming-lab/SimpleMem](https://github.com/aiming-lab/SimpleMem)

Three-stage pipeline:
1. **Semantic Structured Compression** -- distills interactions into compact, multi-view indexed memory units
2. **Online Semantic Synthesis** -- intra-session merging of related context (real-time redundancy elimination)
3. **Intent-Aware Retrieval Planning** -- infers search intent for dynamic retrieval scope

Results: 26.4% F1 improvement on LoCoMo, **30x token reduction**, 64% boost over Claude-Mem.

### 5.7 A-Mem (Agentic Memory, Feb 2026)
[arxiv.org/abs/2502.12110](https://arxiv.org/abs/2502.12110) | [github.com/agiresearch/A-mem](https://github.com/agiresearch/A-mem)

Combines Zettelkasten principles with agent-driven decisions. New memories get contextual descriptions, keywords, tags, and dynamic linking to create interconnected knowledge networks. Doubles performance on multi-hop reasoning.

### 5.8 AWS Bedrock AgentCore Memory
[docs.aws.amazon.com/bedrock-agentcore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)

Asynchronous background pipeline: Extraction -> Consolidation -> Reflection. Two strategies: Episodic (goal/reasoning/actions/outcomes/reflections) and Semantic (facts/knowledge). XML schema with confidence scores (0.1-1.0). LLM decides: keep, update, delete, or insert separately.

---

## 6. Deduplication & Contradiction Resolution

### 6.1 TeleMem (Jan 2026)
[arxiv.org/html/2601.06037v4](https://arxiv.org/html/2601.06037v4)

LLM-based semantic merging. Character isolation prevents cross-entity contamination. 86.33% accuracy (19% above Mem0). Drop-in Mem0 replacement.

### 6.2 FadeMem - Biologically-Inspired Forgetting (Jan 2026)
[arxiv.org/abs/2601.18642](https://arxiv.org/abs/2601.18642) | [github.com/ChihayaAine/FadeMem](https://github.com/ChihayaAine/FadeMem)

Dual-layer hierarchy with differential decay:
- **Long-term Memory Layer (LML):** shape 0.8, sub-linear decay, half-life ~11.25 days
- **Short-term Memory Layer (SML):** shape 1.2, super-linear decay, half-life ~5.02 days

Results: 82.1% retention of critical facts using 55.0% of storage.

### 6.3 MemOS (Jul 2025)
[arxiv.org/abs/2507.03724](https://arxiv.org/abs/2507.03724) | [github.com/MemTensor/MemOS](https://github.com/MemTensor/MemOS)

Memory Operating System with MemCubes (content + metadata + provenance + version). Dedup at MemCube level, versioning with provenance tracking, forgetting policies. 159% temporal reasoning improvement, 60.95% token overhead reduction.

### 6.4 Memoria - EWA Contradiction Resolution (Dec 2025)
[arxiv.org/abs/2512.12686](https://arxiv.org/abs/2512.12686)

Exponential Weighted Average scheme: newer triplets receive higher weight and supersede older ones. 87.1% accuracy, 38.7% latency/token reduction.

### 6.5 Consolidated Dedup Techniques

| Technique | Description | Used By |
|-----------|-------------|---------|
| Fuzzy word-overlap | Block >60% word overlap | oclaw_brain (current) |
| LLM semantic sweep | Periodic cheap-model merge of similar memories | TeleMem, Mem0 |
| Confidence counters | Track confirmation count + `last_confirmed` | CASS, A-Mem, AgentCore |
| Temporal versioning | Track when facts established/changed | Zep/Graphiti, MemOS |
| EWA conflict resolution | Newer facts supersede via weighted average | Memoria |
| Forgetting policies | Explicit rules for memory purge | MemOS, FadeMem |
| Consolidation LLM | LLM decides: keep, update, delete, or insert | AgentCore, Mem0 |

---

## 7. Memory Schemas

### 7.1 Flat Fact Schema (LangMem)
```python
class Fact(BaseModel):
    subject: str       # Entity
    predicate: str     # Relationship/attribute
    object: str        # Value/related entity
```

### 7.2 AgentCore Reflection Schema (XML)
```xml
<reflection>
  <operator>add|update</operator>
  <id>existing-id</id>
  <title>Pattern Title</title>
  <use_cases>When this applies</use_cases>
  <hints>Specific guidance</hints>
  <confidence>0.8</confidence>
</reflection>
```

### 7.3 Production Memory Schema (Consolidated Best Practice)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID | Unique identifier |
| `content` | text | The extracted fact/memory |
| `type` | enum | decision, fix, architecture, preference, correction, procedure |
| `tags` | list[str] | Categorization tags |
| `confidence` | float (0.1-1.0) | Confirmation strength |
| `confirmation_count` | int | Sessions that confirmed this |
| `last_confirmed` | datetime | Last validation |
| `created_at` | datetime | Original extraction |
| `updated_at` | datetime | Last modification |
| `source_session` | str | Session ID where extracted |
| `project` | str | Project scope |
| `scope` | enum | project, global |
| `decay_weight` | float | `similarity * exp(-lambda * days_since_access)` |
| `evidence_links` | list[str] | Supporting session references |
| `supersedes` | UUID | Memory this replaces (contradiction tracking) |
| `embedding` | vector | For semantic retrieval |

### 7.4 Graph Triple Schema (Mem0, Zep, Cognee)
```
(entity_node) --[relationship {valid_from, valid_to, confidence}]--> (entity_node)
```
Zep's bi-temporal model tracks both when an event occurred and when it was ingested.

### 7.5 Statement+Rationale Schema (Gemini)
```
Statement: The user prefers Python for data work.
(Rationale: User explicitly stated on Feb 12, 2026.)
```

### 7.6 Typed Decay Schema (severity1/claude-code-auto-memory)

| Type | Decay | Examples |
|------|-------|---------|
| architecture | permanent | System design, stack choices |
| decisions | permanent | Architectural decisions, trade-offs |
| patterns | permanent | Coding patterns, conventions |
| gotchas | permanent | Pitfalls, known issues |
| progress | 7-day | Current task status |
| context | 30-day | Session-specific context |

### 7.7 Emerging Consensus

- Start with **flat store** (JSON/SQLite). Migrate to **graph** only with 500+ memories needing relationship traversal
- Always include: content, type tag, confidence, timestamps (created + last_confirmed), source session ID
- Atomicity: break raw text into **discrete memory statements**, never store blobs
- Normalize by separating message, memory, and tool logs -- tag with origin

---

## 8. Incremental vs Batch Extraction

### 8.1 Incremental (Real-Time)

| System | Approach |
|--------|----------|
| Letta/MemGPT | Self-editing via `core_memory_append/replace`. New: Context Repositories with git versioning |
| Anthropic Memory Tool API | Client-side tool, agent manages `/memories` directory |
| engram | Agent proactively calls `mem_save` after significant work |
| Claude Code Auto-Memory | Background system saves structured summaries to disk |

**Pros:** Immediate availability, full context when deciding what to store.
**Cons:** Adds latency, may miss facts, consumes reasoning tokens.

### 8.2 Batch (Post-Session)

| System | Approach |
|--------|----------|
| oclaw_brain (current) | Daily cron at 20:15 UTC via GPT-5.2 |
| LangMem background | Async extraction without agent deciding |
| OpenAmnesia | Multi-source normalization + offline extraction |
| AWS AgentCore | Async extraction + consolidation + reflection |
| QMD Sessions | Batch JSONL-to-markdown + QMD indexing |

**Pros:** No latency impact, can use stronger/cheaper models, full conversation context, better dedup.
**Cons:** Memories unavailable until next session.

### 8.3 Hybrid (2026 Best Practice)

| System | Real-Time | Batch |
|--------|-----------|-------|
| **oclaw_brain** | `before_agent_start` hook recall (~0.13s) | Daily cron sweep |
| SimpleMem | Online Semantic Synthesis | Semantic Structured Compression |
| CASS | Real-time episodic capture | Periodic procedural distillation |
| Severance | Claude Hooks auto-trigger | Session note summarization |
| FadeMem | Immediate SML storage (rapid decay) | Consolidation into LML (gradual decay) |

**oclaw_brain's architecture (hook-based recall + batch extraction) is now considered best practice.** Consensus: recall in real-time (sub-second), extract in batch (post-session).

---

## 9. Embedding & Retrieval

### 9.1 Strategy Comparison

| System | Strategy | Speed |
|--------|----------|-------|
| oclaw_brain | Azure AI Search hybrid (vector + FTS5 fallback) | ~0.13s |
| SimpleMem | Intent-aware retrieval planning (dynamic scope) | Sub-second |
| Mem0 | Vector + graph traversal | Sub-second |
| Zep/Graphiti | Cosine + BM25 + breadth-first graph + reranking | Sub-100ms |
| engram | SQLite FTS5 only (no embeddings) | ~5ms |
| mcp-memory-service | Semantic search + knowledge graph | ~5ms |
| QMD | BM25 + vector + LLM re-ranking (3-stage) | Variable |

### 9.2 Hybrid Search (Consensus Best Practice)

**Vector + BM25 fusion** is the dominant pattern. Use **Reciprocal Rank Fusion (RRF)** to combine results. Two-stage retrieval: sentence transformer for fast candidates -> cross-encoder reranker for precision. Reported 25% reduced token usage and up to 48% retrieval quality improvement with reranking.

### 9.3 Zep/Graphiti (Most Sophisticated)
[arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956)

Three search functions combined: cosine similarity + Okapi BM25 + breadth-first graph search. Bi-temporal model. Real-time incremental updates. 94.8% on DMR benchmark, 18.5% accuracy improvement on LongMemEval with 90% latency reduction.

### 9.4 Decay-Weighted Retrieval Scoring

Standard formula:
```
finalScore = (1 - weight) * hybridScore + weight * recencyScore
recencyScore = exp(-decayRate * ageInHours)
decayRate = ln(2) / halfLifeHours
```

Composite approach:
```
S(M_i) = alpha * R_i + beta * E_i + gamma * U_i
R_i = exp(-lambda * (t_now - t_i))    # recency
E_i = embedding_similarity             # relevance
U_i = explicit_utility_score           # importance
```

Half-life recommendations: 7-30 days. FadeMem: 11.25 days (long-term), 5.02 days (short-term).

---

## 10. Graph-Based Memory Systems

### 10.1 Cognee
[github.com/topoteretes/cognee](https://github.com/topoteretes/cognee)

ECL pipeline: Classify -> Check permissions -> Extract chunks -> LLM extracts entities/relationships -> Generate summaries -> Embed + commit graph edges. 1M+ pipelines/month, 70+ companies in production.

### 10.2 Neo4j Agent-Memory (Feb 2026)
[github.com/neo4j-labs/agent-memory](https://github.com/neo4j-labs/agent-memory)

Three memory types: Short-Term, Long-Term, Reasoning. POLE+O entity model (Person, Object, Location, Event, Organization). Multi-stage extraction: spaCy + GLiNER2 + LLM with merge strategies.

### 10.3 mcp-memory-service
[github.com/doobidoo/mcp-memory-service](https://github.com/doobidoo/mcp-memory-service)

Open-source persistent memory MCP server. 5ms retrieval, 75 configurable memory types, SQLite integrity monitoring, D3.js dashboard, optional Cloudflare backend.

---

## 11. Academic Papers (Dec 2025 - Mar 2026)

| Paper | Date | ArXiv | Key Contribution |
|-------|------|-------|-----------------|
| SimpleMem | Jan 2026 | 2601.02553 | Semantic compression, 30x token reduction |
| Agentic Memory | Jan 2026 | 2601.01885 | Unified long/short-term memory management |
| TeleMem | Jan 2026 | 2601.06037 | Semantic dedup, Mem0 drop-in replacement |
| FadeMem | Jan 2026 | 2601.18642 | Bio-inspired forgetting, dual-layer decay |
| A-Mem | Feb 2026 | 2502.12110 | Zettelkasten + agentic memory (NeurIPS 2025) |
| Zep | Jan 2026 | 2501.13956 | Temporal knowledge graph, 94.8% DMR |
| Memoria | Dec 2025 | 2512.12686 | EWA knowledge graph, 87.1% accuracy |
| Forgetful but Faithful | Dec 2025 | 2512.12856 | Privacy-aware cognitive forgetting |
| Hindsight is 20/20 | Dec 2025 | 2512.12818 | Narrative fact extraction, temporal ranges |
| Memory in the Age of AI Agents | Dec 2025 | 2512.13564 | Survey: extraction/updating/retrieval/utilization |
| AI Meets Brain | Dec 2025 | 2512.23343 | Cognitive neuroscience for agent memory |
| Graph-based Agent Memory | Feb 2026 | 2602.05665 | Taxonomy of graph memory approaches |
| AMA-Bench | Feb 2026 | 2602.22769 | Benchmark for long-horizon agent memory |
| MemOS | Jul 2025 | 2507.03724 | Memory OS: dedup, versioning, 159% temporal improvement |

### Curated Paper Lists
- [Awesome Memory for Agents](https://github.com/TsinghuaC3I/Awesome-Memory-for-Agents)
- [Awesome Agent Memory (TeleAI)](https://github.com/TeleAI-UAGI/Awesome-Agent-Memory)
- [Agent Memory Paper List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)

### Upcoming
- **ICLR 2026 MemAgents Workshop** (April 27, Rio de Janeiro): [sites.google.com/view/memagent-iclr26](https://sites.google.com/view/memagent-iclr26/)

---

## 12. Commercial Platform Comparison

| Platform | Strengths | Weaknesses | Cost |
|----------|-----------|------------|------|
| **Mem0** | Most mature, graph memory, 80% token compression | Monthly tiers | SaaS |
| **Zep** | Best temporal reasoning, sub-100ms retrieval | Complex, expensive | Enterprise |
| **LangMem** | Free, LangGraph native | No knowledge graph, flat KV | Open source |
| **MemoClaw** | Simplest API, pay-per-use | Requires crypto wallet | Per-call |
| **Cognee** | Production-proven (70+ companies) | Heavier setup | Open source + enterprise |
| **Letta** | Self-editing memory, Context Repos | More opinionated | Open source + cloud |

---

## 13. Recommendations for oclaw_brain

Current architecture (smart_extractor.py sweep + before_agent_start hook recall + Azure AI Search hybrid + SQLite FTS5 fallback + 60% fuzzy word-overlap dedup) aligns well with 2026 best practices. Enhancement opportunities:

### 13.1 High Priority

1. **Confidence decay** -- Add `confidence_score` (0.1-1.0) and `confirmation_count`. Use FadeMem's dual-layer: long-term half-life ~11 days, short-term ~5 days. Retrieval score: `finalScore = (1-w) * semanticScore + w * exp(-ln(2)/halfLife * ageHours)`.

2. **Semantic dedup sweep** -- Current 60% word-overlap catches lexical dupes but misses semantic ones. Weekly GPT-4.1-mini sweep to catch "User prefers dark mode" vs "Dark mode is preferred theme."

3. **Typed memory decay** -- Adopt severity1's pattern: permanent (architecture, decisions, patterns, gotchas), 7-day (progress), 30-day (context).

### 13.2 Medium Priority

4. **Structured extraction schema** -- LangMem's `Fact(subject, predicate, object)` or AgentCore's XML format makes memories more queryable than free-text.

5. **Contradiction resolution** -- When new fact contradicts existing, update old confidence down and add `supersedes` link. Memoria's EWA is lightweight.

6. **Source provenance** -- Gemini's statement+rationale pattern. Even a simple `(Source: session X, date Y)` suffix helps trust and debugging.

### 13.3 Low Priority / Future

7. **Three-stage retrieval** -- Add LLM reranker as third stage after vector + FTS5 (like QMD). Reported 48% quality improvement.

8. **Cursor-based extraction** -- Track where you last read in each session file, only process new content (severity1 pattern). More efficient than re-reading entire sessions.

9. **Graph memory layer** -- Only when memory count exceeds 500+ and relationship traversal is needed. Start with Neo4j Agent-Memory or Cognee patterns.

---

## Key Sources

### Anthropic Official
- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory)
- [Memory Tool API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [Compaction API](https://platform.claude.com/docs/en/build-with-claude/compaction)

### Reverse Engineering & Analysis
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)
- [Brain Surgery on Claude Code (Tal Raviv)](https://www.talraviv.co/p/i-wanted-to-know-how-compaction-works)
- [Inside Claude Code Session Format (Yi Huang)](https://databunny.medium.com/inside-claude-code-the-session-file-format-and-how-to-inspect-it-b9998e66d56b)
- [Claude Code Auto Memory (Yuanchang)](https://yuanchang.org/en/posts/claude-code-auto-memory-and-hooks/)
- [Context Compaction Research (badlogic)](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f)
- [Analyzing Logs with DuckDB (Liam)](https://liambx.com/blog/claude-code-log-analysis-with-duckdb)

### Community Tools
- [OpenAmnesia](https://github.com/vincentkoc/openamnesia) | [CASS](https://github.com/Dicklesworthstone/coding_agent_session_search) | [QMD Sessions](https://www.williambelk.com/blog/qmd-sessions-claude-code-memory-with-qmd-20260303/) | [Ghost](https://github.com/notkurt/ghost) | [Total Recall](https://github.com/radu2lupu/total-recall) | [Severance](https://github.com/blas0/Severance) | [Mnemon](https://github.com/mnemon-dev/mnemon) | [mnemo](https://pkg.go.dev/github.com/Pilan-AI/mnemo) | [engram](https://github.com/Gentleman-Programming/engram)

### Frameworks & SDKs
- [LangMem](https://langchain-ai.github.io/langmem/) | [Mem0](https://mem0.ai) | [Zep/Graphiti](https://github.com/getzep/graphiti) | [Cognee](https://github.com/topoteretes/cognee) | [Neo4j Agent-Memory](https://github.com/neo4j-labs/agent-memory) | [Letta](https://github.com/letta-ai/letta) | [mcp-memory-service](https://github.com/doobidoo/mcp-memory-service)

### Papers
- [SimpleMem](https://arxiv.org/abs/2601.02553) | [A-Mem](https://arxiv.org/abs/2502.12110) | [TeleMem](https://arxiv.org/html/2601.06037v4) | [FadeMem](https://arxiv.org/abs/2601.18642) | [MemOS](https://arxiv.org/abs/2507.03724) | [Memoria](https://arxiv.org/abs/2512.12686) | [Zep](https://arxiv.org/abs/2501.13956) | [ChatGPT Memory RE](https://manthanguptaa.in/posts/chatgpt_memory/) | [Gemini Memory](https://www.shloked.com/writing/gemini-memory)
