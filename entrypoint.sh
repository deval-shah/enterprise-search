#!/bin/bash
# Run the script to update Ollama server URL in k8s llamaindex library.
/app/update_ollama_server_url_k8s.sh

# Then start the server
exec uvicorn src.server:app --host 0.0.0.0 --port 8000