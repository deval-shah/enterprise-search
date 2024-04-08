#!/bin/bash

# Default URL if OLLAMA_SERVER_URL is not set
OLLAMA_SERVER_URL="${OLLAMA_SERVER_URL:-http://localhost:11434}"

# Ensure URL starts with http://
if [[ ! $OLLAMA_SERVER_URL =~ ^http://.* ]]; then
    OLLAMA_SERVER_URL="http://$OLLAMA_SERVER_URL"
fi

# Use Python to get the installation directory of llama_index
LLAMA_INDEX_DIR=$(python -c "import os, llama_index; print(os.path.dirname(llama_index.__file__))")

# Path to the base.py file
# BASE_PY="$LLAMA_INDEX_DIR/llms/ollama/base.py"
BASE_PY="/usr/local/lib/python3.10/dist-packages/llama_index/llms/ollama/base.py"
echo "Attempting to update base URL in: $BASE_PY"

# Check if the base.py file exists
if [ -f "$BASE_PY" ]; then
    # Use sed to update the default URL for base_url, handling multiline pattern
    # This command looks for the base_url definition and replaces it ensuring only one comma is at the end
    sed -i "/base_url: str = Field(/,/description=/{s|default=.*\",|default=\"${OLLAMA_SERVER_URL}\",|}" "$BASE_PY"
    echo "Updated base_url to ${OLLAMA_SERVER_URL} in ${BASE_PY}"
else
    echo "The base.py file does not exist in the expected directory: $BASE_PY"
fi
