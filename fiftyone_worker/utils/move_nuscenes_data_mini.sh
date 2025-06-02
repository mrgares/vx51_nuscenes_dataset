#!/bin/bash

# Define the root directory for nuScenes
root_dir="/datastore/nuScenes"
mini_dir="$root_dir/v1.0-mini"  # Define the directory for v1.0-mini

# Check if the v1.0-mini directory exists
if [[ -d "$mini_dir" ]]; then
    echo "Processing v1.0-mini directory"

    # Move the contents of the samples folder, overriding existing files
    if [[ -d "$mini_dir/samples" ]]; then
        echo "Moving samples from v1.0-mini"
        rsync -a --remove-source-files "$mini_dir/samples/" "$root_dir/samples/"
        find "$mini_dir/samples" -type d -empty -delete
    fi

    # Move the contents of the sweeps folder, overriding existing files
    if [[ -d "$mini_dir/sweeps" ]]; then
        echo "Moving sweeps from v1.0-mini"
        rsync -a --remove-source-files "$mini_dir/sweeps/" "$root_dir/sweeps/"
        find "$mini_dir/sweeps" -type d -empty -delete
    fi

    echo "Data from v1.0-mini moved successfully."
else
    echo "v1.0-mini directory not found."
fi
