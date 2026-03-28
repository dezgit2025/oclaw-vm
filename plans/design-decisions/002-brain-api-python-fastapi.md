# Decision: Brain API as Python FastAPI Service (Separate from Go CLI)

**Date**: 2026-03-15
**Status**: Accepted
**Deciders**: Dez + Claude (architect session)

## Context

We already built a Go CLI tool (`copilot-cli-llm`) that wraps the GitHub Copilot Go SDK for one-shot terminal LLM calls. Now we need ClawBot (OpenClaw gateway) to consume LLMs via a standard HTTP endpoint. The question is whether to extend the Go CLI into an HTTP server or build a separate Python FastAPI service.

## Options Considered

### Option A: Extend Go CLI into HTTP daemon mode
- **Pros**: Single codebase, Go is fast, binary deployment (no runtime deps)
- **Cons**: Go is not the team's primary language, Go HTTP frameworks less familiar, duplicates OpenAI response formatting that FastAPI handles natively, would need to add hot-reload for dev iteration
- **Deployment impact**: Single binary SCP, but more complex codebase to maintain

### Option B: Separate Python FastAPI service wrapping Python Copilot SDK
- **Pros**: Python is the primary language for this project, native async/await matches Copilot SDK's async API, FastAPI auto-generates OpenAPI docs, Pydantic models for request/response validation, faster dev iteration with uvicorn reload, matches existing VM Python infrastructure (venvs, pip)
- **Cons**: Two separate projects to maintain (Go CLI + Python API), Python runtime dependency on VM, venv management, slightly more deployment steps (rsync + pip install vs single binary SCP)
- **Deployment impact**: Requires Python 3.11+ and venv on VM (both already present), systemd user service for lifecycle management

### Option C: Node.js/TypeScript service wrapping Node Copilot SDK
- **Pros**: Copilot SDK's CLI binary is Node.js-based (closest to native), npm ecosystem
- **Cons**: Adds Node.js as a dependency (already present for Copilot CLI binary, but not used for project code), TypeScript compile step, less familiar stack for this team
- **Deployment impact**: Requires Node.js runtime on VM

## Decision

Option B: Separate Python FastAPI service. The Go CLI continues to serve its purpose as a standalone terminal tool. The Brain API is a different deployment model (persistent service vs one-shot binary) with different requirements (OpenAI-compatible HTTP, model aliasing, failover chains). Python + FastAPI is the best fit for async HTTP + the Copilot Python SDK's native async API.

## Consequences

- **Easier**: Dev iteration (uvicorn reload), request/response validation (Pydantic), OpenAI compatibility (well-trodden FastAPI patterns), failover logic (async/await), VM deployment (matches existing Python infra)
- **Harder**: Two separate codebases to maintain for Copilot SDK access (Go CLI + Python API). If the SDK introduces breaking changes, both need updating. Mitigated by pinning SDK versions independently.
- **New dependency**: `github-copilot-sdk` Python package on VM (in addition to the Go binary already deployed)
- **Port allocation**: 18798 added to SSH tunnel port range

## References

- `plans/copilot-llm-api-plan.md` -- full build plan
- `plans/copilot-cli-llm-plans.md` -- Go CLI build plan (for comparison)
- `plans/research-log.md` -- Copilot SDK research (Go module verification, Python SDK API)
