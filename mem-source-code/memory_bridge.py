"""
Hybrid Memory Bridge
=====================
Daily sync: local mem (SQLite) → Azure AI Search

Design principles:
  1. LOCAL IS SOURCE OF TRUTH — mem CLI works exactly as before
  2. AZURE IS THE INTELLIGENCE LAYER — better embeddings, hybrid search, cross-session analytics
  3. RESILIENCE — if Azure is down, ClawBot degrades gracefully to local-only
  4. DAILY SYNC — not real-time, avoids latency on every mem add

Architecture:
┌────────────────────────────────────────────────────────────────────┐
│                     HYBRID MEMORY BRIDGE                           │
│                                                                    │
│  LOCAL (always available)          CLOUD (intelligence layer)      │
│  ┌──────────────────────┐          ┌──────────────────────────┐   │
│  │ ~/.agent-memory/      │  DAILY   │ Azure AI Search           │   │
│  │   memory.db (SQLite)  │ ──SYNC─▶ │   clawbot-memory-store   │   │
│  │   vocab.json          │          │   text-embedding-3-large  │   │
│  │                       │          │   hybrid + semantic rank  │   │
│  │ Embedder: TF-IDF/     │          │                          │   │
│  │   hybrid (BM25+ngram) │          │ Also stores:             │   │
│  │                       │          │   - improvement history   │   │
│  │ Access: mem CLI       │          │   - error patterns        │   │
│  │ Latency: <5ms         │          │   - token efficiency      │   │
│  │ Offline: ✅            │          │   - cross-session trends  │   │
│  └──────────────────────┘          └──────────────────────────┘   │
│           │                                  │                     │
│           │         ┌──────────────┐         │                     │
│           └────────▶│ QUERY ROUTER │◀────────┘                     │
│                     │              │                                │
│                     │ Try Azure    │                                │
│                     │ Fallback to  │                                │
│                     │ local if     │                                │
│                     │ unavailable  │                                │
│                     └──────────────┘                                │
└────────────────────────────────────────────────────────────────────┘

Edge Cases Handled:
  - Azure down → local search continues, sync queues until reconnected
  - Network timeout → 2s timeout, fallback to local instantly
  - Partial sync failure → tracks sync cursor, resumes from last success
  - Conflicting memories → local wins (source of truth), Azure deduplicates
  - First run → full backfill from SQLite to Azure
  - Schema migration → version field in sync metadata
"""

import os
import json
import time
import sqlite3
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from auth_provider import get_search_client, get_search_index_client, get_vectorizer_params

logger = logging.getLogger("memory_bridge")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LOCAL_DB = os.path.expanduser(os.environ.get("CLAWBOT_MEMORY_DB", "~/.agent-memory/memory.db"))
SYNC_STATE_FILE = os.path.expanduser("~/.agent-memory/.sync_state.json")
AZURE_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "clawbot-memory-store")
AZURE_TIMEOUT = 2  # seconds — fail fast, fall back to local
SYNC_SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Sync state management
# ---------------------------------------------------------------------------

def load_sync_state():
    """Track what's been synced to avoid re-uploading."""
    if os.path.exists(SYNC_STATE_FILE):
        with open(SYNC_STATE_FILE) as f:
            return json.load(f)
    return {
        "last_sync_timestamp": None,
        "last_synced_id": None,
        "pending_deletes": [],
        "failed_queue": [],  # memories that failed to sync — retry next run
        "schema_version": SYNC_SCHEMA_VERSION,
        "total_synced": 0,
        "consecutive_failures": 0,
    }


def save_sync_state(state):
    os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)
    with open(SYNC_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Azure AI Search client with resilience
# ---------------------------------------------------------------------------

class AzureSearchBridge:
    """Wraps Azure AI Search with timeout + fallback logic."""
    
    def __init__(self):
        self._client = None
        self._available = None  # None = unknown, True/False = tested
    
    def _get_client(self):
        if self._client is None:
            try:
                from auth_provider import get_search_client
                self._client = get_search_client(AZURE_INDEX)
                self._available = True
            except Exception as e:
                logger.warning(f"Azure Search init failed: {e}")
                self._available = False
        return self._client
    
    @property
    def is_available(self):
        if self._available is None:
            self._get_client()
        return self._available
    
    def health_check(self) -> bool:
        """Quick connectivity test."""
        try:
            client = self._get_client()
            if not client:
                return False
            # Lightweight query to test connectivity
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Azure health check timed out")
            
            # Set timeout (Unix only — on Windows, use threading)
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(AZURE_TIMEOUT)
            try:
                result = client.search(search_text="*", top=1)
                list(result)  # force execution
                self._available = True
                return True
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        except Exception as e:
            logger.warning(f"Azure health check failed: {e}")
            self._available = False
            return False
    
    def upload_memories(self, documents: list) -> dict:
        """Upload batch to Azure. Returns {success: N, failed: [ids]}."""
        client = self._get_client()
        if not client:
            return {"success": 0, "failed": [d["id"] for d in documents]}
        
        try:
            result = client.upload_documents(documents=documents)
            succeeded = sum(1 for r in result if r.succeeded)
            failed_ids = [r.key for r in result if not r.succeeded]
            return {"success": succeeded, "failed": failed_ids}
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {"success": 0, "failed": [d["id"] for d in documents]}
    
    def delete_memories(self, ids: list) -> int:
        """Delete by ID. Returns count deleted."""
        client = self._get_client()
        if not client:
            return 0
        try:
            docs = [{"id": mid} for mid in ids]
            result = client.delete_documents(documents=docs)
            return sum(1 for r in result if r.succeeded)
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return 0
    
    def search(self, query: str, project: str = None, top: int = 10):
        """Hybrid search with vector + keyword + semantic ranking."""
        client = self._get_client()
        if not client:
            return None  # Caller should fall back to local
        
        try:
            from azure.search.documents.models import VectorizableTextQuery
            
            filters = []
            if project:
                filters.append(f"project eq '{project}'")
            filters.append("active eq true")
            
            results = client.search(
                search_text=query,
                vector_queries=[
                    VectorizableTextQuery(
                        text=query,
                        k_nearest_neighbors=top,
                        fields="content_vector"
                    )
                ],
                query_type="semantic",
                semantic_configuration_name="memory-semantic-config",
                filter=" and ".join(filters) if filters else None,
                top=top,
            )
            return [dict(r) for r in results]
        except Exception as e:
            logger.warning(f"Azure search failed, falling back to local: {e}")
            return None  # Trigger fallback


# ---------------------------------------------------------------------------
# Local SQLite reader
# ---------------------------------------------------------------------------

def read_local_memories(since_timestamp: str = None, include_deleted: bool = False):
    """Read memories from local SQLite, optionally filtered by timestamp."""
    if not os.path.exists(LOCAL_DB):
        return []
    
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    
    query = "SELECT * FROM memories WHERE 1=1"
    params = []
    
    if not include_deleted:
        query += " AND active = 1"
    
    if since_timestamp:
        query += " AND created_at > ?"
        params.append(since_timestamp)
    
    query += " ORDER BY created_at ASC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def read_deleted_since(since_timestamp: str):
    """Find memories that were soft-deleted since last sync."""
    if not os.path.exists(LOCAL_DB):
        return []
    
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    
    # Memories that exist but are inactive (soft-deleted)
    query = """
        SELECT id FROM memories 
        WHERE active = 0 AND updated_at > ?
    """
    rows = conn.execute(query, [since_timestamp]).fetchall()
    conn.close()
    return [dict(r)["id"] for r in rows]


# ---------------------------------------------------------------------------
# Transform local memory → Azure document
# ---------------------------------------------------------------------------

def prepare_embed_content(mem: dict) -> str:
    """Prepend metadata context to memory content before embedding.

    Improves vector similarity for project-scoped and tagged queries.
    The prefix is included in the content field sent to Azure, so the
    integrated vectorizer embeds it alongside the fact text.
    """
    content = mem.get("content", mem.get("fact", ""))
    prefix_parts = []
    if mem.get("project") and mem["project"] != "general":
        prefix_parts.append(f"Project: {mem['project']}")
    if mem.get("tags"):
        prefix_parts.append(f"Tags: {mem['tags']}")
    if mem.get("created_at"):
        date_str = str(mem["created_at"])[:10]
        prefix_parts.append(f"Date: {date_str}")
    prefix = " | ".join(prefix_parts)
    return f"[{prefix}]\n{content}" if prefix else content


def memory_to_azure_doc(mem: dict) -> dict:
    """Convert a local memory row into an Azure AI Search document."""
    content = prepare_embed_content(mem)

    return {
        "id": mem["id"],
        "content": content,
        "project": mem.get("project", "general"),
        "tags": mem.get("tags", ""),
        "importance": mem.get("importance", 5),
        "access_count": mem.get("access_count", 0),
        "created_at": mem.get("created_at", datetime.now(timezone.utc).isoformat()),
        "updated_at": mem.get("updated_at", mem.get("created_at", "")),
        "source": "local_mem",
        "active": mem.get("active", 1) == 1,
        "category": categorize_memory(content, mem.get("tags", "")),
        # content_vector is auto-generated by Azure's integrated vectorizer
    }


def categorize_memory(content: str, tags: str = "") -> str:
    """Derive category from LLM-assigned tags, falling back to content heuristics."""
    if tags:
        if "type:decision" in tags or "type:pivot" in tags:
            return "decision"
        if "type:preference" in tags:
            return "preference"
        if "type:tech_stack" in tags:
            return "tech_stack"
        if "type:architecture" in tags:
            return "architecture"
        if "type:error_pattern" in tags:
            return "error_pattern"
        if "type:fact" in tags:
            return "fact"
        if "type:context" in tags:
            return "context"
    # Fallback to content heuristics for memories without tags
    lower = content.lower()
    if any(w in lower for w in ["chose", "decided", "switched to", "going with"]):
        return "decision"
    if any(w in lower for w in ["prefers", "likes", "always use"]):
        return "preference"
    if any(w in lower for w in ["uses", "built with", "running on", "deployed"]):
        return "tech_stack"
    return "general"


def should_decay(memory: dict) -> bool:
    """Check if a memory should be subject to decay/staleness logic."""
    tags = memory.get("tags", "")
    if "permanent:true" in tags:
        return False
    if "pin:" in tags:
        return False
    return True


# ---------------------------------------------------------------------------
# The Daily Sync
# ---------------------------------------------------------------------------

def daily_sync(force_full: bool = False):
    """
    Sync local memories to Azure AI Search.
    
    Incremental by default — only syncs memories created/updated since last sync.
    Use force_full=True for first run or recovery.
    """
    state = load_sync_state()
    bridge = AzureSearchBridge()
    
    print(f"{'=' * 50}")
    print(f"MEMORY SYNC — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 50}")
    
    # Step 0: Health check
    print("\n🔌 Checking Azure connectivity...")
    if not bridge.health_check():
        state["consecutive_failures"] += 1
        save_sync_state(state)
        print(f"  ❌ Azure unavailable (failure #{state['consecutive_failures']})")
        print("  Local memory continues working. Sync will retry tomorrow.")
        
        if state["consecutive_failures"] >= 7:
            print("  ⚠️  7 consecutive failures — check Azure credentials/network")
        return {"status": "azure_unavailable", "consecutive_failures": state["consecutive_failures"]}
    
    state["consecutive_failures"] = 0
    print("  ✅ Azure AI Search connected")
    
    # Defensive init for variables used in summary
    deleted_ids = []

    # Step 1: Determine sync scope
    since = None if force_full else state.get("last_sync_timestamp")
    if since:
        print(f"\n📥 Incremental sync (since {since})")
    else:
        print(f"\n📥 Full sync (first run or forced)")
    
    # Step 2: Read new/updated memories
    memories = read_local_memories(since_timestamp=since)
    print(f"  {len(memories)} memories to sync")
    
    # Step 3: Include previously failed memories
    failed_queue = state.get("failed_queue", [])
    if failed_queue:
        print(f"  + {len(failed_queue)} from retry queue")
        retry_mems = read_local_memories_by_ids(failed_queue)
        memories.extend(retry_mems)
        state["failed_queue"] = []
    
    # Step 4: Transform and upload in batches
    if memories:
        docs = [memory_to_azure_doc(m) for m in memories]
        
        BATCH_SIZE = 100
        total_success = 0
        new_failures = []
        
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i:i + BATCH_SIZE]
            result = bridge.upload_memories(batch)
            total_success += result["success"]
            new_failures.extend(result["failed"])
            print(f"  Batch {i // BATCH_SIZE + 1}: {result['success']}/{len(batch)} uploaded")
        
        if new_failures:
            state["failed_queue"] = new_failures
            print(f"  ⚠️  {len(new_failures)} failed — queued for retry")
    
    # Step 5: Sync deletions
    if since:
        deleted_ids = read_deleted_since(since)
        if deleted_ids:
            deleted_count = bridge.delete_memories(deleted_ids)
            print(f"\n🗑️  Synced {deleted_count} deletions")
    
    # Step 6: Sync pending deletes from previous runs
    pending_deletes = state.get("pending_deletes", [])
    if pending_deletes:
        deleted = bridge.delete_memories(pending_deletes)
        if deleted == len(pending_deletes):
            state["pending_deletes"] = []
        print(f"  Cleared {deleted} pending deletes")
    
    # Step 7: Update sync state
    state["last_sync_timestamp"] = datetime.now(timezone.utc).isoformat()
    state["total_synced"] = state.get("total_synced", 0) + len(memories)
    save_sync_state(state)
    
    summary = {
        "status": "success",
        "memories_synced": len(memories),
        "failures_queued": len(state.get("failed_queue", [])),
        "deletions_synced": len(deleted_ids) if since else 0,
    }
    
    print(f"\n{'=' * 50}")
    print(f"✅ Sync complete: {summary['memories_synced']} memories synced")
    print(f"{'=' * 50}")
    
    return summary


def read_local_memories_by_ids(ids: list):
    """Read specific memories by ID for retry."""
    if not ids or not os.path.exists(LOCAL_DB):
        return []
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(f"SELECT * FROM memories WHERE id IN ({placeholders})", ids).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Query Router — try Azure, fall back to local
# ---------------------------------------------------------------------------

class HybridMemorySearch:
    """
    Drop-in replacement for local mem search.
    Tries Azure first (better embeddings), falls back to local.
    
    Usage in SKILL.md:
        python3 ~/clawbot-skills/weekly-review/bridge.py search "query" [-p project]
    
    Or import directly:
        from bridge import HybridMemorySearch
        searcher = HybridMemorySearch()
        results = searcher.search("JWT auth setup", project="api-server")
    """
    
    def __init__(self):
        self.bridge = AzureSearchBridge()
        self._azure_checked = False
        self._azure_ok = False
    
    def search(self, query: str, project: str = None, top: int = 10) -> list:
        """
        Search memories. Azure first, local fallback.
        
        Returns list of dicts with: id, content, score, source ("azure"|"local")
        """
        # Try Azure (with fast timeout)
        if not self._azure_checked:
            self._azure_ok = self.bridge.health_check()
            self._azure_checked = True
        
        if self._azure_ok:
            results = self.bridge.search(query, project=project, top=top)
            if results is not None:
                return [
                    {
                        "id": r.get("id"),
                        "content": r.get("content", ""),
                        "score": r.get("@search.score", 0),
                        "source": "azure",
                        "project": r.get("project"),
                        "category": r.get("category"),
                    }
                    for r in results
                ]
        
        # Fallback to local
        return self._local_search(query, project, top)
    
    def _local_search(self, query: str, project: str = None, top: int = 10) -> list:
        """Fall back to the existing mem search."""
        import subprocess
        
        cmd = ["python3", os.path.expanduser("~/.agent-memory/cli/mem.py"), "search", query]
        if project:
            cmd.extend(["-p", project])
        cmd.extend(["-k", str(top)])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse mem search output (varies by format)
                return self._parse_local_output(result.stdout)
        except Exception as e:
            logger.error(f"Local search also failed: {e}")
        
        return []
    
    def _parse_local_output(self, output: str) -> list:
        """Parse mem CLI search output into structured results."""
        results = []
        for line in output.strip().split("\n"):
            if line.strip() and not line.startswith("---"):
                results.append({
                    "content": line.strip(),
                    "score": 0,
                    "source": "local",
                })
        return results


# ---------------------------------------------------------------------------
# Azure AI Search Index Schema for memories
# ---------------------------------------------------------------------------

def ensure_memory_index():
    """Create the memory index in Azure AI Search (run once)."""
    from azure.search.documents.indexes.models import (
        SearchIndex, SearchField, SearchFieldDataType,
        VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
        AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters,
        SemanticConfiguration, SemanticSearch, SemanticPrioritizedFields,
        SemanticField,
        ScoringProfile, TextWeights,
        FreshnessScoringFunction, FreshnessScoringParameters,
        MagnitudeScoringFunction, MagnitudeScoringParameters,
    )
    index_client = get_search_index_client()
    
    try:
        existing = index_client.get_index(AZURE_INDEX)
        print(f"Index '{AZURE_INDEX}' exists — deleting for schema update...")
        index_client.delete_index(AZURE_INDEX)
        print(f"  Deleted.")
    except Exception:
        pass
    
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="project", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="tags", type=SearchFieldDataType.String, searchable=True, filterable=True),
        SearchField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="importance", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SearchField(name="access_count", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SearchField(name="active", type=SearchFieldDataType.Boolean, filterable=True),
        SearchField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="created_at", type=SearchFieldDataType.DateTimeOffset, sortable=True, filterable=True),
        SearchField(name="updated_at", type=SearchFieldDataType.DateTimeOffset, sortable=True, filterable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="memory-vector-profile",
        ),
    ]
    
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
        profiles=[
            VectorSearchProfile(
                name="memory-vector-profile",
                algorithm_configuration_name="hnsw-algo",
                vectorizer_name="openai-vectorizer",
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="openai-vectorizer",
                parameters=AzureOpenAIVectorizerParameters(
                    **get_vectorizer_params()
                ),
            )
        ],
    )

    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="memory-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )
    
    scoring_profile = ScoringProfile(
        name="memory-relevance",
        text_weights=TextWeights(weights={"content": 1.5, "tags": 1.2}),
        functions=[
            FreshnessScoringFunction(
                field_name="updated_at",
                boost=1.5,
                interpolation="quadratic",
                parameters=FreshnessScoringParameters(boosting_duration="P80D"),
            ),
            MagnitudeScoringFunction(
                field_name="importance",
                boost=2.0,
                interpolation="linear",
                parameters=MagnitudeScoringParameters(
                    boosting_range_start=1, boosting_range_end=10,
                ),
            ),
            MagnitudeScoringFunction(
                field_name="access_count",
                boost=1.3,
                interpolation="logarithmic",
                parameters=MagnitudeScoringParameters(
                    boosting_range_start=0, boosting_range_end=20,
                ),
            ),
        ],
    )

    index = SearchIndex(
        name=AZURE_INDEX, fields=fields,
        vector_search=vector_search, semantic_search=semantic_search,
        scoring_profiles=[scoring_profile],
        default_scoring_profile="memory-relevance",
    )
    index_client.create_or_update_index(index)
    print(f"✅ Created index '{AZURE_INDEX}'")


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Bridge: local ↔ Azure AI Search")
    sub = parser.add_subparsers(dest="command")
    
    # sync
    sync_p = sub.add_parser("sync", help="Run daily sync")
    sync_p.add_argument("--full", action="store_true", help="Full re-sync (not incremental)")
    
    # search
    search_p = sub.add_parser("search", help="Hybrid search (Azure → local fallback)")
    search_p.add_argument("query", type=str)
    search_p.add_argument("-p", "--project", type=str)
    search_p.add_argument("-k", "--top", type=int, default=10)
    
    # init
    sub.add_parser("init", help="Create Azure AI Search index")
    
    # status
    sub.add_parser("status", help="Show sync state")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        daily_sync(force_full=args.full)
    
    elif args.command == "search":
        searcher = HybridMemorySearch()
        results = searcher.search(args.query, project=args.project, top=args.top)
        for r in results:
            src = f"[{r['source']}]" 
            print(f"  {src:8s} {r.get('content', '')[:100]}")
    
    elif args.command == "init":
        ensure_memory_index()
    
    elif args.command == "status":
        state = load_sync_state()
        print(json.dumps(state, indent=2, default=str))
    
    else:
        parser.print_help()
