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
