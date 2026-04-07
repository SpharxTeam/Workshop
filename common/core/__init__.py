"""
Workshop V3.0 向后兼容层

提供 V2.0 到 V3.0 的导入重定向，确保旧代码可以正常工作。
"""

import warnings

warnings.warn(
    "从 'common.core' 导入已废弃，请使用 'workshop.core' 代替",
    DeprecationWarning,
    stacklevel=2,
)

from workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    PipelineStatus,
    PipelineContext,
    IStorageBackend,
    LocalStorageBackend,
    FileMetadata,
    IOResult,
    IHardwareDevice,
    DeviceInfo,
    DeviceStatus,
    ErrorCode,
    ErrorSeverity,
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
)

from workshop.core.services import (
    ConfigService,
    LoggingService,
    MetricsService,
)

from workshop.core.security import (
    ValidationService,
    ValidationResult,
    SecurityService,
    SecurityContext,
)

from workshop.core.observability import (
    TracingService,
    PerformanceMonitor,
    HealthService,
)

__all__ = [
    "BasePipeline",
    "PipelineResult",
    "PipelineStatus",
    "PipelineContext",
    "IStorageBackend",
    "LocalStorageBackend",
    "FileMetadata",
    "IOResult",
    "IHardwareDevice",
    "DeviceInfo",
    "DeviceStatus",
    "ErrorCode",
    "ErrorSeverity",
    "WorkshopError",
    "ConfigurationError",
    "PipelineError",
    "ValidationError",
    "HardwareError",
    "DataIOError",
    "ConfigService",
    "LoggingService",
    "MetricsService",
    "ValidationService",
    "ValidationResult",
    "SecurityService",
    "SecurityContext",
    "TracingService",
    "PerformanceMonitor",
    "HealthService",
]
