"""
Workshop V3.0 向后兼容层 - 脚本模块

提供 V2.0 脚本路径的兼容重定向。
"""

import warnings

warnings.warn(
    "从 'common.scripts' 导入已废弃，请使用 'commons.utils' 代替",
    DeprecationWarning,
    stacklevel=2,
)

from commons.utils.logging_utils import get_logger, setup_logging
from commons.utils.decorators import retry, throttle, debounce
from commons.utils.data_utils import deep_merge, safe_get, safe_set

__all__ = [
    "get_logger",
    "setup_logging",
    "retry",
    "throttle",
    "debounce",
    "deep_merge",
    "safe_get",
    "safe_set",
]
