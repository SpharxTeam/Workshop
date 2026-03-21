# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 数据集模型
# 说明：数据集模型

from dataclasses import dataclass
from typing import List, Dict, Optional
from .scene import Scene
from .sensor_stream import SensorStream
import datetime

@dataclass
class DatasetMetadata:
    """数据集元数据"""
    dataset_id: str
    version: str
    created_at: datetime.datetime
    scenes_count: int
    total_frames: int
    cameras_used: List[str]
    data_format: str  # COCO, KITTI, custom等
    license: Optional[str]
    authors: List[str]

@dataclass
class Dataset:
    """完整数据集结构"""
    metadata: DatasetMetadata
    scenes: List[Scene]
    sensor_streams: List[SensorStream]
    annotations: List[Dict]
    calibration_info: Dict