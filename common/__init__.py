"""
Workshop V2 兼容 shim
=====================

此包为 V2 兼容 shim,所有实际内容已迁移到 ``commons/``。
保留此包仅为支持现有 V2 代码 ``from common import X`` 的导入路径。

迁移建议:
    请将 ``from common import X`` 替换为 ``from commons import X``

参见:
    :mod:`commons` — 实际通用层实现
"""

import warnings

warnings.warn(
    "从 'common' 导入已废弃,请使用 'commons' 代替",
    DeprecationWarning,
    stacklevel=2,
)

from commons import *  # noqa: F401,F403
try:
    from commons import __all__  # noqa: F401
except ImportError:
    __all__ = []
