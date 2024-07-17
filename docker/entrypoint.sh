#!/bin/bash
echo "Config path: $CONFIG_PATH"
exec uvicorn llamasearch.api.main:app --host 0.0.0.0 --port 8010
#exec uvicorn llamasearch.main:app --host 0.0.0.0 --port 8000