# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# =================================================================================  
# 场景数据模型
# 说明：场景数据模型
# =================================================================================
from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime

@dataclass
class SceneMetadata:
    """场景元数据"""
    scene_id: str
    timestamp: datetime.datetime
    location: Optional[Dict[str, float]]  # {latitude, longitude, altitude}
    environment: str  # indoor, outdoor, mixed
    lighting_conditions: str
    weather: Optional[str]
    description: Optional[str]

@dataclass
class Scene:
    """场景数据结构"""
    metadata: SceneMetadata
    color_images: List[str]  # 图像文件路径列表
    depth_images: List[str]  # 深度图像路径列表
    annotations: List[Dict]  # 标注数据
    calibration_data: Optional[Dict]  # 标定数据