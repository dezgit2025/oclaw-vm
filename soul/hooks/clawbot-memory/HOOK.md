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
Prepends top 3-5 relevant facts as `<clawbot_context>` context.
Graceful degradation: Azure timeout -> local SQLite -> skip.
