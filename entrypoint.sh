#!/bin/bash
if [ -z "${CLUSTER_DEPLOYMENT+x}" ]; then
  echo "CLUSTER_DEPLOYMENT variable is not set"
else
  # Run the script to update Ollama server URL in k8s llamaindex library.
  if [ "$CLUSTER_DEPLOYMENT" -eq 1 ]; then
    echo "Updating ollama server url..."
    /app/update_ollama_server_url_k8s.sh
  fi
fi

exec uvicorn src.main:app --host 0.0.0.0 --port 8000