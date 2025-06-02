#!/bin/bash

# -------------------------------------------------------------------
# Script: extract_nuscenes_sweeps.sh
# Purpose: 
#   Extract only the "sweeps/CAM_*" camera image folders from all 
#   NuScenes .tgz camera archives in parallel, and copy the images 
#   directly into matching WSL folders at /datastore/nuScenes/sweeps/
#
# What it does:
#   - Processes each *_blobs_camera.tgz archive in /mnt/e/Temp
#   - Extracts only the sweeps/CAM_* folders (not samples/)
#   - Places the extracted images into:
#       /datastore/nuScenes/sweeps/CAM_FRONT/
#       /datastore/nuScenes/sweeps/CAM_BACK/
#       ... etc.
#   - Runs camera extractions in parallel for speed
#   - Prints a progress counter per archive
#
# Dependencies:
#   - GNU tar
#   - bash
#
# Author: Marcelo Garcia
# Date: 2025
# -------------------------------------------------------------------
zip_dir="/mnt/e/Temp"
target_root="/datastore/nuScenes/sweeps"
cams=(CAM_BACK CAM_BACK_LEFT CAM_BACK_RIGHT CAM_FRONT CAM_FRONT_LEFT CAM_FRONT_RIGHT)

# Find all matching .tgz files
tgz_files=($(find "$zip_dir" -name '*_blobs_camera.tgz' | sort))
total=${#tgz_files[@]}
count=0

echo "🔍 Found $total archives to process."
echo

for tgz_file in "${tgz_files[@]}"; do
    count=$((count + 1))
    echo "📦 [$count/$total] Processing: $tgz_file"

    for cam in "${cams[@]}"; do
        (
            out_dir="$target_root/$cam"
            mkdir -p "$out_dir"
            echo "  → Extracting $cam from sweeps/ to $out_dir"
            tar --extract \
                --file="$tgz_file" \
                --wildcards \
                --no-anchored \
                --strip-components=2 \
                --directory="$out_dir" \
                "sweeps/$cam/*"
        ) &
    done

    wait
    echo "✅ Finished archive $count of $total"
    echo
done

echo "🎉 All sweeps camera data extracted successfully!"
