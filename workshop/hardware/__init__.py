# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Workshop 硬件抽象层
==================

提供统一的硬件设备接口，支持：
- RealSense 相机管理
- 相机同步控制
- 内参/外参校准
- 设备健康检查

使用示例:
    from workshop.hardware import DeviceManager, RealSenseDeviceV2
    
    # 初始化设备管理器
    device_mgr = DeviceManager()
    
    # 注册并初始化 RealSense 相机
    camera = RealSenseDeviceV2(device_id='camera_001')
    device_mgr.register('camera_001', camera)
    device_mgr.initialize_all()
    
    # 健康检查
    status = device_mgr.health_check_all()
"""

from .hardware_abstraction import (
    IHardwareDevice,
    DeviceManager,
    DeviceInfo,
    DeviceStatus,
    RealSenseDeviceV2
)

__all__ = [
    'IHardwareDevice',
    'DeviceManager',
    'DeviceInfo',
    'DeviceStatus',
    'RealSenseDeviceV2',
]
