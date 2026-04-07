"""
Workshop V3.0 通用层

提供通用工具、数据模式、配置管理等功能。
"""

from commons.utils import (
    get_logger,
    setup_logging,
    Timer,
    Singleton,
    retry,
    throttle,
    debounce,
    deep_merge,
    flatten_dict,
    safe_get,
    safe_set,
)
from commons.schemas import (
    BaseSchema,
    DatasetSchema,
    SceneSchema,
    SensorStreamSchema,
    ValidationResult,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "Timer",
    "Singleton",
    "retry",
    "throttle",
    "debounce",
    "deep_merge",
    "flatten_dict",
    "safe_get",
    "safe_set",
    "BaseSchema",
    "DatasetSchema",
    "SceneSchema",
    "SensorStreamSchema",
    "ValidationResult",
]
