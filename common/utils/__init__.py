"""
通用工具模块

提供日志、计时器、单例模式、装饰器等通用工具。
"""

from commons.utils.logging_utils import (
    get_logger,
    setup_logging,
    LoggerAdapter,
)
from commons.utils.decorators import (
    retry,
    throttle,
    debounce,
    memoize,
    timed,
)
from commons.utils.data_utils import (
    deep_merge,
    flatten_dict,
    unflatten_dict,
    safe_get,
    safe_set,
    deep_copy,
)
from commons.utils.functional import (
    Singleton,
    SingletonMeta,
    Timer,
    ContextTimer,
    RateLimiter,
    CircuitBreaker,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "LoggerAdapter",
    "retry",
    "throttle",
    "debounce",
    "memoize",
    "timed",
    "deep_merge",
    "flatten_dict",
    "unflatten_dict",
    "safe_get",
    "safe_set",
    "deep_copy",
    "Singleton",
    "SingletonMeta",
    "Timer",
    "ContextTimer",
    "RateLimiter",
    "CircuitBreaker",
]
