"""
任务和流水线结果数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from .base import BaseSpharxModel, PipelineType, ProcessingStatus


class PipelineResult(BaseSpharxModel):
    """流水线执行结果"""
    success: bool = Field(..., description="是否成功")
    scene_id: Optional[str] = Field(None, description="场景ID")
    pipeline_type: Optional[PipelineType] = Field(None, description="流水线类型")
    output_path: Optional[str] = Field(None, description="输出路径")
    error_message: Optional[str] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ProcessingStep(BaseSpharxModel):
    """处理步骤结果"""
    step_name: str = Field(..., description="步骤名称")
    status: ProcessingStatus = Field(..., description="处理状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error: Optional[str] = Field(None, description="错误信息")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """计算持续时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class PipelineTask(BaseSpharxModel):
    """流水线任务"""
    scene_id: str = Field(..., description="场景ID")
    pipeline_type: PipelineType = Field(..., description="流水线类型")
    priority: int = Field(default=1, ge=1, le=10, description="优先级")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    config_overrides: Dict[str, Any] = Field(default_factory=dict)
    
    # 时间戳
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 结果
    result: Optional[PipelineResult] = None
    error_message: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @property
    def processing_time(self) -> Optional[float]:
        """计算处理时间（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None