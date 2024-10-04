#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting LlamaSearch test suite..."

export PYTHONPATH=$PYTHONPATH:$(pwd)

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
for cmd in dvc pytest; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is not installed. Please install it and try again."
        exit 1
    fi
done

# # Pull data from DVC
# echo "Pulling test documents from DVC..."
# if ! dvc pull --force data/test_docs.dvc; then
#     echo "Error: Failed to pull data from DVC."
#     exit 1
# fi

# Check if test_docs directory contains files
if [ -z "$(ls -A data/test_docs)" ]; then
    echo "Error: test_docs directory is empty after DVC pull."
    exit 1
fi

# Run pytest only on the tests directory
echo "Running tests..."
if ! pytest; then
    echo "Error: Some tests failed. Check report.html for details."
    exit 1
fi

echo "Testing process completed successfully. See report.html for detailed results."
