"""
数据集相关数据模型
"""

from typing import List, Optional, Dict
from pydantic import Field
from .base import BaseSpharxModel, QualityLevel

class DatasetInfo(BaseSpharxModel):
    """数据集信息"""
    name: str = Field(..., description="数据集名称")
    version: str = Field(default="1.0.0", description="版本号")
    description: Optional[str] = None
    license: str = Field(default="Apache 2.0")
    quality_level: QualityLevel = Field(default=QualityLevel.DEVELOPMENT)
    num_scenes: int = Field(default=0, description="包含的场景数量")
    total_size_gb: float = Field(default=0.0, description="总大小(GB)")
    
class SceneInfo(BaseSpharxModel):
    """场景信息"""
    dataset_id: str = Field(..., description="所属数据集ID")
    scene_id: str = Field(..., description="场景ID")
    name: str = Field(..., description="场景名称")
    description: Optional[str] = None
    environment_type: str = Field(default="indoor", description="环境类型")
    num_images: int = Field(default=0, description="图像数量")
    has_3d_reconstruction: bool = Field(default=False)
    has_physics_facts: bool = Field(default=False)
    
class DatasetStatistics(BaseSpharxModel):
    """数据集统计信息"""
    dataset_id: str
    total_images: int = 0
    total_annotations_2d: int = 0
    total_objects_3d: int = 0
    total_physics_facts: int = 0
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    