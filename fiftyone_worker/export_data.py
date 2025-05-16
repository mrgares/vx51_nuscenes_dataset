import os
import json
import shutil
import fiftyone as fo

# Load dataset and view
dataset = fo.load_dataset("nuscenes")
view = dataset.load_saved_view("top 5 fewer dymanic objects")

# Only include camera slices (exclude LIDAR, etc.)
camera_slices = [
    "CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT",
    "CAM_BACK_LEFT", "CAM_BACK", "CAM_BACK_RIGHT"
]

# Output root directory
export_root = "./export"
os.makedirs(export_root, exist_ok=True)

# ---------- Save shared camera info once ----------

camera_params = {}

for cam_slice in camera_slices:
    sample = dataset.select_group_slices(cam_slice).first()
    if sample:
        camera_params[cam_slice] = {
            "intrinsics": sample.get_field("intrinsics") if sample.has_field("intrinsics") else None,
            "camera_translation_relative_to_ego": sample.get_field("camera_translation") if sample.has_field("camera_translation") else None,
            "camera_rotation_relative_to_ego": sample.get_field("camera_rotation") if sample.has_field("camera_rotation") else None,
        }

with open(os.path.join(export_root, "camera_parameters.json"), "w") as f:
    json.dump(camera_params, f, indent=2)

# ---------- Export scene-wise data ----------
for scene_name in view.distinct("scene_name"):
    print(f"Exporting scene: {scene_name}")

    # Scene folder
    scene_dir = os.path.join(export_root, scene_name)
    os.makedirs(scene_dir, exist_ok=True)

    # Get view for one scene
    scene_view = view.match({"scene_name": scene_name})
    group_ids = scene_view.values("group.id")

    for gid in group_ids:
        group_samples = dataset.get_group(gid)

        # Use timestamp from any available sample in the group (e.g., CAM_FRONT)
        for cam_slice in camera_slices:
            sample = group_samples.get(cam_slice, None)
            if sample:
                timestamp = str(sample.timestamp)
                break
        else:
            continue  # skip group if no camera slices are present

        # Timestamp folder inside scene folder
        group_dir = os.path.join(scene_dir, timestamp)
        os.makedirs(group_dir, exist_ok=True)

        group_metadata = {}

        for cam_slice in camera_slices:
            sample = group_samples.get(cam_slice, None)
            if not sample:
                continue

            filename = f"{cam_slice}.jpg"
            dst_path = os.path.join(group_dir, filename)
            shutil.copy2(sample.filepath, dst_path)
            # NOTE:
            # We save ego_translation and ego_rotation for each camera slice individually,
            # even though all slices belong to the same group (frame), because:
            #
            # - In nuScenes, each camera is triggered at a slightly different timestamp 
            #   (as the LiDAR sweeps past its field of view).
            # - Each camera sample has its own timestamp, and nuScenes associates the 
            #   ego pose that is closest to that timestamp.
            # - As a result, even within the same frame/group, the ego pose may differ 
            #   slightly between camera slices.
            #
            # Therefore, to preserve precise motion and pose information, we store the 
            # ego pose separately for each camera image (per slice, per group).
            group_metadata[cam_slice] = {
                "ego_translation": sample.get_field("ego_translation") if sample.has_field("ego_translation") else None,
                "ego_rotation": sample.get_field("ego_rotation") if sample.has_field("ego_rotation") else None,
            }

        # Save ego pose metadata
        meta_path = os.path.join(group_dir, "ego_pose.json")
        with open(meta_path, "w") as f:
            json.dump(group_metadata, f, indent=2)
