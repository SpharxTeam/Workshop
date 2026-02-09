"""
基础数据模型和类型定义
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


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


class QualityLevel(str, Enum):
    """质量等级枚举"""
    RESEARCH = "research"      # 研究级
    PRODUCTION = "production"  # 生产级
    DEVELOPMENT = "development" # 开发级


class BaseSpharxModel(BaseModel):
    """Spharx基础模型"""
    id: Optional[str] = Field(None, description="唯一标识符")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def dict(self, **kwargs):
        """重写dict方法，包含时间戳更新"""
        self.updated_at = datetime.now()
        return super().dict(**kwargs)