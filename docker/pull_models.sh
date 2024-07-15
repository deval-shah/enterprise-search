#!/bin/bash

# Function to extract model name from config.yaml
get_config_model() {
    grep 'llm_model:' config.yaml | awk '{print $2}' | tr -d '"'
}

# Pull models
pull_models() {
    for model in "$@"
    do
        echo "Pulling model: $model"
        ollama pull "$model"
    done
}

# Main execution
echo "Starting model pull process..."

# Get model from config.yaml
config_model=$(get_config_model)

# Combine models
all_models="$config_model $docker_models"

# Pull all models
pull_models $all_models

echo "Model pull process completed."

