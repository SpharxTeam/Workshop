"""
Workshop V3.0 向后兼容层 - 模式模块

提供 V2.0 模式路径的兼容重定向。
"""

import warnings

warnings.warn(
    "从 'common.schemas' 导入已废弃，请使用 'commons.schemas' 代替",
    DeprecationWarning,
    stacklevel=2,
)

from commons.schemas.dataset import DatasetSchema, DatasetMetadata, DataSample
from commons.schemas.scene import SceneSchema, SceneMetadata, SceneFrame
from commons.schemas.sensor_stream import SensorStreamSchema, SensorConfig, SensorFrame

__all__ = [
    "DatasetSchema",
    "DatasetMetadata",
    "DataSample",
    "SceneSchema",
    "SceneMetadata",
    "SceneFrame",
    "SensorStreamSchema",
    "SensorConfig",
    "SensorFrame",
]
