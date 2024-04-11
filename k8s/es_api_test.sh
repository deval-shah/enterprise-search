#!/bin/bash

# Make sure you have enabled port forwarding to localhost to port 8000
# Usage: chmod +x es_api_test.sh ; ./es_api_test.sh "query" "path/to/file"

QUERY="$1"
FILEPATH="$2"

curl -X 'POST' \
  'http://127.0.0.1:8000/query/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F "query=${QUERY}" \
  -F "file=@${FILEPATH}"