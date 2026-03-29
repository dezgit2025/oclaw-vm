"""
ClawBot Weekly Review Agent
============================
Continuous improvement loop for skill optimization.

Stores learnings in Azure AI Search with text-embedding-3-large
for high-quality semantic retrieval across sessions.

Usage:
    python weekly_review_agent.py              # Full review cycle
    python weekly_review_agent.py --analyze    # Analysis only (no deploy)
    python weekly_review_agent.py --skill mem  # Review specific skill
    python weekly_review_agent.py --init-index # Create Azure AI Search index
    python weekly_review_agent.py --dry-run    # Preview changes
"""

import os
import sys
import json
import glob
import hashlib
import argparse
from datetime import datetime, timedelta
from typing import Optional
from auth_provider import get_search_client as _auth_get_search_client, get_search_index_client, get_vectorizer_params


# ---------------------------------------------------------------------------
# Azure AI Search client setup
# ---------------------------------------------------------------------------

def get_search_client():
    return _auth_get_search_client("clawbot-learning-store")


def get_index_client():
    return get_search_index_client()


# ---------------------------------------------------------------------------
# Index provisioning (run once)
# ---------------------------------------------------------------------------

def ensure_index():
    """Create the learning store index if it doesn't exist."""
    from azure.search.documents.indexes.models import (
        SearchIndex, SearchField, SearchFieldDataType,
        VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
        AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters,
        SemanticConfiguration, SemanticSearch, SemanticPrioritizedFields,
        SemanticField,
    )
    
    idx_client = get_index_client()
    index_name = os.environ.get("AZURE_SEARCH_INDEX", "clawbot-learning-store")
    
    try:
        idx_client.get_index(index_name)
        print(f"  Index '{index_name}' already exists.")
        return
    except Exception:
        pass
    
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="skill_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="week", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="timestamp", type=SearchFieldDataType.DateTimeOffset, sortable=True),
        SearchField(name="observation", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="analysis", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="action_taken", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="outcome", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="tokens_before", type=SearchFieldDataType.Int32, filterable=True),
        SearchField(name="tokens_after", type=SearchFieldDataType.Int32, filterable=True),
        SearchField(name="token_savings_pct", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SearchField(name="success_rate_before", type=SearchFieldDataType.Double),
        SearchField(name="success_rate_after", type=SearchFieldDataType.Double),
        SearchField(name="error_pattern", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="resolution", type=SearchFieldDataType.String, searchable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="learning-vector-profile",
        ),
    ]
    
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
        profiles=[
            VectorSearchProfile(
                name="learning-vector-profile",
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
                name="learning-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[
                        SemanticField(field_name="observation"),
                        SemanticField(field_name="analysis"),
                        SemanticField(field_name="resolution"),
                    ]
                ),
            )
        ]
    )
    
    index = SearchIndex(
        name=index_name, fields=fields,
        vector_search=vector_search, semantic_search=semantic_search,
    )
    idx_client.create_or_update_index(index)
    print(f"  Created index '{index_name}'")


# ---------------------------------------------------------------------------
# Phase 1: OBSERVE
# ---------------------------------------------------------------------------

def collect_telemetry(days=7, logs_dir=None):
    logs_dir = logs_dir or os.path.expanduser("~/.openclaw/logs/sessions")
    cutoff = datetime.now() - timedelta(days=days)
    logs = []
    if not os.path.isdir(logs_dir):
        return logs
    for path in glob.glob(os.path.join(logs_dir, "*.json")):
        try:
            with open(path) as f:
                entry = json.load(f)
            if datetime.fromisoformat(entry.get("timestamp", "2000-01-01")) > cutoff:
                logs.append(entry)
        except (json.JSONDecodeError, ValueError):
            continue
    return sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)


def load_skills(skills_dir=None):
    skills_dir = skills_dir or os.path.expanduser("~/.openclaw/workspace/skills")
    skills = {}
    if not os.path.isdir(skills_dir):
        return skills
    for skill_md in glob.glob(os.path.join(skills_dir, "*", "SKILL.md")):
        name = os.path.basename(os.path.dirname(skill_md))
        with open(skill_md) as f:
            content = f.read()
        skills[name] = {
            "path": skill_md,
            "content": content,
            "token_estimate": int(len(content.split()) * 1.3),
            "md5": hashlib.md5(content.encode()).hexdigest(),
        }
    return skills


# ---------------------------------------------------------------------------
# Phase 2: ANALYZE
# ---------------------------------------------------------------------------

def retrieve_past_learnings(skill_name=None, limit=10):
    try:
        from azure.search.documents.models import VectorizableTextQuery
        sc = get_search_client()
        q = f"improvements for {skill_name}" if skill_name else "recent skill improvements"
        results = sc.search(
            search_text=q,
            vector_queries=[VectorizableTextQuery(text=q, k_nearest_neighbors=5, fields="content_vector")],
            query_type="semantic",
            semantic_configuration_name="learning-semantic-config",
            filter=f"skill_name eq '{skill_name}'" if skill_name else None,
            top=limit,
        )
        return [dict(r) for r in results]
    except Exception as e:
        print(f"  Warning: Could not retrieve past learnings: {e}")
        return []


def analyze(logs, skills, past_learnings):
    from auth_provider import get_chat_client

    prompt = f"""You are ClawBot's self-improvement analyst. Review the past week and
identify specific, actionable improvements.

SESSION LOGS (past 7 days):
{json.dumps(logs, indent=2, default=str)[:8000]}

CURRENT SKILLS (name -> token cost + preview):
{json.dumps({k: {"tokens": v["token_estimate"], "preview": v["content"][:200]} for k, v in skills.items()}, indent=2)}

PAST IMPROVEMENTS (from Azure AI Search):
{json.dumps(past_learnings, indent=2, default=str)[:3000]}

Return JSON only (no markdown fences):
{{
  "token_waste_hotspots": [{{"skill":"name","current_tokens":N,"estimated_optimal":N,"waste_pct":N,"reason":"..."}}],
  "error_clusters": [{{"pattern":"...","frequency":N,"root_cause":"...","fix":"..."}}],
  "skill_rankings": [{{"skill":"name","success_rate":0.0,"avg_tokens":N,"trend":"improving|stable|degrading"}}],
  "compression_opportunities": [{{"skill":"name","section":"...","current_tokens":N,"proposed_tokens":N,"change":"..."}}],
  "missing_capabilities": [{{"description":"...","frequency":N,"proposed_skill":"..."}}]
}}"""
    
    resp = get_chat_client().chat.completions.create(
        model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
        max_completion_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


# ---------------------------------------------------------------------------
# Phase 3: IMPROVE
# ---------------------------------------------------------------------------

def generate_improvements(analysis, skills):
    from auth_provider import get_chat_client
    api = get_chat_client()
    improvements = []
    
    for opp in analysis.get("compression_opportunities", []):
        name = opp.get("skill", "")
        if name not in skills:
            continue
        
        prompt = f"""Rewrite this SKILL.md to be more token-efficient.
Preserve ALL functional instructions.

CURRENT ({skills[name]['token_estimate']} tokens):
{skills[name]['content']}

ISSUE: {opp['change']}
TARGET: ~{opp['proposed_tokens']} tokens

Rules: max 2 examples/concept, tables > paragraphs for params,
remove repeated instructions, split edge cases to SKILL-ADVANCED.md.

Output ONLY the new SKILL.md (no commentary)."""

        resp = api.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
            max_completion_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        new_content = resp.choices[0].message.content.strip()
        new_tokens = int(len(new_content.split()) * 1.3)
        
        improvements.append({
            "skill": name,
            "original": skills[name]["content"],
            "improved": new_content,
            "reason": opp["change"],
            "tokens_before": skills[name]["token_estimate"],
            "tokens_after": new_tokens,
            "savings_pct": round((1 - new_tokens / max(skills[name]["token_estimate"], 1)) * 100, 1),
        })
    return improvements


# ---------------------------------------------------------------------------
# Phase 4: VERIFY & DEPLOY
# ---------------------------------------------------------------------------

def verify_and_deploy(improvements, skills, dry_run=False):
    deployed = []
    for imp in improvements:
        if imp["tokens_after"] >= imp["tokens_before"]:
            imp["status"] = "rejected:no_savings"
            continue
        if imp["tokens_after"] < 50:
            imp["status"] = "rejected:suspiciously_short"
            continue
        if dry_run:
            imp["status"] = "dry_run"
            deployed.append(imp)
            continue
        
        skill_path = skills[imp["skill"]]["path"]
        backup = skill_path + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(skill_path) as f:
            with open(backup, "w") as bf:
                bf.write(f.read())
        with open(skill_path, "w") as f:
            f.write(imp["improved"])
        
        imp["status"] = "deployed"
        imp["backup_path"] = backup
        deployed.append(imp)
    return deployed


def store_learnings(analysis, improvements):
    try:
        sc = get_search_client()
        week = datetime.now().strftime("%Y-W%W")
        docs = [{
            "id": f"analysis-{week}",
            "category": "weekly_analysis",
            "skill_name": "all",
            "week": week,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "observation": json.dumps(analysis.get("token_waste_hotspots", []))[:5000],
            "analysis": json.dumps(analysis.get("error_clusters", []))[:5000],
            "action_taken": json.dumps(analysis.get("compression_opportunities", []))[:5000],
            "outcome": f"{len(improvements)} improvements generated",
        }]
        for imp in improvements:
            docs.append({
                "id": f"imp-{week}-{imp['skill']}-{hashlib.md5(imp['reason'].encode()).hexdigest()[:8]}",
                "category": "skill_improvement",
                "skill_name": imp["skill"],
                "week": week,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "observation": imp["reason"],
                "action_taken": f"Rewrote SKILL.md: {imp['reason'][:200]}",
                "outcome": imp.get("status", "unknown"),
                "tokens_before": imp["tokens_before"],
                "tokens_after": imp["tokens_after"],
                "token_savings_pct": imp["savings_pct"],
            })
        sc.upload_documents(documents=docs)
        print(f"  Stored {len(docs)} documents in Azure AI Search")
    except Exception as e:
        print(f"  Warning: Failed to store learnings: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ClawBot Weekly Review")
    parser.add_argument("--analyze", action="store_true", help="Analysis only")
    parser.add_argument("--skill", type=str, help="Review specific skill")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--init-index", action="store_true")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"CLAWBOT WEEKLY REVIEW - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    if args.init_index:
        print("\nProvisioning Azure AI Search index...")
        ensure_index()
        return
    
    # Phase 1
    print("\nPhase 1: OBSERVE")
    logs = collect_telemetry(days=args.days)
    skills = load_skills()
    print(f"  {len(logs)} sessions, {len(skills)} skills (~{sum(s['token_estimate'] for s in skills.values())} tokens)")
    
    if args.skill:
        skills = {k: v for k, v in skills.items() if args.skill.lower() in k.lower()}
    
    # Phase 2
    print("\nPhase 2: ANALYZE")
    past = retrieve_past_learnings(args.skill)
    analysis = analyze(logs, skills, past)
    print(f"  {len(analysis.get('compression_opportunities', []))} compression opportunities")
    
    if args.analyze:
        print(json.dumps(analysis, indent=2))
        return
    
    # Phase 3
    print("\nPhase 3: IMPROVE")
    improvements = generate_improvements(analysis, skills)
    for imp in improvements:
        print(f"  {imp['skill']}: {imp['tokens_before']}->{imp['tokens_after']} ({imp['savings_pct']}%)")
    
    # Phase 4
    print(f"\nPhase 4: {'DRY RUN' if args.dry_run else 'DEPLOY'}")
    deployed = verify_and_deploy(improvements, skills, dry_run=args.dry_run)
    
    if not args.dry_run:
        store_learnings(analysis, improvements)
    
    total = sum(i["tokens_before"] - i["tokens_after"] for i in deployed)
    print(f"\nSUMMARY: {len(deployed)} deployed, ~{total} tokens saved/session")


if __name__ == "__main__":
    main()
