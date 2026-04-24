"""
Core-Workshop V3.0 向后兼容层 - 配置模块

提供 V2.0 配置路径的兼容重定向。
"""

import warnings

warnings.warn(
    "从 'common.configs' 导入已废弃，请使用 'core_workshop.core.services.ConfigService' 代替",
    DeprecationWarning,
    stacklevel=2,
)

from core_workshop.core.services.config_service import (
    ConfigService,
    ConfigLoader,
    ConfigValidator,
)

__all__ = [
    "ConfigService",
    "ConfigLoader",
    "ConfigValidator",
]
