# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# =================================================================================
# 传感器数据流模型
# 说明：传感器数据流模型
# =================================================================================
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

@dataclass
class CameraFrame:
    """相机帧数据"""
    timestamp: float
    frame_number: int
    color_image: Optional[np.ndarray]
    depth_image: Optional[np.ndarray]
    camera_id: str

@dataclass
class IMUData:
    """IMU传感器数据"""
    timestamp: float
    linear_acceleration: Dict[str, float]  # x, y, z
    angular_velocity: Dict[str, float]  # x, y, z
    orientation: Optional[Dict[str, float]]  # quaternion or euler angles

@dataclass
class SensorStream:
    """传感器数据流"""
    camera_frames: List[CameraFrame]
    imu_data: List[IMUData]
    sync_timestamps: List[float]