"""
场景和数据集数据模型
"""

from typing import Optional, Dict, Any, List
from pydantic import Field
from .base import BaseSpharxModel, QualityLevel


class SceneMetadata(BaseSpharxModel):
    """场景元数据"""
    scene_id: str = Field(..., description="场景ID")
    name: Optional[str] = Field(None, description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    capture_date: Optional[str] = Field(None, description="采集日期")
    image_count: int = Field(default=0, description="图像数量")
    resolution: Optional[str] = Field(None, description="分辨率")
    file_size_mb: float = Field(default=0.0, description="文件大小(MB)")
    tags: List[str] = Field(default_factory=list, description="标签")
    camera_parameters: Optional[Dict[str, Any]] = Field(None, description="相机参数")
    environment: Optional[Dict[str, Any]] = Field(None, description="环境信息")


class DatasetInfo(BaseSpharxModel):
    """数据集信息"""
    name: str = Field(..., description="数据集名称")
    version: str = Field(default="1.0.0", description="版本号")
    description: Optional[str] = None
    license: str = Field(default="Apache 2.0")
    quality_level: QualityLevel = Field(default=QualityLevel.DEVELOPMENT)
    num_scenes: int = Field(default=0, description="包含的场景数量")
    total_size_gb: float = Field(default=0.0, description="总大小(GB)")
    coordinate_system: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "right_handed",
            "units": "meters",
            "origin": "scene_center"
        }
    )


class DatasetStatistics(BaseSpharxModel):
    """数据集统计信息"""
    dataset_id: str = Field(..., description="数据集ID")
    total_images: int = Field(default=0, description="总图像数")
    total_annotations_2d: int = Field(default=0, description="2D标注总数")
    total_objects_3d: int = Field(default=0, description="3D物体总数")
    total_physics_facts: int = Field(default=0, description="物理事实总数")
    quality_scores: Dict[str, float] = Field(default_factory=dict, description="质量分数")