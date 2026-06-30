"""
Workshop V2 兼容 shim - core 子包
==================================

此包为 V2 兼容 shim,实际 V2→V3 转换逻辑已迁移到 ``commons/core/``。
保留此包仅为支持现有 V2 代码 ``from common.core import X`` 的导入路径。

迁移建议:
    请将 ``from common.core import X`` 替换为:
    - ``from commons.core import X`` (V2 兼容入口,保留 V2 符号)
    - 或 ``from core_workshop.core.X import Y`` (V3 原生入口,推荐)

参见:
    :mod:`commons.core` — V2→V3 兼容转换层
    :mod:`core_workshop.core` — V3 原生核心层
"""

import warnings

warnings.warn(
    "从 'common.core' 导入已废弃,请使用 'commons.core' 或 'core_workshop.core' 代替",
    DeprecationWarning,
    stacklevel=2,
)

from commons.core import *  # noqa: F401,F403
try:
    from commons.core import __all__  # noqa: F401
except ImportError:
    __all__ = []
