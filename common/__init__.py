"""
Workshop V3.0 向后兼容层

提供 V2.0 到 V3.0 的导入重定向。
"""

import warnings

warnings.warn(
    "从 'common' 导入已废弃，请使用新的模块结构代替",
    DeprecationWarning,
    stacklevel=2,
)

from common.core import *
from common.configs import *
from common.scripts import *
from common.schemas import *
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
