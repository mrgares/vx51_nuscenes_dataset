#!/bin/bash

# Define the root directory for nuScenes
root_dir="/datastore/nuScenes"
test_dir="$root_dir/v1.0-test"  # Define the directory for v1.0-test

# Check if the v1.0-test directory exists
if [[ -d "$test_dir" ]]; then
    echo "Processing v1.0-test directory"

    # Move the contents of the samples folder, overriding existing files
    if [[ -d "$test_dir/samples" ]]; then
        echo "Moving samples from v1.0-test"
        rsync -a --remove-source-files "$test_dir/samples/" "$root_dir/samples/"
        find "$test_dir/samples" -type d -empty -delete
    fi

    # Move the contents of the sweeps folder, overriding existing files
    if [[ -d "$test_dir/sweeps" ]]; then
        echo "Moving sweeps from v1.0-test"
        rsync -a --remove-source-files "$test_dir/sweeps/" "$root_dir/sweeps/"
        find "$test_dir/sweeps" -type d -empty -delete
    fi

    echo "Data from v1.0-test moved successfully."
else
    echo "v1.0-test directory not found."
fi
