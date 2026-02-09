#!/bin/bash

# next-ai-draw-io Docker Container Setup
# This runs the AI-powered draw.io application

echo "Starting next-ai-draw-io container..."
echo "========================================"

# Configuration
CONTAINER_NAME="next-ai-drawio"
PORT=3000
AI_PROVIDER="anthropic"
AI_MODEL="claude-sonnet-4-5"

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable not set"
    echo ""
    echo "Please set your API key first:"
    echo "  export ANTHROPIC_API_KEY='your_actual_key_here'"
    echo ""
    echo "Or run this script with the key:"
    echo "  ANTHROPIC_API_KEY='your_key' ./run_drawio_container.sh"
    exit 1
fi

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

# Run the container
echo "Launching container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:3000 \
  -e AI_PROVIDER=$AI_PROVIDER \
  -e AI_MODEL=$AI_MODEL \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  ghcr.io/dayuanjiang/next-ai-draw-io:latest

# Check if container started successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Container started successfully!"
    echo "========================================"
    echo "Container name: $CONTAINER_NAME"
    echo "Access at:      http://localhost:$PORT"
    echo "AI Provider:    $AI_PROVIDER"
    echo "AI Model:       $AI_MODEL"
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
