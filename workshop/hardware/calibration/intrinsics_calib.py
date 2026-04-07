# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 内参标定工具
# 负责相机内参（焦距、主点、畸变系数）的标定

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class IntrinsicsCalibrator:
    """相机内参标定器"""
    
    def __init__(self, chessboard_size: Tuple[int, int] = (9, 6)):
        """
        初始化内参标定器
        
        Args:
            chessboard_size: 棋盘格尺寸 (内角点数)
        """
        self.chessboard_size = chessboard_size
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.object_points = []  # 3D世界坐标点
        self.image_points = []   # 2D图像坐标点
        self.calibration_data = {}
        
        # 准备棋盘格的世界坐标点
        self._prepare_object_points()
    
    def _prepare_object_points(self):
        """准备棋盘格的世界坐标点"""
        objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)
        self.object_point_template = objp
    
    def add_calibration_image(self, image: np.ndarray) -> bool:
        """
        添加标定图像
        
        Args:
            image: 输入图像
            
        Returns:
            bool: 是否成功检测到棋盘格
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 查找棋盘格角点
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)
            
            if ret:
                # 精确化角点位置
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                
                # 添加点到列表
                self.object_points.append(self.object_point_template)
                self.image_points.append(corners_refined)
                
                logger.info(f"成功添加标定图像，当前共 {len(self.image_points)} 张")
                return True
            else:
                logger.warning("未检测到棋盘格角点")
                return False
                
        except Exception as e:
            logger.error(f"添加标定图像失败: {e}")
            return False
    
    def calibrate(self, image_size: Tuple[int, int]) -> Optional[Dict]:
        """
        执行内参标定
        
        Args:
            image_size: 图像尺寸 (width, height)
            
        Returns:
            Dict: 标定结果或None
        """
        if len(self.object_points) < 5:
            logger.error("标定图像数量不足，至少需要5张")
            return None
            
        try:
            # 执行标定
            ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
                self.object_points, self.image_points, image_size, None, None
            )
            
            if not ret:
                logger.error("标定失败")
                return None
            
            # 计算重投影误差
            mean_error = self._calculate_reprojection_error(
                camera_matrix, dist_coeffs, rvecs, tvecs
            )
            
            # 保存标定数据
            self.calibration_data = {
                'camera_matrix': camera_matrix.tolist(),
                'distortion_coefficients': dist_coeffs.tolist(),
                'rotation_vectors': [r.tolist() for r in rvecs],
                'translation_vectors': [t.tolist() for t in tvecs],
                'image_size': image_size,
                'rms_error': float(mean_error),
                'chessboard_size': self.chessboard_size,
                'sample_count': len(self.object_points)
            }
            
            logger.info(f"内参标定完成，RMS误差: {mean_error:.6f}")
            return self.calibration_data
            
        except Exception as e:
            logger.error(f"标定过程异常: {e}")
            return None
    
    def _calculate_reprojection_error(self, camera_matrix: np.ndarray, 
                                    dist_coeffs: np.ndarray,
                                    rvecs: List[np.ndarray], 
                                    tvecs: List[np.ndarray]) -> float:
        """
        计算重投影误差
        
        Args:
            camera_matrix: 相机矩阵
            dist_coeffs: 畸变系数
            rvecs: 旋转向量列表
            tvecs: 平移向量列表
            
        Returns:
            float: 平均重投影误差
        """
        total_error = 0
        for i in range(len(self.object_points)):
            img_points, _ = cv2.projectPoints(
                self.object_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs
            )
            error = cv2.norm(self.image_points[i], img_points, cv2.NORM_L2) / len(img_points)
            total_error += error
        
        return total_error / len(self.object_points)
    
    def undistort_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        图像去畸变
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 去畸变后的图像或None
        """
        if not self.calibration_data:
            logger.error("无标定数据，请先执行标定")
            return None
            
        try:
            camera_matrix = np.array(self.calibration_data['camera_matrix'])
            dist_coeffs = np.array(self.calibration_data['distortion_coefficients'])
            
            h, w = image.shape[:2]
            new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
                camera_matrix, dist_coeffs, (w, h), 1, (w, h)
            )
            
            # 去畸变
            undistorted = cv2.undistort(image, camera_matrix, dist_coeffs, None, new_camera_matrix)
            
            # 裁剪有效区域
            x, y, w, h = roi
            undistorted = undistorted[y:y+h, x:x+w]
            
            return undistorted
            
        except Exception as e:
            logger.error(f"去畸变处理失败: {e}")
            return None
    
    def save_calibration_data(self, filepath: str) -> bool:
        """
        保存标定数据到文件
        
        Args:
            filepath: 保存路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            logger.info(f"标定数据已保存到 {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存标定数据失败: {e}")
            return False
    
    def load_calibration_data(self, filepath: str) -> bool:
        """
        从文件加载标定数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            with open(filepath, 'r') as f:
                self.calibration_data = json.load(f)
            logger.info(f"标定数据已从 {filepath} 加载")
            return True
        except Exception as e:
            logger.error(f"加载标定数据失败: {e}")
            return False
    
    def get_calibration_summary(self) -> Dict:
        """
        获取标定摘要信息
        
        Returns:
            Dict: 标定摘要
        """
        if not self.calibration_data:
            return {"status": "not_calibrated"}
        
        camera_matrix = np.array(self.calibration_data['camera_matrix'])
        dist_coeffs = np.array(self.calibration_data['distortion_coefficients'])
        
        return {
            "status": "calibrated",
            "focal_length": {
                "fx": float(camera_matrix[0, 0]),
                "fy": float(camera_matrix[1, 1])
            },
            "principal_point": {
                "cx": float(camera_matrix[0, 2]),
                "cy": float(camera_matrix[1, 2])
            },
            "distortion": {
                "k1": float(dist_coeffs[0, 0]),
                "k2": float(dist_coeffs[0, 1]),
                "p1": float(dist_coeffs[0, 2]),
                "p2": float(dist_coeffs[0, 3]),
                "k3": float(dist_coeffs[0, 4]) if len(dist_coeffs[0]) > 4 else 0.0
            },
            "rms_error": self.calibration_data['rms_error'],
            "sample_count": self.calibration_data['sample_count']
        }


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建标定器
    calibrator = IntrinsicsCalibrator(chessboard_size=(9, 6))
    
    # 模拟添加标定图像（实际使用时应该是真实的棋盘格图像）
    for i in range(10):
        # 创建模拟棋盘格图像
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        calibrator.add_calibration_image(img)
    
    # 执行标定
    result = calibrator.calibrate((640, 480))
    if result:
        print("标定成功!")
        summary = calibrator.get_calibration_summary()
        print("标定摘要:", summary)
        
        # 保存标定数据
        calibrator.save_calibration_data("calibration_data.json")