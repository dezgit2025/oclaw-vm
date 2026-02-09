#!/bin/bash

set -euo pipefail

echo "Running GPT-5.2 via Entra ID token (Docker)"

COMPOSE_CMD=(docker compose)
if ! docker compose version >/dev/null 2>&1; then
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    echo ""
    echo "❌ Docker Compose not found. Install Docker Desktop (recommended) or docker-compose."
    exit 127
  fi
fi

if [ ! -f .env.foundry-gpt52 ]; then
  echo ""
  echo "Creating .env.foundry-gpt52 from example..."
  cp .env.foundry-gpt52.example .env.foundry-gpt52
  echo "✅ Created .env.foundry-gpt52"
  echo "Edit it and set ONE auth method (typically service principal) then re-run:"
  echo "  ${0}"
  exit 1
fi

# Load env to validate (the compose run will still use --env-file)
set -a
# shellcheck disable=SC1091
. ./.env.foundry-gpt52
set +a

if [ -z "${AZURE_TENANT_ID:-}" ] && [ -z "${AZURE_CLIENT_ID:-}" ] && [ -z "${AZURE_CLIENT_SECRET:-}" ] && [ -z "${AZURE_FEDERATED_TOKEN_FILE:-}" ]; then
  echo ""
  echo "⚠️  No Entra auth variables detected in .env.foundry-gpt52."
  echo "DefaultAzureCredential will only work if you're on Azure with Managed Identity,"
  echo "or if you provide service principal / federated token values."
  echo ""
  echo "For local Docker, set: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET"
  exit 1
fi

# Idempotency: if a container with the fixed name already exists (for example from a prior
# `docker compose up`), remove it so `docker compose run` won't fail with a name conflict.
CONTAINER_NAME="foundry-gpt52-entra"
if docker ps -aq -f "name=^${CONTAINER_NAME}$" | grep -q .; then
  echo ""
  echo "Found existing container '${CONTAINER_NAME}' — removing it first..."
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

"${COMPOSE_CMD[@]}" -f docker-compose.foundry-gpt52.yml --env-file .env.foundry-gpt52 build

"${COMPOSE_CMD[@]}" -f docker-compose.foundry-gpt52.yml --env-file .env.foundry-gpt52 run --rm foundry-gpt52-entra
