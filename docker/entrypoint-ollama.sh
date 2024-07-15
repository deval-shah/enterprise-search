#!/bin/sh
set -e

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready
until ollama list >/dev/null 2>&1; do
    echo "Waiting for Ollama to start..."
    sleep 1
done

# Run the pull_models.sh script
./pull_models.sh

# Keep the container running
wait
