"""
相机同步控制器
负责多相机系统的同步控制和时间戳管理
"""

import time
import threading
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SyncMode(Enum):
    """同步模式枚举"""
    MASTER = "master"
    SLAVE = "slave"
    STANDALONE = "standalone"


@dataclass
class CameraConfig:
    """相机配置数据类"""
    camera_id: str
    sync_mode: SyncMode
    exposure_time: int = 33000  # 微秒
    gain: float = 16.0
    fps: int = 30


class SyncController:
    """相机同步控制器"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraConfig] = {}
        self.sync_thread: Optional[threading.Thread] = None
        self.is_syncing = False
        self.sync_interval = 1.0 / 30  # 30Hz 同步频率
        
    def add_camera(self, camera_id: str, config: CameraConfig) -> bool:
        """
        添加相机到同步控制系统
        
        Args:
            camera_id: 相机ID
            config: 相机配置
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.cameras[camera_id] = config
            logger.info(f"添加相机 {camera_id} 到同步系统")
            return True
        except Exception as e:
            logger.error(f"添加相机失败: {e}")
            return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """
        从同步系统移除相机
        
        Args:
            camera_id: 相机ID
            
        Returns:
            bool: 移除是否成功
        """
        if camera_id in self.cameras:
            del self.cameras[camera_id]
            logger.info(f"从同步系统移除相机 {camera_id}")
            return True
        return False
    
    def start_sync(self) -> bool:
        """
        启动同步控制
        
        Returns:
            bool: 启动是否成功
        """
        if self.is_syncing:
            logger.warning("同步系统已在运行")
            return False
            
        try:
            self.is_syncing = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            logger.info("同步控制系统启动")
            return True
        except Exception as e:
            logger.error(f"启动同步系统失败: {e}")
            self.is_syncing = False
            return False
    
    def stop_sync(self):
        """停止同步控制"""
        self.is_syncing = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2.0)
        logger.info("同步控制系统停止")
    
    def _sync_loop(self):
        """同步控制循环"""
        while self.is_syncing:
            try:
                # 发送同步信号
                self._send_sync_signal()
                
                # 等待下一个同步周期
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"同步循环异常: {e}")
                time.sleep(0.1)  # 出错时短暂等待
    
    def _send_sync_signal(self):
        """发送同步信号给所有相机"""
        timestamp = time.time()
        for camera_id, config in self.cameras.items():
            try:
                # 这里应该调用具体的相机SDK发送同步信号
                self._trigger_camera(camera_id, timestamp)
            except Exception as e:
                logger.error(f"向相机 {camera_id} 发送同步信号失败: {e}")
    
    def _trigger_camera(self, camera_id: str, timestamp: float):
        """
        触发单个相机拍照
        
        Args:
            camera_id: 相机ID
            timestamp: 时间戳
        """
        # 实际实现应该调用相机SDK的具体API
        logger.debug(f"触发相机 {camera_id} 拍照，时间戳: {timestamp}")
        pass
    
    def get_sync_status(self) -> Dict:
        """
        获取同步状态
        
        Returns:
            Dict: 同步状态信息
        """
        return {
            'is_syncing': self.is_syncing,
            'camera_count': len(self.cameras),
            'cameras': list(self.cameras.keys()),
            'sync_interval': self.sync_interval
        }
    
    def set_sync_frequency(self, frequency: float) -> bool:
        """
        设置同步频率
        
        Args:
            frequency: 同步频率(Hz)
            
        Returns:
            bool: 设置是否成功
        """
        if frequency <= 0:
            logger.error("同步频率必须大于0")
            return False
            
        self.sync_interval = 1.0 / frequency
        logger.info(f"同步频率设置为 {frequency} Hz")
        return True


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建同步控制器
    controller = SyncController()
    
    # 添加相机
    cam1_config = CameraConfig("cam1", SyncMode.MASTER)
    cam2_config = CameraConfig("cam2", SyncMode.SLAVE)
    
    controller.add_camera("cam1", cam1_config)
    controller.add_camera("cam2", cam2_config)
    
    # 启动同步
    controller.start_sync()
    
    # 运行一段时间
    time.sleep(5)
    
    # 停止同步
    controller.stop_sync()
    
    print("同步状态:", controller.get_sync_status())