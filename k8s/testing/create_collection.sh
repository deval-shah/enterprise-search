#!/bin/bash

# Ensure the log directory exists
mkdir -p /data/logs/qdrant/

# Redirect all output to a log file
exec > /data/logs/qdrant/hook.log 2>&1

# Configuration
CONFIG_PATH="/app/config/config.yml"
QDRANT_SERVICE_URL=$(grep 'url:' ${CONFIG_PATH} | cut -d " " -f 2)

# Wait for Qdrant service to become available
echo "Waiting for Qdrant service to become available..."
until curl --output /dev/null --silent --head --fail ${QDRANT_SERVICE_URL}; do 
  sleep 5; 
done

echo "Qdrant service is up."

echo "Reading configuration from ConfigMap..."
COLLECTION_NAME=$(grep 'collection_name:' ${CONFIG_PATH} | cut -d " " -f 2)
VECTOR_SIZE=$(grep 'vector_size:' ${CONFIG_PATH} | cut -d " " -f 2)
DISTANCE=$(grep 'distance:' ${CONFIG_PATH} | cut -d " " -f 2)

if [[ -z "$COLLECTION_NAME" ]] || [[ -z "$VECTOR_SIZE" ]] || [[ -z "$DISTANCE" ]]; then
    echo "Error: Unable to find collection name, vector size, or distance in ${CONFIG_PATH}."
    exit 1
else
    echo "Configuration read successfully."
    echo "Collection Name: ${COLLECTION_NAME}"
    echo "Vector Size: ${VECTOR_SIZE}"
    echo "Distance: ${DISTANCE}"
fi

echo "Waiting for Qdrant service to become available..."
until curl --output /dev/null --silent --head --fail "${QDRANT_SERVICE_URL}"; do
    printf '.'
    sleep 5
done

echo "Qdrant service is up. Attempting to create the collection '${COLLECTION_NAME}'..."

RESPONSE=$(curl -s -o response.txt -w "%{http_code}" -X PUT "${QDRANT_SERVICE_URL}/collections/${COLLECTION_NAME}" \
    -H 'Content-Type: application/json' \
    --data-raw "{\"vectors\": {\"size\": ${VECTOR_SIZE}, \"distance\": \"${DISTANCE}\" } }")

if [ "$RESPONSE" == "200" ]; then
    echo "Collection '${COLLECTION_NAME}' created successfully."
else
    echo "Failed to create the collection '${COLLECTION_NAME}'."
    echo "Response Code: ${RESPONSE}"
    echo "Response Body: $(cat response.txt)"
fi

rm response.txt  # Clean up the temporary file