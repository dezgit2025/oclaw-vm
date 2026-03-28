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

---

## Research: Recall Benchmarks and LLM-as-Judge Rubrics for Memory Retrieval Systems

**Date**: 2026-03-28
**Triggered by**: Memory CI Loop PRD (MEMORY-CI-LOOP.PRD) — the SCORE phase requires a benchmark harness and a judge rubric before any quality measurement can begin
**Stack relevance**: Directly affects `smart_extractor.py` recall quality measurement, `memory_bridge.py` Azure AI Search retrieval scoring, and the SCORE phase of the Memory CI Loop pipeline. Python + SQLite + Azure AI Search (hybrid BM25 + vector).

---

### Question

How do production memory systems benchmark retrieval quality? What metrics, rubric dimensions, judge models, and test design patterns should we adopt for the ClawBot memory system recall benchmark?

---

### Sources Consulted

1. [RAGAS — Available Metrics (official docs)](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) — Authoritative RAGAS metric definitions: context precision, context recall, faithfulness, answer relevancy
2. [RAGAS arXiv paper — 2309.15217](https://arxiv.org/abs/2309.15217) — Original RAGAS paper; reference-free evaluation methodology
3. [Mem0 Benchmark Blog — AI Memory Comparison](https://mem0.ai/blog/benchmarked-openai-memory-vs-langmem-vs-memgpt-vs-mem0-for-long-term-memory-here-s-how-they-stacked-up) — LOCOMO benchmark results: Mem0 66.9% vs OpenAI 52.9% vs MemGPT on LLM-as-Judge score, F1, BLEU-1
4. [Mem0 arXiv — 2504.19413](https://arxiv.org/pdf/2504.19413) — Production memory system architecture; evaluation methodology details
5. [LongMemEval — arXiv 2410.10813](https://arxiv.org/abs/2410.10813) — ICLR 2025; 500-question benchmark; 5 memory dimensions: IE, MR, TR, KU, ABS
6. [LongMemEval GitHub](https://github.com/xiaowu0162/LongMemEval) — Open-source benchmark with scalable chat histories
7. [MemoryBench — arXiv 2510.17281](https://arxiv.org/abs/2510.17281) — Multi-domain continual learning memory benchmark; user feedback simulation
8. [MemoryAgentBench — arXiv 2507.05257](https://arxiv.org/abs/2507.05257) — ICLR 2026; 4-axis memory evaluation: Accurate Retrieval, Test-Time Learning, Long-Range Understanding
9. [MemBench — arXiv 2506.21605](https://arxiv.org/abs/2506.21605) — ACL 2025 Findings; comprehensive agent memory evaluation
10. [Zep arXiv paper — 2501.13956](https://arxiv.org/abs/2501.13956) — Jan 2025; temporal KG architecture; Deep Memory Retrieval benchmark 94.8%; LongMemEval +18.5% accuracy
11. [Zep blog — State of the Art Agent Memory](https://blog.getzep.com/state-of-the-art-agent-memory/) — Reranking strategies: RRF, MMR, episode-mentions reranker, graph-distance reranker, cross-encoders
12. [G-Eval — Confident AI blog](https://www.confident-ai.com/blog/g-eval-the-definitive-guide) — Chain-of-thought rubric evaluation; weighted token probability scoring; CoT improved Spearman ρ from 0.51 → 0.66
13. [LLM-as-Judge best practices — Evidently AI](https://www.evidentlyai.com/llm-guide/llm-as-a-judge) — Comprehensive survey; pairwise vs pointwise tradeoffs; bias mitigation
14. [LLM-as-Judge best practices — Monte Carlo Data](https://www.montecarlodata.com/blog-llm-as-judge/) — 7 best practices including criteria decomposition and CoT
15. [Pairwise vs Pointwise — arXiv 2504.14716](https://arxiv.org/abs/2504.14716) — Empirical study; pairwise flips 35% vs absolute 9%; absolute more robust to manipulation
16. [Position Bias study — ACL IJCNLP 2025](https://aclanthology.org/2025.ijcnlp-long.18.pdf) — Systematic study; all judge models affected; swapping order shifts accuracy >10%
17. [BenchmarkQED — Microsoft Research](https://www.microsoft.com/en-us/research/blog/benchmarkqed-automated-benchmarking-of-rag-systems/) — Automated benchmark harness; AutoQ query generation; bootstrap significance testing at 95% CI
18. [Qdrant RAG Evaluation Guide](https://qdrant.tech/blog/rag-evaluation-guide/) — Golden dataset construction; hard negatives; offline evaluation patterns
19. [Qdrant + Relari AI blog](https://qdrant.tech/blog/qdrant-relari/) — Data-driven offline evaluation without production index
20. [RAG Evaluation Complete Guide — Maxim AI 2025](https://www.getmaxim.ai/articles/complete-guide-to-rag-evaluation-metrics-methods-and-best-practices-for-2025/) — Test set design; statistical significance at 200 queries (50 per class); bootstrap win-rate methodology
21. [Governed Memory Architecture — arXiv 2603.17787](https://arxiv.org/html/2603.17787) — Production multi-agent memory; domain-specific rubric presets (default, sales, support, research); trace-grounded evaluation
22. [Memory in LLMs Survey — arXiv 2509.18868](https://arxiv.org/html/2509.18868) — Layered evaluation: parametric, contextual, external, procedural/episodic memory dimensions
23. [Judge model comparison — Statsig](https://www.statsig.com/perspectives/modelselection-gpt4-vs-claude-vs-gemini) — Gemini 2.5 top hit rate (97.4%); Claude 4 Sonnet strong on coding tasks
24. [Galtea — LLMs as Judges study](https://galtea.ai/blog/exploring-state-of-the-art-llms-as-judges) — Cross-model evaluation comparison; GPT-4o + Claude 3.5 Sonnet exceed baseline
25. [Anthropic cookbook — RAG evaluation (DeepWiki)](https://deepwiki.com/anthropics/anthropic-cookbook/5-retrieval-augmented-generation) — Anthropic-specific retrieval patterns and evaluation guidance

---

### Findings

#### 1. Recall Benchmark Design — Metrics Beyond Precision@k and MRR

Production memory systems use a multi-metric evaluation stack. The key metrics beyond Precision@k and MRR are:

**RAGAS-family retrieval metrics:**
- **Context Precision@K**: Mean of Precision@k for each position, weighted by relevance. Measures whether relevant chunks rank higher than irrelevant ones. Formula: `mean(relevant_chunks_at_rank_k / total_chunks_at_rank_k)` across K positions.
- **Context Recall**: Measures whether the retrieved set covers all ground-truth reference claims. Formula: `claims_in_reference_supported_by_retrieved / total_claims_in_reference`.
- **Faithfulness**: Whether the final answer is grounded in retrieved context (no hallucination). Uses LLM decompose-then-check approach.
- **Answer Relevancy**: Semantic similarity between generated answer and original query.

**Memory-system-specific metrics (production benchmarks):**
- **F1 Score** (LOCOMO benchmark): Overlap between predicted and reference answer tokens. Mem0 uses this as primary metric alongside LLM-as-Judge.
- **BLEU-1**: Unigram overlap for factual recall accuracy.
- **LLM-as-Judge Score** (J): LLM evaluates answer quality against multi-turn conversation ground truth. Mem0 scores 66.9% vs OpenAI memory 52.9% on this.
- **Deep Memory Retrieval (DMR)**: Zep-originated benchmark. Single-hop fact retrieval from long conversation histories. Zep: 94.8%.

**LongMemEval benchmark dimensions** (ICLR 2025 — best-in-class for memory eval):
| Dimension | What it tests |
|-----------|--------------|
| Information Extraction (IE) | Single-hop fact recall from distant history |
| Multi-Session Reasoning (MR) | Synthesis across multiple conversation sessions |
| Temporal Reasoning (TR) | Time-stamped fact resolution, "last known" updates |
| Knowledge Updates (KU) | Tracking when the user changes a fact (old → new) |
| Abstention (ABS) | Correctly returning "I don't know" for unknown facts |

**For the ClawBot memory system specifically**, the most relevant dimensions are IE (can it recall a specific fact?), KU (does recency win when a fact is updated?), and TR (does a newer memory about the same entity surface over an older one?). MR and ABS are lower priority for the current architecture but worth including at low weight.

**Latency as a quality dimension:**
Mem0 tracks p50 and p95 retrieval latency as first-class metrics alongside accuracy. The current hook budget is 4 seconds. Tracking `time_to_first_result_ms` per query in the benchmark harness is recommended — a recall that takes 3.8s is operationally different from one that takes 0.2s even if accuracy is identical.

---

#### 2. LLM-as-Judge for Retrieval — Best Practices and Bias Mitigation

**The core framework: G-Eval (EMNLP 2023, widely adopted)**

G-Eval is the standard approach for building custom LLM judges. It works in two phases:
1. Give the LLM a task description and evaluation criteria → it generates chain-of-thought evaluation steps automatically.
2. Feed those steps plus the actual input into a scoring call → get a 1–5 score.

The key finding: requiring CoT reasoning before the score improves Spearman correlation with human judgments from 0.51 → 0.66. This is the single highest-ROI change when building a judge.

**Scoring mechanism:** Rather than taking the raw "5" label, G-Eval uses the **token log-probabilities** for scores 1–5 and computes a weighted average. This gives a continuous score (e.g., 3.72) rather than a coarse integer, which improves statistical sensitivity when comparing A vs B systems.

**Seven best practices (synthesized from Evidently AI, Monte Carlo, Confident AI):**

1. **One criterion per judge call.** A judge scoring "relevance + specificity + freshness" simultaneously performs worse than three separate calls. Each call should evaluate a single, clearly defined criterion.
2. **Chain-of-thought before scoring.** The judge must emit reasoning before emitting the score — not after. "Rate 1-5, then explain" produces worse calibration than "explain your reasoning, then rate 1-5."
3. **Behavioral anchors on every scale point.** Define what score "1", "3", and "5" mean concretely for each criterion. Anchor-free rubrics drift significantly.
4. **Include the full context.** For retrieval evaluation, pass: the original query, the retrieved memory text(s), and any additional context (tags, age, source session). The judge cannot assess freshness or specificity without knowing the retrieval date.
5. **Provide few-shot examples.** At least 2–3 labeled examples per score level anchor the judge's calibration. Especially critical for dimensions like "actionability" where the definition is subjective.
6. **Run at temperature=0 or near-0.** Evaluation judges should be deterministic. Variability in the judge score introduces noise that masks real retrieval differences.
7. **Log all judge outputs with reasoning.** The `reasoning` field is the audit trail — it surfaces systematic failures (e.g., judge always scores freshness 5 for recent memories regardless of content).

**Biases to guard against:**

| Bias | Severity | Mitigation |
|------|----------|------------|
| Position bias | High (>10% accuracy shift from reordering) | When judging a ranked list, run judge twice with order swapped; average the scores |
| Verbosity bias | Medium | Judge prompt must state: "length is not a quality signal; penalize verbose answers that add no information" |
| Self-preference bias | Medium for same-model judge | Use a different model family as judge than the model that produced the memories |
| Anchoring bias | Medium | Present query first, then memory; never present the "correct" answer before asking for a relevance score |

**Key finding on memory systems specifically:** Retrieval judges for memory differ from RAG judges because the ground truth is not a document but a user's conversational history. The judge needs to understand **what the user would benefit from knowing** — not just whether two strings match semantically.

---

#### 3. Pairwise Comparison vs Absolute Scoring

**Recommendation: Use absolute scoring for the ClawBot benchmark, pairwise as a secondary check.**

The empirical evidence (arXiv 2504.14716):
- **Pairwise**: Preferences flip in ~35% of cases when conditions are re-run. More reliable for relative comparisons (A vs B) but vulnerable to distractor features the LLM judge happens to favor.
- **Absolute pointwise**: Score flips in only ~9% of cases. More robust to manipulation (models can't exploit spurious attributes as easily). Better for production monitoring where you evaluate every retrieval individually.

**When each is appropriate:**

| Scenario | Method |
|----------|--------|
| Comparing two retrieval strategies (BM25 vs hybrid) | Pairwise: judge picks winner per query, aggregate win rate |
| Measuring system quality over time (CI loop) | Absolute: scores per dimension per query; track drift |
| Evaluating after a scoring change (boost/decay tuning) | Pairwise: before-after comparison on same query set |
| Production monitoring of each recall event | Absolute: feasible to run per-request; pairwise requires pairs |

**Pairwise at scale:** The `n^2` scaling problem is real. With 100 test queries and 2 systems, pairwise requires 200 comparisons (100 per direction). With 5 system variants, it requires 1,000 comparisons. Mitigation: use pairwise only for the top-2 candidates after absolute scoring narrows the field.

---

#### 4. Test Query Design — Diversity, Edge Cases, and Statistical Significance

**How many queries are needed?**

The BenchmarkQED/AutoQ methodology (Microsoft Research, 2025): 50 queries per category × 4 categories = 200 total queries. With bootstrap significance testing at 95% CI, this is sufficient for a production benchmark with 6 trials per query. LongMemEval uses 500 questions for a publishable academic benchmark.

**Practical guidance for the ClawBot benchmark:**

For a 2-hour construction effort with human review, target **80–120 queries** across category groups (see rubric section below). This is the minimum for statistical significance with bootstrap testing. Below 50 queries, individual query variance dominates.

**Query type taxonomy (adapted from LongMemEval + MemoryAgentBench):**

| Category | Examples | % of test set |
|----------|----------|---------------|
| Verbatim fact recall | "What framework does ClawBot use?" | 20% |
| Temporal ordering | "What was the model before the current one?" | 20% |
| Knowledge update | "What is the current port for the gateway?" (answer changed) | 15% |
| Multi-hop synthesis | "What services depend on the VM being on?" | 15% |
| Negatives / abstention | "What is ClawBot's Slack channel?" (never mentioned) | 15% |
| Hard negatives | Similar-sounding but different facts | 15% |

**Hard negatives are critical.** Without them, a retrieval system that returns everything scores 100% on recall but has useless precision. Hard negatives are queries where a plausible-sounding but wrong memory exists (e.g., query about "port 18792" where a memory about "port 18789" also exists).

**Adversarial / edge case queries to include:**
- Short queries (1–2 words): "tailscale IP"
- Over-specified queries: full exact sentence from a memory
- Ambiguous queries: "the main config file" (multiple files in memory)
- Stale queries: facts that have been superseded (tests KU dimension)
- Cross-domain queries: query spans two unrelated memory clusters

**Query construction workflow:**
1. Mine actual ClawBot session queries from `~/.openclaw/agents/main/sessions/` — these are real queries, high ecological validity.
2. Augment with synthetic queries generated by GPT-4.1 or Claude Sonnet against each memory in the DB.
3. Human review to remove trivially easy queries and add the missing edge-case categories.
4. For each query, manually label 1–3 ground-truth memory IDs that should be returned.

---

#### 5. Local Testing Patterns — Offline Without Production Search Index

**Three approaches for offline testing:**

**Approach A: Snapshot replay (recommended for ClawBot)**
- Export the current SQLite DB: `cp ~/.claude-memory/memory.db /tmp/benchmark-snapshot-YYYYMMDD.db`
- Run benchmark queries against the snapshot using `smart_extractor.py recall` with `--db /tmp/benchmark-snapshot-YYYYMMDD.db` (requires adding a `--db` flag if not present)
- All Azure AI Search calls are real but against the indexed state at snapshot time
- Advantage: tests the actual search stack; no mocking needed
- Risk: search index state and DB state can diverge; run `memory_bridge.py sync` before taking the snapshot

**Approach B: Local mock with pre-computed embeddings**
- Pre-compute embeddings for all memories and store them in the snapshot
- Run cosine similarity locally (numpy/sklearn) against pre-computed vectors
- No network calls; fully deterministic; fast (~5ms per query)
- Best for unit testing the scoring logic in isolation, not for testing the full retrieval pipeline
- Library: `sentence-transformers` or Azure OpenAI embeddings cached to disk

**Approach C: Ragas offline evaluation**
The RAGAS framework can run entirely offline against a local dataset:
```python
from ragas import evaluate
from ragas.metrics import context_precision, context_recall
from datasets import Dataset

# Build dataset from your ground-truth file
data = {
    "question": [...],           # test queries
    "contexts": [[...]],         # retrieved memory texts
    "ground_truth": [...]        # expected answer or reference text
}
result = evaluate(Dataset.from_dict(data), metrics=[context_precision, context_recall])
```
RAGAS calls an LLM internally for LLM-based metrics — configure it to use Azure OpenAI to stay on-stack.

**Recommended pattern for the Memory CI Loop:**
- Approach A (snapshot) for full end-to-end benchmark runs (weekly or per-cycle)
- Approach B (local mock) for fast iteration on scoring algorithm changes (runs in seconds)
- Store benchmark results as `quality/data/benchmark-results-YYYYMMDD.json` per the CI Loop artifact convention

---

#### 6. Scoring Rubric Dimensions for Memory Retrieval

**Core rubric (6 dimensions, 1–5 scale each):**

| Dimension | Definition | Weight |
|-----------|-----------|--------|
| **Topical Relevance** | Does the memory address the query's subject matter? | 30% |
| **Specificity** | Is the memory precise (exact value, name, path) or vague? | 20% |
| **Temporal Freshness** | Is this the most current version of this fact? | 20% |
| **Actionability** | Can the user act on this memory to solve their problem? | 15% |
| **Completeness** | Does the retrieved set cover all sub-aspects of the query? | 10% |
| **Noise Penalty** | Are irrelevant memories absent from the returned set? | 5% |

**Behavioral anchors — Topical Relevance (example):**
- **5**: Memory directly answers the query or provides the exact fact being asked for.
- **4**: Memory is on the same topic and substantially reduces the answer search space.
- **3**: Memory is related to the topic but requires inference to connect to the query.
- **2**: Memory is in the same domain (e.g., "VM") but does not address the query's specific aspect.
- **1**: Memory is topically unrelated or contradicts the query's assumptions.

**Freshness scoring note:** Freshness cannot be scored on a simple recency-of-creation basis. A memory about a permanent configuration fact (e.g., Tailscale IP) does not lose freshness with age, while a memory about "current model being used" (a volatile fact) becomes stale in days. The judge prompt must include the memory's `created` timestamp, `updated` timestamp, and `access_count` — and the rubric anchor for "5" should be "this is the most current version of this fact in the context of what would be true today."

**Actionability scoring note:** This is the hardest dimension to calibrate. Behavioral anchor for "5": "The user can take a concrete next step using only this memory without additional lookup." For "3": "The memory is useful background but requires combining with other information."

**Optional dimension: Precision-of-Source (for trust calibration):**
Does the memory cite enough context to verify its origin? (e.g., "from session 2026-02-20" is better than no source). This is useful for catching GPT-hallucinated memories that slipped through extraction.

**Judge prompt template (sketch):**

```
You are evaluating a memory retrieval system. Given a user query and a retrieved memory, score the memory on the following dimension:

DIMENSION: {dimension_name}
DEFINITION: {definition}

Scale:
5 — {anchor_5}
3 — {anchor_3}
1 — {anchor_1}

Query: {query}
Memory text: {memory_text}
Memory created: {created}
Memory tags: {tags}

Think through your evaluation carefully, then output:
REASONING: [your explanation]
SCORE: [1-5]
```

**Per the G-Eval finding**: always put REASONING before SCORE in the output format. The judge produces better scores when forced to commit to a reasoning trace before emitting the number.

---

### Recommendation

**Phase 1 (immediate — 1 week):** Build a golden query set of 80 queries across the 6 category types above. Mine 40 from real session logs, generate 40 synthetically against the current memory DB, manually label ground-truth memory IDs. Store in `quality/data/benchmark/golden-queries.json`.

**Phase 2 (1–2 weeks):** Build a RAGAS-based offline evaluation harness using Approach A (snapshot replay) + Approach B (local mock cosine for fast runs). Use RAGAS context_precision and context_recall as the primary retrieval metrics. Add a custom LLM judge for Specificity and Freshness (the two dimensions RAGAS does not measure natively).

**Phase 3 (2–3 weeks):** Integrate the benchmark into the Memory CI Loop SCORE phase. Target metrics: Context Precision ≥ 0.70, Context Recall ≥ 0.75, LLM-Judge composite ≥ 3.5/5. Run on every optimization cycle.

**For the judge model:** Use Claude claude-sonnet-4-6 (already available via the gateway) or GPT-5.2 (already on-stack for extraction). Do not use the same model for extraction AND judging — this introduces self-preference bias. If extraction uses GPT-5.2, judge with Claude Sonnet. If extraction switches to Claude, judge with GPT-5.2.

**For pairwise A/B testing** (when evaluating a new scoring tuning): run pairwise comparison on the same 80-query golden set; report win rates with bootstrap significance at 95% CI. Require at least 60% win rate to declare a variant superior (guard against noise with the small set).

---

### Compatibility Notes

- RAGAS library requires Python 3.10+; the ClawBot venv (`~/.openclaw/workspace/skills/clawbot-memory/.venv/`) is Python 3.10 — compatible.
- RAGAS `evaluate()` uses an LLM internally. Configure to use the same Azure OpenAI endpoint already in `/etc/environment` (`AZURE_OPENAI_CHAT_ENDPOINT`). Set `ragas.llm` to an `AzureChatOpenAI` instance to avoid OpenAI API key requirement.
- The RAGAS framework calls the judge LLM once per metric per query — for 80 queries × 2 metrics × ~500 tokens per call = ~80K tokens per full benchmark run. At GPT-5.2 pricing, this is roughly $0.10–0.20 per run. Acceptable for weekly cadence.
- Token log-probabilities (required for the G-Eval weighted scoring approach) are available from Azure OpenAI with `logprobs=True` in the API call. Confirm this is supported on the `2024-08-01-preview` or later API version already in use.
- Azure AI Search hybrid mode (BM25 + vector) is the retrieval backend. The benchmark harness should test both modes separately and combined to isolate which component is limiting recall.

---

### Design Decision Flags

1. **Rubric weight calibration** — The 30/20/20/15/10/5 weights above are starting estimates. After the first benchmark run, measure which dimensions show the most variance across queries — high-variance dimensions carry more diagnostic signal and should receive higher weight in the composite score. Flag for: `plans/design-decisions/` — "What weights should the memory retrieval rubric dimensions use?"

2. **Judge model pairing** — Currently GPT-5.2 is used for extraction. The recommendation is to use Claude Sonnet as the judge to avoid self-preference bias. This requires the benchmark harness to call the openclaw gateway (Claude model via GitHub Copilot) rather than Azure OpenAI directly. Flag for: `plans/design-decisions/` — "Which model serves as the retrieval quality judge, and how is it called from the benchmark harness?"

3. **Snapshot vs live index** — Approach A (snapshot) gives reproducible benchmarks but can drift from the live index. Consider adding a weekly automated benchmark that runs against the live index and a separate regression suite that runs against a pinned snapshot. Flag for: `plans/design-decisions/` — "Should the benchmark harness use a pinned DB snapshot or the live Azure AI Search index?"

---

### Confidence: High

Primary sources: 6 peer-reviewed/ICLR papers from 2025 (LongMemEval, MemoryBench, MemoryAgentBench, Zep, G-Eval lineage, arXiv pairwise/pointwise), official RAGAS docs (stable release), Mem0 production benchmark (public), Microsoft Research BenchmarkQED (2025), Qdrant evaluation guide (2025), and 5 practitioner guides from Evidently AI, Monte Carlo, Confident AI, and Statsig — all dated within 12 months.

What would increase confidence: Running the actual benchmark harness against the ClawBot memory DB and calibrating rubric anchors against human-labeled examples from real ClawBot sessions. The theoretical framework is well-established; the open question is whether the behavioral anchors generalize to the specific content types in the ClawBot memory store (VM ops, OAuth flows, model configs).


---

## Research: Memory Retrieval Best Practices for AI Agent Systems (2025-2026)

**Date**: 2026-03-28
**Triggered by**: Planning round for Memory CI Loop Phase 2 improvements — specifically to inform the recall optimizer plan (plans/memory-recall-optimizer1.md) and identify where the current ClawBot memory system lags production best practices
**Stack relevance**: Azure AI Search (oclaw-search, basic tier), SQLite (memory.db), smart_extractor.py recall pipeline, memory_bridge.py hybrid search, static topic expansion map, freshness + importance scoring profile

---

### Question

What are the 2025-2026 best practices for the following 10 areas in an AI agent memory system with ~100 memories, hybrid Azure AI Search, hook-based recall injection, and a 4-second budget per turn?

1. Query reformulation (HyDE, decomposition, entity extraction)
2. Reranking strategies (cross-encoder vs LLM vs semantic)
3. Contextual retrieval (Anthropic's approach applied to memory facts)
4. Adaptive retrieval (relevance gating — when to skip recall)
5. Memory consolidation (atomic facts vs summaries)
6. Reciprocal Rank Fusion for multi-query combination
7. Late interaction models (ColBERT/ColPali) viability
8. Few-shot retrieval — example-guided query expansion
9. Embedding model selection for small stores
10. Conversation-context-weighted retrieval (Mem0, Zep, MemGPT approaches)

---

### Sources Consulted

1. [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) — Technique for prepending per-chunk context before embedding; reduces failed retrievals 49%; prompt caching makes it cheap
2. [Arxiv — Adaptive Memory Admission Control for LLM Agents (2603.04549, Mar 2026)](https://arxiv.org/abs/2603.04549) — A-MAC framework for relevance gating; 5-factor scoring for memory admission
3. [Arxiv — Zep: Temporal Knowledge Graph (2501.13956, Jan 2025)](https://arxiv.org/abs/2501.13956) — Bitemporal KG architecture; 18.5% accuracy gain, 90% latency reduction vs baseline
4. [Arxiv — Mem0: Production-Ready Scalable Memory (2504.19413)](https://arxiv.org/pdf/2504.19413) — Hybrid vector + graph; 26% F1 uplift on LOCOMO vs OpenAI memory
5. [Arxiv — Choosing How to Remember: Adaptive Memory Structures (2602.14038, Feb 2026)](https://arxiv.org/html/2602.14038) — MoE gate functions for adaptive retrieval weight assignment
6. [Arxiv — RAG-Fusion (2402.03367)](https://arxiv.org/abs/2402.03367) — Multi-query generation + RRF; +8-10% answer accuracy, +30-40% comprehensiveness
7. [Voyage AI — The Case Against LLMs as Rerankers (Oct 2025)](https://blog.voyageai.com/2025/10/22/the-case-against-llms-as-rerankers/) — Purpose-built cross-encoders: 60x cheaper, 48x faster, up to 15% better NDCG@10 than LLMs
8. [ZeroEntropy — Ultimate Guide to Reranking 2026](https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025) — Cross-encoder delivers 95% of LLM reranking accuracy at 3x speed
9. [ZeroEntropy — LLM as Reranker Deep Dive](https://www.zeroentropy.dev/articles/should-you-use-llms-for-reranking-a-deep-dive-into-pointwise-listwise-and-cross-encoders) — Latency data: LLM reranking adds 4-6s vs cross-encoder's ms range
10. [Microsoft Learn — Azure AI Search Hybrid Search Scoring (RRF)](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking) — Azure's built-in RRF implementation for hybrid; scoring profiles applied pre- and post-semantic rerank
11. [Microsoft Learn — Use Scoring Profiles with Semantic Ranking](https://learn.microsoft.com/en-us/azure/search/semantic-how-to-enable-scoring-profiles) — Scoring profiles applied twice in hybrid + semantic pipeline; functions (freshness/magnitude) survive semantic rerank; text_weights do not
12. [Microsoft Learn — Add Scoring Profiles](https://learn.microsoft.com/en-us/azure/search/index-add-scoring-profiles) — Freshness function supports linear/constant/quadratic interpolation; quadratic favors very recent docs strongly
13. [Jina AI — ColBERT v2 Multilingual](https://jina.ai/news/jina-colbert-v2-multilingual-late-interaction-retriever-for-embedding-and-reranking/) — 128-dim token embeddings; available on Azure marketplace; 1.5% perf drop from 128→64 dims
14. [Weaviate — Late Interaction Overview (ColBERT, ColPali)](https://weaviate.io/blog/late-interaction-overview) — Token-level storage requirement makes ColBERT impractical for tiny stores
15. [Voyage AI — voyage-3-large launch (Jan 2025)](https://blog.voyageai.com/2025/01/07/voyage-3-large/) — +9.74% over text-embedding-3-large on RTEB; Matryoshka + int8 quantization supported
16. [Reintech — Embedding Models 2026 Comparison](https://reintech.io/blog/embedding-models-comparison-2026-openai-cohere-voyage-bge) — Cohere embed-v4 leads MTEB at 65.2; OpenAI text-embedding-3-large at 64.6; Voyage-3-large dominates retrieval-specific benchmarks
17. [Mem0 Docs — Graph Memory](https://docs.mem0.ai/open-source/features/graph-memory) — Entity extractor + relations generator → directed labeled graph; entity-centric retrieval with subgraph expansion
18. [Promptagator — Few-shot Dense Retrieval from 8 Examples (arxiv 2209.11755)](https://arxiv.org/abs/2209.11755) — 8 task-specific examples allow dual encoders to outperform heavily-engineered MS MARCO models
19. [Personalize Before Retrieve — LLM-based Personalized Query Expansion (arxiv 2510.08935)](https://arxiv.org/html/2510.08935v1) — User history + explicit persona context improves query expansion for personal retrieval
20. [Haystack — Contextual Retrieval Implementation](https://www.anthropic.com/news/contextual-retrieval) — Contextual BM25 + contextual embeddings combined reduces failures 67%
21. [Microsoft Tech Community — Azure AI Search Hybrid + Semantic Ranking](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/azure-ai-search-outperforming-vector-search-with-hybrid-retrieval-and-reranking/3929167) — Benchmarks show hybrid + semantic ranking outperforms pure vector search significantly
22. [Mem0 — AI Memory Research LOCOMO Benchmark](https://mem0.ai/research) — 26% relative uplift in LLM-as-judge score vs OpenAI memory (66.9% vs 52.9%)
23. [Zep Blog — Temporal Knowledge Graph Architecture](https://blog.getzep.com/zep-a-temporal-knowledge-graph-architecture-for-agent-memory/) — Graphiti engine; episodic/semantic/community subgraph hierarchy
24. [Knowledge-Aware Query Expansion with LLMs — ACL 2025](https://aclanthology.org/2025.naacl-long.216.pdf) — Entity-anchored query expansion with knowledge graph context outperforms plain LLM expansion

---

### Findings

#### 1. Query Reformulation — HyDE, Decomposition, Entity Extraction

**HyDE (Hypothetical Document Embeddings):**
HyDE generates a synthetic answer to the query, embeds that answer, and uses the embedding for retrieval rather than the raw query. This bridges the query-document embedding space gap (short question vs longer fact). However:
- HyDE adds 25-60% latency on small LLMs
- For small stores (~100 facts), the benefit is reduced because keyword overlap is high anyway
- Risk: if the generated hypothesis is wrong, retrieval degrades
- **Verdict for this use case:** Marginal benefit given 100-memory store + 4s budget. Low priority. Use the static/LLM hybrid expansion already planned.

**Query Decomposition:**
Enterprise search pipelines decompose multi-intent queries into 3-7 sub-queries. For memory recall, this matters when the user message contains two unrelated topics (e.g., "what model does the gateway use and what's the Tailscale IP?"). The current static domain map handles this partially. The planned LLM fallback expansion is the right direction.

**Entity Extraction Before Search:**
The A-Mem paper (Feb 2026) and Mem0 architecture both extract named entities from the input before search. Entity tokens (e.g., "Tailscale", "Claude Opus", "oclaw") are then used as keyword anchors for BM25. This is particularly effective for small stores where entity hit rate is high. Recommendation: extract key nouns/proper nouns from user message as an additional BM25 filter. Cost: one small LLM call or a regex pass.

**Best practice for small stores (< 1K facts):** Static map + LLM fallback + entity extraction is the right stack. Full HyDE is overkill; entity anchoring is cheap and high-value.

---

#### 2. Reranking Strategies

**The core finding is clear and consistent across sources:**
- LLM reranking adds 4-6 seconds of latency — exceeds the 4s budget entirely
- Cross-encoder reranking runs in 5-10ms on top-20 candidates
- Purpose-built cross-encoders are 60x cheaper, 48x faster, and up to 15% better on NDCG@10 than LLMs for reranking tasks (Voyage AI analysis, Oct 2025)
- ZeroEntropy benchmarks: cross-encoder delivers 95% of LLM reranking accuracy at 3x the speed

**Azure AI Search Semantic Ranking** (the L2 reranker built into Azure) uses Microsoft's language understanding models. It is a form of semantic cross-encoder. According to MS docs and benchmarks, it measurably improves over pure BM25+vector RRF on text queries. Critically, semantic ranking is applied to the top-50 results from L1 (RRF), not to all documents.

**Important Azure-specific behavior for scoring profiles + semantic ranking:**
- Scoring profile functions (freshness, magnitude boosts) are applied **twice**: once at L1 before semantic ranking, and once after semantic ranking
- Text_weights (field-level boosts like `"content": 1.5, "tags": 1.2`) are **NOT applied** after semantic reranking — only scoring functions survive
- This means the tags field weight in the current plan will be erased after semantic rerank. Must use magnitude/freshness functions, not text_weights, for durable boosting.

**Recommendation:** Keep Azure semantic ranking enabled. Do not add cross-encoder on top — that's double-reranking and adds latency. The Azure semantic ranker IS the cross-encoder for this stack. Ensure scoring profile uses functions (not text_weights) for importance and freshness.

---

#### 3. Contextual Retrieval (Anthropic's Approach Applied to Memory Facts)

Anthropic's contextual retrieval prepends a context snippet to each chunk before embedding. For documents, this looks like: "This chunk describes the X section of Y document. The main topic is Z. [original chunk text]."

**For memory facts, this translates to:** prepending metadata context before embedding the fact. Instead of embedding just "The gateway uses claude-opus-4.6", embed: "Memory from project openclaw_vm, domain: infrastructure, type: architecture, stored 2026-02-20. The gateway uses claude-opus-4.6 as its primary model."

The result:
- Contextual embeddings reduce failed retrievals by 49% in Anthropic's tests
- Combined with contextual BM25, failure rate drops 67%
- Cost: one Claude API call per fact at indexing time (not retrieval time); prompt caching makes this cheap for batch updates

**Key insight:** This is a one-time re-indexing improvement, not a per-query cost. The current memory facts are stored as bare text in Azure. Re-indexing with contextual embeddings would require: (1) generate a 1-2 sentence context prefix per memory using the tags/project/date metadata already available, (2) concatenate to the content before calling the embedding model, (3) re-sync to Azure AI Search.

**Verdict:** High value, modest implementation cost. Applicable to memory facts. Flag as design decision.

---

#### 4. Adaptive Retrieval — When to Skip Recall

**A-MAC (Adaptive Memory Admission Control, Mar 2026)** addresses the retrieval side too. The paper introduces a relevance gate as a structured decision problem decomposed into 5 factors: future utility, factual confidence, semantic novelty, temporal recency, and content type prior.

More practically, the Adaptive Memory Structures paper (Feb 2026) identifies:
- Simple conversational turns (greetings, acknowledgments, short social exchanges) rarely benefit from recall
- Recall is most useful when: entity names are present, questions reference past state, planning queries require context

**Production heuristics used in the wild:**
- Skip recall if message token count < 10 tokens
- Skip recall if message contains no nouns or named entities
- Skip recall if message starts with pure social phrases ("thanks", "ok", "sounds good", etc.)
- Lightweight classifier: measure cosine similarity between the query embedding and a centroid of all memories; if similarity < threshold (e.g., 0.15), skip recall

**Verdict:** The current system fires recall on every turn. Adding a lightweight relevance gate (token count + entity check + cosine threshold) can reduce unnecessary recall calls by 20-35% based on the A-MAC paper results, while reducing latency on trivial turns. Implement as a pre-filter in the hook handler before calling smart_extractor.py.

---

#### 5. Memory Consolidation — Atomic Facts vs Summaries

**The research community has largely converged on a hybrid approach:**
- Mem0 stores atomic statements (one fact per memory entry) — better for retrieval precision
- Zep stores entities + relationships in a knowledge graph + episodic subgraph — better for temporal reasoning and multi-hop
- MemGPT/Letta stores structured memory blocks in context and actively rewrites them — best for coherence, worse for recall diversity

**Why atomic facts win for retrieval:**
- A single query matches one atomic fact more precisely than a summary that bundles N facts
- Summaries blur semantic signal — the embedding of "The system uses Tailscale, which is version 1.94.2 and connects via exit node chromeos-nissa" is less focused than three separate facts
- Retrieval systems (especially BM25) score exact keyword matches more reliably against atomic facts

**Why summaries fail:**
- Consolidation is lossy — the summary never fully captures the original facts
- No ground-truth re-check: the system never verifies summaries against source after time passes
- Summaries become stale silently (key risk per EverMind-AI EverMemOS research)

**Exception — community nodes (Zep pattern):** High-level summaries of a domain (e.g., "User's overall infrastructure setup") stored as a "community node" can serve as a router to atomic facts. This two-tier approach (atomic facts + domain summaries) retrieves better than either alone.

**Verdict:** Keep atomic fact storage (current approach is correct). Consider adding a single "summary node" per domain as a routing aid, but not as a replacement for atomic facts.

---

#### 6. Reciprocal Rank Fusion (RRF) for Multi-Query Combination

Azure AI Search uses RRF natively for hybrid search (BM25 + vector). The formula is `score = sum(1 / (k + rank_i))` where k=60 by default.

**RAG-Fusion pattern** (arxiv 2402.03367) extends this: generate N sub-queries → run N separate searches → RRF-fuse the result lists. This yields +8-10% answer accuracy and +30-40% comprehensiveness vs single-query RAG.

**For the current system:** smart_extractor.py already runs 5 parallel queries per expanded topic. The results are currently deduped and priority-ranked. **RRF is strictly better** than priority-based dedup for combining lists from parallel queries because:
- RRF rewards results that appear in multiple sub-query result lists (consensus signal)
- Priority ranking ignores cross-query rank information
- RRF is parameter-free and doesn't require tuning per-domain

**Implementation:** Replace the current dedup+priority sort in `cmd_recall()` with RRF fusion:
```python
def rrf_fuse(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for result_list in result_lists:
        for rank, item in enumerate(result_list, start=1):
            mem_id = item["id"]
            scores[mem_id] = scores.get(mem_id, 0) + 1.0 / (k + rank)
            items[mem_id] = item
    return sorted(items.values(), key=lambda x: -scores[x["id"]])
```

This is a ~15-line change to smart_extractor.py and likely the highest-ROI improvement available with zero additional API calls.

---

#### 7. Late Interaction Models (ColBERT/ColPali) — Viability for Small Stores

ColBERT stores per-token embeddings (128 dims × N tokens per document) rather than a single document embedding. For a 100-word memory fact, this means ~25 token vectors × 128 dims = 3,200 floats vs 3,072 floats for a single text-embedding-3-large embedding.

**For 100 memories:** Storage overhead is manageable (~320K floats vs ~307K). The problem is infrastructure:
- ColBERT requires a compatible vector store (Qdrant supports it natively; Weaviate supports it)
- **Azure AI Search does NOT natively support ColBERT late interaction** as of March 2026 — it uses single-vector fields
- Jina ColBERT v2 is on Azure Marketplace as an embedding API, but the multi-vector scoring is handled at the client side, not server side
- This would require replacing Azure AI Search with Qdrant or implementing client-side MaxSim scoring

**Verdict:** Not viable for this stack. Azure AI Search doesn't support token-level multi-vector scoring. The accuracy gain (ColBERT typically +3-8% over bi-encoder on retrieval benchmarks) is not worth migrating the vector store for a 100-memory system. Skip.

---

#### 8. Few-Shot Retrieval — Example-Guided Query Expansion

Promptagator (Google, NeurIPS 2022, still widely cited) showed that 8 task-specific examples in the query expansion prompt allow dual-encoder retrievers to outperform models trained on MS MARCO. The key mechanism: examples teach the LLM the vocabulary and specificity level expected.

**Applied to smart_extractor.py's LLM fallback expansion:**
The current planned prompt is: `"Generate 3-5 search synonyms/related terms for: '{topic}'. Return comma-separated list only."`

Adding 2-3 few-shot examples from the actual ClawBot domain would improve expansion quality:
```
Examples:
  "gateway restart" → "openclaw-gateway.service, restart_gateway.py, systemctl user, watchdog, gateway crash"
  "google auth expired" → "invalid_grant, token refresh, oauth2, reauth, credential rotation"
  "tailscale down" → "exit node, wireguard, tailscale status, residential IP, failover, egress"

Now expand: "{topic}"
```

**Cost:** ~200-300 extra tokens per expansion call. Negligible at $0.001/call.
**Benefit:** More domain-specific expansions that match actual memory content. Especially valuable because ClawBot's domain vocabulary (openclaw, desazure, gateway, IMDS) is not in general-purpose training data.

**Verdict:** High value, low cost. Add 3-5 domain examples to the LLM expansion prompt. Flag for Round 2 of the recall optimizer.

---

#### 9. Embedding Model Selection for Small Stores (~100 memories)

**2025-2026 benchmark summary (MTEB + RTEB):**

| Model | MTEB Score | Retrieval (RTEB) | Dims | Notes |
|-------|-----------|-----------------|------|-------|
| Cohere embed-v4 | 65.2 | Strong | 1024 | Multimodal; 128K context window |
| text-embedding-3-large | 64.6 | Baseline | 3072 | Current model; Matryoshka |
| Voyage-3-large | N/A (MTEB) | +14% over OAI on RTEB | 1024 | Best retrieval; Matryoshka + int8 |
| Voyage-3.5 | N/A | +9.74% over OAI-v3-large | 1024 | Latest as of Mar 2026 |
| BGE-M3 | ~64 | Competitive | 1024 | Open source; multilingual |

**Key finding for small stores:**
For a ~100-memory store, the embedding model choice matters less than for million-document corpora because:
- All top models perform within ~5% of each other on small, coherent corpora
- With 100 facts, cosine similarity space is not crowded — even a weaker embedding separates facts well
- The bigger gains come from query expansion, contextual embedding, and scoring profile tuning

**Should you switch from text-embedding-3-large (3072 dims)?**
- The 3072-dim vector is genuinely oversized for 100 memories (Azure AI Search stores ~307K floats of mostly redundant signal)
- Switching to Voyage-3.5 (1024 dims) would: save ~67% vector storage, reduce search latency marginally, and gain +9.74% on retrieval benchmarks
- However, switching requires: re-embedding all memories, updating the Azure index schema, testing the re-indexed store
- **At 100 memories, this is low-risk** — re-embedding takes minutes and costs ~$0.001

**Verdict:** text-embedding-3-large is adequate for now. If re-indexing for contextual retrieval (item 3 above), switch to Voyage-3.5 at the same time — combining two improvements into one migration.

---

#### 10. Memory Weighting by Conversation Context (Mem0, Zep, MemGPT)

**Mem0 approach:**
- Extracts entities and relationships from the full conversation (not just last message)
- Weights retrieval by: entity overlap, semantic similarity to most recent N turns, and importance score
- Graph layer tracks which entities co-occur across memories
- On LOCOMO benchmark: 66.9% LLM-as-judge score vs 52.9% for OpenAI memory (26% relative gain)

**Zep approach (Temporal Knowledge Graph):**
- Stores every memory with both event time (T) and ingestion time (T') — bitemporal
- When querying, the graph traversal scores edges by temporal recency and validity window
- Supports "what was true at time T?" queries — critical for superseded fact handling
- 18.5% accuracy improvement + 90% latency reduction vs naive RAG baseline
- Key insight: invalidating old facts (not deleting) allows temporal reasoning without hallucination

**MemGPT/Letta approach:**
- Maintains structured memory blocks in the active context window
- Agent rewrites blocks in real-time when new information contradicts stored state
- Drawback: requires memory to fit in context window; doesn't scale beyond ~50-100 facts

**Most relevant insight for this system:**
The current system queries on the last user message only. Using the last 2-3 conversation turns as additional query context (concatenated or averaged) would significantly improve recall for multi-turn conversations. Zep's benchmark shows this is one of the highest-value changes.

**Practical implementation:**
```python
# Current: query = user_message
# Improved: query = last_3_turns_summary + user_message
def build_recall_query(current_message: str, recent_turns: list[str]) -> str:
    if recent_turns:
        context = " ".join(recent_turns[-2:])  # Last 2 turns
        return f"{context} {current_message}"
    return current_message
```

This is already available in the hook handler context (the hook receives the full conversation object). Adding it is a ~10-line change.

---

### Recommendation

**Ranked by ROI × effort:**

| Priority | Improvement | Effort | Expected Gain | When |
|----------|-------------|--------|---------------|------|
| 1 | **RRF fusion** for multi-query combination (replace dedup+priority sort) | 30 min | +8-10% precision | Round 2 |
| 2 | **Conversation context** in recall query (last 2 turns + current message) | 30 min | +5-10% MRR for multi-turn queries | Round 2 |
| 3 | **Relevance gate** — skip recall on trivial turns (<10 tokens, no entities) | 45 min | -20-35% unnecessary calls, -latency | Round 2 |
| 4 | **Few-shot domain examples** in LLM expansion prompt (3-5 ClawBot examples) | 30 min | Better expansion vocabulary | Round 2 |
| 5 | **Scoring profile fix** — remove text_weights, keep functions only (freshness + importance) | 30 min | Boosts survive semantic rerank | Before deploy |
| 6 | **Contextual re-indexing** — add metadata prefix to memory embeddings before Azure sync | 2h | -49% failed retrievals | Quarterly re-index |
| 7 | **Entity extraction** as BM25 anchor (extract nouns before search) | 1h | Better BM25 precision | Round 3 |
| 8 | Switch embedding to Voyage-3.5 during next re-index | 1h | +9.74% RTEB; combined with item 6 | Quarterly |
| 9 | ColBERT late interaction | Not viable | Azure AI Search doesn't support it | Skip |
| 10 | HyDE query expansion | Low priority | Marginal for 100-fact store | Defer |

**Critical finding for the current scoring profile plan:**
The text_weights (`"content": 1.5, "tags": 1.2`) in the planned scoring profile are erased after Azure semantic reranking. Only scoring **functions** (freshness, magnitude) survive. The plan in mem-optimize-v5.md Phase 3a must be updated to remove text_weights and rely entirely on magnitude/freshness functions for durable boosting.

**Critical finding for the recall optimizer plan:**
RRF fusion (item 1 above) should be implemented before the Round 2 topic expansion change, or alongside it. It requires no additional LLM calls and directly improves multi-query result combination.

---

### Compatibility Notes

- **RRF fusion:** Pure Python, no new dependencies. Compatible with the existing smart_extractor.py structure. Works identically for local SQLite and Azure AI Search backends.
- **Conversation context in query:** Hook handler already receives conversation context. No new infrastructure needed.
- **Relevance gate:** Requires spaCy or regex for entity check (spaCy already available in the venv). Alternatively, a simple heuristic (token count + presence of uppercase tokens) works without spaCy.
- **Contextual re-indexing:** Requires one Claude API call per memory (or GPT-4.1-mini for cost). 100 memories × ~200 tokens = ~20K tokens total. Cost: ~$0.003 with GPT-4.1-mini. One-time cost per major re-index.
- **Voyage-3.5 embedding switch:** Requires updating `EMBEDDING_MODEL` in memory_bridge.py, changing the Azure AI Search index vector dimension from 3072 to 1024, and running `memory_bridge.py sync --full`. Index schema changes require deleting and recreating the Azure index (brief downtime). Test on staging index first (per mem-optimize-v5.md Phase 3a protocol).
- **Semantic ranking in Azure:** Requires Standard tier or above. Current system is on Basic tier — semantic ranking may not be available. Verify: `az search service show --name oclaw-search --resource-group oclaw-rg --query "sku"`. If Basic, semantic ranking is not included; skip that layer and rely on RRF + scoring profile only.
- **A-MAC relevance gate:** The full A-MAC paper (Mar 2026) framework is heavyweight. The practical heuristic version (token count + entity check) is sufficient for this use case and requires no additional models.

---

### Design Decision Flags

1. **Contextual embedding re-indexing** — Should memory facts be re-indexed with Anthropic-style context prefixes? If yes, what prefix template to use? Flag for: `plans/design-decisions/` — "Contextual re-indexing: prefix template for memory facts and re-index schedule"

2. **RRF vs priority-rank fusion** — Should the multi-query result fusion in cmd_recall() switch from dedup+priority to RRF? Given the consistent research evidence, this should be an unambiguous yes, but flag the k parameter choice (k=60 is Azure's default; k=10 may be better for 5-query fusion). Flag for: `plans/design-decisions/` — "RRF k parameter for 5-query memory recall fusion"

3. **Embedding model migration** — Should the next full re-index use Voyage-3.5 (1024-dim) instead of text-embedding-3-large (3072-dim)? Combines well with contextual re-indexing as a single migration. Flag for: `plans/design-decisions/` — "Embedding model: stay on text-embedding-3-large or migrate to Voyage-3.5 at next re-index?"

4. **Azure tier check for semantic ranking** — The current Basic tier may not include semantic ranking. If it doesn't, the scoring profile text_weights warning is moot. Verify tier before implementing semantic ranking dependencies. Flag for: `plans/design-decisions/` — "Does the oclaw-search Basic tier include Azure semantic ranking?"

---

### Confidence: High

Primary sources: 5 arXiv preprints from Jan-Mar 2026 (Zep, Adaptive Memory Admission, Adaptive Memory Structures, Mem0 production paper, Contextual Retrieval), official Azure AI Search documentation (Mar 2026 API version), Voyage AI blog (Oct 2025 reranker analysis), ZeroEntropy reranking benchmarks (2025-2026), Anthropic official contextual retrieval docs, RAG-Fusion paper. All sources dated within 12 months.

What would increase confidence: Running the actual RRF fusion and conversation-context changes against the live benchmark (plans/memory-recall-optimizer1.md Rounds 2-3) to verify the +8-10% precision claim holds for the specific ClawBot memory content. The research is from general-purpose RAG settings; the domain-specific vocabulary of ClawBot (Tailscale, openclaw, desazure, Azure IMDS, etc.) may amplify or dampen these effects.


---

## Research: Production Memory System Retrieval Patterns — Mem0, Zep, MemGPT/Letta, LangChain

**Date**: 2026-03-28
**Triggered by**: User request to survey how leading production memory systems handle retrieval in 2025-2026, with focus on patterns applicable to the ClawBot memory system: small store (~100 facts), Azure AI Search backend, hook-based per-turn injection.
**Stack relevance**: Directly affects `smart_extractor.py` recall logic, the `before_agent_start` hook, and any planned Memory CI Loop improvements. Informs whether to add query reformulation, relevance gating, reranking, or conversation-aware retrieval to the existing pipeline.

---

### Question

How do Mem0, Zep, MemGPT/Letta, and LangChain handle memory retrieval in production? What patterns are table stakes vs cutting edge? Specifically: query reformulation, adaptive/relevance gating, memory consolidation, reranking, conversation-aware retrieval, and skip-on-trivial behavior.

---

### Sources Consulted

1. [Mem0 Advanced Retrieval — docs.mem0.ai](https://docs.mem0.ai/platform/features/advanced-retrieval) — Keyword expansion, intelligent reranking, precision filtering
2. [Mem0 Reranker-Enhanced Search — docs.mem0.ai](https://docs.mem0.ai/open-source/features/reranker-search) — Second scoring pass after vector retrieval
3. [Mem0 LLM Reranker — docs.mem0.ai](https://docs.mem0.ai/components/rerankers/models/llm_reranker) — LLM-based reranking component
4. [Mem0 Search Memory — docs.mem0.ai](https://docs.mem0.ai/core-concepts/memory-operations/search) — Search API, v2 logical operators
5. [Mem0 Criteria Retrieval — docs.mem0.ai](https://docs.mem0.ai/platform/features/criteria-retrieval) — Filter-based precision retrieval
6. [Mem0 Add Memory — docs.mem0.ai](https://docs.mem0.ai/core-concepts/memory-operations/add) — Two-phase pipeline: Extraction + Update
7. [Mem0 Custom Update Memory Prompt — docs.mem0.ai](https://docs.mem0.ai/open-source/features/custom-update-memory-prompt) — ADD/UPDATE/DELETE/NOOP operations
8. [Mem0 AI Memory Research — mem0.ai/research](https://mem0.ai/research) — 26% accuracy boost; 91% p95 latency reduction vs full-context; ~1.8K vs 26K tokens
9. [Mem0 AI Memory Layer Guide — mem0.ai/blog](https://mem0.ai/blog/ai-memory-layer-guide) — Production guidance, December 2025
10. [Mem0 Graph Memory — mem0.ai/blog](https://mem0.ai/blog/graph-memory-solutions-ai-agents) — Mem0ᵍ graph-enhanced variant, January 2026
11. [Mem0 for OpenClaw — mem0.ai/blog](https://mem0.ai/blog/mem0-memory-for-openclaw) — Plugin for OpenClaw: auto-recall + auto-persist per turn; two-scope (long-term user-scoped vs short-term session-scoped)
12. [Mem0 OpenClaw Docs — docs.mem0.ai](https://docs.mem0.ai/integrations/openclaw) — Official integration docs
13. [Zep Temporal Knowledge Graph Paper — arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956) — January 2025; three-tier graph; four-reranker pipeline; 94.8% DMR accuracy
14. [Zep Paper HTML — arxiv.org/html/2501.13956v1](https://arxiv.org/html/2501.13956v1) — Ingestion with n=4 context messages; event time vs ingestion time timestamps
15. [Zep Blog — blog.getzep.com](https://blog.getzep.com/zep-a-temporal-knowledge-graph-architecture-for-agent-memory/) — Architecture overview
16. [Graphiti GitHub — github.com/getzep/graphiti](https://github.com/getzep/graphiti) — Open-source temporal KG engine powering Zep
17. [Zep Graph Overview — help.getzep.com](https://help.getzep.com/graph-overview) — Production docs: edge invalidation, validity windows
18. [Letta Intro / MemGPT — docs.letta.com](https://docs.letta.com/concepts/memgpt/) — Tiered memory model (core/recall/archival)
19. [Letta Memory Management — docs.letta.com](https://docs.letta.com/advanced/memory-management/) — Eviction, summarization, 70% threshold
20. [Letta Agent Memory Blog — letta.com/blog](https://www.letta.com/blog/agent-memory) — Full tiered architecture walkthrough
21. [Letta Archival Memory — docs.letta.com](https://docs.letta.com/guides/agents/archival-memory/) — Semantic search, on-demand only
22. [Letta Stateful Agents — docs.letta.com](https://docs.letta.com/guides/agents/memory/) — Core memory blocks, always in context
23. [Letta Benchmarking AI Agent Memory — letta.com/blog](https://www.letta.com/blog/benchmarking-ai-agent-memory) — Filesystem vs DB benchmark
24. [LangChain ConversationSummaryMemory — python.langchain.com](https://python.langchain.com/api_reference/langchain/memory/langchain.memory.summary.ConversationSummaryMemory.html) — LLM-generated rolling summary; reduces tokens vs buffer
25. [LangChain Memory Jan 2026 — oneuptime.com/blog](https://oneuptime.com/blog/post/2026-01-27-langchain-memory/view) — Recent implementation patterns
26. [Two-Room Memory Architecture — github.com/zachseven/two-room-memory](https://github.com/zachseven/two-room-memory) — Triviality gating: classifier trained on 113 examples, 100% accuracy on test; paper "Epstein and Claude 2026"
27. [Hacker News: Two-Room Memory — news.ycombinator.com](https://news.ycombinator.com/item?id=46499184) — Community discussion on triviality gating
28. [6 Best AI Agent Memory Frameworks 2026 — machinelearningmastery.com](https://machinelearningmastery.com/the-6-best-ai-agent-memory-frameworks-you-should-try-in-2026/) — Framework comparison survey
29. [5 Memory Systems Compared — dev.to](https://dev.to/varun_pratapbhardwaj_b13/5-ai-agent-memory-systems-compared-mem0-zep-letta-supermemory-superlocalmemory-2026-benchmark-59p3) — Mem0 vs Zep vs Letta vs Supermemory vs SuperLocalMemory, 2026 benchmarks
30. [LLM Context Problem 2026 — blog.logrocket.com](https://blog.logrocket.com/llm-context-problem/) — Context strategy survey
31. [Design Patterns for Long-Term Memory — serokell.io](https://serokell.io/blog/design-patterns-for-long-term-memory-in-llm-powered-architectures) — Flat/structured/policy-managed taxonomy
32. [Azure Foundry Agent Memory — learn.microsoft.com](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agentic-memories) — Extract/Consolidate/Retrieve/Customize lifecycle; hybrid search injection at conversation start
33. [Choosing How to Remember: Adaptive Memory Structures — arxiv.org/html/2602.14038](https://arxiv.org/html/2602.14038) — Mix-of-Experts gating for retrieval weights (recency, semantic similarity, importance)
34. [Synapse: Episodic-Semantic Memory — arxiv.org/html/2601.02744](https://arxiv.org/html/2601.02744) — Spreading activation from episodic to semantic; conversation history drives retrieval
35. [Diagnosing Retrieval vs Utilization Bottlenecks — arxiv.org/html/2603.02473](https://arxiv.org/html/2603.02473) — Retrieval bottleneck vs utilization bottleneck distinction, March 2026

---

### Findings

#### 1. Mem0 — Two-Phase Pipeline with LLM Decision Layer

**Retrieval pipeline:**
Mem0 uses a two-phase architecture:

- **Extraction phase**: Ingests the latest exchange + a rolling summary + the last m messages. An LLM extracts a concise set of candidate memory facts from this combined context (not just the last message).
- **Update phase**: Each extracted candidate is compared to the top-s similar entries in the vector store. An LLM then selects one of four operations: **ADD**, **UPDATE**, **DELETE**, or **NOOP**. This prevents duplicate accumulation and keeps the store coherent.

**Retrieval at inference time (search):**
- Default: semantic similarity (vector search)
- Advanced retrieval (platform tier): keyword expansion + intelligent reranking + precision filtering
- Reranker: optional second-pass LLM or cross-encoder that re-scores vector hits for relevance ordering
- v2 search API: supports AND/OR/NOT with comparison operators for metadata filtering

**Query reformulation:** Mem0 does not expose query reformulation as a documented first-class feature. The LLM-based extraction phase effectively "reformulates" what to recall by identifying salient concepts, but the search query itself is the raw user message.

**Memory consolidation:** Explicit — the Update phase merges duplicates. Rule: if two facts "convey the same thing," keep the one with more information. This is LLM-judged at write time, not at read time.

**Adaptive retrieval (skip irrelevant turns):** Not a built-in documented feature. The system retrieves on every `search()` call; the caller decides whether to call it.

**Performance benchmarks (published):**
- 26% higher response accuracy vs OpenAI memory
- 91% p95 latency reduction vs full-context (1.44s vs 17.12s)
- 90% token reduction (~1.8K vs ~26K per conversation)

**Relevant to our use case:** The ADD/UPDATE/DELETE/NOOP pattern is something our `smart_extractor.py` only partially implements (it adds and searches; update/delete are manual). The keyword expansion at retrieval time is directly applicable to Azure AI Search.

---

#### 2. Zep — Temporal Knowledge Graph with Multi-Stage Reranking

**Architecture:**
Zep is powered by Graphiti, a temporally-aware knowledge graph with three subgraph tiers:
- **Episode subgraph**: raw conversation turns
- **Semantic entity subgraph**: extracted named entities and facts
- **Community subgraph**: clustered entity groups

**Temporal model:**
Every edge has four timestamps:
- `t'created` / `t'expired`: when the fact was ingested/invalidated in the system
- `tvalid` / `tinvalid`: the real-world time window during which the fact was true

When new information contradicts an existing edge, an LLM compares them and sets `t'expired` on the old edge rather than deleting it. This enables queries like "what was true at time T?" — important for tracking state changes (e.g., "user's preferred model changed from X to Y on date Z").

**Retrieval pipeline (4-stage reranking):**
1. Candidate identification via: cosine semantic search + Okapi BM25 full-text + breadth-first graph traversal
2. Maximal Marginal Relevance (MMR) reranker — ensures diversity, prevents redundant results
3. Episode-mentions reranker — boosts entities that appear frequently in recent episodes
4. Node-distance reranker — boosts nodes topologically close to the query entity in the graph
5. Cross-encoder final reranker — generates relevance scores using cross-attention against the query

**Conversation-aware ingestion:**
During ingestion, the system processes the current message plus the last **n=4** messages (2 full turns) to provide context for named entity recognition. This means entity extraction is conversation-aware, not single-turn.

**Relevance gating:** Not explicitly implemented as a skip gate. Zep processes all turns but the graph structure naturally de-emphasizes low-information episodes (they contribute few or no new nodes/edges).

**Performance:** 94.8% accuracy on Deep Memory Retrieval (DMR) benchmark; 18.5% improvement on LongMemEval; 90% latency reduction vs naive approaches.

**Applicable pattern for us:** The 4-stage reranking is overkill for a ~100-fact store. However, the **conversation context window during retrieval** (using last N messages, not just the current message, to form the recall query) is directly applicable and underused in our current hook.

---

#### 3. MemGPT / Letta — OS-Inspired Tiered Memory, Agent-Driven Retrieval

**Three tiers:**

| Tier | Analogy | Always in context? | How retrieved |
|------|---------|-------------------|---------------|
| Core Memory (Memory Blocks) | RAM | Yes — always injected | Agent edits via tools (`memory_replace`, `memory_insert`, `memory_rethink`) |
| Recall Memory | Disk — conversation log | No | Agent calls `conversation_search` or `conversation_search_date` |
| Archival Memory | Disk — semantic DB | No | Agent calls `archival_memory_search` (semantic) |

**Key design principle:** The agent itself decides when to search archival/recall memory. There is no automatic per-turn injection of archival results. The LLM reasons over what it sees in core memory and decides whether it needs more — then issues a tool call. This is fundamentally different from Mem0/Zep/our hook which inject automatically.

**Context window eviction:** When the context window fills (~70% threshold), old messages are evicted via summarization. Important details are archived before removal. The agent can re-retrieve them later via search tools.

**Core memory:** Fixed slots (e.g., "persona" block + "human" block). These are always visible. Agents can write to them. Size-bounded — not suitable for large fact stores.

**Applicable pattern for us:** The core memory concept maps well to our hook injection: a small set of always-on facts injected every turn. The key difference is Letta makes core memory agent-editable; our hook is read-only. The on-demand archival search model could be added as a second-tier: if recall score < threshold, skip injection; if user asks a specific question, do a deep search. This is more complex but eliminates irrelevant injections.

---

#### 4. LangChain — Rolling Summary + Vector Retriever

**ConversationBufferMemory:** Passes entire history to the LLM. No retrieval; scales poorly. Deprecated for long sessions.

**ConversationSummaryMemory:** After each turn, an LLM generates a rolling summary that replaces the raw history. Good for long sessions; loses detail. No vector retrieval.

**VectorStoreRetrieverMemory:** Stores each exchange as a vector embedding. At retrieval time, queries the vector store for the most semantically similar past exchanges. Returns top-k relevant past turns, not the full history. No temporal logic, no entity graph.

**ConversationSummaryBufferMemory:** Hybrid — keeps recent messages verbatim, summarizes older ones. Most practical for medium-length sessions.

**Recent improvements (2025-2026):** No major architectural changes documented. LangChain memory modules are broadly considered lower-level primitives. The community recommendation for production use is to layer Mem0 or Zep on top rather than use LangChain memory directly. Query expansion is not a built-in feature of any LangChain memory type.

**Applicable pattern for us:** `ConversationSummaryMemory`'s rolling summary concept is relevant — we could maintain a rolling summary of the conversation that gets included in the recall query (instead of or alongside the raw last message), giving the recall engine more context.

---

#### 5. Relevance Gating — Skipping Retrieval for Trivial Messages

**Finding:** This is an emerging area with a clear research result.

The **Two-Room Memory Architecture** (Epstein & Claude, 2026; `github.com/zachseven/two-room-memory`) is the most relevant paper. Key findings:

- Triviality forms a **tighter semantic cluster** than meaningfulness. It's easier to define "trivially dismissible" than "important."
- A lightweight classifier trained on only **113 labeled examples** achieves **100% accuracy** on novel test cases.
- Examples classified as trivial: "what color are ladybugs", "ok", "thanks", "hello", "sure"
- Examples classified as non-trivial: "my dad died yesterday", "I prefer TypeScript over JavaScript", "remember my API key format"

The architecture:
```
USER INPUT → Room 1 (Active Buffer) → Triviality Gate → FLUSH (trivial) OR PERSIST → Room 2 (Storage)
```

**No production memory system (Mem0, Zep, Letta) implements built-in relevance gating at the per-turn injection level.** Zep processes all turns but the graph structure naturally absorbs low-information messages with minimal side effects. Mem0 relies on the extraction LLM to produce empty candidates for trivial inputs (implicit gating via extraction). Letta delegates to the agent's judgment.

The practical implementation pattern used in production: a **small, fast binary classifier** (logistic regression or small fine-tuned model) or a **simple heuristic rule** (message length < N tokens AND no nouns → skip) runs as a pre-filter before calling the recall API. This reduces latency and avoids polluting injection context with irrelevant recalls.

**For our hook:** Currently `smart_extractor.py recall` runs on every turn regardless. A triviality pre-filter before the Azure AI Search call would reduce unnecessary API calls and eliminate edge cases where "ok thanks" triggers a spurious memory injection.

---

#### 6. Conversation-Aware Retrieval — Using Full Context, Not Just Last Message

**Finding:** All three leading systems use more than the current message for retrieval context.

| System | Context used for retrieval |
|--------|---------------------------|
| Mem0 | Last message + rolling summary + last m messages (extraction phase) |
| Zep | Current message + last n=4 messages (ingestion NER context) |
| Letta | Agent reasons over full in-context window before issuing search |
| LangChain VectorStoreRetriever | Last message only (basic); can be augmented with history manually |

**Pattern:** The consensus is to use a **sliding window of the last 2-4 turns** as the retrieval query context, not just the final user message. This substantially improves recall for multi-turn conversations where the intent is distributed across messages (e.g., "... and do that with the thing we talked about earlier").

**Query reformulation** (distinct from multi-turn context): Some agentic RAG frameworks apply RL-trained rewriters to reformulate the user query before retrieval. This is uncommon in pure memory systems but appears in multi-step retrieval pipelines. None of Mem0/Zep/Letta do this explicitly in their documented retrieval paths.

**For our hook:** Currently we pass only the last user message to `smart_extractor.py recall`. Switching to the last 2-3 messages (concatenated or summarized) as the recall query would improve accuracy on multi-turn conversations with no architectural changes required — just a change to what gets passed to the recall function.

---

#### 7. Common Patterns — Table Stakes vs Cutting Edge

**Table stakes (all production systems do this):**

| Pattern | What it means |
|---------|--------------|
| Two-phase write pipeline | Extract candidates from context → LLM decides ADD/UPDATE/DELETE/NOOP |
| Deduplication at write time | Merge similar facts before storing; don't accumulate redundant entries |
| Semantic (vector) search at retrieval | Embed query, cosine similarity against store |
| Small fact store, not raw history | Store extracted facts (50-200 tokens each), not full conversation logs |
| Persistence across sessions | Memory survives restarts; stored in DB, not in-process |

**Current industry standard (most do this):**

| Pattern | What it means |
|---------|--------------|
| Hybrid search | Vector similarity + keyword (BM25/FTS) combined; better recall on named entities |
| Reranking after vector retrieval | Second-pass scoring to improve precision; LLM or cross-encoder |
| Metadata filtering | Filter by user ID, date range, category before ranking |
| Temporal tracking | Know when facts changed; don't just overwrite |

**Cutting edge / emerging (some do this):**

| Pattern | What it means |
|---------|--------------|
| Graph-enhanced memory | Entity relationships + temporal edges (Zep/Graphiti, Mem0ᵍ) |
| Triviality gating | Pre-filter to skip retrieval for low-information turns |
| Conversation-window retrieval | Use last N turns (not just last message) as retrieval context |
| Adaptive retrieval weights | MoE gates that learn recency vs semantic vs importance weights |
| Agent-driven retrieval decisions | Agent issues search tool calls on demand rather than auto-inject |

**Where our system stands today:**
- Table stakes: mostly covered (Azure AI Search semantic, SQLite FTS5, session extraction)
- Standard: partial (FTS5 hybrid, no reranking, no metadata filtering, no temporal tracking)
- Cutting edge: not implemented

**Highest-leverage gaps for our ~100-fact store:**

1. **Conversation-window retrieval** — Pass last 2-3 messages to recall, not just the current message. Zero architecture change; modify one parameter in the hook. Expected improvement: meaningful for multi-turn sessions.
2. **Trivial turn gating** — Pre-filter in the hook before calling Azure AI Search. Reduce unnecessary calls and spurious injections. Simple heuristic or tiny classifier.
3. **ADD/UPDATE/DELETE/NOOP at write time** — Currently `smart_extractor.py` only adds. Updating and soft-deleting contradicted facts would keep the store coherent as ClawBot learns new information (e.g., model config changes, OAuth token paths that moved).

---

### Recommendation

**Immediate (low effort, high impact):**

1. **Multi-turn retrieval context**: In the `before_agent_start` hook, pass the last 2-3 messages (not just the last user message) as the recall query. No new infrastructure needed — just concatenate or join them before calling `smart_extractor.py recall`.

2. **Trivial turn gate**: Add a pre-check in the hook. If `len(message.strip()) < 20 and no_proper_nouns(message)` → skip recall entirely. This eliminates spurious Azure AI Search calls on ack messages ("ok", "got it", "thanks").

**Medium term (moderate effort):**

3. **ADD/UPDATE/DELETE/NOOP write pipeline**: Extend `smart_extractor.py` extraction to detect when a new fact contradicts an existing memory and mark the old one as superseded (soft delete or update). This prevents the store from containing both "gateway model is gpt-5.2" and "gateway model is claude-opus-4.6" simultaneously.

4. **Hybrid search validation**: Confirm that Azure AI Search is being called with both semantic + keyword (BM25) modes for each recall. The current implementation may be doing semantic-only. Adding keyword search improves recall for entity names (model IDs, OAuth paths, port numbers).

**Not recommended for our scale:**

- Graph-based memory (Zep/Graphiti approach): overhead is designed for thousands of entities and multi-session relationship tracking. At ~100 facts, a flat semantic store with good dedup is sufficient.
- Cross-encoder reranking: adds ~200-500ms latency per recall; not justified at ~100 facts where top-3 results from Azure AI Search are already precise.
- Full Mem0 or Zep adoption: our existing stack (SQLite + Azure AI Search + smart_extractor.py) implements the core of what these systems provide. We'd be replacing working infrastructure for marginal gains.

---

### Design Decision Flags

The following questions should be tracked in `plans/design-decisions/`:

1. **Multi-turn retrieval window size**: How many prior messages should the hook concatenate for the recall query? Options: last 1 (current), last 2, last 3, or rolling LLM summary. Trade-off: more context = better recall accuracy vs slightly larger recall query token cost.

2. **Trivial turn gate implementation**: Simple heuristic (length + noun check) vs lightweight classifier (Two-Room approach, 113 training examples). Heuristic is zero-latency; classifier needs training data curation.

3. **Contradiction handling at write time**: Should `smart_extractor.py` detect and soft-delete contradicted facts during extraction, or should this be a separate nightly cleanup job (similar to the planned Memory CI Loop dedup sweep)?

---

### Compatibility Notes

- All recommendations above are compatible with the existing Azure AI Search + SQLite + Python stack on the VM.
- The Two-Room Memory Architecture classifier approach requires training data from real ClawBot sessions — the 113-example dataset in the repo is generic and would need supplementing with domain-specific examples (VM ops messages, OAuth flows, model config messages).
- Mem0's OpenClaw integration plugin exists (`docs.mem0.ai/integrations/openclaw`) but would replace our custom stack entirely; not recommended unless we want to externalize memory management.
- Zep/Graphiti requires Neo4j or a compatible graph DB — not currently in the VM stack; significant infra addition.

### Confidence: High

Primary sources: official docs for all four systems (docs.mem0.ai, docs.letta.com, help.getzep.com, python.langchain.com); peer-reviewed paper for Zep (arXiv 2501.13956, January 2025); Two-Room Memory Architecture paper (2026); multiple 2026 framework comparison surveys from MachineLearningMastery, DEV Community, and Vectorize.io. Benchmark numbers are from Mem0's own published research and Zep's paper — treat as vendor-reported (not independently verified). The "common patterns" taxonomy is consensus-derived from 5+ independent sources dated within 12 months.

What would increase confidence: running the ClawBot hook with multi-turn context enabled and measuring retrieval accuracy delta against the existing rubric from the Memory CI Loop PRD.

---

## Research: Anthropic Contextual Retrieval — Applicability to Fact-Based Memory Stores

**Date**: 2026-03-28
**Triggered by**: User request to evaluate Contextual Retrieval for the ClawBot memory system (~100 atomic facts in Azure AI Search + SQLite), and to survey Anthropic's latest RAG, embedding, and tool-use memory recommendations.
**Stack relevance**: Directly affects `smart_extractor.py`, `memory_bridge.py`, and the embedding pipeline in `~/.openclaw/workspace/skills/clawbot-memory/`. Any changes to how facts are embedded before sync to Azure AI Search would require modifications to `memory_bridge.py` and potentially a one-time re-embedding run.

---

### Question

1. How does Anthropic's Contextual Retrieval work, and what improvement numbers did they report?
2. Is the technique applicable to a small fact-based memory store (~100 atomic facts) vs large document chunk corpora?
3. How would you implement it for memory facts specifically?
4. What are Anthropic's latest recommendations for RAG/retrieval, tool-use memory, and prompt injection vs tool-based retrieval?
5. Any Azure AI Search integration considerations?

---

### Sources Consulted

1. [Anthropic — Contextual Retrieval (Sept 2024)](https://www.anthropic.com/news/contextual-retrieval) — Primary source; full method description and benchmarks
2. [Anthropic — Contextual Retrieval Appendix II (full experiment results)](https://assets.anthropic.com/m/1632cded0a125333/original/Contextual-Retrieval-Appendix-2.pdf) — Breakdown of results per dataset
3. [Anthropic Claude Cookbook — Contextual Embeddings Guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide) — Official implementation reference
4. [DataCamp — Anthropic Contextual Retrieval: A Guide with Implementation](https://www.datacamp.com/tutorial/contextual-retrieval-anthropic) — Implementation walkthrough
5. [Together AI Docs — How to Implement Contextual RAG from Anthropic](https://docs.together.ai/docs/how-to-implement-contextual-rag-from-anthropic) — Cross-platform implementation guide
6. [Anthropic Engineering — Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — 2025 agent memory patterns; "just in time" retrieval
7. [Anthropic Engineering — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) — Tool-use vs prompt injection patterns
8. [Anthropic — Memory Tool docs](https://console.anthropic.com/docs/en/agents-and-tools/tool-use/memory-tool) — File-based memory tool pattern
9. [Azure AI Search — Hybrid Search Overview](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview) — BM25 + vector RRF merging
10. [Azure AI Search — BM25 Relevance Scoring](https://learn.microsoft.com/en-us/azure/search/index-similarity-and-scoring) — BM25 tuning knobs
11. [InfoQ — Anthropic Unveils Contextual Retrieval](https://www.infoq.com/news/2024/09/anthropic-contextual-retrieval/) — Third-party coverage confirming benchmarks
12. [arXiv — Reconstructing Context (Apr 2025)](https://arxiv.org/html/2504.19754v1) — Academic follow-up on context reconstruction in RAG
13. [AWS — Contextual Retrieval in Anthropic using Amazon Bedrock Knowledge Bases](https://aws.amazon.com/blogs/machine-learning/contextual-retrieval-in-anthropic-using-amazon-bedrock-knowledge-bases/) — Cross-cloud implementation notes

---

### Findings

#### 1. How Contextual Retrieval Works

Published September 2024, Contextual Retrieval solves a fundamental flaw in standard RAG: when a document is split into chunks, each chunk loses its surrounding context. A chunk reading "The company's revenue grew by 3%" is ambiguous without knowing which company or time period. This causes retrieval to fail because the embedding does not capture the right semantic identity.

**Two sub-techniques, both applied at ingestion time (not query time):**

**Contextual Embeddings:**
- For each chunk, pass both the chunk AND its source document to Claude
- Ask Claude to generate a short 50–100 token contextual description that situates the chunk within the whole document
- Prepend that context to the chunk
- Embed the augmented chunk
- Store the augmented text in the vector index

**Contextual BM25:**
- Apply the same context-prepended chunk to the BM25 (keyword/TF-IDF) index as well
- This gives keyword search the same disambiguation benefit

**The prompt Anthropic used:**
```
Here is the document:
<document>
{{WHOLE_DOCUMENT}}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{{CHUNK_CONTENT}}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.
```

**Cost optimization with prompt caching:**
The whole document is loaded into the cache ONCE. Each subsequent chunk request is a cache hit. With 800-token chunks, 8k-token documents, 50-token instructions, and 100-token context output, the one-time ingestion cost is approximately $1.02 per million document tokens. Prompt caching reduces this cost by up to 90% vs cold reads.

#### 2. Performance Numbers Reported

| Technique | Retrieval Failure Rate (top-20 chunks) | Reduction vs Baseline |
|-----------|----------------------------------------|-----------------------|
| Baseline (standard embeddings only) | 5.7% | — |
| Contextual Embeddings only | 3.7% | -35% |
| Contextual Embeddings + Contextual BM25 | 2.9% | -49% |
| Contextual Embeddings + Contextual BM25 + Reranking | ~1.9% | -67% |

On codebase retrieval specifically: Pass@10 improved from ~87% to ~95%.

**Best embedding models tested:** Voyage AI and Gemini embeddings outperformed others. Cohere was the reranker tested (Voyage reranker not evaluated in Anthropic's published run).

**Recommended production stack:**
1. Contextual Embeddings (Voyage AI or Gemini for the vectors)
2. Contextual BM25 (keyword index on the same augmented text)
3. Rank fusion (combine vector + BM25 results)
4. Reranking step (Cohere Rerank or equivalent)
5. Top-20 chunks in prompt

#### 3. Applicability to Small Fact-Based Memory Stores (~100 Atomic Facts)

**Verdict: Partially applicable, but different tradeoffs than large document corpora.**

Anthropic explicitly notes: "If your knowledge base is smaller than 200,000 tokens (~500 pages), you can just include the entire knowledge base in the prompt — no RAG needed at all."

100 atomic facts averaging ~50–100 tokens each = 5,000–10,000 tokens total. This fits easily in a single prompt and is below the 200k threshold. **For pure retrieval accuracy, full-context injection beats RAG entirely at this scale.**

However, the ClawBot memory system faces a different constraint: the facts span multiple sessions and projects, and the hook must return in under 4 seconds at every turn. At scale (if the memory store grows to 1,000+ facts), full-context injection becomes impractical.

**Where Contextual Retrieval still helps at small scale:**

Atomic facts can suffer from the same decontextualization problem as document chunks, but in a different way. A fact like "The gateway crashed after setting tailscale.mode to direct" is self-contained. But a fact like "Port 18793 is used for this service" becomes ambiguous without the project context embedded in the vector.

The contextual prefix approach for facts would look like:

```
# Without context prefix (current state)
Embedded text: "Port 18793 is used for Google OAuth redirect (GDrive)"

# With context prefix (contextual embedding)
Embedded text: "This fact is from the openclaw_vm project, SSH tunnel configuration domain, recorded 2026-02-20: Port 18793 is used for Google OAuth redirect (GDrive)"
```

The prefix adds ~20–40 tokens per fact (minimal cost) but substantially improves semantic disambiguation when:
- The same concept appears across multiple projects (e.g., "port X is used for Y" in different systems)
- The fact is terse and relies on ambient context (e.g., "max retries set to 3" — for which system?)
- Time-sensitive facts need temporal ordering (e.g., two conflicting facts from different dates)

**Quantitative benefit at 100-fact scale: likely low (~5–15% recall improvement).** The gains are highest when the corpus is large and chunks are ambiguous. At 100 facts with distinct content, the vector similarity search already works reasonably well. But the technique becomes more valuable as the store grows past 500–1,000 facts.

#### 4. Proposed Implementation for ClawBot Memory Facts

Three types of context prefixes are applicable:

**Option A — Project + Domain Context (highest priority)**
```
[Project: openclaw_vm | Domain: SSH/networking | Type: fix]
Port 18793 is used for Google OAuth redirect (GDrive)
```
This is the most impactful: prevents cross-project collisions and disambiguates terse facts.

**Option B — Temporal Context**
```
[Date: 2026-02-20 | Project: openclaw_vm | Domain: OAuth]
The GDrive token path changed to ~/.config/openclaw-gdrive/token-openclawshared.json
```
Helps when facts get updated over time and the old + new versions coexist.

**Option C — LLM-Generated Situational Context (full Contextual Retrieval approach)**
For each fact at sync time, call Claude to generate a situational sentence:
```
This fact relates to the SSH tunnel port configuration in the openclaw_vm project, specifically the Google OAuth service port assignments recorded in February 2026.

Port 18793 is used for Google OAuth redirect (GDrive)
```

**Implementation path in current stack:**

The `memory_bridge.py sync` cron job currently embeds the raw fact content before pushing to Azure AI Search. The change would be:

1. Before embedding in `memory_bridge.py`, construct a context prefix from the fact's existing metadata fields: `project`, `tags`, `created_at`
2. Prepend to the text: `f"[Project: {fact.project} | Tags: {', '.join(fact.tags)} | Date: {fact.created_at[:10]}]\n{fact.content}"`
3. Embed the augmented string
4. Store the raw fact in the `content` field (for display) but the augmented string as the embedding input

This is Option A and requires no LLM call — just metadata formatting. Cost: zero. Benefit: measurable disambiguation improvement.

For Option C (LLM-generated context), use prompt caching: load all facts in a single cached prompt, generate context for each. One-time cost at ingestion. For ~100 facts at ~100 tokens each = ~10,000 tokens; with prompt caching, subsequent runs cost ~10% of first run.

**Important:** The recall side (at query time) does NOT need to change. The query is still the raw user message or topic string — only the stored embeddings are augmented.

#### 5. Anthropic's Latest RAG and Retrieval Recommendations (2025–2026)

From Anthropic Engineering — "Effective Context Engineering for AI Agents" (2025):

**"Just in time" context strategy:**
Agents should maintain lightweight identifiers (file paths, stored queries, memory IDs, web links) and use these to dynamically load data into context at runtime via tools. This is preferred over stuffing everything into the system prompt.

**Progressive disclosure:**
Rather than front-loading all context, agents should be designed to discover and retrieve context iteratively — each tool call yields context that informs the next.

**Note-taking for persistence:**
Agents summarize completed phases and store to external memory before context fills. When approaching context limits, spawn fresh subagents with clean context + a handoff summary from memory.

**When to use full-context injection (no RAG):**
- Knowledge base < 200,000 tokens: inject everything, skip RAG entirely
- Prompt caching makes repeated injection cheap (>90% cost reduction after first cache load)

**Tool-use memory vs prompt injection:**
- Prompt injection (system prompt memory): appropriate for small, stable, high-priority facts. Fast, zero latency, always present.
- Tool-use retrieval: appropriate for large or growing knowledge bases, lower-priority facts, or when facts need to be dynamically selected based on query. Higher latency but scales indefinitely.
- Hybrid (ClawBot current approach): hook injects top-3–5 recalled facts into the system prompt at call time. This is a reasonable middle ground — retrieval happens but facts appear as prompt context, not tool results.

**Anthropic's note on retrieval quality:**
The primary bottleneck in RAG systems is not the LLM's ability to use retrieved context — it is the retrieval step itself (failing to surface the right chunks). Contextual Retrieval directly attacks this bottleneck. Reranking is the most impactful single addition after contextual embeddings.

#### 6. Azure AI Search Integration Considerations

Azure AI Search already supports hybrid search (BM25 + vector) with RRF merging — this is the current ClawBot deployment. Applying Contextual Retrieval to this setup means:

**Index-side changes (ingestion):**
- Add a new field or use the existing content field: store the context-augmented text as the value that gets embedded and indexed for BM25
- Store the raw fact separately (e.g., `raw_content` field) for display/recall output
- OR: keep a single `content` field but generate the embedding from `context_prefix + content`; Azure AI Search lets you control which fields are vectorized

**Query-side: no changes required.** The query embedding is still the raw user topic string. The context-augmented embeddings in the index are closer to the right neighbors in embedding space.

**Reranking on Azure:**
Azure AI Search has its own semantic reranker (powered by Microsoft's cross-encoder models, not Cohere). It can be applied after hybrid retrieval as a third pass. This is the Azure-native equivalent of the Cohere rerank step Anthropic recommends. The semantic reranker is available on Basic+ tier (already in use at ~$74/mo).

**Azure-specific BM25 tuning:**
Azure's BM25 uses `b=0.75` and `k1=1.2` by default. For short atomic facts (50–100 tokens), consider lowering `b` toward 0.5 to reduce document-length normalization sensitivity — all facts are approximately the same length so length normalization adds noise.

**Practical upgrade path for current stack:**

| Step | Change | Effort | Expected Gain |
|------|--------|--------|---------------|
| 1 | Add metadata prefix to facts before embedding in `memory_bridge.py` | Low (~15 lines) | +5–15% recall |
| 2 | Enable Azure semantic reranker on retrieval queries in `smart_extractor.py` | Low (1 query param) | +10–20% precision |
| 3 | Add BM25 field with context-augmented text to Azure index schema | Medium (re-index required) | +10–20% keyword recall |
| 4 | Add LLM-generated situational context at extraction time | High (Claude API call per fact) | +20–35% recall (per Anthropic numbers, but on smaller corpus) |

Steps 1 and 2 are the recommended near-term changes: low effort, no re-index required for step 2, and provides measurable improvements before investing in the full LLM-generated context pipeline.

---

### Recommendation

**Near-term (low effort, high ROI):**
1. Modify `memory_bridge.py` to prepend a structured metadata prefix to fact content before generating embeddings. Use existing fields: `project`, `tags`, `created_at`. No LLM calls, no schema changes — just format the embedding input string.
2. Enable the Azure AI Search semantic reranker on the `smart_extractor.py` recall query. One query parameter change.

**Medium-term (when corpus exceeds ~500 facts):**
3. Add a BM25-indexed `augmented_content` field to the Azure Search index schema. Populate it with the same context-prefixed text used for embeddings. Re-index (one-time cost — ~100 facts is trivial to re-sync).
4. Evaluate whether the `smart_extractor.py` recall path should do two-pass retrieval: first vector + BM25 for top-20 candidates, then semantic reranker for top-5 to inject into the hook.

**Long-term (if corpus grows to 1,000+ facts):**
5. Implement full LLM-generated contextual sentences at extraction time (Option C above). Use prompt caching to amortize cost. This is the full Anthropic Contextual Retrieval approach and is expected to reduce retrieval failures by 35–49% vs baseline embeddings.

**Do NOT** implement contextual retrieval by changing the query-side embedding — only the stored/indexed embeddings should be augmented. Query text stays raw.

**Design decision flagged:** See `plans/design-decisions/` — "Should memory_bridge.py prepend metadata context prefix before embedding, and how should the Azure AI Search index schema be updated to support hybrid contextual retrieval?"

---

### Compatibility Notes

- `memory_bridge.py` currently uses `azure-search-documents` with 3072-dim embeddings (Azure OpenAI text-embedding-3-large). Prepending 20–40 token context prefix does not change the embedding model, dimension, or Azure index schema — it only changes the input string. Safe to deploy without re-indexing existing documents (new embeds will be generated only for new/updated facts).
- Azure AI Search semantic reranker requires `queryType=semantic` and `semanticConfiguration` in the query. The index must have a semantic configuration defined. Check the existing index definition: `az search index show --name <index-name> --service-name oclaw-search --resource-group oclaw-rg`.
- Reranking adds ~100–300ms latency per query. The hook currently has a 4-second timeout. This is within budget.
- Voyage AI embeddings (Anthropic's top recommendation) are NOT currently used — the stack uses Azure OpenAI embeddings. Switching would require a full re-index and adds an external API dependency. Not recommended given the existing Azure setup.
- Cohere Rerank is NOT required — Azure semantic reranker is functionally equivalent and already part of the Azure AI Search subscription.

---

### Confidence: High

Primary sources are Anthropic's own blog post (Sept 2024), the official cookbook, and the published Appendix II results PDF. The improvement numbers (35% / 49% / 67%) are directly from Anthropic's published benchmarks, not third-party claims. The applicability analysis for small fact stores is a reasoned extrapolation — Anthropic's explicit 200k-token threshold guidance is cited directly. Azure AI Search integration notes are from official Microsoft Learn docs (2025).

What would increase confidence: Running an A/B test on the actual ClawBot memory index — compare recall@5 with and without the metadata prefix on a set of 20–30 representative queries from past ClawBot sessions.

