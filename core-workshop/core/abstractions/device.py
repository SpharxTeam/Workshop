"""
Device Abstractions - V3.0
=========================

硬件设备抽象接口

参考:
    - AgentOS Hardware 模块
    - Deepness Hardware Service
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import threading
import logging


class DeviceStatus(Enum):
    """设备状态"""
    UNKNOWN = "unknown"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class DeviceType(Enum):
    """设备类型"""
    CAMERA = "camera"
    LIDAR = "lidar"
    IMU = "imu"
    GPS = "gps"
    ROBOT = "robot"
    SENSOR = "sensor"
    OTHER = "other"


@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str
    device_type: DeviceType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    driver_version: Optional[str] = None
    connection_type: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type.value,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'firmware_version': self.firmware_version,
            'driver_version': self.driver_version,
            'connection_type': self.connection_type,
            'capabilities': self.capabilities,
            'metadata': self.metadata,
        }


class IHardwareDevice(ABC):
    """
    硬件设备抽象接口 - V3.0
    
    所有硬件设备必须实现此接口
    """

    def __init__(self, device_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化设备
        
        Args:
            device_id: 设备唯一标识符
            config: 设备配置
        """
        self._device_id = device_id
        self._config = config or {}
        self._status = DeviceStatus.DISCONNECTED
        self._last_error: Optional[str] = None
        self._lock = threading.RLock()
        self._logger = logging.getLogger(f"{self.__class__.__name__}.{device_id}")

    @property
    def device_id(self) -> str:
        """设备ID"""
        return self._device_id

    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        """设备类型"""
        pass

    @property
    def status(self) -> DeviceStatus:
        """当前状态"""
        return self._status

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._status in [DeviceStatus.READY, DeviceStatus.BUSY]

    @property
    def last_error(self) -> Optional[str]:
        """最后错误"""
        return self._last_error

    @abstractmethod
    def connect(self) -> bool:
        """
        连接设备
        
        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开设备连接
        
        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    def health_check(self) -> DeviceStatus:
        """
        健康检查
        
        Returns:
            DeviceStatus: 设备状态
        """
        pass

    @abstractmethod
    def get_info(self) -> DeviceInfo:
        """
        获取设备信息
        
        Returns:
            DeviceInfo: 设备信息
        """
        pass

    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> bool:
        """
        配置设备
        
        Args:
            settings: 配置参数
            
        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    def reset(self) -> bool:
        """
        复位设备
        
        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    def calibrate(self, calibration_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        校准设备
        
        Args:
            calibration_data: 校准数据
            
        Returns:
            bool: 是否成功
        """
        pass

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.device_id} status={self._status.value}>"


class DeviceManager:
    """
    设备管理器 - V3.0
    
    管理所有硬件设备
    """

    def __init__(self):
        self._devices: Dict[str, IHardwareDevice] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("DeviceManager")

    def register(self, device_id: str, device: IHardwareDevice) -> bool:
        """
        注册设备
        
        Args:
            device_id: 设备ID
            device: 设备实例
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            if device_id in self._devices:
                self._logger.warning(f"设备 {device_id} 已存在")
                return False
            self._devices[device_id] = device
            return True

    def unregister(self, device_id: str) -> bool:
        """
        注销设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            if device_id not in self._devices:
                return False
            del self._devices[device_id]
            return True

    def get_device(self, device_id: str) -> Optional[IHardwareDevice]:
        """
        获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            IHardwareDevice: 设备实例
        """
        return self._devices.get(device_id)

    def list_devices(self) -> List[str]:
        """列出所有设备ID"""
        return list(self._devices.keys())

    def connect_all(self) -> Dict[str, bool]:
        """连接所有设备"""
        results = {}
        for device_id, device in self._devices.items():
            results[device_id] = device.connect()
        return results

    def disconnect_all(self) -> Dict[str, bool]:
        """断开所有设备"""
        results = {}
        for device_id, device in self._devices.items():
            results[device_id] = device.disconnect()
        return results

    def health_check_all(self) -> Dict[str, DeviceStatus]:
        """检查所有设备健康状态"""
        results = {}
        for device_id, device in self._devices.items():
            results[device_id] = device.health_check()
        return results

    def __len__(self) -> int:
        return len(self._devices)

    def __contains__(self, device_id: str) -> bool:
        return device_id in self._devices
