# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 硬件抽象层 (Hardware Abstraction Layer)
# 统一设备接口、生命周期管理和安全防护

import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Type
from enum import Enum, auto
from dataclasses import dataclass

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    BasePipeline,
    ConfigManager,
    setup_logging,
    InputValidator,
    ErrorCode,
    HardwareError,
    WorkshopError,
    error_code_manager
)


class DeviceStatus(Enum):
    """设备状态枚举"""
    UNKNOWN = auto()
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    ERROR = auto()
    SHUTDOWN = auto()


@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str
    device_type: str
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    firmware_version: str = ""
    connection_type: str = ""  # USB, Ethernet, etc.
    capabilities: List[str] = None  # ['depth', 'color', 'imu', ...]
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'firmware_version': self.firmware_version,
            'connection_type': self.connection_type,
            'capabilities': self.capabilities
        }


@dataclass
class DeviceMetrics:
    """设备性能指标"""
    frames_captured: int = 0
    frames_dropped: int = 0
    avg_capture_time_ms: float = 0.0
    uptime_seconds: float = 0.0
    temperature_celsius: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    
    @property
    def drop_rate(self) -> float:
        total = self.frames_captured + self.frames_dropped
        return (self.frames_dropped / max(total, 1)) * 100


class IHardwareDevice(ABC):
    """
    硬件设备接口 - 参考 AgentOS 设备抽象设计
    
    所有硬件设备必须实现此接口，提供统一的生命周期管理。
    
    设计原则：
    - K-3 服务隔离：每个设备独立运行
    - E-3 资源确定性：明确的初始化/使用/清理流程
    - 安全性：输入验证、错误恢复、超时控制
    """
    
    @abstractmethod
    def initialize(self, config: Optional[Dict] = None) -> bool:
        """
        初始化设备
        
        Args:
            config: 设备配置参数
            
        Returns:
            bool: 是否初始化成功
        """
        pass
    
    @abstractmethod
    def get_device_info(self) -> DeviceInfo:
        """获取设备信息"""
        pass
    
    @abstractmethod
    def get_status(self) -> DeviceStatus:
        """获取当前状态"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态字典，包含：
            - status: 'healthy'/'degraded'/'unhealthy'
            - metrics: 性能指标
            - issues: 问题列表
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """优雅关闭设备"""
        pass
    
    # 可选方法（子类可按需实现）
    
    def reset(self) -> bool:
        """重置设备到初始状态"""
        raise NotImplementedError(f"{self.__class__.__name__} 不支持 reset 操作")
    
    def update_firmware(self, firmware_path: str) -> bool:
        """
        更新固件
        
        Args:
            firmware_path: 固件文件路径
            
        Returns:
            bool: 是否更新成功
        """
        raise NotImplementedError(f"{self.__class__.__name__} 不支持固件更新")
    
    def __enter__(self):
        """上下文管理器入口"""
        success = self.initialize()
        if not success:
            raise HardwareError(
                ErrorCode.HARDWARE_INIT_FAILED,
                f"设备初始化失败: {self.__class__.__name__}"
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()


class DeviceManager:
    """
    设备管理器 - 参考 AgentOS AgentRegistry 设计
    
    功能：
    - 设备注册与发现
    - 生命周期管理
    - 资源分配与释放
    - 健康监控
    - 错误恢复
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._devices: Dict[str, IHardwareDevice] = {}
        self._device_status: Dict[str, DeviceStatus] = {}
        self._logger = setup_logging("hardware.manager")
        self._initialized = True
        
        self._health_check_interval = 60  # 秒
        self._auto_recovery_enabled = True
    
    def register(self, device_id: str, device: IHardwareDevice) -> bool:
        """
        注册设备
        
        Args:
            device_id: 设备唯一标识
            device: 设备实例
            
        Returns:
            bool: 注册是否成功
        """
        if device_id in self._devices:
            self._logger.warning(f"设备已存在: {device_id}，将被替换")
        
        self._devices[device_id] = device
        self._device_status[device_id] = DeviceStatus.DISCONNECTED
        
        self._logger.info(f"设备注册成功: {device_id} ({device.__class__.__name__})")
        return True
    
    def unregister(self, device_id: str) -> bool:
        """
        注销设备
        
        Args:
            device_id: 设备标识
            
        Returns:
            bool: 注销是否成功
        """
        if device_id not in self._devices:
            self._logger.warning(f"设备未注册: {device_id}")
            return False
        
        device = self._devices.pop(device_id)
        self._device_status.pop(device_id, None)
        
        try:
            device.shutdown()
        except Exception as e:
            self._logger.warning(f"关闭设备时出错: {device_id} - {e}")
        
        self._logger.info(f"设备注销成功: {device_id}")
        return True
    
    def initialize_all(self, configs: Optional[Dict[str, Dict]] = None) -> Dict[str, bool]:
        """
        批量初始化所有注册的设备
        
        Args:
            configs: 各设备的配置字典 {device_id: config}
            
        Returns:
            初始化结果 {device_id: success}
        """
        results = {}
        configs = configs or {}
        
        for device_id, device in self._devices.items():
            try:
                self._device_status[device_id] = DeviceStatus.INITIALIZING
                
                config = configs.get(device_id)
                success = device.initialize(config)
                
                if success:
                    self._device_status[device_id] = DeviceStatus.READY
                    self._logger.info(f"✓ 设备初始化成功: {device_id}")
                else:
                    self._device_status[device_id] = DeviceStatus.ERROR
                    self._logger.error(f"✗ 设备初始化失败: {device_id}")
                
                results[device_id] = success
                
            except Exception as e:
                self._device_status[device_id] = DeviceStatus.ERROR
                results[device_id] = False
                self._logger.error(f"设备初始化异常: {device_id} - {e}")
                
                error_code_manager.record_error(
                    HardwareError(ErrorCode.HARDWARE_INIT_FAILED, str(e), cause=e)
                )
        
        return results
    
    def get_device(self, device_id: str) -> Optional[IHardwareDevice]:
        """获取设备实例"""
        return self._devices.get(device_id)
    
    def get_status(self, device_id: Optional[str] = None) -> Dict[str, DeviceStatus]:
        """获取设备状态"""
        if device_id:
            status = self._device_status.get(device_id)
            return {device_id: status} if status else {}
        
        return dict(self._device_status)
    
    def list_devices(self) -> List[DeviceInfo]:
        """列出所有已注册设备的信息"""
        devices_info = []
        
        for device_id, device in self._devices.items():
            try:
                info = device.get_device_info()
                devices_info.append(info)
            except Exception as e:
                self._logger.warning(f"获取设备信息失败: {device_id} - {e}")
                devices_info.append(DeviceInfo(
                    device_id=device_id,
                    device_type=device.__class__.__name__,
                    model="unknown",
                    error=str(e)
                ))
        
        return devices_info
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """对所有设备执行健康检查"""
        results = {}
        
        for device_id, device in self._devices.items():
            try:
                health = device.health_check()
                results[device_id] = health
                
                if health.get('status') == 'unhealthy':
                    self._logger.warning(f"设备健康检查异常: {device_id}")
                    
                    if self._auto_recovery_enabled:
                        self._attempt_recovery(device_id, device)
                        
            except Exception as e:
                results[device_id] = {
                    'status': 'error',
                    'error': str(e),
                    'issues': [f"健康检查异常: {e}"]
                }
        
        return results
    
    def shutdown_all(self) -> None:
        """关闭所有设备"""
        self._logger.info("开始关闭所有设备...")
        
        for device_id, device in list(self._devices.items()):
            try:
                self._device_status[device_id] = DeviceStatus.SHUTDOWN
                device.shutdown()
                self._logger.info(f"设备已关闭: {device_id}")
            except Exception as e:
                self._logger.error(f"关闭设备时出错: {device_id} - {e}")
        
        self._devices.clear()
        self._device_status.clear()
        self._logger.info("所有设备已关闭")
    
    def _attempt_recovery(self, device_id: str, device: IHardwareDevice) -> bool:
        """尝试自动恢复故障设备"""
        self._logger.info(f"尝试自动恢复设备: {device_id}")
        
        try:
            # 重置设备状态
            self._device_status[device_id] = DeviceStatus.CONNECTING
            
            # 尝试重新初始化
            success = device.initialize()
            
            if success:
                self._device_status[device_id] = DeviceStatus.READY
                self._logger.info(f"✓ 设备恢复成功: {device_id}")
                return True
            else:
                self._device_status[device_id] = DeviceStatus.ERROR
                self._logger.error(f"✗ 设备恢复失败: {device_id}")
                return False
                
        except Exception as e:
            self._device_status[device_id] = DeviceStatus.ERROR
            self._logger.error(f"设备恢复异常: {device_id} - {e}")
            return False


class RealSenseDeviceV2(IHardwareDevice):
    """
    RealSense 相机设备 V2 - 基于 IHardwareDevice 接口的完整实现
    
    改进：
    - 完整的生命周期管理
    - 健康检查
    - 性能统计
    - 错误恢复
    - 配置验证
    """
    
    DEVICE_TYPE = "realsense_camera"
    
    def __init__(self, serial_number: Optional[str] = None):
        self._serial_number = serial_number
        self._pipeline = None
        self._config = None
        self._profile = None
        self._status = DeviceStatus.UNKNOWN
        self._metrics = DeviceMetrics()
        self._start_time: Optional[float] = None
        self._logger = setup_logging("hardware.realsense")
        
        # 配置默认值
        self._default_config = {
            'depth_width': 640,
            'depth_height': 480,
            'color_width': 640,
            'color_height': 480,
            'depth_fps': 30,
            'color_fps': 30,
            'enable_depth': True,
            'enable_color': True
        }
    
    def initialize(self, config: Optional[Dict] = None) -> bool:
        """初始化 RealSense 相机"""
        try:
            import pyrealsense2 as rs
            
            self._status = DeviceStatus.CONNECTING
            self._logger.info(f"正在初始化 RealSense 相机: {self._serial_number or '默认'}")
            
            # 合并配置
            merged_config = {**self._default_config}
            if config:
                merged_config.update(config)
            
            # 创建 pipeline
            self._pipeline = rs.pipeline()
            self._config = rs.config()
            
            # 配置指定设备
            if self._serial_number:
                self._config.enable_device(self._serial_number)
            
            # 配置流
            if merged_config.get('enable_depth'):
                self._config.enable_stream(
                    rs.stream.depth,
                    width=merged_config['depth_width'],
                    height=merged_config['depth_height'],
                    format=rs.format.z16,
                    framerate=merged_config['depth_fps']
                )
            
            if merged_config.get('enable_color'):
                self._config.enable_stream(
                    rs.stream.color,
                    width=merged_config['color_width'],
                    height=merged_config['color_height'],
                    format=rs.format.bgr8,
                    framerate=merged_config['color_fps']
                )
            
            # 启动 pipeline
            self._profile = self._pipeline.start(self._config)
            self._status = DeviceStatus.READY
            self._start_time = time.time()
            
            info = self.get_device_info()
            self._logger.info(
                f"✓ RealSense 相机初始化成功\n"
                f"  序列号: {info.serial_number}\n"
                f"  型号: {info.model}\n"
                f"  固件版本: {info.firmware_version}"
            )
            
            return True
            
        except Exception as e:
            self._status = DeviceStatus.ERROR
            self._logger.error(f"RealSense 初始化失败: {e}", exc_info=True)
            
            error_code_manager.record_error(
                HardwareError(ErrorCode.HARDWARE_INIT_FAILED, str(e), cause=e)
            )
            
            return False
    
    def get_device_info(self) -> DeviceInfo:
        """获取相机信息"""
        if not self._profile:
            return DeviceInfo(
                device_id=self._serial_number or "unknown",
                device_type=self.DEVICE_TYPE,
                model="unknown",
                status="not_initialized"
            )
        
        try:
            import pyrealsense2 as rs
            
            device = self._profile.get_device()
            
            return DeviceInfo(
                device_id=device.get_info(rs.camera_info.serial_number),
                device_type=self.DEVICE_TYPE,
                manufacturer="Intel",
                model=device.get_info(rs.camera_info.name),
                serial_number=device.get_info(rs.camera_info.serial_number),
                firmware_version=device.get_info(rs.camera_info.firmware_version),
                connection_type=device.get_info(rs.camera_info.usb_type_descriptor),
                capabilities=['depth', 'color'] if self._is_depth_enabled() else ['color']
            )
        except Exception as e:
            self._logger.warning(f"获取设备信息失败: {e}")
            return DeviceInfo(
                device_id=self._serial_number or "unknown",
                device_type=self.DEVICE_TYPE,
                error=str(e)
            )
    
    def get_status(self) -> DeviceStatus:
        return self._status
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        issues = []
        
        # 检查连接状态
        if self._status not in [DeviceStatus.READY, DeviceStatus.RUNNING]:
            issues.append(f"设备状态异常: {self._status.name}")
        
        # 检查帧捕获能力
        if self._pipeline and self._status == DeviceStatus.READY:
            try:
                frames = self._pipeline.wait_for_frames(timeout_ms=1000)
                
                if not frames or not (frames.get_depth_frame() or frames.get_color_frame()):
                    issues.append("无法捕获帧数据")
                    
            except Exception as e:
                issues.append(f"帧捕获测试失败: {e}")
        
        # 计算丢帧率
        drop_rate = self._metrics.drop_rate
        if drop_rate > 5.0:  # 超过5%丢帧率
            issues.append(f"丢帧率过高: {drop_rate:.1f}%")
        
        # 确定健康状态
        if len(issues) == 0:
            status = 'healthy'
        elif len(issues) <= 2:
            status = 'degraded'
        else:
            status = 'unhealthy'
        
        return {
            'status': status,
            'metrics': {
                'frames_captured': self._metrics.frames_captured,
                'frames_dropped': self._metrics.frames_dropped,
                'drop_rate': f"{drop_rate:.2f}%",
                'uptime_seconds': time.time() - self._start_time if self._start_time else 0
            },
            'issues': issues,
            'device_type': self.DEVICE_TYPE
        }
    
    def capture_frame(self, timeout_ms: int = 5000) -> Optional[tuple]:
        """
        捕获一帧数据
        
        Args:
            timeout_ms: 超时时间（毫秒）
            
        Returns:
            tuple: (depth_image, color_image) 或 None
        """
        if self._status != DeviceStatus.READY:
            self._logger.warning("相机未就绪，无法捕获帧")
            return None
        
        try:
            import numpy as np
            import pyrealsense2 as rs
            
            frames = self._pipeline.wait_for_frames(timeout_ms=timeout_ms)
            
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            
            if not depth_frame and not color_frame:
                self._metrics.frames_dropped += 1
                return None
            
            result = ()
            
            if depth_frame:
                depth_image = np.asanyarray(depth_frame.get_data())
                result += (depth_image,)
            
            if color_frame:
                color_image = np.asanyarray(color_frame.get_data())
                result += (color_image,)
            
            self._metrics.frames_captured += 1
            
            return result if len(result) > 2 else (result[0], None) if result else None
            
        except Exception as e:
            self._logger.error(f"帧捕获失败: {e}")
            self._metrics.frames_dropped += 1
            return None
    
    def shutdown(self) -> None:
        """关闭相机"""
        self._status = DeviceStatus.SHUTDOWN
        
        if self._pipeline:
            try:
                self._pipeline.stop()
                self._logger.info("RealSense 相机已停止")
            except Exception as e:
                self._logger.warning(f"停止相机时出错: {e}")
            
            self._pipeline = None
        
        self._profile = None
    
    def _is_depth_enabled(self) -> bool:
        """检查深度流是否启用"""
        return self._default_config.get('enable_depth', True)


def main():
    """硬件抽象层演示"""
    print("=" * 60)
    print("Workshop 硬件抽象层 V2.0")
    print("=" * 60)
    
    # 创建设备管理器
    manager = DeviceManager()
    
    # 创建并注册 RealSense 设备
    realsense = RealSenseDeviceV2(serial_number=None)  # 使用默认设备
    manager.register("camera_0", realsense)
    
    # 初始化设备
    print("\n▶ 初始化设备...")
    init_results = manager.initialize_all()
    
    for device_id, success in init_results.items():
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {device_id}: {status}")
    
    # 获取设备列表
    print("\n▶ 已注册设备:")
    devices = manager.list_devices()
    for device in devices:
        print(f"  - {device.device_id}: {device.device_type} ({device.model})")
    
    # 健康检查
    print("\n▶ 健康检查:")
    health_results = manager.health_check_all()
    for device_id, health in health_results.items():
        status_icon = "✓" if health['status'] == 'healthy' else "⚠"
        print(f"  {status_icon} {device_id}: {health['status']}")
        if health.get('issues'):
            for issue in health['issues']:
                print(f"      ⚠ {issue}")
    
    # 关闭所有设备
    print("\n▶ 关闭设备...")
    manager.shutdown_all()
    print("  ✓ 所有设备已关闭")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
