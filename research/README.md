# Research function (WIP)

Goal: implement a reliable “research mode” that uses:
- Brave Search API for retrieval (same backend as OpenClaw `web_search`)
- Azure AI Foundry Kimi K2.5 (via localhost Managed Identity proxy) for synthesis

This folder currently contains a standalone runner script (`run.mjs`). Next step is to integrate it into an OpenClaw skill/slash command.
