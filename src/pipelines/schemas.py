"""
数据模型定义
使用Pydantic确保数据验证和类型安全
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PipelineType(str, Enum):
    """流水线类型枚举"""
    PIPELINE_2D = "2d"
    PIPELINE_3D = "3d"
    PIPELINE_FULL = "full"


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineResult(BaseModel):
    """流水线执行结果"""
    success: bool
    scene_id: Optional[str] = None
    pipeline_type: Optional[PipelineType] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessingStep(BaseModel):
    """处理步骤结果"""
    step_name: str
    status: ProcessingStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SceneMetadata(BaseModel):
    """场景元数据"""
    scene_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    capture_date: Optional[str] = None
    image_count: int = 0
    resolution: Optional[str] = None
    file_size_mb: float = 0.0
    tags: List[str] = Field(default_factory=list)


class AnnotationObject(BaseModel):
    """标注对象"""
    object_id: str
    category: str
    bbox: List[float]  # [x, y, width, height]
    confidence: float = 1.0
    attributes: Dict[str, Any] = Field(default_factory=dict)
    segmentation: Optional[List[List[float]]] = None  # 多边形坐标