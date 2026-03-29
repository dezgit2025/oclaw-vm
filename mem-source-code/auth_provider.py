#!/usr/bin/env python3
"""
Centralized Azure Auth Provider
================================
Single source of truth for Azure credentials + client factories.
All other modules import from here — no direct credential handling elsewhere.

Auth priority:
  1. Entra ID (DefaultAzureCredential) — picks up az login, managed identity
  2. API key fallback (AZURE_SEARCH_KEY env var)
  3. Fail with helpful error message

Usage:
  from auth_provider import get_search_client, get_search_index_client, get_credential

  # Get a ready-to-use search client
  client = get_search_client("clawbot-memory-store")

  from auth_provider import get_chat_client

  # Get Azure OpenAI client for chat completions
  client = get_chat_client()

  # Health check
  python3 auth_provider.py
"""

import os
import logging
from enum import Enum
from typing import Union

logger = logging.getLogger("auth_provider")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "clawbot-memory-store")
AZURE_LEARNING_INDEX = "clawbot-learning-store"
AZURE_TIMEOUT = 2  # seconds — fail fast, fall back to local


class AuthMode(Enum):
    ENTRA = "entra_id"
    API_KEY = "api_key"


# ---------------------------------------------------------------------------
# Credential resolver
# ---------------------------------------------------------------------------

_cached_credential = None
_cached_auth_mode = None


def get_credential() -> tuple:
    """
    Returns (credential, auth_mode).
    Try Entra ID first, fall back to API key.
    Caches the credential after first successful resolution.
    """
    global _cached_credential, _cached_auth_mode
    if _cached_credential is not None:
        return _cached_credential, _cached_auth_mode

    # Attempt 1: Entra ID (DefaultAzureCredential)
    try:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        credential.get_token("https://search.azure.com/.default")
        _cached_credential = credential
        _cached_auth_mode = AuthMode.ENTRA
        logger.info("Auth: Using Entra ID (DefaultAzureCredential)")
        return credential, AuthMode.ENTRA
    except Exception as e:
        logger.warning(f"Entra ID auth failed: {e}")

    # Attempt 2: API key fallback
    api_key = os.environ.get("AZURE_SEARCH_KEY")
    if api_key:
        from azure.core.credentials import AzureKeyCredential
        credential = AzureKeyCredential(api_key)
        _cached_credential = credential
        _cached_auth_mode = AuthMode.API_KEY
        logger.info("Auth: Using API key fallback")
        return credential, AuthMode.API_KEY

    raise RuntimeError(
        "No valid Azure credential found.\n"
        "  Option 1: Run 'az login' (Entra ID — recommended)\n"
        "  Option 2: Set AZURE_SEARCH_KEY environment variable\n"
        "  Docs: https://learn.microsoft.com/azure/search/search-security-rbac"
    )


# ---------------------------------------------------------------------------
# Client factories
# ---------------------------------------------------------------------------

def get_search_client(index_name: str = None):
    """Factory → SearchClient for querying/uploading documents."""
    from azure.search.documents import SearchClient
    credential, _ = get_credential()
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    if not endpoint:
        raise RuntimeError("AZURE_SEARCH_ENDPOINT environment variable not set")
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name or AZURE_SEARCH_INDEX,
        credential=credential,
    )


def get_search_index_client():
    """Factory → SearchIndexClient for index management (create/update/delete indexes)."""
    from azure.search.documents.indexes import SearchIndexClient
    credential, _ = get_credential()
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    if not endpoint:
        raise RuntimeError("AZURE_SEARCH_ENDPOINT environment variable not set")
    return SearchIndexClient(endpoint=endpoint, credential=credential)


def get_vectorizer_params() -> dict:
    """Return vectorizer config dict for index creation.
    Used by memory_bridge.py and weekly_review_agent.py when creating indexes.
    """
    _, auth_mode = get_credential()
    aoai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not aoai_endpoint:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT environment variable not set")
    params = {
        "resource_url": aoai_endpoint,
        "deployment_name": "text-embedding-3-large",
        "model_name": "text-embedding-3-large",
    }
    if auth_mode == AuthMode.API_KEY:
        aoai_key = os.environ.get("AZURE_OPENAI_KEY")
        if aoai_key:
            params["api_key"] = aoai_key
    return params


def get_chat_client():
    """Factory → AzureOpenAI client for chat completions (GPT-5.2 via AI Foundry).

    Uses Entra ID auth via AzureCliCredential + bearer token provider.
    Env vars:
      AZURE_OPENAI_CHAT_ENDPOINT  — required (e.g. https://pitchbook-resource.cognitiveservices.azure.com/)
      AZURE_OPENAI_CHAT_DEPLOYMENT — optional (default: gpt-5.2)
      AZURE_OPENAI_API_VERSION    — optional (default: 2025-04-01-preview)
    """
    from openai import AzureOpenAI
    from azure.identity import AzureCliCredential, get_bearer_token_provider

    endpoint = os.environ.get("AZURE_OPENAI_CHAT_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "AZURE_OPENAI_CHAT_ENDPOINT environment variable not set.\n"
            "  Set it to your Azure AI Foundry endpoint, e.g.:\n"
            "  export AZURE_OPENAI_CHAT_ENDPOINT=https://pitchbook-resource.cognitiveservices.azure.com/"
        )

    credential = AzureCliCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )

    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
        azure_ad_token_provider=token_provider,
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def health_check() -> dict:
    """Returns auth status, connectivity, and configuration."""
    result = {
        "auth_mode": None,
        "credential_type": None,
        "search_endpoint": os.environ.get("AZURE_SEARCH_ENDPOINT", "NOT SET"),
        "openai_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", "NOT SET"),
        "chat_endpoint": os.environ.get("AZURE_OPENAI_CHAT_ENDPOINT", "NOT SET"),
        "chat_deployment": os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
        "search_reachable": False,
        "chat_reachable": False,
        "error": None,
    }
    try:
        credential, auth_mode = get_credential()
        result["auth_mode"] = auth_mode.value
        result["credential_type"] = type(credential).__name__
        client = get_search_client()
        list(client.search(search_text="*", top=1))
        result["search_reachable"] = True
    except Exception as e:
        result["error"] = str(e)
    try:
        client = get_chat_client()
        client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_completion_tokens=5,
        )
        result["chat_reachable"] = True
    except Exception as e:
        result["chat_error"] = str(e)
    return result


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    status = health_check()
    print(json.dumps(status, indent=2))
    if status["search_reachable"]:
        print("\n✅ Azure AI Search is reachable")
    else:
        print(f"\n❌ Azure AI Search not reachable: {status.get('error', 'unknown')}")
    if status["chat_reachable"]:
        print("✅ Azure AI Foundry LLM is reachable")
    else:
        print(f"❌ Azure AI Foundry LLM not reachable: {status.get('chat_error', 'unknown')}")
