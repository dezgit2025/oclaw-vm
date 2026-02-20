# AI Foundry + Microsoft Agent Framework: proactive context-window management (avoid “context rot”)

Scope: best practices inferred from:
- Microsoft Agent Framework core repo: https://github.com/microsoft/agent-framework
- Samples repo (providers, workflows, multi-agent): https://github.com/microsoft/Agent-Framework-Samples
- Multi-Agent Custom Automation Engine Solution Accelerator: https://github.com/microsoft/Multi-Agent-Custom-Automation-Engine-Solution-Accelerator/tree/main
- Agent Framework docs (memory + reducers + checkpoints):
  - Agent memory: https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-memory
  - Checkpointing: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints
  - Checkpointing tutorial: https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/checkpointing-and-resuming

## What “context rot” means (in practice)
When a multi-agent system runs for many turns, you tend to get:
- the prompt grows until it hits the context window
- old but *still-relevant* constraints get pushed out
- the agent starts contradicting earlier decisions
- different agents diverge on “what we already decided”

Agent Framework’s docs explicitly put the burden on the developer to avoid overflowing the context window when using non–in-service chat history storage (Chat Completions):
- “It is up to the implementer of ChatHistoryProvider to ensure that the size of the chat history does not exceed the context window…” https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-memory

## Key primitives in MS Agent Framework that help

### 1) Chat history reducers (short-term memory control)
The default `InMemoryChatHistoryProvider` can be configured with an `IChatReducer` to reduce history size. You can invoke reduction either **after adding a message** or **before retrieving messages for the next run**.

(see reducer trigger events) https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-memory

### 2) Context providers (long-term memory injection)
Agent Framework supports “long-term memory” via custom `AIContextProvider` components that can:
- inspect messages after a run (`InvokedAsync`)
- inject additional context before a run (`InvokingAsync`)

https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-memory

### 3) AgentSession serialization
Sessions can be serialized/deserialized so the agent can resume later *without losing state*.

https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-memory

### 4) Workflow checkpoints
Workflows support checkpoints at “superstep boundaries” and can resume/rehydrate.

https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints

## 5 best-practice suggestions (with simple diagrams)

### Suggestion 1 — Add a Token Budget Manager + reduce history at 50% and 80% thresholds
**Idea:** Don’t wait for failures. Track estimated prompt tokens. When usage hits a threshold (e.g., 50%), run a reduction strategy.

**How (Agent Framework):**
- Use `InMemoryChatHistoryProvider` + an `IChatReducer`.
- Choose reducer trigger event **BeforeMessagesRetrieval** so every run is guaranteed to fit.

**Reducer behavior (tiered):**
- <50%: no reduction
- 50–80%: drop low-value turns (tool chatter, repeated confirmations)
- >80%: compress older turns into a “running summary” + keep last N messages verbatim

Diagram:

```
Messages grow
   |
   v
[Token Estimator] ---- if > 50% ----> [Reducer tier 1]
        |               if > 80% ----> [Reducer tier 2 (summarize)]
        v
  Fit-for-model history  ----> Agent Run
```

Why this helps:
- prevents sudden “context cliff”
- keeps recent details verbatim while preserving older constraints in summary

---

### Suggestion 2 — Split memory: “conversation” ≠ “facts/decisions”; write decisions into mem0 (or any durable store)
**Idea:** The convo is a volatile transport. The durable source-of-truth is a **decision ledger**.

Pattern:
- After each meaningful step, extract:
  - decisions made
  - constraints
  - open questions
  - state variables (ids, URLs, file paths)
- Store those as structured entries in **mem0** (or Cosmos/SQL/Redis) keyed by:
  - user/project
  - workflow id
  - agent role

Then, on every run:
- inject only the *top relevant* decisions back into context (don’t replay the whole chat).

Diagram:

```
Chat Turns  ---> [Decision Extractor] ---> mem0 (facts/decisions)
     |                                        |
     |                                        v
     +---- next run ---- [Retriever: top-k] -> Inject “Decision Brief”
```

How this maps to Agent Framework:
- implement an `AIContextProvider`:
  - `InvokedAsync`: write extracted “memories” to mem0
  - `InvokingAsync`: retrieve and inject “Decision Brief”

Why this helps:
- the system doesn’t “forget” key constraints even as chat is reduced
- multi-agent teams can share a consistent state snapshot

---

### Suggestion 3 — Use workflow checkpoints + “summary state” so the workflow can rehydrate without carrying huge prompts
**Idea:** Workflows already checkpoint state at supersteps. Use that to keep LLM context smaller.

Pattern:
- At the end of each superstep:
  - checkpoint executor states
  - also persist a small **State Summary** blob (the minimal info needed to continue)
- On resume/rehydration:
  - restore state from checkpoint
  - only inject the latest summary + last N messages

Diagram:

```
Superstep N completes
   |
   +--> Checkpoint (executor state + pending messages)
   +--> State Summary (tiny)

Resume later
   |
   v
Restore checkpoint + inject summary  ---> continue workflow
```

Source for checkpoints/resume/rehydration patterns:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/checkpointing-and-resuming
- https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints

Why this helps:
- long workflows stop depending on “infinite chat history”
- crash recovery + human-in-the-loop become natural points to compress context

---

### Suggestion 4 — Multi-agent: enforce per-agent context budgets + shared “canonical state”
**Idea:** In multi-agent orchestration, context rot often comes from agents drifting apart.

Pattern:
- Give each agent:
  - a small local history window (e.g., last 10–20 turns)
  - a strict token budget
- Maintain a shared **canonical state object** (JSON) that every agent reads/writes:
  - plan
  - tasks
  - decisions
  - artifacts

Diagram:

```
Agent A context  ─┐
Agent B context  ─┼─> Shared Canonical State (JSON) <─┬─ Agent C context
Agent D context  ─┘                                  └─ mem0 backing store
```

Implementation hooks:
- canonical state stored in DB (Cosmos in the solution accelerator) or mem0
- agents use context provider to inject only:
  - the canonical state
  - their relevant slice

Why this helps:
- agents converge on the same “truth” even if individual chat histories get reduced

---

### Suggestion 5 — Prefer retrieval over replay: store artifacts externally and reference them (RAG/file search) instead of pasting
**Idea:** Don’t paste entire docs/logs into context. Store them externally and pull only excerpts.

In these repos/samples, “RAG” and “File search” patterns show up as first-class sample areas (Samples repo sections for RAG/file search). https://github.com/microsoft/Agent-Framework-Samples

Pattern:
- Put large content in:
  - file search index / vector store
  - blob storage
  - database
- Inject into the prompt only:
  - citations
  - short excerpts
  - IDs/handles to retrieve more if needed

Diagram:

```
Large docs/logs
   |
   v
Vector store / file search
   |
   v
Top-k excerpts + citations  ---> Agent run
```

Why this helps:
- context window stays stable
- you can re-fetch the right slice when needed
- reduces prompt injection surface (less raw untrusted text pasted)

---

## Questions (so we can design this “for real”)
1) Which runtime are you targeting?
   - .NET Agent Framework, Python Agent Framework, or both?
2) Are you using **Foundry Persistent Agents** (in-service history) or classic Chat Completions where we manage history ourselves?
   - If persistent agents: you can’t swap in ChatHistoryProvider easily; you focus more on “decision ledger” + external state + tools.
3) Where do you want durable memory to live?
   - mem0 (preferred?), Cosmos DB (like the solution accelerator), Postgres, Redis, files?
4) What’s your failure mode tolerance?
   - Is it acceptable to occasionally lose a nuance, as long as decisions/constraints are stable?
5) What is your token budget policy?
   - Per-agent budgets? A global workflow budget? Hard cutoff vs degrade-to-summary?

## Bottom line
- Agent Framework already gives you the right extension points: reducers (short-term), context providers (long-term), session serialization, and workflow checkpointing.
- The “proactive” part is adding **token-budget thresholds** + a **decision ledger** (mem0) so the system stabilizes decisions before the context window gets dangerous.
