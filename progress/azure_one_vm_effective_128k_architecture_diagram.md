# One-VM (Ubuntu) architecture: “effective 128k” via RAG + rolling summaries

This is a simple architecture for simulating “long context” while keeping the model’s **native context window** at ~**8k–16k** (or 16k–32k if you have headroom).

## Diagram

```text
                    (You / OpenClaw / Browser)
                               |
                               | HTTPS (optional) / SSH tunnel / Tailscale
                               v
+---------------------------------------------------------------------+
|                     Azure GPU VM (Ubuntu)                           |
|               Size: Standard_NC8as_T4_v3 (example)                  |
|                                                                     |
|  +----------------------+        +-------------------------------+  |
|  | Orchestrator API      |        | LLM Server                    |  |
|  | (FastAPI)             |<------>| (Ollama or llama.cpp server)  |  |
|  |  - /chat              |  prompt|  - model: quantized 7B        |  |
|  |  - /ingest            |  + ctx |  - context: 8k–16k            |  |
|  |  - tool router (opt)  |  resp  |  - outputs answer / summaries |  |
|  +----------+-----------+        +-------------------------------+  |
|             |                                                      |
|   retrieve   | embed(query/doc chunks)                              |
|             v                                                      |
|  +----------------------+        +-------------------------------+  |
|  | Vector DB            |        | Embeddings                     |  |
|  | (Qdrant, Docker)     |<------>| (Hosted in Azure Foundry/AOAI  |  |
|  |  - chunks + metadata | vectors|  OR local embed model)         |  |
|  +----------------------+        +-------------------------------+  |
|                                                                     |
|  Storage on VM disk:                                                |
|   - model files (if local)                                          |
|   - Qdrant data volume                                              |
|   - memory state (working_summary, pinned_facts JSON)               |
+---------------------------------------------------------------------+
```

## What happens on each chat request (high level)

1) **Orchestrator receives your message** (from OpenClaw or another client).
2) It **embeds** the query and **retrieves** relevant chunks from **Qdrant**.
3) It builds a prompt with:
   - **Pinned facts** (stable preferences/constraints)
   - **Working summary** (rolling summary memory)
   - **Retrieved context chunks** (RAG context)
   - Your question
4) It calls the **LLM server** (Ollama / llama.cpp) to produce the answer.
5) It optionally calls the LLM again to **update the rolling summary**.

## Notes
- This setup gives you “functionally long context” without paying the full runtime cost of a true 128k KV-cache.
- For a $500/mo budget and ~28 hours/mo usage, a **T4 16GB** VM is a common starting point; you use **RAG** to compensate for limited native context.
