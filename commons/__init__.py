"""
Workshop V3.0 通用层
====================

提供通用工具、数据模式、配置管理等功能。

子模块:
    - utils: 日志、计时器、单例、装饰器、数据工具
    - schemas: 数据模式（BaseSchema / DatasetSchema / SceneSchema / SensorStreamSchema）
    - configs: YAML 配置加载
    - scripts: 数据 IO、配置加载脚本
    - dashboard: Streamlit 可视化应用
    - core: V2→V3 兼容 shim（保留供 V2 代码导入过渡）
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
    # utils
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
    # schemas
    "BaseSchema",
    "DatasetSchema",
    "SceneSchema",
    "SensorStreamSchema",
    "ValidationResult",
]
