# Description: Import nuscenes dataset to fiftyone dataset for the first time
# Author: Marcelo Garcia
# Reference: Followed tutorial from https://voxel51.com/blog/nuscenes-dataset-navigating-the-road-ahead/

import os
import fiftyone as fo
from nuscenes import NuScenes
from nuscenes.utils.geometry_utils import BoxVisibility, view_points
import numpy as np
from PIL import Image
from nuscenes.utils.data_classes import LidarPointCloud
from nuscenes.utils.splits import create_splits_scenes
import open3d as o3d
import time
from datetime import datetime, timezone
from tqdm import tqdm

DATASET_ROOT = "/datastore/nuScenes/"

def load_lidar(lidar_token):
    filepath = DATASET_ROOT + nusc.get("sample_data", lidar_token)['filename']
    root, extension = os.path.splitext(filepath)

    if extension == ".pcd":
        return filepath

    cloud = LidarPointCloud.from_file(filepath)
    pcd = o3d.geometry.PointCloud()
    points_np = cloud.points[:3, :].T.astype(np.float64)
    pcd.points = o3d.utility.Vector3dVector(points_np)
    o3d.io.write_point_cloud(root, pcd)
    return root

def lidar_sample(group, filepath, sensor, lidar_token):
    data = nusc.get('sample_data', lidar_token)
    data_path, boxes, camera_intrinsic = nusc.get_sample_data(lidar_token, box_vis_level=BoxVisibility.NONE)
    calibrated = nusc.get('calibrated_sensor', data['calibrated_sensor_token'])
    ego_pose = nusc.get('ego_pose', data['ego_pose_token'])

    sample = fo.Sample(filepath=filepath, group=group.element(sensor))

    # Add extrinsics as flat fields
    sample["lidar_translation"] = calibrated["translation"]
    sample["lidar_rotation"] = calibrated["rotation"]
    sample["ego_translation"] = ego_pose["translation"]
    sample["ego_rotation"] = ego_pose["rotation"]

    detections = []
    for box in boxes:
        x, y, z = box.orientation.yaw_pitch_roll
        w, l, h = box.wlh.tolist()
        detection = fo.Detection(
            label=box.name,
            location=box.center.tolist(),
            rotation=[z, y, x],
            dimensions=[l, w, h]
        )
        detections.append(detection)
    sample["lidar_gt_cuboids"] = fo.Detections(detections=detections)
    return sample

def camera_sample(group, filepath, sensor, token):
    data = nusc.get('sample_data', token)
    data_path, boxes, camera_intrinsic = nusc.get_sample_data(token, box_vis_level=BoxVisibility.ANY)
    calibrated = nusc.get('calibrated_sensor', data['calibrated_sensor_token'])
    ego_pose = nusc.get('ego_pose', data['ego_pose_token'])

    image = Image.open(data_path)
    width, height = image.size

    sample = fo.Sample(filepath=filepath, group=group.element(sensor))

    # Add intrinsics and extrinsics as flat fields
    sample["intrinsics"] = camera_intrinsic.flatten().tolist()
    sample["camera_translation"] = calibrated["translation"]
    sample["camera_rotation"] = calibrated["rotation"]
    sample["ego_translation"] = ego_pose["translation"]
    sample["ego_rotation"] = ego_pose["rotation"]

    polylines = []
    for box in boxes:
        corners = view_points(box.corners(), camera_intrinsic, normalize=True)[:2, :]
        front = [(corners[0][i] / width, corners[1][i] / height) for i in range(4)]
        back = [(corners[0][i] / width, corners[1][i] / height) for i in range(4, 8)]
        polyline = fo.Polyline.from_cuboid(front + back, label=box.name)
        polylines.append(polyline)

    sample["image_gt_cuboids"] = fo.Polylines(polylines=polylines)
    return sample

if 'nuscenes' not in fo.list_datasets():
    nusc = NuScenes(version='v1.0-trainval', dataroot=DATASET_ROOT, verbose=True)

    dataset = fo.Dataset(name='nuscenes', persistent=True, overwrite=True)
    dataset.add_group_field("group", default="CAM_FRONT")
    dataset.add_sample_field("split", fo.StringField)

    print('Loading dataset...')

    groups = ("CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_BACK_LEFT", "CAM_BACK",
            "CAM_BACK_RIGHT", "LIDAR_TOP", "RADAR_FRONT",
            "RADAR_FRONT_LEFT", "RADAR_FRONT_RIGHT", "RADAR_BACK_LEFT",
            "RADAR_BACK_RIGHT")

    splits = create_splits_scenes()
    train_scenes = splits["train"]
    val_scenes = splits["val"]

    batch_samples = []
    scene_len = len(nusc.scene)
    for scene_idx, scene in enumerate(tqdm(nusc.scene, desc="Processing scenes", unit="scene")):
        token = scene['first_sample_token']
        my_sample = nusc.get('sample', token)
        scene_name = scene["name"]

        if scene_name in train_scenes:
            split = "train"
        elif scene_name in val_scenes:
            split = "validation"
        else:
            continue

        while not my_sample["next"] == "":
            group = fo.Group()
            for sensor in groups:
                if "RADAR" in sensor:
                    continue  # Optional

                sample_token = my_sample['data'][sensor]
                data = nusc.get('sample_data', sample_token)
                filepath = DATASET_ROOT + data["filename"]

                if data["sensor_modality"] == "lidar":
                    filepath = load_lidar(sample_token)
                    sample = lidar_sample(group, filepath, sensor, sample_token)
                elif data["sensor_modality"] == "camera":
                    sample = camera_sample(group, filepath, sensor, sample_token)
                else:
                    sample = fo.Sample(filepath=filepath, group=group.element(sensor))

                sample["split"] = split
                sample["scene_name"] = scene_name
                sample["sample_token"] = sample_token
                sample["timestamp"] = datetime.fromtimestamp(data["timestamp"] / 1e6, tz=timezone.utc)
                sample["frame_index"] = data["filename"].split('/')[-1].split('.')[0]
                

                batch_samples.append(sample)

            token = my_sample["next"]
            my_sample = nusc.get('sample', token)

        if batch_samples:
            dataset.add_samples(batch_samples)
            batch_samples = []


    # Set sidebar groups
    # Define field schemas explicitly
    sidebar_groups = fo.DatasetAppConfig.default_sidebar_groups(dataset)

    sidebar_groups.append(
        fo.SidebarGroupDocument(
            name="Scene Info",
            paths=["split", "scene_name", "sample_token", "timestamp", "frame_index"]
        )
    )

    sidebar_groups.append(
        fo.SidebarGroupDocument(
            name="Camera Extrinsics",
            paths=["camera_translation", "camera_rotation"]
        )
    )

    sidebar_groups.append(
        fo.SidebarGroupDocument(
            name="Ego Pose",
            paths=["ego_translation", "ego_rotation"]
        )
    )
 
    sidebar_groups.append(
    fo.SidebarGroupDocument(
        name="LiDAR Extrinsics",
        paths=["lidar_translation", "lidar_rotation"]
        )
    )
    sidebar_groups.append(
        fo.SidebarGroupDocument(
            name="Intrinsics",
            paths=["intrinsics"]
        )
    )
    dataset.app_config.sidebar_groups = sidebar_groups
    dataset.save()


    train_view = dataset.match({"split": "train"})
    val_view = dataset.match({"split": "validation"})

    print('Created dataset with %d samples' % len(dataset))
    print('%d train samples' % len(train_view))
    print('%d validation samples' % len(val_view))
else:
    dataset = fo.load_dataset("nuscenes")
    train_view = dataset.match({"split": "train"})
    val_view = dataset.match({"split": "validation"})
    print('Loaded dataset with %d samples' % len(dataset))
    print('%d train samples' % len(train_view))
    print('%d validation samples' % len(val_view))

print(dataset)
session = fo.launch_app(dataset)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")