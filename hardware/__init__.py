# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# hardware — V2→V3 向后兼容 shim
#
# ⚠ DEPRECATED: 此包已迁移至 core_workshop.hardware
#   新代码应使用: from core_workshop.hardware import ...
#   此 shim 仅用于向后兼容,将在未来版本移除。

import warnings

warnings.warn(
    "hardware 模块已迁移至 core_workshop.hardware, "
    "请使用 'from core_workshop.hardware import ...' 替代。"
    "此 shim 将在未来版本移除。",
    DeprecationWarning,
    stacklevel=2,
)

from core_workshop.hardware import (
    DeviceStatus,
    DeviceInfo,
    DeviceMetrics,
    IHardwareDevice,
    DeviceManager,
    RealSenseDeviceV2,
)

__all__ = [
    "DeviceStatus",
    "DeviceInfo",
    "DeviceMetrics",
    "IHardwareDevice",
    "DeviceManager",
    "RealSenseDeviceV2",
]
