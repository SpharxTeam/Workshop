"""
数据模型和模式定义
使用Pydantic确保数据验证和类型安全
"""

from .base import BaseSpharxModel, PipelineType, ProcessingStatus, QualityLevel
from .task import PipelineResult, ProcessingStep, PipelineTask
from .scene import SceneMetadata, DatasetInfo, DatasetStatistics
from .annotation import BoundingBox2D, AnnotationObject, ImageAnnotation, COCOAnnotation
from .config import PipelineConfig, SAMConfig, COLMAPConfig, PipelineStageConfig

__all__ = [
    # 基础模型
    'BaseSpharxModel',
    'PipelineType',
    'ProcessingStatus', 
    'QualityLevel',
    
    # 任务和流水线
    'PipelineResult',
    'ProcessingStep',
    'PipelineTask',
    
    # 场景和数据集
    'SceneMetadata',
    'DatasetInfo', 
    'DatasetStatistics',
    
    # 标注数据
    'BoundingBox2D',
    'AnnotationObject',
    'ImageAnnotation',
    'COCOAnnotation',
    
    # 配置
    'PipelineConfig',
    'SAMConfig',
    'COLMAPConfig',
    'PipelineStageConfig',
]