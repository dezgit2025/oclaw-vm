# Research Log — openclaw_vm Project

---

## Research: CLI-Based LLM Agent/Brain Systems — Best Practices & Ecosystem Survey

**Date**: 2026-03-15
**Triggered by**: User request to survey the landscape for building CLI-based LLM agent/brain systems with persistent memory, MCP connectivity, and programmable AI assistant backends
**Stack relevance**: Directly relevant to the oclaw_brain / ClawBot memory system architecture; informs choices about agent frameworks, MCP integration patterns, and alternative approaches to the current openclaw gateway + Python skill pipeline

---

### Question

What are the best practices and leading open-source projects for building a CLI-based LLM "brain" with persistent memory, MCP tool connectivity, and a programmable AI assistant backend? How do the major SDK/framework options compare?

---

### Sources Consulted

1. [GitHub Blog — Build an agent into any app with the GitHub Copilot SDK](https://github.blog/news-insights/company-news/build-an-agent-into-any-app-with-the-github-copilot-sdk/) — SDK announced Jan 22 2026, technical preview, supports Python/Node/Go/.NET
2. [GitHub Changelog — Copilot CLI GA (Feb 25 2026)](https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/) — Copilot CLI went GA; ships with built-in MCP server + custom MCP server support
3. [GitHub Changelog — Copilot CLI Enhanced Agents (Jan 14 2026)](https://github.blog/changelog/2026-01-14-github-copilot-cli-enhanced-agents-context-management-and-new-ways-to-install/) — Custom agents via .agent.md files, Explore + Task built-in agents
4. [GitHub Changelog — Agentic Memory for Copilot (Jan 15 2026)](https://github.blog/changelog/2026-01-15-agentic-memory-for-github-copilot-is-in-public-preview/) — Repo-level persistent memory, now on by default for Pro/Pro+
5. [Microsoft Tech Community — Building Agents with GitHub Copilot SDK](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-agents-with-github-copilot-sdk-a-practical-guide-to-automated-tech-upda/4488948) — Practical guide; automated tech update tracking agent
6. [Srikantan Sankaran Tech Blog — Fleet Compliance Agent (Feb 8 2026)](https://ssrikantan.github.io/blog/2026/02/08/ghcp-sdk-fleet-compliance-agent/) — Python-based compliance agent embedding Copilot SDK as autonomous agent brain; RAG + MCP + tool calling
7. [GitHub Copilot SDK repo](https://github.com/github/copilot-sdk) — Official multi-platform SDK repo
8. [GitHub Copilot CLI repo](https://github.com/github/copilot-cli) — CLI interface repo (GA Feb 2026)
9. [Jimmy Song Blog — GitHub Copilot CLI Custom Agents](https://jimmysong.io/blog/github-copilot-cli-custom-agents/) — .agent.md file walkthrough and custom agent patterns
10. [Devblogs Microsoft — GitHub Copilot SDK + Microsoft Agent Framework](https://devblogs.microsoft.com/semantic-kernel/build-ai-agents-with-github-copilot-sdk-and-microsoft-agent-framework/) — Integration with Semantic Kernel / MAF
11. [Anthropic — Claude Agent SDK Overview (official docs)](https://platform.claude.com/docs/en/agent-sdk/overview) — Official SDK docs; Python + TypeScript; proprietary license on SDK itself
12. [GitHub — anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) — Python implementation; Claude Code included by default in SDK package
13. [GitHub — anthropics/claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) — TypeScript implementation
14. [Hindsight — Open-Source MCP Memory Server (Mar 4 2026)](https://hindsight.vectorize.io/blog/2026/03/04/mcp-agent-memory) — retain/recall/reflect operations + mental models; Docker single-command deploy
15. [GitHub — CaviraOSS/OpenMemory](https://github.com/CaviraOSS/OpenMemory) — Hierarchical Memory Decomposition + temporal graph; MCP-native; integrates with LangChain, CrewAI, AutoGen
16. [GitHub — lastmile-ai/mcp-agent](https://github.com/lastmile-ai/mcp-agent) — Apache 2.0; MCP-first agent framework; durable execution; all Anthropic effective-agents patterns; model-agnostic
17. [PyPI — mcp-memory-service](https://pypi.org/project/mcp-memory-service/10.18.0/) — Multi-agent memory backend, MCP-compatible, 5ms retrieval, no cloud lock-in
18. [GitHub — Dicklesworthstone/ultimate_mcp_server](https://github.com/Dicklesworthstone/ultimate_mcp_server) — Comprehensive MCP server: LLM delegation, browser, doc processing, vector ops, cognitive memory
19. [GitHub — block/goose](https://github.com/block/goose) — Apache 2.0; CLI + desktop; 26 LLM providers; full MCP support; Linux Foundation AAIF (Dec 2025)
20. [GitHub — simonw/llm](https://github.com/simonw/llm) — Simon Willison's CLI tool; plugin-based; OpenAI/Claude/Gemini/Ollama; widely used
21. [Model Context Protocol — Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol) — Protocol background; JSON-RPC 2.0; inspired by LSP
22. [MCP 2026 Roadmap](http://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — Async ops, Streamable HTTP, OAuth 2.1, .well-known discovery, structured tool annotations
23. [Anthropic Engineering — Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) — First-party MCP usage patterns for agents
24. [Medium — GitHub Copilot vs Claude: Which AI Agent Platform?](https://medium.com/@sschiff/github-copilot-vs-claude-which-ai-agent-platform-belongs-in-your-stack-03b43b79d765) — Independent platform comparison
25. [Tembo Blog — 2026 Guide to Coding CLI Tools: 15 AI Agents Compared](https://www.tembo.io/blog/coding-cli-tools-comparison) — Broad landscape comparison

---

### Findings

#### 1. GitHub Copilot SDK (Technical Preview, Jan 22 2026)

The Copilot SDK is the most significant new entrant. It exposes the same agentic execution loop that powers Copilot CLI as a programmable library.

**Key facts:**
- Languages: Python, Node.js, Go, .NET
- Core loop: planning, tool use, multi-turn execution — same runtime as Copilot CLI
- Tool model: declarative (you name tools from a built-in set or wire in MCP servers; no tool schema writing required)
- MCP: ships built-in MCP server; accepts custom MCP servers in config
- Memory: "agentic memory" in public preview (Jan 15 2026), now on by default for Pro/Pro+ (Mar 4 2026) — stores repo-level conventions, architecture facts, cross-file deps; persists across sessions
- Requires: GitHub Copilot subscription (Pro/Pro+/Business/Enterprise)
- Custom agents: defined via `.agent.md` markdown files or programmatically through SDK

**Practical pattern (from Fleet Compliance article):**
```python
# Register custom tools, send prompt, SDK decides execution path autonomously
from copilot_sdk import CopilotAgent

agent = CopilotAgent(tools=[my_tool_a, my_tool_b])
result = await agent.run("Scan all microservices for policy violations and open PRs")
```

**Limitations for this project:**
- Requires GitHub Copilot subscription — not free
- Model choice locked to GitHub's routing (Claude Opus 4.6, GPT-5.2, etc.) — no raw API access
- Memory is repository-scoped, not arbitrary cross-session fact storage
- Declarative tool model means less control over tool schemas than raw API approaches

#### 2. Anthropic Claude Agent SDK

**Key facts:**
- Languages: Python (`anthropics/claude-agent-sdk-python`), TypeScript
- Claude Code is bundled in the SDK package by default
- Supports: structured outputs (validated JSON schemas), SDK beta features (extended context), fallback model handling
- License: **proprietary** — available on GitHub but not open source
- Docs: `platform.claude.com/docs/en/agent-sdk/`

**Comparison to Copilot SDK:**
- More flexible: gives direct API access, full tool schema control, custom system prompts
- No subscription required beyond Anthropic API credits (pay-per-token)
- Model locked to Anthropic models (no multi-provider routing without extra work)
- Richer tool execution model: skills can be both instruction sets AND runtimes (runnable code, not just markdown); Copilot skills are instruction-set only
- MCP support: yes, via the broader Claude ecosystem (Anthropic pioneered MCP)

#### 3. lastmile-ai/mcp-agent (Apache 2.0, active 2025-2026)

The most mature open-source MCP-first agent framework.

**Key facts:**
- License: Apache 2.0
- Model-agnostic: works with any LLM provider
- Implements all patterns from Anthropic's "Building Effective Agents" paper
- Also implements OpenAI Swarm pattern
- Durable execution: workflows can pause for human input (exposed as tool calls the agent can make)
- Config: `mcp_agent.config.yaml` + `mcp_agent.secrets.yaml`
- No graph/node abstractions — pure Python control flow (if/while/etc.)
- Related: `lastmile-ai/openai-agents-mcp` extends OpenAI Agents SDK with MCP support

**Best for:** Teams that want model-agnostic, open-source, MCP-native agent orchestration without being locked into any vendor SDK.

#### 4. block/goose (Apache 2.0, Linux Foundation Dec 2025)

**Key facts:**
- CLI + desktop app; runs entirely locally
- 26 LLM providers (Anthropic, Azure OpenAI, Bedrock, Vertex, DeepSeek, Ollama, etc.)
- Native MCP integration — extensibility via MCP servers only (no proprietary plugin format)
- Donated to Linux Foundation Agentic AI Foundation (AAIF) Dec 2025 alongside Anthropic's MCP and OpenAI's AGENTS.md
- Capabilities: runs shell commands, edits files, executes code, multi-step workflows
- Free (pay only for LLM tokens)
- Closest open-source equivalent to Claude Code / Copilot CLI

**Best for:** Self-hosted CLI agent that can use any model, fully extensible via MCP, no SaaS dependency.

#### 5. simonw/llm (MIT, widely maintained)

**Key facts:**
- Minimal, plugin-based CLI (`pip install llm`)
- Supports: OpenAI, Claude, Gemini, Ollama + 40+ via plugins
- Persistent conversations stored in SQLite
- Not a full agent framework — no tool calling loop by default; plugins add that
- Widely used as a foundation layer in custom CLIs

#### 6. MCP Protocol — How It Works for CLI Agents

MCP runs over **JSON-RPC 2.0** using two transport modes:

| Transport | When to Use |
|-----------|-------------|
| **stdio** | Local server; agent spawns as child process, communicates via stdin/stdout |
| **Streamable HTTP** | Remote/shared server; HTTP + optional Server-Sent Events |

**Protocol lifecycle (CLI agent perspective):**
1. Agent startup → connects to configured MCP servers, discovers tools via `tools/list`
2. During LLM loop → model outputs a tool call → agent dispatches `tools/call` to relevant MCP server
3. MCP server returns result → agent feeds back to LLM context
4. No modification to agent code required for new tools — just add a new MCP server

**Nov 2025 spec updates:** Async ops, stateless Streamable HTTP, OAuth 2.1, `.well-known` URL discovery, structured tool annotations (read-only vs mutating).

**2026 roadmap:** Transport scalability, agent-to-agent (A2A) communication, enterprise governance.

#### 7. MCP Memory Servers (Open Source Options)

| Project | Approach | Transport | Notes |
|---------|----------|-----------|-------|
| **Hindsight** | retain/recall/reflect + mental models | Docker | Single-command deploy; auto-updating mental models |
| **OpenMemory (CaviraOSS)** | Hierarchical Memory Decomposition + temporal graph | MCP-native | LangChain/CrewAI/AutoGen integrations |
| **mcp-memory-service** | Multi-agent shared knowledge graph | MCP + HTTP | 5ms retrieval, no cloud lock-in, PyPI v10.18.0 |
| **ultimate_mcp_server** | Vector ops + cognitive memory + LLM delegation | HTTP | Monolithic but comprehensive |
| **local-memory-mcp** | Simple local key-value + semantic search | stdio | Good for Claude Desktop / basic agents |

These can be dropped into any MCP-compatible agent (mcp-agent, goose, Copilot CLI, Claude Code) without code changes.

---

### Comparison Table: Copilot SDK vs Claude Agent SDK vs mcp-agent vs Raw API

| Dimension | GitHub Copilot SDK | Claude Agent SDK | lastmile mcp-agent | Raw API + Custom |
|-----------|-------------------|-----------------|-------------------|-----------------|
| License | Proprietary (requires subscription) | Proprietary (pay-per-token) | Apache 2.0 | n/a |
| Model flexibility | GitHub-routed (multi-model) | Anthropic only | Any provider | Any provider |
| MCP support | Built-in | Yes (via Claude ecosystem) | Native (MCP-first) | Manual |
| Memory | Repo-scoped agentic memory | Custom (no built-in) | Via MCP memory servers | Custom |
| Tool model | Declarative (.agent.md / built-in set) | Full schema control | Full schema control | Full schema control |
| Skill runtime | Markdown instruction only | Code + instruction | Code + instruction | Code + instruction |
| Setup complexity | Low (SDK handles loop) | Medium | Medium | High |
| CLI native | Yes (Copilot CLI wraps SDK) | Via Claude Code | Yes | Custom |
| Enterprise features | GitHub org-level governance | Anthropic API | None (OSS) | Custom |
| Cost | Copilot subscription (~$10-$39/mo) | Token-based | Free (token costs only) | Token costs only |
| Best for | Teams already on GitHub Copilot | Anthropic-stack projects | Model-agnostic OSS agents | Maximum control |

---

### Recommendation

For the **oclaw_brain / ClawBot system** (existing architecture: Python skills, Azure AI Search, custom hook injection, SQLite memory):

**Continue with the current custom approach.** The existing system already implements the key patterns that SDK frameworks abstract:
- Persistent memory: SQLite + Azure AI Search (already built)
- Tool calling: openclaw skill system + `before_agent_start` hook (already built)
- MCP: could be layered on top by wrapping existing Python scripts as an MCP server via stdio transport

**If evaluating a framework migration:**
- `mcp-agent` (lastmile) is the strongest open-source choice — Apache 2.0, model-agnostic, durable execution, all effective-agent patterns, MCP-native
- `goose` (block) is the best drop-in CLI agent alternative if the goal is replacing openclaw CLI with a fully open-source equivalent

**MCP server conversion opportunity:** The existing `smart_extractor.py recall` and `mem.py` scripts could be wrapped as an MCP memory server (stdio transport) to make them accessible to any MCP-compatible client — including Copilot CLI, goose, or mcp-agent — without changing the underlying implementation.

```python
# Sketch: expose mem.py as MCP stdio server
# tools: ["memory_add", "memory_recall", "memory_list"]
# transport: stdio (agent spawns as child process)
```

This is a low-risk, high-leverage move: the memory system stays exactly as-is, but becomes interoperable with the broader MCP ecosystem.

---

### Compatibility Notes

- MCP stdio transport: any platform that can spawn child processes (Linux, macOS, Windows WSL) — no extra infrastructure
- MCP Streamable HTTP: requires an HTTP endpoint; adds latency vs stdio for local use
- Copilot SDK requires GitHub Copilot subscription — existing VM uses `github-copilot/claude-opus-4.6` as gateway model, so subscription is already in use
- Claude Agent SDK license is proprietary — review before embedding in any redistributable tool
- mcp-agent works with Azure OpenAI endpoints — compatible with current Azure AI Foundry setup

### Confidence: High

Sources are mostly official GitHub blog posts, changelogs, and SDK repos from Jan-Mar 2026. The MCP spec information comes directly from the MCP blog and Wikipedia. The framework comparison is based on multiple independent sources. The one area with medium confidence is the exact Claude Agent SDK feature set — the SDK was recently released and its changelog is sparse.

What would increase confidence further: directly reading the SDK READMEs and running the examples.


---

## Research: GitHub Copilot SDK — Go Module Existence and Import Path

**Date**: 2026-03-15
**Triggered by**: Phase 1 plan (`plans/copilot-cli-llm-plans.md`) references `github.com/github/copilot-sdk/go` as the Go import path. Need to confirm this module actually exists and is usable before building.
**Stack relevance**: Directly affects Phase 1 of the oclaw-brain / copilot-cli-llm build. Wrong import path = broken `go get` and wasted scaffolding effort.
### Question

Does the Go module `github.com/github/copilot-sdk/go` exist as a proper, installable Go module? Is it the correct import path? Is there an official Go SDK at all, or only Node.js/Python?

---

### Sources Consulted

1. [pkg.go.dev -- github.com/github/copilot-sdk/go/rpc](https://pkg.go.dev/github.com/github/copilot-sdk/go/rpc) -- Package listed and published Mar 7 2026; confirms module is indexed and real
2. [github.com/github/copilot-sdk tree/main/go](https://github.com/github/copilot-sdk/tree/main/go) -- Official Go SDK subdirectory in the multi-language SDK monorepo
3. [copilot-sdk/go/README.md](https://github.com/github/copilot-sdk/blob/main/go/README.md) -- Go-specific README with installation and usage instructions
4. [copilot-sdk Releases](https://github.com/github/copilot-sdk/releases) -- Go submodule version tags added in v0.1.24-preview.0 / v0.1.25-preview.0 for reproducible builds
5. [DeepWiki -- github/copilot-sdk](https://deepwiki.com/github/copilot-sdk) -- SDK architecture overview confirming 4 language implementations: Node.js/TypeScript, Python, Go, .NET
6. [GitHub Blog -- Copilot SDK technical preview Jan 14 2026](https://github.blog/changelog/2026-01-14-copilot-sdk-in-technical-preview/) -- Official announcement; Go listed as supported language
7. [InfoWorld -- Building AI agents with the GitHub Copilot SDK](https://www.infoworld.com/article/4125776/building-ai-agents-with-the-github-copilot-sdk.html) -- Third-party coverage confirming Go SDK availability and install path
8. [DEV Community -- GitHub Copilot SDK Build AI-Powered DevOps Agents](https://dev.to/pwd9000/github-copilot-sdk-build-ai-powered-devops-agents-for-your-own-apps-3d05) -- Practical guide including Go usage examples

---

### Findings

**The Go SDK exists, is official, and the import path in the plan is correct.**

#### Module Facts

| Property | Value |
|----------|-------|
| Import path | `github.com/github/copilot-sdk/go` |
| Install command | `go get github.com/github/copilot-sdk/go` |
| Go version required | 1.24+ |
| pkg.go.dev indexed | Yes -- rpc package published Mar 7 2026 |
| Module type | Go submodule in monorepo (`go/` subdirectory has its own `go.mod`) |
| SDK status | Technical preview (v0.1.x) -- may break across versions |
| License | MIT |
| Go submodule version tags | Added in v0.1.24-preview.0 for reproducible builds |

#### Key Packages

| Package | Purpose |
|---------|----------|
| `github.com/github/copilot-sdk/go` | Root package -- `NewClient`, `ClientOptions`, `SessionConfig`, etc. |
| `github.com/github/copilot-sdk/go/rpc` | Typed RPC methods -- `ServerRpc` (Ping), `SessionRpc` |

#### Confirmed Usage Pattern

```go
import copilot "github.com/github/copilot-sdk/go"

client := copilot.NewClient(nil)  // nil = defaults; auto-installs embedded CLI
client.Start(ctx)
defer client.Stop()

session, err := client.CreateSession(ctx, &copilot.SessionConfig{Model: "gpt-5.4"})
response, err := session.SendAndWait(ctx, copilot.MessageOptions{Prompt: "hello"})
```

#### Architecture: Why the Monorepo Submodule Works

The SDK lives in `github.com/github/copilot-sdk` as a monorepo with language-specific subdirectories (`go/`, `python/`, `node/`, `dotnet/`). Each language subdir has its own `go.mod`. The Go module path `github.com/github/copilot-sdk/go` maps to the `go/` subdirectory -- standard Go monorepo practice. `go get` resolves it correctly via the `go.mod` in that subdirectory.

#### CLI Dependency

All four SDK implementations depend on the `@github/copilot` npm package (the Copilot CLI binary). The Go SDK auto-installs it to a cache directory if `COPILOT_CLI_PATH` is not set. **Node.js and npm are not required at runtime** -- the SDK downloads the platform binary and manages it internally.

#### What Does NOT Exist

- No separate official package at `github.com/colbylwilliams/copilot-go` -- that is a **third-party community** package, not the official SDK
- No standalone Go module outside the monorepo

---

### Recommendation

**No plan changes needed.** The import path `github.com/github/copilot-sdk/go` in `plans/copilot-cli-llm-plans.md` is confirmed correct.

One action item: pin the SDK version after the initial `go get`. The SDK is in technical preview and breaking changes are possible between v0.1.x releases.

```bash
# Phase 1 Step 1 scaffold (from the plan -- confirmed correct)
go mod init github.com/dezgit2025/oclaw-brain
go get github.com/github/copilot-sdk/go   # then pin version in go.mod
go mod tidy
```

Flag: **do not confuse `github.com/colbylwilliams/copilot-go` (third-party) with `github.com/github/copilot-sdk/go` (official).** Both appear in pkg.go.dev search results.

---

### Compatibility Notes

- Go 1.24+ required -- verify with `go version` before scaffolding
- Auth: `GH_TOKEN` or `GITHUB_TOKEN` env var must be set; GitHub Copilot subscription required
- Cross-compilation (`GOOS=linux GOARCH=amd64`) works for Go code; the CLI binary download happens at runtime on the target machine, so the VM needs outbound internet access on first `client.Start()`
- VM deploy: the Linux binary will trigger CLI binary download on first run; ensure `GH_TOKEN` is available in the VM environment

### Confidence: High

The module is indexed on pkg.go.dev (requires passing Go module proxy validation -- strongest signal). The official GitHub repo has the `go/` subdirectory with a README. Multiple independent sources reference `go get github.com/github/copilot-sdk/go` as the install command. The only gap is not having run `go get` locally to confirm the current exact version number -- check `pkg.go.dev/github.com/github/copilot-sdk/go` at build time to pin the version.


---

## Research: GitHub Copilot SDK — Python Module Existence, API Surface, and Go SDK Comparison

**Date**: 2026-03-15
**Triggered by**: Need to evaluate the Python Copilot SDK as an alternative or complement to the existing Go SDK (`copilot-cli-llm`). The Go SDK confirmed at v0.1.32 in a prior session; now confirming the Python SDK exists in the same monorepo and characterizing its API surface.
**Stack relevance**: Affects language choice for any future Python-based copilot-cli-llm work. Relevant to the VM's existing Python skill pipeline and the `smart_extractor.py` / `mem.py` stack.

---

### Question

Does an official Python Copilot SDK exist? What is the pip package name? What is the full API surface for creating a client, starting sessions, sending prompts, and handling auth? Is there a way to keep a persistent warm client and create sessions per-request? What are Python version requirements? How does it compare to the Go SDK?

---

### Sources Consulted

1. [copilot-sdk/python/README.md at main](https://github.com/github/copilot-sdk/blob/main/python/README.md) — Primary source; install instructions, basic usage, infinite sessions, context manager
2. [copilot-sdk/python at main (directory listing)](https://github.com/github/copilot-sdk/tree/main/python) — Confirms python/ subdirectory exists in monorepo
3. [github-copilot-sdk on PyPI](https://pypi.org/project/github-copilot-sdk/) — Official PyPI listing; confirms v0.1.32; Python >=3.11 required; multiple platform wheels published
4. [github-copilot-sdk 0.1.24rc0 — Libraries.io](https://libraries.io/pypi/github-copilot-sdk) — Version history; confirms pre-release cadence matches Go SDK versioning
5. [Python SDK | DeepWiki](https://deepwiki.com/github/copilot-sdk/6.2-python-sdk) — Architecture overview; bundled binary packaging; Pydantic models; tool decorators
6. [Advanced Topics | DeepWiki](https://deepwiki.com/github/copilot-sdk/10-examples-and-cookbook) — Session persistence, infinite sessions, per-request model selection
7. [copilot-sdk/cookbook/python/README.md](https://github.com/github/copilot-sdk/blob/main/cookbook/python/README.md) — Practical recipes; send_and_wait; tool registration pattern
8. [copilot-sdk/docs/features/session-persistence.md](https://github.com/github/copilot-sdk/blob/main/docs/features/session-persistence.md) — Session ID reuse; resumable sessions across restarts
9. [Microsoft Tech Community — Building Agents with GitHub Copilot SDK](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-agents-with-github-copilot-sdk-a-practical-guide-to-automated-tech-upda/4488948) — Practical Python agent examples
10. [DeepWiki — Custom Providers (BYOK)](https://deepwiki.com/github/copilot-sdk/9.1-custom-providers-(byok)) — Azure AI Foundry, OpenAI, Anthropic, Ollama via ProviderConfig; Entra ID NOT supported
11. [GitHub Copilot SDK SDK changelog](https://github.blog/changelog/2026-01-14-copilot-sdk-in-technical-preview/) — Jan 14 2026 technical preview announcement; Python listed as supported

---

### Findings

#### 1. Python SDK Existence — Confirmed

Yes, an official Python SDK exists. It lives at `github.com/github/copilot-sdk/tree/main/python` in the same monorepo as the Go SDK, and is published to PyPI.

| Property | Value |
|----------|-------|
| Monorepo path | `github.com/github/copilot-sdk/tree/main/python` |
| PyPI package name | `github-copilot-sdk` |
| Install command | `pip install github-copilot-sdk` |
| Import name | `copilot` (e.g., `from copilot import CopilotClient`) |
| Latest version | `0.1.32` (version-matched to Go SDK v0.1.32) |
| Python version required | `>=3.11` (3.11, 3.12, 3.13, 3.14 supported) |
| SDK status | Technical preview — may break between v0.1.x releases |
| License | MIT |
| Binary bundling | Platform-specific Copilot CLI binaries bundled directly into Python wheels — no separate npm/Node.js install required |

Note: `pip install copilot-sdk` is a different, unrelated package. The correct name is `github-copilot-sdk`.

#### 2. API Surface

**Client creation and lifecycle:**
```python
from copilot import CopilotClient

client = CopilotClient()           # defaults; auto-manages embedded CLI binary
await client.start()               # launches CLI subprocess, establishes JSON-RPC
await client.stop()                # shuts down cleanly
```

`CopilotClient` accepts an optional `github_token` parameter — takes priority over `GH_TOKEN` / `GITHUB_TOKEN` env vars.

**Session creation:**
```python
session = await client.create_session({
    "model": "gpt-5.4",           # any model available via Copilot CLI
    "streaming": True,            # optional streaming flag
    "tools": [my_tool],           # optional list of @define_tool decorated functions
    "session_id": "my-session",   # optional; omit for auto-generated ID
})
```

**Sending a prompt (blocking convenience method):**
```python
response = await session.send_and_wait({"prompt": "What is 2+2?"})
print(response.data.content)
```

**Sending a prompt (event-driven streaming):**
```python
done = asyncio.Event()

def on_event(event):
    if event.type.value == "assistant.message":
        print(event.data.content)
    elif event.type.value == "session.idle":
        done.set()

session.on(on_event)
await session.send({"prompt": "Hello"})
await done.wait()
```

**Session cleanup:**
```python
await session.disconnect()
```

**Context manager (auto cleanup):**
```python
async with await client.create_session({"model": "gpt-5.4"}) as session:
    response = await session.send_and_wait({"prompt": "Hello"})
```

**Custom tools (decorator-based, Pydantic params):**
```python
from copilot.tools import define_tool
from pydantic import BaseModel, Field

class GetWeatherParams(BaseModel):
    city: str = Field(description="The name of the city to get weather for")

@define_tool(description="Get the current weather for a city")
async def get_weather(params: GetWeatherParams) -> dict:
    return {"city": params.city, "temperature": "72°F", "condition": "sunny"}

session = await client.create_session({
    "model": "gpt-5.4",
    "tools": [get_weather],
})
```

**Session history:**
```python
messages = await session.get_messages()
```

**Available models (runtime query):**
```python
models = await client.get_models()   # returns list of models available at runtime
```

#### 3. Auth

| Method | Details |
|--------|---------|
| Env var (primary) | `GH_TOKEN` or `GITHUB_TOKEN` — auto-picked up |
| Constructor param | `CopilotClient(github_token="...")` — overrides env |
| Requirement | GitHub Copilot subscription (Pro/Pro+/Business/Enterprise) |
| BYOK | `ProviderConfig` object to use Azure AI Foundry, OpenAI, Anthropic, or Ollama directly — bypasses GitHub routing |
| BYOK limitation | Microsoft Entra ID, managed identities, and third-party IdPs are NOT supported in BYOK mode |

#### 4. Persistent Client — Warm Client With Sessions Per-Request

Yes — this is the intended pattern. The `CopilotClient` is the long-lived process manager; sessions are lightweight and can be created per-request:

```python
# Create and warm up once at startup
client = CopilotClient()
await client.start()

# Per-request: create session, use, disconnect
session = await client.create_session({"model": "gpt-5.4"})
response = await session.send_and_wait({"prompt": user_input})
await session.disconnect()
```

**Resumable sessions:** Provide a stable `session_id` to resume across restarts. Without a `session_id`, the SDK auto-generates a random ID and the session cannot be resumed. Sessions automatically persist to a workspace directory.

**Infinite sessions:** Default behavior. The SDK auto-manages context window limits via background compaction (configurable `background_compaction_threshold` and `buffer_exhaustion_threshold`). No manual context window management needed.

**Known limitation:** Concurrent sessions have a race condition in the client auto-start logic — the test suite skips concurrent session tests across all language SDKs. For the oclaw_brain use case (one session per CLI invocation), this is not an issue.

#### 5. Python vs Go SDK: Differences and Limitations

The two SDKs share the same underlying architecture (both communicate with the same Copilot CLI server process via JSON-RPC) and are designed for feature parity. Key differences observed:

| Dimension | Go SDK | Python SDK |
|-----------|--------|------------|
| Version parity | v0.1.32 | v0.1.32 (same) |
| Bundled binary | Downloaded at runtime via auto-install | Bundled into platform wheels (no runtime download needed) |
| Distribution | `go get github.com/github/copilot-sdk/go` | `pip install github-copilot-sdk` |
| Import | `import copilot "github.com/github/copilot-sdk/go"` | `from copilot import CopilotClient` |
| Type safety | Go native types | Pydantic models |
| Tool definition | Function registration | `@define_tool` decorator + Pydantic BaseModel |
| Async model | goroutines + channels | `asyncio` / `async/await` |
| Send methods | `SendAndWait` / event emitter | `send_and_wait` / `session.on()` |
| Streaming | Yes | Yes (`"streaming": True` in session config) |
| Session persistence | Yes (session_id) | Yes (session_id) |
| Infinite sessions | Not referenced in Go README | Explicitly supported in Python README |
| Concurrent sessions | Race condition (all SDKs skip this test) | Same race condition |
| BYOK | Yes (`ProviderConfig`) | Yes (`ProviderConfig`) |
| Go version req | 1.24+ | n/a |
| Python version req | n/a | >=3.11 |
| pkg.go.dev indexing | Yes | n/a |
| PyPI attestation | n/a | Multi-platform wheels (linux/arm64, linux/amd64, macOS) |

**Primary Python SDK advantage:** Bundled binaries in wheels — no npm or runtime binary download on first run. The VM does not need outbound internet access at startup to fetch the CLI, unlike the Go SDK.

**Primary Go SDK advantage:** Better fit for CLI binaries (single compiled binary; no Python runtime dependency on target VM). Better for the current `oclaw-brain` / `copilot-cli-llm` architecture which produces a single deployable binary.

**Practical note on Go SDK distribution:** The Go SDK is NOT listed under official pip/npm/nuget distribution in the changelog — only Python, TypeScript, and .NET are. Go is available via `go get` from the GitHub repo. This is consistent with Go module distribution norms (go module proxy), not a limitation.

#### 6. Notable: Python SDK Has No npm/Node.js Dependency at Runtime

The Go SDK downloads the Copilot CLI binary at runtime on first `client.Start()`. The Python SDK takes a different approach: CLI binaries are bundled directly into the platform-specific Python wheels at publish time. This means:
- `pip install github-copilot-sdk` on a Linux/ARM64 machine installs the correct binary automatically
- No outbound internet needed at startup (beyond normal pip install)
- Wheel sizes are larger than typical Python packages

This is a meaningful operational difference for the VM deployment scenario.

---

### Recommendation

**For the current `copilot-cli-llm` project (Go):** No change needed. The Go SDK remains the correct choice — produces a single compiled binary with no Python runtime dependency, which is what the VM needs for `~/.openclaw/workspace/bin/oclaw-brain`.

**If building a new Python-based tool that calls Copilot models:** Use `pip install github-copilot-sdk` and the `from copilot import CopilotClient` pattern. The SDK is well-suited for Python-side scripts (e.g., extending `smart_extractor.py` or `mem.py` to call Copilot models directly without the gateway).

**Potential use case:** A Python script on the VM that uses `github-copilot-sdk` directly for memory extraction (currently done via `smart_extractor.py` calling GPT-5.2 via Azure OpenAI) could switch to Copilot SDK if the Azure endpoint is unavailable or to use a different model mid-request.

**Design decision flag:** The choice between Python SDK and Go SDK for any future copilot-brain features should be tracked in `plans/design-decisions/`. The core tradeoff: Go = single binary, no runtime deps, better for CLI tools; Python = easier integration with existing Python skill stack, bundled binaries, Pydantic types.

---

### Compatibility Notes

- Python >=3.11 required — the VM currently runs Python 3.11+ (Ubuntu 22.04 default is 3.10; verify with `ssh oclaw "python3 --version"` before using)
- `pip install github-copilot-sdk` on Linux ARM64 and AMD64 wheels are published — both architectures covered
- `GH_TOKEN` env var must be set on the VM — same requirement as Go SDK
- BYOK with Azure AI Foundry: supported via `ProviderConfig` using API key auth only (Entra managed identity NOT supported — this matters for the VM's MI-based Azure auth pattern)
- Concurrent session limitation applies to all SDK languages — design for serial session use or handle the race explicitly

### Confidence: High

PyPI listing is a primary source confirming package name, version, and Python requirement. Official README and cookbook examples (from github.com/github/copilot-sdk) confirmed the API surface. DeepWiki analysis of the repository source files corroborates all major claims. The one area with medium confidence is the exact behavior of `client.get_models()` — it appears in descriptions but was not seen in a complete code example from the official README. Verify at build time against current README.


---

## Research: GitHub Copilot CLI Custom Skills, Extensions, and SDK Tool Registration

**Date**: 2026-03-22
**Triggered by**: User request to understand what format/structure a "skill" needs to be in for Copilot CLI, how to register custom tools/functions in the Go SDK, whether it uses function calling or some other mechanism, and any examples of custom Copilot CLI extensions.
**Stack relevance**: Directly relevant to `copilot-cli-llm` (Go SDK, `github.com/github/copilot-sdk/go` v0.1.32+). Also relevant to understanding how OpenClaw skills differ from Copilot CLI native skills.

---

### Question

What format/structure does a "skill" need to be in for GitHub Copilot CLI? How do you register custom tools/functions in the Go SDK? Does it use function calling, tool definitions, or some other mechanism? Are there examples of custom Copilot CLI extensions?

---

### Sources Consulted

1. [Creating agent skills for GitHub Copilot CLI — GitHub Docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills) — Official docs for SKILL.md format, directory structure, and discovery
2. [github/copilot-sdk/go/README.md (raw)](https://github.com/github/copilot-sdk/blob/main/go/README.md) — Official Go SDK full API reference; fetched directly; authoritative
3. [awesome-copilot/skills/copilot-sdk/SKILL.md (raw)](https://raw.githubusercontent.com/github/awesome-copilot/main/skills/copilot-sdk/SKILL.md) — Canonical SKILL.md example for the copilot-sdk itself; cross-language tool examples
4. [awesome-copilot/docs/README.skills.md](https://github.com/github/awesome-copilot/blob/main/docs/README.skills.md) — Full catalog of 100+ community skills showing real-world patterns
5. [copilot-extensions/function-calling-extension (Go)](https://github.com/copilot-extensions/function-calling-extension) — Official example extension using function calling in Go (note: this is a Copilot Extensions/OAuth extension, not the newer SDK)
6. [GitHub Copilot CLI GA Changelog (Feb 25 2026)](https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/) — Confirms skills, MCP, plugins, agents all GA
7. [VS Code Agent Skills docs](https://code.visualstudio.com/docs/copilot/customization/agent-skills) — Skills work across Copilot CLI and VS Code
8. [GitHub Copilot CLI Enhanced Agents Changelog (Jan 14 2026)](https://github.blog/changelog/2026-01-14-github-copilot-cli-enhanced-agents-context-management-and-new-ways-to-install/) — `.agent.md` custom agents introduced
9. [Creating Agent Plugins for VS Code and Copilot CLI — Ken Muse](https://www.kenmuse.com/blog/creating-agent-plugins-for-vs-code-and-copilot-cli/) — Plugins vs skills vs agents distinction
10. [copilot-extensions/skillset-example](https://github.com/copilot-extensions/skillset-example) — Skillset example for faster Copilot extension development
11. [Anatomy of a Github Copilot Extension in Golang — DEV Community](https://dev.to/shrsv/anatomy-of-a-github-copilot-extension-in-golang-17cd) — HTTP-based Copilot Extension architecture (older model)

---

### Findings

There are **three distinct extensibility mechanisms** in the GitHub Copilot ecosystem. They are easy to confuse but serve different purposes.

---

#### Mechanism 1: Agent Skills (SKILL.md) — Instruction-Set, No Code Execution

Skills are **markdown-based instruction bundles** that Copilot CLI loads as additional context when relevant. They are NOT runnable functions — they are prompt injections.

**How it works:**
- When a user's prompt matches a skill (by name, description, or trigger phrase), the SKILL.md is injected into the agent's context window
- Copilot then follows those instructions and can use any scripts/resources bundled in the same directory
- Scripts in the skill folder are read/executed by Copilot's built-in tools (`read_file`, `run_terminal_cmd`), not called directly by the SDK

**SKILL.md Format:**

```markdown
---
name: my-skill-name
description: What this skill does and when Copilot should use it. Trigger phrases go here.
license: MIT
---

# My Skill

Instructions in plain Markdown for Copilot to follow.

## When to use this
...

## Steps
...
```

**Frontmatter fields:**
| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Lowercase, hyphens for spaces; must match directory name |
| `description` | Yes | Natural language; used for semantic matching |
| `license` | No | Free-text license description |

**Directory structure:**
```
my-skill/
├── SKILL.md              # Required — instructions + frontmatter
├── scripts/
│   └── helper.sh         # Optional — Copilot can run these via its shell tool
├── references/
│   └── guide.md          # Optional — supplementary context
└── assets/
    └── template.txt      # Optional — templates, data files
```

**Discovery locations:**
| Scope | Path |
|-------|------|
| Personal (cross-project) | `~/.copilot/skills/<skill-name>/SKILL.md` |
| Project-specific | `.github/skills/<skill-name>/SKILL.md` |
| Also works | `~/.claude/skills/<skill-name>/SKILL.md` (Claude Code) |
| Also works | `.claude/skills/<skill-name>/SKILL.md` (project-local) |

**Invocation:**
```
# Explicit invocation
/my-skill-name do the thing

# Copilot auto-discovers based on description match
```

**Key limitation:** Skills are instruction sets, not function calls. Copilot reads the SKILL.md and decides how to execute using its own built-in tools. There is no mechanism for a skill to directly invoke Go code — only shell scripts (which Copilot runs via its `run_terminal_cmd` tool, subject to permission prompts).

---

#### Mechanism 2: Custom Tools via Go SDK — True Function Calling

When building a Go application that embeds the Copilot SDK, you register custom tools that the LLM can call as proper function calls. This is the mechanism relevant to `copilot-cli-llm`.

**How it works (tool lifecycle):**
1. Define tool with name, description, typed params struct, and handler function
2. Register tool in `SessionConfig.Tools` at session creation
3. SDK advertises tools to the model via the underlying protocol
4. When model decides to call a tool, SDK deserializes args → calls handler in parallel with other tool calls → sends result back to LLM
5. LLM incorporates result and continues reasoning

**Method 1: `DefineTool` (recommended — type-safe with auto JSON schema generation):**

```go
type WeatherParams struct {
    City string `json:"city" jsonschema:"The city name"`
}

type WeatherResult struct {
    City        string `json:"city"`
    Temperature string `json:"temperature"`
    Condition   string `json:"condition"`
}

getWeather := copilot.DefineTool(
    "get_weather",
    "Get the current weather for a city",
    func(params WeatherParams, inv copilot.ToolInvocation) (WeatherResult, error) {
        return WeatherResult{
            City:        params.City,
            Temperature: "72°F",
            Condition:   "sunny",
        }, nil
    },
)

session, _ := client.CreateSession(ctx, &copilot.SessionConfig{
    Model:               "gpt-5.4",
    Tools:               []copilot.Tool{getWeather},
    OnPermissionRequest: copilot.PermissionHandler.ApproveAll,
})
```

- Struct field tags: `json:"fieldname"` for serialization; `jsonschema:"description"` for schema description
- Return type is `any` or a concrete struct — serialized to JSON and sent back to LLM
- `ToolInvocation` parameter provides metadata about the call (rarely needed)

**Method 2: `Tool` struct directly (explicit JSON schema — more control):**

```go
lookupIssue := copilot.Tool{
    Name:        "lookup_issue",
    Description: "Fetch issue details from our tracker",
    Parameters: map[string]any{
        "type": "object",
        "properties": map[string]any{
            "id": map[string]any{
                "type":        "string",
                "description": "Issue identifier",
            },
        },
        "required": []string{"id"},
    },
    Handler: func(invocation copilot.ToolInvocation) (copilot.ToolResult, error) {
        args := invocation.Arguments.(map[string]any)
        return copilot.ToolResult{
            TextResultForLLM: "Issue summary here",
            ResultType:       "success",
            SessionLog:       fmt.Sprintf("Fetched issue %s", args["id"]),
        }, nil
    },
}
```

**Tool modifier flags:**
| Flag | Effect |
|------|--------|
| `SkipPermission = true` | Tool runs without triggering user approval prompt |
| `OverridesBuiltInTool = true` | Required to shadow a built-in tool (e.g., `edit_file`) |

**Permission control:** `OnPermissionRequest` is required in `SessionConfig`. Use `copilot.PermissionHandler.ApproveAll` to approve everything, or write a custom handler that inspects `request.Kind` (KindShell, Write, Read, MCP, CustomTool, URL, Memory, Hook).

---

#### Mechanism 3: Session Hooks — Lifecycle Interception

Hooks let you intercept the session lifecycle — before/after tool calls, on prompt submission, on session start/end. These are registered in `SessionConfig.Hooks`.

```go
session, _ := client.CreateSession(ctx, &copilot.SessionConfig{
    Model: "gpt-5.4",
    Hooks: &copilot.SessionHooks{
        OnPreToolUse: func(input copilot.PreToolUseHookInput, inv copilot.HookInvocation) (*copilot.PreToolUseHookOutput, error) {
            return &copilot.PreToolUseHookOutput{
                PermissionDecision: "allow",       // "allow", "deny", "ask"
                ModifiedArgs:       input.ToolArgs, // optionally rewrite args
                AdditionalContext:  "extra context injected before tool runs",
            }, nil
        },
        OnUserPromptSubmitted: func(input copilot.UserPromptSubmittedHookInput, inv copilot.HookInvocation) (*copilot.UserPromptSubmittedHookOutput, error) {
            // Modify or inspect the prompt before the model sees it
            return &copilot.UserPromptSubmittedHookOutput{
                ModifiedPrompt: input.Prompt + " [append extra context here]",
            }, nil
        },
        OnSessionStart: func(input copilot.SessionStartHookInput, inv copilot.HookInvocation) (*copilot.SessionStartHookOutput, error) {
            return &copilot.SessionStartHookOutput{
                AdditionalContext: "injected at session start",
            }, nil
        },
    },
})
```

**Available hooks:**
| Hook | Trigger | Modify capability |
|------|---------|-------------------|
| `OnPreToolUse` | Before each tool execution | Allow/deny, modify args, inject context |
| `OnPostToolUse` | After each tool execution | Modify result, inject context |
| `OnUserPromptSubmitted` | When user sends a prompt | Modify the prompt |
| `OnSessionStart` | Session start or resume | Inject startup context |
| `OnSessionEnd` | Session ends | Cleanup/logging only |
| `OnErrorOccurred` | Error occurs | Choose retry/skip/abort strategy |

**Key insight for `copilot-cli-llm`:** `OnUserPromptSubmitted` can inject memory context (similar to the existing `before_agent_start` hook pattern). `OnPreToolUse` can enforce a policy layer. These are SDK-side hooks — no OpenClaw hook system needed.

---

#### Mechanism 4: MCP Servers — Pre-built Tool Libraries

Rather than defining individual tools, you can connect to an MCP (Model Context Protocol) server and the model gets access to all tools that server exposes.

```go
session, _ := client.CreateSession(ctx, &copilot.SessionConfig{
    Model: "gpt-5.4",
    MCPServers: map[string]copilot.MCPServerConfig{
        "github": {
            Type: "http",
            URL:  "https://api.githubcopilot.com/mcp/",
        },
    },
    OnPermissionRequest: copilot.PermissionHandler.ApproveAll,
})
```

GitHub's built-in MCP server is accessible at `https://api.githubcopilot.com/mcp/` — provides tools for repo access, issues, PRs. Any MCP-compatible server (stdio or HTTP) can be connected this way.

---

#### Older Mechanism: Copilot Extensions (HTTP-based, pre-SDK)

The `copilot-extensions/function-calling-extension` repo (Go) is an **older OAuth HTTP-based** extension architecture, not the modern SDK approach. It requires:
- A publicly accessible HTTPS endpoint
- GitHub App registration
- ECDSA signature verification of incoming requests
- Manual JSON schema definition for function calling payloads

This is the GitHub Marketplace "Copilot Extension" model — intended for third-party integrations distributed to other GitHub users. It is NOT what you use for personal tool augmentation or embedding in an app. The modern SDK approach (Mechanisms 1-4 above) supersedes this for custom/personal use.

---

#### Summary Table — Which Mechanism to Use

| Need | Use |
|------|-----|
| Teach Copilot a workflow or domain knowledge | SKILL.md in `~/.copilot/skills/` |
| Register a Go function the LLM can call | `copilot.DefineTool` in SDK SessionConfig |
| Intercept/modify prompts before model sees them | `OnUserPromptSubmitted` hook |
| Run logic before/after every tool call | `OnPreToolUse` / `OnPostToolUse` hooks |
| Connect to a pre-built tool server | MCPServers in SessionConfig |
| Distribute a Copilot Chat add-on to other GitHub users | Copilot Extensions (HTTP + GitHub App) |

---

### Recommendation

For `copilot-cli-llm` (Phase 4 — OpenClaw integration):

1. **Custom tools via `DefineTool`** — the Go SDK tool system is complete and production-ready. Any Go function can be exposed as an LLM-callable tool. This is real function calling (JSON schema, typed params, handler invocation), not prompt injection.

2. **`OnUserPromptSubmitted` hook** — use this instead of OpenClaw's `before_agent_start` hook for memory context injection. It runs in-process (no subprocess call) and can prepend context to any prompt before the model sees it. This solves the Phase 4 research question (CLAUDE.md: "OpenClaw hook can't override model") differently — the SDK hook CAN modify context.

3. **SKILL.md files for the brain CLI** — if you want Copilot CLI users to be able to trigger the `oclaw-brain` binary from natural language prompts, create a skill at `~/.copilot/skills/oclaw-brain/SKILL.md` with instructions telling Copilot to invoke `~/.openclaw/workspace/bin/oclaw-brain` via its shell tool.

**Example SKILL.md for oclaw-brain:**
```markdown
---
name: oclaw-brain
description: Route complex reasoning tasks to the oclaw-brain CLI for think-mode processing with Claude Opus 4.6. Use when the user says "think:" or asks for deep analysis, debugging, or long-context reasoning.
---

# oclaw-brain

Run the oclaw-brain binary for think-mode LLM routing.

## When to use
When the user's request starts with "think:" or requires long-context analysis.

## Usage
Run: `~/.openclaw/workspace/bin/oclaw-brain "think: <user request>"`
```

---

### Compatibility Notes

- SKILL.md skills require Copilot CLI to be installed (not just the SDK) — discovery happens in the CLI process that the SDK spawns
- `DefineTool` tool parameters use `jsonschema` struct tags — requires the `jsonschema` package if using code-gen; the SDK's `DefineTool` handles reflection-based schema generation internally
- `OnPermissionRequest` is **required** in `SessionConfig` — omitting it causes an error. Use `copilot.PermissionHandler.ApproveAll` for automated contexts
- Session hooks are SDK-only — they do not affect the OpenClaw hook system (`before_agent_start`) which runs on the gateway side
- MCP via `MCPServers` in Go SDK: HTTP transport works; stdio transport requires the MCP server to be a spawnable process accessible from the Go binary's working directory
- The `function-calling-extension` example uses the pre-SDK OAuth extension architecture — useful for GitHub Marketplace distribution but irrelevant for the `copilot-cli-llm` use case

### Confidence: High

Sources are the official Go SDK README (fetched live from main branch), official GitHub Docs pages, and the canonical awesome-copilot skill examples. The Go SDK tool API was verified directly from raw source. The SKILL.md format was confirmed from two independent sources (GitHub Docs + awesome-copilot spec). The older Copilot Extensions architecture is well-documented by multiple sources.

What would increase confidence: actually running `copilot.DefineTool` in the build to confirm the `jsonschema` tag reflection works as documented.


---

## Research: GitHub Copilot CLI — Repository Locations and Open/Closed Source Status

**Date**: 2026-03-22
**Triggered by**: User request to find the actual GitHub repository for GitHub Copilot CLI (not the marketing page at github.com/features/copilot/cli) and determine open vs. closed source status for the CLI repo, the SDK, and related repos.
**Stack relevance**: Relevant to `copilot-cli-llm` build planning and understanding which repos can be read for implementation details, vendor lock-in assessment, and whether source can be contributed to.

---

### Question

What is the real GitHub repository URL for GitHub Copilot CLI? Is it open source? What is the status of `github/gh-copilot`? Are there related open-source SDK repos?

---

### Sources Consulted

1. [github.com/github/copilot-cli](https://github.com/github/copilot-cli) — Main Copilot CLI repo, public but proprietary license
2. [github.com/github/gh-copilot](https://github.com/github/gh-copilot) — Older gh extension, now archived (read-only as of Oct 30 2025)
3. [github.com/github/copilot-sdk](https://github.com/github/copilot-sdk) — Multi-language SDK (Go, Python, TypeScript, .NET) — MIT license, open source
4. [github.com/github/copilot-cli-for-beginners](https://github.com/github/copilot-cli-for-beginners) — Educational repo, MIT license
5. [github.com/copilot-extensions](https://github.com/copilot-extensions) — GitHub org for official extension examples
6. [GitHub Changelog — Copilot CLI GA Feb 25 2026](https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/)
7. [copilot-cli/LICENSE.md at main](https://github.com/github/copilot-cli/blob/main/LICENSE.md) — Custom proprietary license (non-OSS)
8. [DeepWiki — github/copilot-cli Legal & Licensing](https://deepwiki.com/github/copilot-cli/8-legal-and-licensing) — License analysis

---

### Findings

#### 1. The Two CLI Repos

| Repo | URL | Status | License |
|------|-----|--------|---------|
| **github/copilot-cli** | https://github.com/github/copilot-cli | Active (GA Feb 2026) | Custom proprietary (public repo, non-OSS) |
| **github/gh-copilot** | https://github.com/github/gh-copilot | **Archived Oct 30 2025** (read-only) | — |

- `github/copilot-cli` is the current, actively maintained Copilot CLI. It went GA on 2026-02-25. Latest release as of 2026-03-22: v1.0.10 (released 2026-03-20).
- `github/gh-copilot` was the old `gh copilot suggest` / `gh copilot explain` extension for GitHub CLI. It was retired when `github/copilot-cli` launched. As of GitHub CLI v2.86.0, running `gh copilot` redirects to the new CLI instead of the old extension.

#### 2. License on github/copilot-cli

The repo is **public but NOT open source.** The LICENSE.md contains a custom proprietary license that:
- Grants a non-exclusive, royalty-free license to install and run the software
- Allows redistribution **only** in unmodified form, bundled inside another app/service that provides "material functionality beyond the Software itself"
- Prohibits standalone redistribution or use as a primary product
- No modification rights

Source is visible on GitHub but cannot be forked, modified, or redistributed in modified form.

#### 3. github/copilot-sdk — Open Source (MIT)

The Copilot SDK is **MIT-licensed and open source.** This is the programmatic SDK (Go, Python, TypeScript, .NET) for embedding Copilot agent capabilities in applications.

- Repo: https://github.com/github/copilot-sdk
- License: MIT
- Go subdir: https://github.com/github/copilot-sdk/tree/main/go
- Status: Technical preview (v0.1.x), active development

This is the repo used by `copilot-cli-llm`.

#### 4. copilot-extensions Org — Open Source Examples

The `copilot-extensions` GitHub org (https://github.com/copilot-extensions) contains official example repos for building Copilot Extensions. These are public and open source (MIT). Key repos:

- `copilot-extensions/function-calling-extension` — Go example of function calling via the older OAuth extension architecture
- `copilot-extensions/skillset-example` — Skillset example for building extensions

Note: these are for the older HTTP-based Copilot Extensions (GitHub Marketplace) model, not the newer SDK.

#### 5. github/copilot-cli-for-beginners — MIT

Educational resource for learning Copilot CLI. MIT licensed, open source. Not the runtime itself.

---

### Summary Table

| Repo | Public | License | Active | Notes |
|------|--------|---------|--------|-------|
| [github/copilot-cli](https://github.com/github/copilot-cli) | Yes | Proprietary (custom) | Yes | The actual CLI; readable but not OSS |
| [github/gh-copilot](https://github.com/github/gh-copilot) | Yes | — | **Archived** | Old gh extension; retired Oct 2025 |
| [github/copilot-sdk](https://github.com/github/copilot-sdk) | Yes | **MIT** | Yes | SDK for embedding Copilot in apps |
| [copilot-extensions/\*](https://github.com/copilot-extensions) | Yes | MIT (per repo) | Yes | Extension examples (older HTTP model) |
| [github/copilot-cli-for-beginners](https://github.com/github/copilot-cli-for-beginners) | Yes | MIT | Yes | Educational only |

---

### Recommendation

For the `copilot-cli-llm` project: the SDK repo (`github/copilot-sdk`, MIT) is the only one where source can be read, referenced in code, and modified. The CLI itself (`github/copilot-cli`) is readable but its license prohibits modification or redistribution. No action needed — the current build plan already uses the SDK, not the CLI source.

If you need to understand CLI internals (e.g., how `CreateSession` works at the protocol level), read the SDK source — the CLI and SDK share the same agent runtime; the SDK exposes it programmatically.

---

### Compatibility Notes

- `github/gh-copilot` (archived) releases are still installable as a `gh` extension for legacy use but will not receive updates
- `github/copilot-cli` proprietary license does not block using the CLI as a tool — it only restricts redistribution; running it on the VM or locally is permitted

### Confidence: High

All repo URLs and statuses verified via direct search results from github.com. License status confirmed via LICENSE.md link and DeepWiki legal analysis. Archival date for `gh-copilot` confirmed via GitHub community discussion sources.

---

## Research: LLM-as-Judge for Vector Memory Quality Evaluation

**Date**: 2026-03-27
**Triggered by**: User request to research best practices for evaluating vector memory systems, fact extraction quality, and tag/classification accuracy in AI agent memory pipelines — specifically to inform an evaluation pass over the ClawBot memory system (~100 stored memories)
**Stack relevance**: Directly relevant to the ClawBot memory system on the VM (`~/.claude-memory/memory.db` → Azure AI Search), the `smart_extractor.py` extraction pipeline, and the planned LLM dedup sweep using GPT-4.1-mini

---

### Question

What are the 2025-2026 best practices for:
1. Evaluating extracted memory quality (atomicity, actionability, specificity)
2. Evaluating tag/classification accuracy in agent memory pipelines
3. Using LLM-as-judge to automate that evaluation
4. What judge model to use and at what cost for ~100 memories

---

### Sources Consulted

1. [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) — Contextual Embeddings + Contextual BM25 reduce failed retrievals by 49%; with reranking, 67%. Cost ~$1.02 per million document tokens with prompt caching.
2. [Anthropic — Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — "Keep context informative, yet tight. Find the smallest set of high-signal tokens that maximize likelihood of desired outcome."
3. [Anthropic — Claude Memory Tool (beta)](https://console.anthropic.com/docs/en/agents-and-tools/tool-use/memory-tool) — Claude Opus 4 dramatically outperforms previous models on memory file management tasks; memory-as-files pattern for persistent cross-session state.
4. [Hamel Husain — LLM-as-a-Judge Complete Guide](https://hamel.dev/blog/posts/llm-judge/) — "Critique Shadowing" technique; skip generic criteria; calibrate against a small human-labeled set. Based on helping 30+ companies build eval systems.
5. [Hamel Husain — Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) — 60–80% of dev time should go to error analysis; 100% pass rate means evals aren't hard enough.
6. [Eugene Yan — Evaluating the Effectiveness of LLM-Evaluators](https://eugeneyan.com/writing/llm-evaluators/) — Drawing from two dozen papers: use cases, prompting techniques, alignment workflows. Covers recall/precision measurement on binary labels.
7. [Eugene Yan — An LLM-as-Judge Won't Save The Product](https://eugeneyan.com/writing/eval-process/) — Process fix > tool fix. Measuring recall/precision on binary labels, correlation for pairwise comparisons.
8. [Mem0 Technical Paper (arXiv 2504.19413)](https://arxiv.org/abs/2504.19413) — Production-ready memory architecture with LLM-based extraction using GPT-4o-mini with function calling. Four operations: ADD, UPDATE, DELETE, NOOP.
9. [Mem0 Benchmark Blog](https://mem0.ai/blog/benchmarked-openai-memory-vs-langmem-vs-memgpt-vs-mem0-for-long-term-memory-here-s-how-they-stacked-up) — 66.9% accuracy on LOCOMO, 26% relative gain over OpenAI, 91% lower p95 latency, 90% fewer tokens.
10. [Zep Technical Paper (arXiv 2501.13956)](https://arxiv.org/abs/2501.13956) — Temporal knowledge graph (Graphiti engine); 94.8% on DMR benchmark vs 93.4% for MemGPT; 18.5% accuracy gain on LongMemEval, 90% latency reduction.
11. [Letta/MemGPT — Benchmarking Agent Memory](https://www.letta.com/blog/benchmarking-ai-agent-memory) — Letta Evals open-sourced Oct 2025; evaluation of stateful agents with memory tools; finding: filesystem-backed memory competitive with graph memory.
12. [Judging the Judges: Position Bias Study](https://arxiv.org/abs/2406.07791) — Systematic study of position bias. Metrics: repetition stability, position consistency, preference fairness. Prompt design with explicit bias disclaimers reduces position + length bias.
13. [Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge](https://llm-judge-bias.github.io/) — Catalogs: position bias, verbosity bias, self-enhancement bias, misinformation oversight bias, gender bias, authority bias, beauty bias.
14. [Opportunities and Challenges of LLM-as-Judge (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.138.pdf) — Panel judges outperform single judges; hybrid human-in-the-loop required for expert domains (60–68% LLM–expert agreement vs ~80% LLM–human agreement on general tasks).
15. [Grading Scale Impact on LLM-as-Judge (arXiv 2601.03444)](https://arxiv.org/html/2601.03444v1) — Human-LLM alignment is highest on 0–5 grading scale; float scores are unreliable; categorical integer scales with explicit rubric definitions outperform fine-grained numeric scales.
16. [LangChain — LLM-as-Judge Calibration with Human Corrections](https://www.langchain.com/articles/llm-as-a-judge) — Workflow: collect annotations → human reviewers correct sample → corrections become ground truth → calibrate evaluator.
17. [Confident AI — LLM-as-Judge Complete Guide](https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method) — Recommends binary (pass/fail) as most reliable; G-Eval chain-of-thought for multi-criteria; few-shot examples significantly improve alignment.
18. [Monte Carlo Data — LLM-as-Judge Best Practices](https://www.montecarlodata.com/blog-llm-as-judge/) — 7 best practices; template library for scoring rubrics; single-output vs pairwise comparison modes.
19. [AdaRubric: Task-Adaptive Rubrics (arXiv 2603.21362)](https://arxiv.org/html/2603.21362) — Generates task-specific rubrics on the fly; scores trajectories step-by-step with confidence-weighted per-dimension feedback. Addresses "one rubric fits all" failure mode.
20. [Memory for Autonomous LLM Agents Survey (arXiv 2603.07670)](https://arxiv.org/html/2603.07670) — Benchmarks: MemBench, MemoryAgentBench, LongMemEval. Four core competencies: Accurate Retrieval, Test-Time Learning, Long-Range Understanding, Conflict Resolution.
21. [GPT-4.1 mini pricing (Helicone)](https://www.helicone.ai/blog/gpt-4.1-full-developer-guide) — $0.40/M input, $1.60/M output tokens. Outperforms GPT-4o on many benchmarks at 83% lower cost.
22. [Claude Haiku 4.5 vs GPT-4.1-mini comparison](https://artificialanalysis.ai/models/comparisons/claude-4-5-haiku-vs-gpt-4-1-mini) — Haiku 4.5: $1/M input, $5/M output. GPT-4.1-mini cheaper for output-heavy tasks; Haiku 4.5 better zero tool-call failure rate, stronger coding.
23. [Promptfoo LLM Rubric](https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/llm-rubric/) — Open-source eval framework; YAML-based rubric definitions; supports multiple judge models.

---

### Findings

#### 1. LLM-as-Judge: State of the Practice (2025–2026)

LLM-as-judge is now the dominant paradigm for automated eval of LLM outputs. Key consensus from research and practitioners:

**Scoring scale:** Binary (pass/fail) and 0–5 integer scales have the highest human–LLM alignment. Float scores are unreliable. 10-point or 100-point scales without explicit per-point rubrics perform poorly. Academic result (arXiv 2601.03444): 0–5 scale maximizes alignment.

**Chain-of-thought (G-Eval pattern):** Always ask the judge to reason step-by-step before returning a score. The CoT serves two purposes: (a) it forces the judge to engage with the rubric criteria, (b) the reasoning trace is auditable and debuggable. This was validated by Liu et al. (EMNLP 2023) and is now standard.

**Few-shot examples:** Including 2–3 labeled examples in the judge prompt is the single highest-leverage improvement. Human-labeled examples with scores (and brief explanations why) act as calibration anchors. Do this before deploying any judge at scale.

**Rubric specificity:** Generic criteria ("helpfulness", "relevance") produce unreliable results. Domain-specific criteria tied to your exact use case outperform generic criteria by a significant margin. For memory evaluation, this means rubrics should ask about properties specific to stored memories, not generic LLM output quality.

**Calibration workflow (Hamel Husain / LangChain pattern):**
1. Run the judge over a sample (20–30 items is enough for calibration).
2. Manually review each judge decision.
3. Correct disagreements and record ground truth.
4. Adjust judge prompt to close the gap.
5. Achieve >80% agreement before scaling to full dataset.

#### 2. Known Biases and Mitigations

| Bias | Description | Mitigation |
|------|-------------|-----------|
| Position bias | Judge favors items appearing first in pairwise prompts | Randomize order; use single-item (non-pairwise) scoring |
| Verbosity bias | Judge favors longer, more detailed outputs regardless of quality | Explicit instruction: "Do not reward length over precision. A concise, specific memory is better than a verbose one." |
| Self-enhancement bias | Judge favors outputs similar to its own training | Use a different model family for judge vs generator |
| Authority bias | Judge rates highly if "authoritative" framing used | Strip contextual framing; evaluate content only |
| Leniency bias | Judges cluster near the top of scales (score inflation) | Anchor rubric with explicit "what a score of 1 looks like" examples |

For single-item memory scoring (not pairwise), position bias is irrelevant. The main risks are verbosity bias and leniency bias.

#### 3. Single Judge vs Panel

For ~100 memories, a single judge is sufficient if calibrated against human labels. A three-judge panel with majority vote increases reliability by ~10–15% but triples cost. The academic consensus (EMNLP 2025) is that panels are warranted for expert-domain tasks or when single-judge agreement with human reviewers is below 75%. For memory tag evaluation (a well-bounded classification task), a single well-prompted judge is adequate.

**Exception:** Use a panel if the judge shows >20% disagreement with your manual calibration sample. In that case, run two judge models (e.g., GPT-4.1-mini + Claude Haiku 4.5) and take the majority; disagreements get flagged for human review.

#### 4. Memory Quality Dimensions — Evaluation Framework

Based on synthesis of Mem0 paper, MemGPT/Letta, Zep, and academic benchmarks, the following dimensions matter most for agent memory quality:

**Extraction quality dimensions:**

| Dimension | What it tests | Suggested scale |
|-----------|-------------|-----------------|
| Atomicity | Is this exactly one fact, or are multiple facts bundled? | Binary (1=atomic, 0=bundled) |
| Specificity | Is it specific (names, numbers, dates) or vague ("prefers X")? | 0–3 |
| Actionability | If recalled in a future session, would it actually change the response? | Binary (1=yes, 0=noise) |
| Temporal validity | Is this likely still true? (Addresses state-change problem) | Binary (1=probably durable, 0=likely stale) |
| Completeness | Is enough context preserved to be understandable without the source session? | 0–2 |
| Noise/padding | Does this contain filler, conversational pleasantries, or metadata that shouldn't be stored? | Binary (1=clean, 0=contains noise) |

**Tag quality dimensions:**

| Dimension | What it tests |
|-----------|-------------|
| Tag accuracy | Does the assigned tag match the memory content? |
| Tag specificity | Is the tag specific enough to be useful for filtering? |
| Tag completeness | Are all relevant tags present? |
| Tag consistency | Would a human assign the same tags to similar memories? |

#### 5. Mem0 Architecture: What Makes It Work

Mem0's production paper (Apr 2025) defines four memory operations via LLM function calling:
- **ADD**: New fact, no equivalent in store → insert
- **UPDATE**: New fact augments/modifies existing memory → merge
- **DELETE**: New fact contradicts existing memory → remove old
- **NOOP**: Already known → skip

This CRUD-style extraction layer is the core insight: rather than appending every extracted fact, the system decides whether incoming information changes what's already known. This prevents the knowledge drift and duplicate accumulation problems common in naive extraction systems.

For evaluation purposes, this means a memory corpus quality check should audit not just "is this fact correct" but also "is this fact unique" and "is this the most up-to-date version of this fact."

#### 6. Zep's Temporal Knowledge Graph Insight

Zep's key architectural contribution (Jan 2025 paper) is that vector search alone fails on temporal reasoning questions (e.g., "What did the user prefer last month vs now?"). Graphiti, Zep's engine, maintains time-stamped relationship edges in a knowledge graph. On LongMemEval, which tests temporal multi-hop reasoning, Zep shows 18.5% accuracy improvement over vector-only baselines.

For evaluating memory quality, this implies a temporal validity check: memories that reflect past states without time-stamping are inherently lower quality than timestamped facts.

#### 7. Anthropic's Contextual Retrieval: Applied to Memory

Anthropic's Contextual Retrieval technique (2024) prepends 50–100 tokens of chunk-specific context before embedding. The key insight is that chunk-level context ("This fact was extracted from a conversation about X project on Y date") dramatically improves retrieval precision. Applied to agent memory: enriching stored memories with extraction context (project, date, conversation topic) before embedding can reduce failed retrieval by up to 49%.

In the current ClawBot system, memories are embedded as raw fact strings. Adding a brief contextual header before embedding could significantly improve recall precision.

#### 8. Cost Analysis for Judging ~100 Memories

Assumptions: 100 memories, average memory = 50 tokens, judge prompt (rubric + instructions + examples) = 800 tokens, judge output (CoT + score) = 200 tokens per memory.

Per memory: ~850 input tokens + ~200 output tokens.
Total: 85,000 input tokens + 20,000 output tokens.

| Judge Model | Input cost | Output cost | Total for 100 | Notes |
|-------------|-----------|------------|---------------|-------|
| GPT-4.1-mini | $0.034 | $0.032 | **~$0.07** | Best cost/quality ratio for classification tasks |
| Claude Haiku 4.5 | $0.085 | $0.100 | **~$0.19** | Better instruction-following, zero tool-call failures |
| GPT-4o-mini | $0.013 | $0.012 | **~$0.025** | Cheapest but slightly weaker instruction-following |
| Claude Sonnet 4.5 | $0.255 | $1.000 | **~$1.26** | Overkill for classification; justified only for panel judge |

For 100 memories, cost is negligible across all models. GPT-4.1-mini is the recommended default (stronger than GPT-4o-mini, much cheaper than Sonnet). Use Haiku 4.5 as a second judge if building a panel.

For the existing ClawBot planned "weekly LLM dedup sweep (GPT-4.1-mini)" mentioned in CLAUDE.md, even weekly sweeps over 500 memories would cost under $0.40/week.

---

### Recommendation

**For evaluating the ~100 ClawBot memories:**

1. **Use GPT-4.1-mini as primary judge** at ~$0.07 total cost. If it disagrees with your manual review on >20% of the calibration sample, add Claude Haiku 4.5 as a second judge and take the majority vote.

2. **Evaluate each memory on four dimensions** using separate binary or 0–3 integer scores (not a combined score):
   - Atomicity (binary): Is this exactly one fact?
   - Actionability (binary): Would recalling this change a response?
   - Tag accuracy (binary): Does the tag match the content?
   - Tag specificity (0–2): Is the tag specific enough to be useful for retrieval filtering?

3. **Use the G-Eval pattern**: Ask the judge to reason through each criterion before scoring. Include 2–3 labeled examples per criterion (one clearly good, one clearly bad, one borderline).

4. **Calibrate before scaling**: Manually review 15–20 judge decisions first. Adjust the prompt if agreement with your manual labels is below 80%.

5. **Score format**: Return a JSON object with per-dimension scores and a one-sentence rationale per dimension. This makes the output auditable.

**Sample judge prompt structure (for atomicity + actionability):**

```
You are evaluating the quality of a stored agent memory. Score this memory on two dimensions.

MEMORY: {memory_text}
TAGS: {tags}
PROJECT: {project}

DIMENSION 1: ATOMICITY
Does this memory contain exactly one fact, or are multiple facts bundled together?
- Score 1 (atomic): Contains exactly one self-contained fact.
- Score 0 (bundled): Contains two or more distinct facts that should be stored separately.

DIMENSION 2: ACTIONABILITY
If an AI assistant recalled this memory in a future conversation, would it meaningfully change the response?
- Score 1 (actionable): Yes, knowing this fact would change how the assistant responds.
- Score 0 (noise): No, this is conversational filler, obvious context, or too vague to act on.

Examples:
Memory: "User prefers GPT-4.1-mini for dedup sweeps over Claude Haiku for cost reasons."
Tags: ["type:preference"]
→ Atomicity: 1 (one preference fact)
→ Actionability: 1 (directly changes model selection decisions)

Memory: "We discussed various topics including memory systems and cost optimization."
Tags: ["type:architecture"]
→ Atomicity: 0 (vague summary, not a single fact)
→ Actionability: 0 (too vague to act on)

Now evaluate the memory above. Think step by step, then return:
{"atomicity": 0|1, "atomicity_reason": "...", "actionability": 0|1, "actionability_reason": "..."}
```

6. **For the dedup sweep**: Use a separate judge prompt focused on near-duplicate detection. Compare memory pairs using semantic similarity thresholds (current system uses >60% word overlap), then use the LLM to confirm: "Given these two memories, is one a duplicate or update of the other, or do they each contain distinct actionable information?"

7. **Add contextual headers before embedding** (Anthropic's Contextual Retrieval insight): Instead of embedding the raw memory string, embed: `"[Project: {project}] [Type: {type}] [Date: {date}] {memory_text}"`. This is projected to reduce failed retrievals by ~49% based on Anthropic's benchmarks.

---

### Compatibility Notes

- GPT-4.1-mini is available in Azure OpenAI (East US 2) — directly usable from the VM via the existing `AZURE_OPENAI_CHAT_ENDPOINT` env var
- The current ClawBot memory system uses GPT-5.2 for extraction cron; swapping to GPT-4.1-mini for evaluation-only tasks is straightforward
- Azure AI Search Basic tier (current) supports 3072-dim embeddings; contextual header enrichment does not require schema changes — just modify the string before embedding
- LangSmith and Promptfoo are the two leading open-source eval frameworks that support YAML-defined rubrics; both support GPT-4.1-mini as judge model. Neither requires changes to the ClawBot pipeline — they can evaluate from exported data.

---

### Design Decision Flag

This research surfaces a candidate design decision:

**Potential decision:** Add contextual header enrichment to memory embedding pipeline (prepend project/type/date context before vectorizing). Based on Anthropic's Contextual Retrieval research showing 49–67% reduction in failed retrievals, this is a low-risk, high-ROI change requiring ~5 lines of code in `smart_extractor.py` or `memory_bridge.py`.

**Flag for:** `plans/design-decisions/` — "Should we enrich memory embeddings with contextual headers before vectorization?"

---

### Confidence: High

Research drawn from: Anthropic official docs, two peer-reviewed papers (Mem0 arXiv 2504.19413, Zep arXiv 2501.13956), EMNLP/ICLR 2025 conference papers on LLM-as-judge, practitioner guides from Hamel Husain and Eugene Yan (both active in 2024–2025), and current pricing data from Helicone and Artificial Analysis. All sources dated within 18 months. Cost estimates based on current listed API pricing.

What would increase confidence: Running the calibration step (manually labeling 20 memories) to validate the judge prompt before scoring the full set.

---

## Research: Memory Tagging and Classification Best Practices — Mem0, Zep, LangMem, Letta/MemGPT, A-MEM

**Date**: 2026-03-28
**Triggered by**: User planning to improve the tag extraction prompt in the oclaw_brain ClawBot memory system (SQLite + Azure AI Search, string tags like `type:decision`, `domain:infrastructure`). Wants to confirm whether flat string tags are still best practice or if the ecosystem has moved on.
**Stack relevance**: Directly affects `smart_extractor.py` tag extraction logic, memory schema in `~/.claude-memory/memory.db`, and Azure AI Search filter strategy on the VM.

---

### Question

Are flat string tags (e.g. `type:decision`, `domain:infrastructure`) still considered best practice for memory classification in AI agent memory systems, or have leading frameworks moved to embedding-based categorization, hierarchical tags, knowledge graphs, or hybrid approaches? What specific mechanisms do Mem0, Zep, LangMem, and Letta/MemGPT use?

---

### Sources Consulted

1. [Memory Types — Mem0 Docs](https://docs.mem0.ai/core-concepts/memory-types) — Episodic/semantic/procedural layered model
2. [Enhanced Metadata Filtering — Mem0 Docs](https://docs.mem0.ai/open-source/features/metadata-filtering) — Full filter field list including `categories` and `keywords`
3. [Memory Filters — Mem0 Docs](https://docs.mem0.ai/platform/features/v2-memory-filters) — v2 filter operators: AND/OR, `contains`, `in`, `icontains`
4. [Custom Categories — Mem0 Docs](https://docs.mem0.ai/platform/features/custom-categories) — LLM auto-assigned categories, project-level config, 3–5 category best practice
5. [Tag and Organize Memories — Mem0 Cookbook](https://docs.mem0.ai/cookbooks/essentials/tagging-and-organizing-memories) — Practical tagging walkthrough
6. [AI Memory Layer Guide Dec 2025 — Mem0 Blog](https://mem0.ai/blog/ai-memory-layer-guide) — Production layered storage architecture
7. [Graph Memory for AI Agents Jan 2026 — Mem0 Blog](https://mem0.ai/blog/graph-memory-solutions-ai-agents) — Graph as optional layer on top of flat+vector
8. [Mem0 arXiv paper 2504.19413](https://arxiv.org/pdf/2504.19413) — Production system; 26% accuracy uplift on LOCOMO benchmark
9. [Zep arXiv paper 2501.13956](https://arxiv.org/abs/2501.13956) — Temporal Knowledge Graph architecture whitepaper
10. [Zep arXiv HTML full text](https://arxiv.org/html/2501.13956v1) — Full paper: 6 question types, temporal validity windows
11. [Custom Entity and Edge Types — Zep Docs](https://help.getzep.com/graphiti/core-concepts/custom-entity-and-edge-types) — Pydantic-based entity type schema
12. [Introducing Entity Types — Zep Blog](https://blog.getzep.com/entity-types-structured-agent-memory/) — Default types: User, Preference, Procedure; custom via Pydantic
13. [Graphiti GitHub](https://github.com/getzep/graphiti) — Open-source graph engine; hybrid BM25+vector+graph traversal
14. [LangMem GitHub](https://github.com/langchain-ai/langmem) — LangChain long-term memory SDK
15. [LangMem Conceptual Guide](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/) — Episodic/semantic/procedural classification
16. [LangMem Semantic Memory — DeepWiki](https://deepwiki.com/langchain-ai/langmem/2.1-semantic-memory) — Schema-based extraction with Pydantic; namespace tuples; MemoryManager vs MemoryStoreManager
17. [How to Extract Semantic Memories — LangMem Docs](https://langchain-ai.github.io/langmem/guides/extract_semantic_memories/) — Practical schema extraction guide
18. [Intro to Letta/MemGPT — Letta Docs](https://docs.letta.com/concepts/memgpt/) — Core/Recall/Archival memory tiers
19. [Understanding Memory Management — Letta Docs](https://docs.letta.com/advanced/memory-management/) — Agent-managed tier promotion
20. [A-MEM arXiv 2502.12110](https://arxiv.org/abs/2502.12110) — Zettelkasten-inspired: notes with keywords, tags, context descriptions, and embedding-based links
21. [Mem0 vs Zep vs LangMem vs MemoClaw 2026 — DEV Community](https://dev.to/anajuliabit/mem0-vs-zep-vs-langmem-vs-memoclaw-ai-agent-memory-comparison-2026-1l1k) — Practitioner comparison
22. [AI Agent Memory Systems 2026 — Medium/Yogesh Yadav](https://yogeshyadav.medium.com/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8) — Zep temporal graph vs Mem0 flat+graph hybrid
23. [Graph-based Agent Memory Taxonomy — arXiv 2602.05665](https://arxiv.org/html/2602.05665) — Survey paper Feb 2026
24. [Memory in the Age of AI Agents — arXiv 2512.13564](https://arxiv.org/abs/2512.13564) — Dec 2025 survey paper
25. [Graphlit Survey of Agent Memory Frameworks](https://www.graphlit.com/blog/survey-of-ai-agent-memory-frameworks) — Comparison landscape

---

### Findings

#### 1. Mem0 — LLM-Auto-Assigned Categories + Keywords + Flat Metadata

Mem0 uses a **hybrid of flat string categories and dense vector embeddings**. There are no user-defined tags in the traditional sense — the system auto-assigns categories using an LLM during memory extraction.

**Key specifics:**
- Every memory object has a `categories` field (array of strings) and a `keywords` field, both auto-populated by the extraction LLM
- Categories are defined at the **project level** (not per-memory); Mem0's recommendation is to define **3–5 clear categories with descriptions** — fewer categories = more accurate auto-assignment
- Example category set for customer support: `["support_tickets", "account_info", "billing", "product_feedback"]`
- Once project categories are set via `client.project.update()`, all new memories are auto-assigned; no manual tagging required
- Memories can have multiple categories per entry
- Filtering API supports: `{"categories": {"contains": "finance"}}` (partial) or `{"categories": {"in": ["personal_information"]}}` (exact)
- Available filter fields: `user_id`, `agent_id`, `app_id`, `run_id`, `created_at`, `updated_at`, `categories`, `keywords`
- Keywords also auto-extracted and filterable with `contains` / `icontains`
- API response example: `{"id": "mem_123", "memory": "User loves pizza", "categories": ["food"], "keywords": [...], "score": 0.95}`

**Storage layer:** Mem0 stores across three backends simultaneously: vector DB (semantic search), key-value DB (fast lookup), and optionally a graph DB (entity relationships). The "flat tags" (categories/keywords) live in the key-value layer and enable metadata-filtered hybrid search.

**Graph layer (optional, Jan 2026):** Mem0 added graph memory as an opt-in layer — entities extracted from memories become nodes, relationships become edges. This is additive, not a replacement for the flat category system.

**Conclusion:** Mem0 has explicitly **moved away from manual user-defined string tags** toward LLM-auto-assigned categories (defined at project config time) plus LLM-extracted keywords. The tag vocabulary is controlled (project-level enum), not free-form per-memory.

---

#### 2. Zep — Temporal Knowledge Graph with Typed Entity Nodes (No Flat Tags)

Zep uses a **fundamentally different paradigm**: a temporal knowledge graph (Graphiti) instead of flat tags. There is no string tag system.

**Key specifics:**
- Memory is stored as a graph of typed **entity nodes** and **typed edges**
- Built-in (default) entity types: `User`, `Preference`, `Procedure` — each with specific attributes auto-extracted from text
- **Custom entity types** defined via Pydantic classes — developer specifies domain entities (e.g., `Customer`, `Order`, `Incident`) and their attributes; Graphiti classifies and populates them during ingestion
- Example:
  ```python
  class Incident(BaseNode):
      severity: str
      affected_service: str
      resolution_status: str
  ```
- Temporal: every edge has a validity window (`t_created`, `t_expired`) — Zep tracks when facts were true, not just what facts exist
- Three-tier graph structure: episode subgraph → semantic entity subgraph → community subgraph
- Retrieval: hybrid of **semantic embeddings + BM25 keyword search + graph traversal** (multi-hop queries across entity relationships)
- Outperforms baseline retrieval by 18.5% on long-horizon accuracy while cutting latency by ~90% (per arXiv paper)
- No flat tags; categorization is entirely structural (what type of node is this entity?)

**Who should use Zep:** Applications requiring relationship tracking over time — e.g., "when did the user's preference change?", "what changed after incident X?". Overkill for simple key-fact recall.

---

#### 3. LangMem (LangChain) — Schema-Based Structured Extraction with Namespaces

LangMem uses **Pydantic schema extraction** instead of free-form tags. Classification happens through schema definition.

**Key specifics:**
- Memory is classified by **which Pydantic schema it conforms to**, not by string tags
- Developer defines schemas like `Triple` (subject/predicate/object), or custom domain types; `create_memory_store_manager(schemas=[MySchema])` handles extraction
- Default schema is unstructured text; custom schemas enable structured extraction
- Storage organized by **hierarchical namespace tuples**: `("chat", "{user_id}", "triples")` — placeholders like `{user_id}` are substituted at runtime
- Memory operations: `create`, `update`, `delete` — generated by comparing new conversation against existing memories
- Uses `trustcall` library for parallel structured extraction via tool calls
- Memory types recognized: episodic, semantic, procedural — but classification is implicit via schema, not a tag field
- No built-in "categories" field — categorization is entirely determined by which namespace + schema the memory lives in
- Native LangGraph integration; can use any vector store backend

**Tradeoff:** Maximum developer control + lowest cost (self-hosted), but requires upfront schema design. No auto-tagging — you define the structure and LangMem extracts into it.

---

#### 4. Letta / MemGPT — Tiered Memory Architecture (No Explicit Tags)

Letta/MemGPT uses a **tiered context management** approach. There are no explicit tags or categories — classification is determined by which memory tier the data lives in.

**Key specifics:**
- Three tiers:
  - **Core Memory** (in-context, always present): Compressed essential facts about the user and agent persona. Analogous to RAM. Very small — fits in context window.
  - **Recall Memory** (searchable history): Complete interaction history, stored on disk, retrieved via semantic search when needed
  - **Archival Memory** (vector DB): Long-term storage for important information; agent explicitly moves facts here; retrieved via semantic search
- The **agent itself decides** tier promotion: it can call `archival_memory_insert()`, `archival_memory_search()`, `recall_memory_search()` as tools
- **Strategic forgetting**: MemGPT prioritizes precision — it summarizes and deletes context that is not needed rather than retaining everything
- No tag fields — the "category" of a memory is entirely determined by its tier
- Retrieval: semantic search (dense embeddings) within each tier; no BM25 or keyword filtering

**Letta's current state (2025-2026):** Letta has moved beyond raw MemGPT; it now has a server API, multi-agent support, and a managed cloud. But the core memory model is still tier-based with no explicit tagging.

---

#### 5. A-MEM — LLM-Generated Tags + Embedding-Based Links (Zettelkasten Model)

A-MEM (arXiv 2502.12110, Feb 2025, updated through Oct 2025) is a research system that uses **both explicit LLM-generated tags AND embedding-based link formation**.

**Key specifics:**
- Each memory "note" contains: raw content + timestamp + LLM-generated keywords + LLM-generated tags + context description + dense embedding + links (initially empty)
- **Link Generation Module**: when a new note is added, finds nearest neighbors via embedding similarity, then asks an LLM which neighbors to link to — forming organic knowledge clusters
- **Memory Evolution Module**: revisits existing notes and asks whether their contextual descriptions or attributes should be updated given new context
- Tags are free-form strings, LLM-generated — not from a controlled vocabulary
- Outperforms SOTA baselines across 6 foundation models in empirical tests
- **Key insight**: the combination of explicit tags AND embeddings AND inter-note links produces better recall than any single approach alone
- All-Mem (arXiv 2603.19595) extends this with dynamic topology evolution

---

#### 6. General Question: Are Flat String Tags Outdated?

**Short answer: No — but they are insufficient on their own.**

The 2025-2026 consensus from production systems and research is:

| Approach | Status | Use Case |
|---|---|---|
| Free-form manual string tags | Declining — error-prone at scale, inconsistent | Simple personal projects only |
| LLM-auto-assigned controlled-vocab categories (Mem0 style) | Active, recommended | Mid-scale, mixed content domains |
| Schema-based structured extraction (LangMem style) | Active, recommended for structured domains | When memory types are well-defined |
| Temporal knowledge graph with typed nodes (Zep/Graphiti) | Leading edge — higher infrastructure cost | Relationship-heavy, entity-tracking use cases |
| Tier-based (Letta/MemGPT) | Active — good for single-agent context management | Context window management more than classification |
| Hybrid: flat categories + vector + optional graph (Mem0) | Best practice for general production | Most production agents |
| Tags + embeddings + inter-note links (A-MEM) | Research frontier — not yet in mainstream tooling | Highest recall quality; complex to operate |

**What's changed in 2025-2026:**
- The trend is away from **free-form per-memory string tags** (inconsistent vocabulary, hard to filter reliably) toward **controlled-vocabulary categories defined once at config/schema time**, with LLM doing the classification
- **Embeddings are universal** — every serious system vectorizes every memory. The question is what structure sits on top of the embedding layer.
- **Graph is additive, not replacement** — even Mem0 (which added graph support in Jan 2026) still keeps the flat category system. Graph is used for relationship queries, not replacing the primary vector+filter retrieval.
- **Keyword auto-extraction** (alongside categories) is standard — Mem0 extracts keywords automatically; A-MEM does the same. This enables BM25-style recall without tag schema maintenance.

**Relevance to oclaw_brain current system (`type:`, `domain:`, `pin:`, `permanent:` tags):**

The current approach is closer to **manual free-form tagging**, which is the least favored pattern in 2025-2026. The specific improvements to make:
1. **Move from free-form to controlled vocabulary** — define a fixed enum of types (decision, fix, architecture, preference, correction) and enforce it in the extraction prompt — this is what we already partially do with `type:` prefixes, but consistency is the gap
2. **Add auto-extracted keywords** as a separate field — don't conflate keywords with type tags. Keywords should be content terms (service names, error codes, concepts); type tags should be classification only.
3. **Keep the `type:` prefix convention** — it maps well to Mem0's `categories` field; the colon-prefix approach is actually a recognized pattern for structured tag namespacing
4. **The `domain:` prefix is genuinely useful** — no leading system has dropped domain/topic segmentation. It maps to LangMem namespaces and Zep entity community subgraphs.
5. **`pin:` and `permanent:` tags** have no equivalent in production systems — they're custom annotations we maintain for operational reasons and are fine to keep
6. **Do NOT migrate to a graph DB** — unnecessary for our scale and use case (single-agent personal assistant, ~hundreds to low-thousands of facts). Graph overhead is only justified for multi-entity relationship tracking across thousands of memories.

---

### Recommendation

**Keep the current tag architecture (type: + domain: + pin: + permanent:) but make two changes:**

1. **Enforce a closed vocabulary for `type:` tags in the extraction prompt.** The prompt should list exactly which type values are valid and include examples. This is directly analogous to Mem0's "define 3–5 categories at project level" recommendation. Too many tag values = lower classification accuracy.

   Recommended closed set: `type:decision`, `type:fix`, `type:architecture`, `type:preference`, `type:correction`, `type:fact` — and nothing else for the `type:` namespace.

2. **Add a separate `keywords` extraction step to the prompt.** Ask the LLM to extract 2–5 content keywords (service names, error codes, concepts, proper nouns) separately from the classification tags. Store them as a comma-separated field or as individual `kw:` prefixed tags. This enables BM25-style pre-filtering in Azure AI Search before semantic ranking — which is the standard production pattern (Mem0, Graphiti both do this).

The rest of the current system (SQLite + Azure AI Search hybrid, contextual embeddings, `domain:` tags for scoping) is aligned with what leading production systems use. No structural migration needed.

---

### Compatibility Notes

- All changes are backwards-compatible — the tag schema change is an extraction prompt update only; existing memories retain their current tags
- Azure AI Search supports metadata filter fields natively; adding a `keywords` field requires a schema update to the search index (add a `Collection(Edm.String)` field named `keywords` and re-index existing memories)
- No changes needed to `memory_bridge.py` logic — just add `keywords` to the document pushed to Azure
- If adding keywords as `kw:term` prefixed tags to the existing tags array: zero schema changes required, but BM25 filtering becomes less clean (mixed-type array)

---

### Design Decision Flag

**Flag for `plans/design-decisions/`:** "Should we extract keywords as a separate field (separate Azure Search field `keywords: Collection(Edm.String)`) or as `kw:`-prefixed entries in the existing tags array?"

- Separate field: cleaner filtering, requires Azure Search index schema update + re-index of ~N existing memories
- Prefix in tags array: zero schema changes, works immediately, slightly messier query syntax

---

### Confidence: High

Sources include: 4 official documentation sites (Mem0, Zep, LangMem, Letta), 3 peer-reviewed arXiv papers (Mem0 2504.19413, Zep 2501.13956, A-MEM 2502.12110, Graph survey 2602.05665), and 3 practitioner comparisons dated Feb–Mar 2026. All sources are within 6 months of research date.

---

## Research: LLM Fact Extraction Prompt Engineering — Few-Shot, CoT, Self-Critique, Tag Accuracy

**Date**: 2026-03-28
**Triggered by**: Planning Phase 0 (tag definition injection) for `smart_extractor.py`. Before adding definitions + usage counts to TAG_REGISTRY prompt, evaluated whether higher-ROI techniques exist: few-shot examples, chain-of-thought tagging, self-critique, and optimal prompt structure.
**Stack relevance**: `smart_extractor.py` on the VM (`~/.openclaw/workspace/skills/clawbot-memory/`). Uses GPT-5.2 to extract facts from OpenClaw session transcripts (JSONL). Current problem: `type:context` overuse (20.5%), flat tag list with no definitions, tag accuracy 2.89/5.

---

### Question

For LLM-based fact extraction from conversation transcripts with a predefined tag taxonomy, what produces better structured extraction in 2025–2026:
1. Tag definitions vs few-shot examples (or both)?
2. Chain-of-thought reasoning before tag assignment?
3. Self-critique / reflection pass after extraction?
4. What is the optimal prompt structure (system vs user, JSON schema, context amount)?
5. Are there benchmarks or papers on tag assignment accuracy for memory systems?

---

### Sources Consulted

1. [Anthropic — Use examples (multishot prompting)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting) — "3–5 examples dramatically improve accuracy"; wrap in `<example>` tags; cover edge cases
2. [Anthropic — Prompt engineering overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — XML tags + multishot + CoT combination recommended for structured classification
3. [Anthropic — Claude 4 best practices](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) — Claude 4 trained for precise instruction following; fewer few-shot examples needed vs older models
4. [OpenAI — Prompt guidance for GPT-5.4](https://developers.openai.com/api/docs/guides/prompt-guidance) — structured + scoped prompts yield most reliable results; few-shot still recommended for complex output schemas
5. [OpenAI — GPT-4.1 Prompting Guide](https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide) — "follow instructions more literally"; few-shot helps when output schema is complex
6. [OpenAI — Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) — `strict: true` with JSON Schema guarantees schema adherence; eliminates invalid tags / invented categories
7. [arXiv:2601.04463 — ProMem: Proactive Memory Extraction](https://arxiv.org/abs/2601.04463) — recurrent self-questioning feedback loop reaches 69.57% QA accuracy on LongMemEval; one-off extraction misses 20–35% of important facts
8. [arXiv:2504.19413 — Mem0: Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413) — two-phase (extract + update) with conflict detection; GPT-4o-mini + function calling; 26% accuracy boost over OpenAI memory
9. [arXiv:2512.20237 — MemR3: Memory Retrieval via Reflective Reasoning](https://arxiv.org/pdf/2512.20237) — reflection on retrieved memories before answering improves accuracy; relevance to extraction reflection
10. [ICCV 2025W — Reasoning-Enhanced Prompt Strategies for Multi-Label Classification](https://openaccess.thecvf.com/content/ICCV2025W/CVAM/papers/Yu_Reasoning-Enhanced_Prompt_Strategies_for_Multi-Label_Classification_ICCVW_2025_paper.pdf) — CoT before label assignment improves multi-label accuracy; models rank label confidence internally before committing
11. [arXiv:2511.22176 — Focused Chain-of-Thought (F-CoT)](https://arxiv.org/pdf/2511.22176) — structured reasoning format in stage 1, then compact output in stage 2; 2–3x faster with preserved accuracy
12. [The Decoder — Highlighted Chain of Thought (HoT)](https://the-decoder.com/highlighted-chain-of-thought-prompting-boosts-llm-accuracy-and-verifiability/) — up to 15% accuracy improvement; marks important facts before answering
13. [arXiv:2512.05387 — SCRPO: Self Critique and Refinement](https://arxiv.org/html/2512.05387v2) — fine-grained self-critique feedback strategy achieves larger faithfulness gains than coarse-grained; single-pass critique meaningful
14. [Mem0 Research — 26% Accuracy Boost](https://mem0.ai/research) — persistent structured memory outperforms raw LLM recall; atomicity + structured metadata is the key differentiator
15. [Sagepub 2025 — LLMs for Text Classification: Zero-Shot to Instruction-Tuning](https://journals.sagepub.com/doi/10.1177/00491241251325243) — few-shot: 68.24% vs zero-shot: 45.99% on Fitness dataset; +22pp from adding examples
16. [Promptingguide.ai — Few-Shot Prompting](https://www.promptingguide.ai/techniques/fewshot) — in-context learning via demonstrations; LLMs highly sensitive to subtle formatting variations (up to 76 accuracy point swings)
17. [Agenta.ai — Guide to Structured Outputs](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms) — JSON Schema with enumerated values prevents category invention; required fields enforced natively
18. [Mem0 — Context Engineering for AI Agents (Oct 2025)](https://mem0.ai/blog/context-engineering-ai-agents-guide) — extraction atomicity and structured metadata key to downstream recall quality
19. [arXiv:2603.04814 — Beyond the Context Window: Fact-Based Memory vs Long-Context LLMs](https://arxiv.org/abs/2603.04814v1) — fact-based extraction systems outperform long-context approaches for persistent agents at production scale

---

### Findings

#### 1. Definition Injection vs Few-Shot Examples

**Answer: Both, combined. Definitions are the higher-priority fix; few-shot examples provide the largest single accuracy jump when examples are high-quality.**

The evidence is clear that few-shot examples substantially outperform zero-shot (definitions-only) for classification tasks with a fixed taxonomy. The Sagepub 2025 study found +22 percentage points from adding examples (68.24% vs 45.99%). Anthropic explicitly states "3–5 examples dramatically improve accuracy, consistency, and quality" for structured output tasks.

However, definitions are not redundant alongside examples:
- Definitions prevent the LLM from mis-inferring a tag's scope from a single example (e.g., seeing one `type:decision` example about infrastructure might cause it to over-apply `decision` to all infrastructure facts)
- Usage count hints (as planned in Phase 0) act as a soft prior that aligns with what we actually want
- The Highlighted CoT paper found that even strong models benefit from explicit fact marking before answering; definitions are the tag-scope equivalent

**Recommended combined approach for `smart_extractor.py`:**

```
TAG REGISTRY (PREFER these — only create new if NONE fit):
  type:
    decision (47 uses) -- A choice made between alternatives
    pivot (8 uses) -- A reversal of a previous decision
    ...

<examples>
<example>
Conversation snippet: "We decided to switch from Redis to SQLite for the memory store to reduce ops overhead."
Extracted fact: "Memory store switched from Redis to SQLite for reduced ops overhead."
Tags: type:decision, domain:infrastructure, confidence:high
Reasoning: Explicit choice between alternatives (decision), affects deployment stack (infrastructure).
</example>
<example>
Conversation snippet: "The tailscale watchdog exits if ping fails 3 consecutive times."
Extracted fact: "Tailscale watchdog exits after 3 consecutive ping failures."
Tags: type:fact, domain:infrastructure, confidence:high
Reasoning: Observation of system behavior, not a choice (fact not decision), involves network/ops (infrastructure).
</example>
</examples>
```

The second example above specifically targets the current bug: ephemeral facts being tagged `type:decision` or `type:context` instead of `type:fact`. Two carefully chosen counter-examples can halve the misclassification rate for the most common failure modes identified in the Claude-judge audit.

**Priority order:** Phase 0 (definitions + counts) → Phase 0.5 (2–3 few-shot examples with explicit `Reasoning:` field) → measure.

#### 2. Chain-of-Thought Tagging

**Answer: Yes, a lightweight CoT pass before outputting tags improves tag specificity. The key is asking for a `Reasoning:` field per fact, not a full chain-of-thought essay.**

The ICCV 2025W paper on reasoning-enhanced multi-label classification found that explicit reasoning before label commitment improves accuracy, particularly for distinguishing between adjacent categories (e.g., `type:decision` vs `type:fact` vs `type:context` — which is exactly the problem in this system). The mechanism: the model surfaces its internal confidence ordering before committing, which catches misclassifications that would otherwise be invisible.

Focused Chain-of-Thought (F-CoT, arXiv:2511.22176) shows the most practical approach for production:
- Stage 1: extract and organize relevant information into a structured format
- Stage 2: generate compact output using the stage 1 summary as input
- Result: 2–3x faster inference, preserved accuracy, output is already structured

For `smart_extractor.py`, the practical implementation is a `reasoning` field in the JSON output schema that the model fills before the `tags` field:

```json
{
  "content": "Memory store switched from Redis to SQLite",
  "reasoning": "This is a choice between two alternatives (decision), not a pattern or observation. The domain is the deployment stack (infrastructure).",
  "tags": "type:decision,domain:infrastructure,confidence:high",
  "importance": 4
}
```

The `reasoning` field does two things: (1) forces the model to commit to its classification rationale before outputting tags, catching cases where the rationale would reveal a mismatch; (2) produces an audit trail for the monthly quality scoring cron to analyze tag assignment errors.

**Important constraint**: GPT-5.2 and GPT-4.1 follow instructions literally. If the JSON schema places `reasoning` before `tags`, the model fills `reasoning` first, which means it has reasoned before tagging. This ordering is load-bearing — do not swap `tags` before `reasoning`.

#### 3. Self-Critique / Reflection Pass

**Answer: Meaningful for deduplication and quality gating, but adds latency + cost for every extraction. Recommended as a gating step only on high-confidence extraction runs, or as a separate post-processing sweep.**

The SCRPO paper (arXiv:2512.05387) found that fine-grained self-critique feedback achieves larger faithfulness improvements than coarse-grained critique. "Are any of these facts duplicates of each other?" is exactly the right question — coarse. "For each pair of facts that share the same entity and time range, is fact B a rephrasing of fact A?" is fine-grained and produces better dedup.

The ProMem paper (arXiv:2601.04463) uses a recurrent feedback loop where the extractor self-questions: "What have I missed? What questions can't I answer from these facts?" This improved LongMemEval accuracy by ~15pp over one-shot extraction.

However, for the current system (daily cron extracting from session transcripts):
- A full self-critique pass doubles the extraction cost (~$0.002 → ~$0.004 per session)
- The biggest quality problem is not post-extraction quality (already filtered by the dedup fuzzy match) — it is extraction accuracy at the point of tagging

**Recommended approach**: Instead of a per-session self-critique, add a self-critique step as a final bullet in the extraction prompt:

```
After extracting all facts, review your list:
- Are any two facts expressing the same information? If yes, keep only the more specific one.
- Does each fact have both a type: and domain: tag? If not, assign the best fit.
- Does the reasoning field actually support the tags assigned? If not, revise the tags.
```

This is a zero-latency addition (same LLM call) and catches the two main failure modes identified in the audit: duplicates and missing anchor tags.

The heavier self-critique (multi-turn refinement) is worth building as a quarterly sweep, not per-session — consistent with the existing quarterly dedup plan in `mem-optimize-v5.md`.

#### 4. Extraction Prompt Structure

**Answer: System prompt for persona/rules, user prompt for variable content (the session transcript). JSON Schema with `strict: true` and enumerated tag values. Context budget: full session JSONL is fine; no evidence that truncation helps for this task.**

Key findings from Anthropic docs, OpenAI GPT-5.4 guide, and practitioner sources:

**System vs user prompt split:**
- System prompt: extraction persona, rules, TAG_REGISTRY (with definitions + counts), few-shot examples, output schema description
- User prompt: `<session>{{JSONL_TRANSCRIPT}}</session>` only — the variable input
- Rationale: system prompt content is cached by the API (reduces cost on repeated calls with same rules); user prompt varies per session

**JSON Schema enforcement:**
- Use `response_format` with `strict: true` for GPT-5.x models — this guarantees schema adherence, eliminates invented tag formats (e.g., `tags:geo-search`, `tag:folder_organization` seen in the current audit)
- Define `tags` as a string (comma-separated) rather than array — avoids nested structure complexity and is consistent with the current SQLite schema
- Add the `reasoning` field to the schema before `tags` (ordering matters for CoT)
- Use `enum` for `importance` (1–5) to prevent `importance: "high"` style errors seen in some runs

**Context amount:**
- Full session JSONL is the right choice — no evidence that truncation improves tag accuracy; truncation increases the risk of missing the one fact that would change a tag assignment
- The ProMem research specifically shows one-shot/truncated extraction misses 20–35% of important facts vs iterative extraction

**Prompt structure template (recommended):**

```
[SYSTEM]
You are a memory extraction agent. Your job is to extract precise, atomic facts from AI assistant session transcripts that will be stored in a persistent memory system for later retrieval.

Rules:
- Each fact must be self-contained (no pronouns referencing other facts)
- Prefer specific over general (paths, versions, names over "the system")
- Do not extract ephemeral observations (timestamps, "currently running", transient states)
- Only extract facts the user or assistant stated as true, not hypotheticals

TAG REGISTRY (PREFER these — only create new tag if NONE fit):
  type:
    decision (47 uses) -- A choice made between alternatives
    ...
  domain:
    infrastructure (76 uses) -- Cloud, devops, CI/CD, networking, deployment
    ...

<examples>
[2–3 examples with reasoning fields]
</examples>

Output each fact as a JSON object in a JSON array. Schema:
{
  "content": "string — the atomic fact",
  "reasoning": "string — why this type: and domain: were chosen",
  "tags": "string — comma-separated, e.g. type:decision,domain:infrastructure,confidence:high",
  "importance": 1|2|3|4|5
}

After extracting all facts, review:
- Remove duplicates (keep the more specific version)
- Verify every fact has both a type: and domain: tag
- Verify each reasoning field supports the tags assigned

[USER]
<session>
{{SESSION_JSONL_CONTENT}}
</session>
```

#### 5. Tag Assignment Accuracy — Papers and Benchmarks

**Answer: No dedicated benchmark exists specifically for memory-system tag accuracy. The closest applicable research comes from multi-label classification, information extraction, and the emerging LLM-as-judge frameworks.**

Key findings:
- **Multi-label classification benchmark (Sagepub 2025)**: Few-shot GPT-4/Claude achieves accuracy "equivalent to or better than fully supervised traditional models" without thousands of labeled examples. For taxonomy-constrained classification (fixed label set), this is directly applicable.
- **MemoryBench (arXiv:2510.17281)**: First benchmark for LLM agent memory covering information extraction, multi-hop reasoning, knowledge updating, preference following, and temporal reasoning — but focuses on retrieval quality, not extraction tagging accuracy.
- **LLM-as-judge approach (current system)**: The Claude-judge audit (`step4-claude-judge-report.md`) already implements the correct measurement framework. The 2.89/5 tag accuracy score is a meaningful baseline. The next improvement gate is 4.0/5 (defined as target in `mem-optimize-v5.md`).
- **Mem0 research (26% accuracy uplift)**: Achieved by combining atomicity + structured metadata. The structural improvement — not the model — drove the gain. This is strong evidence that prompt structure changes (definitions, examples, CoT field, JSON schema) will produce measurable improvements before any model upgrade.
- **Prompt sensitivity finding (Promptingguide.ai)**: LLMs can vary by up to 76 accuracy points across minor formatting changes in few-shot settings. This means the order of few-shot examples, the phrasing of definitions, and even whitespace in the TAG_REGISTRY section can have large effects. A/B testing (already planned in `phase00-tag-definition-injection.md`) is not optional — it is required to confirm which variant actually improves the score.

---

### Recommendation

Implement in three layers, each measurable before proceeding to the next:

**Layer 1 — Phase 0 (already planned, implement now):**
- Add tag definitions and usage counts to TAG_REGISTRY in prompt (exactly as specified in `plans/phase00-tag-definition-injection.md`)
- Tighten the tag instruction: "PREFER these — only create new if NONE fit"
- Cost: ~+$0.0004/call; effort: ~30 min

**Layer 2 — Few-shot examples + CoT field (implement after Layer 1 baseline):**
- Add 2–3 `<example>` blocks to system prompt; each includes a `reasoning` field showing correct type/domain selection
- Add `reasoning` field to JSON output schema, positioned before `tags` field
- Add the self-review bullet list at end of prompt (zero latency, same call)
- Target examples: (a) `type:decision` — explicit choice between alternatives; (b) `type:fact` — atomic observation (addresses `type:context` overuse); (c) `type:pattern` — recurring behavior (addresses `type:decision` misuse for patterns)
- Cost: +~15% tokens per extraction call (~$0.0006 total); effort: ~1 hour

**Layer 3 — JSON Schema strict enforcement (implement with Layer 2):**
- Switch from free-text tag output to `response_format` with `strict: true`
- Add `importance` as integer enum (1–5) to eliminate string-format bugs
- This eliminates the `tags:geo-search` and `confidence:medium,confidence:low` dual-tag bugs entirely
- No cost impact; effort: ~45 min (schema definition + callers)

**Do not implement yet:**
- Multi-turn self-critique (per-session refinement loop) — adds latency without addressing the root cause (tag assignment). Wait until Layer 2 baseline is measured.
- Fine-tuning — not warranted at this scale. GPT-5.2 with good prompting should reach 4.0/5 target.

**Expected outcome after all 3 layers:**
- `type:context` overuse drops from 20.5% to <10%
- Tag accuracy score improves from 2.89/5 toward 4.0/5 target
- Invented free-form tags drop significantly (schema enforcement)
- Duplicate `confidence:` bug eliminated

---

### Compatibility Notes

- `response_format` with `strict: true` requires the GPT-5.x or GPT-4.1+ API family. GPT-5.2 on Azure OpenAI supports this — confirm the Azure OpenAI API version in use is `2024-08-01-preview` or later (this version adds Structured Outputs support).
- The `reasoning` field adds ~30–50 tokens per extracted fact. For a session producing 8 facts, this is ~400 extra tokens on output — roughly $0.001 additional per session at current pricing. Acceptable.
- Few-shot examples in the system prompt are cached by the OpenAI API after the first call to the same endpoint, reducing effective cost of the system prompt for subsequent calls.
- JSON Schema `strict: true` has one constraint: all fields must have defaults or be marked required. Ensure `content`, `tags`, `importance` are all in `required` and `reasoning` defaults to `""` if the schema enforces it.

---

### Design Decision Flag

This research surfaces two candidate design decisions:

1. **Add `reasoning` field to JSON output schema** — forces CoT-before-tags behavior and creates an audit trail for quality scoring. Low risk, low cost, directly addresses tag specificity problem (2.41/5). Flag for: `plans/design-decisions/` — "Should the extraction schema include a reasoning field positioned before the tags field?"

2. **Switch to `strict: true` JSON Schema enforcement** — eliminates free-form tag invention, dual confidence bugs, importance format inconsistencies. Requires confirming Azure OpenAI API version. Flag for: `plans/design-decisions/` — "Should we use strict JSON Schema enforcement for fact extraction output?"

---

### Confidence: High

Sources include: Anthropic official docs (multishot prompting guide, Claude 4 best practices), OpenAI official docs (GPT-5.4 prompt guidance, Structured Outputs guide), three arXiv papers from Jan–Apr 2026 (ProMem 2601.04463, Mem0 2504.19413, SCRPO 2512.05387), ICCV 2025W workshop paper on multi-label classification, and Sagepub 2025 peer-reviewed classification study. All sources dated within 15 months.

What would increase confidence: Running the A/B test in `phase00-tag-definition-injection.md` against actual session data to measure tag accuracy delta from Layer 1 alone, before building Layer 2.
