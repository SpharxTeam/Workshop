"""
Workshop Core - Abstractions
============================

核心抽象层 - 定义所有接口和抽象基类

模块:
    - pipeline: BasePipeline ABC 和相关类型
    - storage: IStorageBackend ABC
    - device: IHardwareDevice ABC
    - models: 数据模型和异常定义
"""

from workshop.core.abstractions.pipeline import (
    BasePipeline,
    PipelineResult,
    PipelineStatus,
    PipelineContext,
)
from workshop.core.abstractions.storage import (
    IStorageBackend,
    LocalStorageBackend,
    FileMetadata,
    IOResult,
)
from workshop.core.abstractions.device import (
    IHardwareDevice,
    DeviceInfo,
    DeviceStatus,
)
from workshop.core.abstractions.models import (
    ErrorCode,
    ErrorSeverity,
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
)

__all__ = [
    # Pipeline
    'BasePipeline',
    'PipelineResult',
    'PipelineStatus',
    'PipelineContext',
    # Storage
    'IStorageBackend',
    'LocalStorageBackend',
    'FileMetadata',
    'IOResult',
    # Device
    'IHardwareDevice',
    'DeviceInfo',
    'DeviceStatus',
    # Models
    'ErrorCode',
    'ErrorSeverity',
    'WorkshopError',
    'ConfigurationError',
    'PipelineError',
    'ValidationError',
    'HardwareError',
    'DataIOError',
]
