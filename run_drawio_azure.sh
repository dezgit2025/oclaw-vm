#!/bin/bash

# next-ai-draw-io with Azure OpenAI GPT-5.2
# This runs the AI-powered draw.io application using Azure OpenAI

echo "Starting next-ai-draw-io with Azure OpenAI GPT-5.2..."
echo "========================================"

set -euo pipefail

# Configuration
CONTAINER_NAME="next-ai-drawio-azure"
PORT=3000

# Azure OpenAI Configuration
AI_PROVIDER="azure"
AZURE_BASE_URL="${AZURE_BASE_URL:-https://pitchbook-resource.openai.azure.com}"
AI_MODEL="${AI_MODEL:-gpt-5.2}"  # This is your deployment name

# Load env file if present (keeps secrets out of the repo)
if [ -f .env.azure-drawio ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env.azure-drawio
    set +a
fi

AZURE_API_KEY="${AZURE_API_KEY:-}"

if [ -z "$AZURE_API_KEY" ]; then
    echo ""
    echo "❌ AZURE_API_KEY is not set."
    echo "Set it in your environment or create .env.azure-drawio from .env.azure-drawio.example."
    echo ""
    echo "Example:"
    echo "  cp .env.azure-drawio.example .env.azure-drawio"
    echo "  # edit .env.azure-drawio and set AZURE_API_KEY=..."
    exit 1
fi

# Optional: Set temperature for more deterministic output (recommended for diagrams)
TEMPERATURE="0"

# Check if container already exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "⚠️  Container '$CONTAINER_NAME' already exists"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping and removing existing container..."
        docker stop $CONTAINER_NAME 2>/dev/null
        docker rm $CONTAINER_NAME 2>/dev/null
    else
        echo "Aborted."
        exit 0
    fi
fi

# Run the container with Azure OpenAI configuration
echo "Launching container with Azure OpenAI..."
echo "  Provider:   $AI_PROVIDER"
echo "  Model:      $AI_MODEL"
echo "  Endpoint:   $AZURE_BASE_URL"
echo ""

docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:3000 \
  -e AI_PROVIDER=$AI_PROVIDER \
  -e AI_MODEL=$AI_MODEL \
  -e AZURE_API_KEY=$AZURE_API_KEY \
  -e AZURE_BASE_URL=$AZURE_BASE_URL \
  -e TEMPERATURE=$TEMPERATURE \
  ghcr.io/dayuanjiang/next-ai-draw-io:latest

# Check if container started successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Container started successfully!"
    echo "========================================"
    echo "Container name: $CONTAINER_NAME"
    echo "Access at:      http://localhost:$PORT"
    echo "AI Provider:    Azure OpenAI"
    echo "AI Model:       $AI_MODEL (GPT-5.2)"
    echo "Endpoint:       $AZURE_BASE_URL"
    echo ""
    echo "Checking container status..."
    sleep 3
    docker logs $CONTAINER_NAME --tail 20
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker logs $CONTAINER_NAME"
    echo "  Follow logs:  docker logs -f $CONTAINER_NAME"
    echo "  Stop:         docker stop $CONTAINER_NAME"
    echo "  Start:        docker start $CONTAINER_NAME"
    echo "  Remove:       docker rm -f $CONTAINER_NAME"
else
    echo ""
    echo "❌ Failed to start container"
    echo "Check Docker is running: docker ps"
    exit 1
fi
