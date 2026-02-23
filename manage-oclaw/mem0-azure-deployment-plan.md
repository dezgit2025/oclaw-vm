# Plan: Self-Hosted Mem0 API on Azure (Local Test → Container Apps)

## Context

OpenClaw session logs grow unbounded (10 MB / 2,350 entries) causing context overflow. Mem0 provides memory management so sessions can be rotated without losing context. Rather than using Mem0 Cloud (Option 1) or Qdrant on the VM (Option 2), we're deploying a self-hosted mem0 REST API backed entirely by Azure services: **Azure AI Search** (vector store) + **Azure OpenAI** (LLM + embeddings). No pgvector, no Neo4j, no third-party API keys.

The user wants to **test locally on Mac first**, then push to Azure Container Apps.

## Environment Summary

- Docker 28.3.2, Azure CLI 2.81.0 installed on Mac
- Azure OpenAI resource: `dezazureaihubn3517051700` (eastus2) — has gpt-4.1-mini deployed
- No Azure AI Search service exists yet — need to create
- No Azure Container Registry exists yet — need to create
- Ports 8888/8000 free locally, 167 GB disk free
- VM is currently shut down (not needed for this work)

---

## Revised Steps (8 total)

### Step 1: Create Azure AI Search (Free tier)
- `az search service create --name oclaw-mem0-search --resource-group RG_OCLAW2026 --sku free --location eastus2`
- Get admin API key for local testing

### Step 2: Deploy embedding model on Azure OpenAI
- Deploy `text-embedding-3-small` on `dezazureaihubn3517051700`
- Need to verify resource group name first (`az cognitiveservices account list -o table`)
- Verify with a test embedding call

### Step 3: Create mem0 server project locally
Create `/Users/dez/Projects/openclaw_vm/mem0-server/` with:

| File | Purpose |
|------|---------|
| `main.py` | Forked from mem0 `server/main.py` — Azure-only DEFAULT_CONFIG, no pgvector/neo4j, added `/health` endpoint |
| `requirements.txt` | `fastapi`, `uvicorn`, `pydantic`, `mem0ai>=0.1.48`, `python-dotenv`, `azure-search-documents`, `azure-identity`, `openai` (dropped `psycopg`) |
| `Dockerfile` | `python:3.12-slim`, pip install, uvicorn on port 8000 |
| `docker-compose.yaml` | Single service (no postgres, no neo4j), port 8888→8000, volume mount for SQLite history |
| `.env` | API keys for local testing (gitignored) |
| `.env.example` | Template without secrets |

Key config in `main.py`:
```python
DEFAULT_CONFIG = {
    "version": "v1.1",
    "vector_store": {"provider": "azure_ai_search", "config": {
        "service_name": AZURE_SEARCH_SERVICE_NAME,
        "api_key": AZURE_SEARCH_API_KEY,
        "collection_name": "mem0-memories",
        "embedding_model_dims": 1536
    }},
    "llm": {"provider": "azure_openai", "config": {
        "model": "gpt-4.1-mini",
        "azure_kwargs": {"azure_deployment": "gpt-4.1-mini",
                         "azure_endpoint": AZURE_OPENAI_ENDPOINT,
                         "api_key": AZURE_OPENAI_API_KEY}
    }},
    "embedder": {"provider": "azure_openai", "config": {
        "model": "text-embedding-3-small",
        "azure_kwargs": {"azure_deployment": "text-embedding-3-small",
                         "azure_endpoint": AZURE_OPENAI_ENDPOINT,
                         "api_key": AZURE_OPENAI_API_KEY}
    }}
    # No graph_store — mem0 skips Neo4j when omitted
}
```

### Step 4: Build Docker image
- `docker compose build` in `mem0-server/`

### Step 4.5: Local end-to-end testing (NEW)
- `docker compose up -d`
- Test all endpoints with curl:
  1. `GET /health` — verify server is up
  2. `POST /memories` — add a test memory (user_id: "desazure")
  3. `POST /search` — search for the memory by semantic query
  4. `GET /memories?user_id=desazure` — list all memories
  5. `GET /memories/{id}` — get specific memory
  6. `PUT /memories/{id}` — update a memory
  7. `DELETE /memories/{id}` — delete a memory
  8. Verify SQLite history file persists in `./history/`
  9. `docker compose restart` — verify memories survive restart (stored in Azure AI Search)
  10. Open `http://localhost:8888/docs` — verify Swagger UI
- Fix any issues before proceeding

### Step 5: Deploy to Azure Container Apps
- Create ACR: `az acr create --name oclawacr --resource-group RG_OCLAW2026 --sku Basic`
- Build in ACR: `az acr build --registry oclawacr --image mem0-server:latest ./mem0-server/`
- Create Container Apps Environment: `az containerapp env create --name oclaw-cae --resource-group RG_OCLAW2026 --location eastus2`
- Deploy with system-assigned managed identity, scale-to-zero, 0.5 CPU / 1 GB RAM
- Pass empty `AZURE_OPENAI_API_KEY` → triggers DefaultAzureCredential (managed identity)
- AI Search Free tier doesn't support managed identity → pass API key as Container Apps secret

### Step 6: Assign RBAC roles
- **Azure OpenAI**: `Cognitive Services OpenAI User` role to Container App's managed identity
- **ACR pull**: `AcrPull` role (or use `--registry-identity system`)
- (If AI Search upgraded to Basic later: `Search Index Data Contributor` + `Search Service Contributor`)

### Step 7: Point OpenClaw mem0 plugin at API URL
- Get Container App FQDN
- Update OpenClaw `openclaw.json` on VM with the self-hosted API URL
- Verify end-to-end: OpenClaw agent → mem0 API → Azure AI Search

---

## Cost Estimate

| Resource | Cost |
|----------|------|
| Azure AI Search (Free) | $0 |
| Azure OpenAI (gpt-4.1-mini + embeddings) | ~$1-3/mo at mem0 volumes |
| Azure Container Registry (Basic) | ~$5/mo |
| Azure Container Apps (scale-to-zero) | ~$0 idle (within free grant) |
| **Total** | **~$6-8/mo** |

---

## Verification Plan

**Local (Step 4.5):**
- All 7 mem0 REST endpoints return expected responses
- Memories persist across container restart
- Swagger UI accessible at localhost:8888/docs

**Azure (after Step 6):**
- `curl https://<FQDN>/health` returns OK
- Add + search memories via the public FQDN
- Managed identity auth works (no API keys in env vars for Azure OpenAI)

---

## Files to Create

| File | Action |
|------|--------|
| `mem0-server/main.py` | Create (forked from mem0 stock, Azure config) |
| `mem0-server/requirements.txt` | Create |
| `mem0-server/Dockerfile` | Create |
| `mem0-server/docker-compose.yaml` | Create |
| `mem0-server/.env` | Create (gitignored) |
| `mem0-server/.env.example` | Create |
| `.gitignore` | Update (add mem0-server/.env and history/) |
