#!/bin/bash

# Function to update and initialize git submodules
update_submodules() {
    echo "Initializing and updating submodules..."
    git submodule init
    git submodule update --init --recursive
    if [ $? -eq 0 ]; then
        echo "Submodules initialized successfully!"
        # Fetch the latest changes
        git submodule foreach git fetch origin
        # Try to checkout the default branch
        git submodule foreach 'git checkout $(git remote show origin | sed -n "/HEAD branch/s/.*: //p")'
        echo "Submodules updated successfully!"
    else
        echo "Failed to initialize submodules."
        return 1
    fi
}

# Function to checkout specific branch for submodule
checkout_submodule_branch() {
    echo "Checking out specific branch for submodule..."
    cd llamasearch/ragflow
    git checkout main  # Try master, then main if master doesn't exist
    if [ $? -eq 0 ]; then
        echo "Submodule branch checked out successfully!"
        cd ../..
    else
        echo "Failed to checkout submodule branch."
        cd ../..
        return 1
    fi
}

# Function to verify submodule content
verify_submodule() {
    echo "Verifying submodule content..."
    if [ -d "llamasearch/ragflow" ] && [ "$(ls -A llamasearch/ragflow)" ]; then
        echo "Submodule content verified successfully!"
    else
        echo "Submodule appears to be empty or missing."
        return 1
    fi
}

# Main function
main() {
    echo "Starting the submodule initialization process..."
    update_submodules || exit 1
    checkout_submodule_branch || exit 1
    verify_submodule || exit 1
    echo "Submodule initialization completed successfully!"
}

# Run the main function
main
