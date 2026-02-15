"""
RealSense 相机管理器
负责相机设备的初始化、配置和数据流管理
"""

import pyrealsense2 as rs
import numpy as np
import cv2
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RealSenseManager:
    """RealSense 相机管理类"""
    
    def __init__(self, serial_number: Optional[str] = None):
        """
        初始化相机管理器
        
        Args:
            serial_number: 相机序列号，None表示使用第一个可用相机
        """
        self.serial_number = serial_number
        self.pipeline = None
        self.config = None
        self.profile = None
        self.is_running = False
        
    def initialize(self) -> bool:
        """
        初始化相机设备
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建 pipeline
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # 如果指定了序列号，配置特定设备
            if self.serial_number:
                self.config.enable_device(self.serial_number)
            
            # 配置流
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            
            # 启动 pipeline
            self.profile = self.pipeline.start(self.config)
            self.is_running = True
            
            logger.info(f"RealSense 相机初始化成功: {self.serial_number or '默认设备'}")
            return True
            
        except Exception as e:
            logger.error(f"相机初始化失败: {e}")
            return False
    
    def get_frames(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        获取一帧数据
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (深度图像, 彩色图像) 或 None
        """
        if not self.is_running:
            logger.warning("相机未启动")
            return None
            
        try:
            # 等待下一帧
            frames = self.pipeline.wait_for_frames()
            
            # 获取深度和彩色帧
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                return None
                
            # 转换为 numpy 数组
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            return depth_image, color_image
            
        except Exception as e:
            logger.error(f"获取帧数据失败: {e}")
            return None
    
    def get_camera_info(self) -> Dict:
        """
        获取相机信息
        
        Returns:
            Dict: 相机信息字典
        """
        if not self.profile:
            return {}
            
        try:
            device = self.profile.get_device()
            return {
                'serial_number': device.get_info(rs.camera_info.serial_number),
                'firmware_version': device.get_info(rs.camera_info.firmware_version),
                'name': device.get_info(rs.camera_info.name),
                'usb_type': device.get_info(rs.camera_info.usb_type_descriptor)
            }
        except Exception as e:
            logger.error(f"获取相机信息失败: {e}")
            return {}
    
    def stop(self):
        """停止相机"""
        if self.pipeline and self.is_running:
            self.pipeline.stop()
            self.is_running = False
            logger.info("RealSense 相机已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 使用上下文管理器
    with RealSenseManager() as camera:
        print("相机信息:", camera.get_camera_info())
        
        # 获取几帧数据
        for i in range(10):
            frames = camera.get_frames()
            if frames:
                depth_img, color_img = frames
                print(f"帧 {i}: 深度图像形状 {depth_img.shape}, 彩色图像形状 {color_img.shape}")