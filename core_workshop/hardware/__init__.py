# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# core_workshop.hardware — 硬件抽象层 (V3)

"""硬件抽象层 — 统一设备接口、生命周期管理和安全防护

V3 迁移说明:
    - 原 hardware/hardware_abstraction.py → core_workshop/hardware/hardware_abstraction.py
    - 原 hardware/camera/ → core_workshop/hardware/camera/
    - 原 hardware/calibration/ → core_workshop/hardware/calibration/
"""

from core_workshop.hardware.hardware_abstraction import (
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
