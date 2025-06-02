#!/bin/bash

# Define the root directory for nuScenes
root_dir="/datastore/nuScenes"

# Loop through each v1.0-trainval*_blobs folder
for blob_dir in "$root_dir"/v1.0-trainval*_blobs; do
    # Check if the directory exists
    if [[ -d "$blob_dir" ]]; then
        echo "Processing $blob_dir"

        # Move the contents of the samples folder, overriding existing files
        if [[ -d "$blob_dir/samples" ]]; then
            echo "Moving samples from $blob_dir"
            rsync -a --remove-source-files "$blob_dir/samples/" "$root_dir/samples/"
            find "$blob_dir/samples" -type d -empty -delete
        fi

        # Move the contents of the sweeps folder, overriding existing files
        if [[ -d "$blob_dir/sweeps" ]]; then
            echo "Moving sweeps from $blob_dir"
            rsync -a --remove-source-files "$blob_dir/sweeps/" "$root_dir/sweeps/"
            find "$blob_dir/sweeps" -type d -empty -delete
        fi
    fi
done

echo "Data moved successfully."
