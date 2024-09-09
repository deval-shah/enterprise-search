#!/bin/bash

# Function to update and initialize git submodules
update_submodules() {
    echo "Initializing and updating submodules..."
    git submodule init
    git submodule update --recursive --remote

    if [ $? -eq 0 ]; then
        echo "Submodules updated successfully!"
    else
        echo "Failed to update submodules."
        exit 1
    fi
}

# Main function
main() {
    echo "Starting the script..."
    update_submodules
}

# Run the main function
main
