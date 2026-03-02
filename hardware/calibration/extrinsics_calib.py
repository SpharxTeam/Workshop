# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 外参标定工具
# 负责相机间相对位置和姿态的标定（立体视觉）

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ExtrinsicsCalibrator:
    """相机外参标定器"""
    
    def __init__(self, chessboard_size: Tuple[int, int] = (9, 6)):
        """
        初始化外参标定器
        
        Args:
            chessboard_size: 棋盘格尺寸 (内角点数)
        """
        self.chessboard_size = chessboard_size
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.stereo_pairs = {}  # 存储立体相机对标定数据
        self.criteria_stereo = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
        
        # 准备棋盘格的世界坐标点
        self._prepare_object_points()
    
    def _prepare_object_points(self):
        """准备棋盘格的世界坐标点"""
        self.objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)
    
    def add_stereo_pair_images(self, left_images: List[np.ndarray], 
                             right_images: List[np.ndarray],
                             pair_id: str = "default") -> bool:
        """
        添加立体相机对标定图像
        
        Args:
            left_images: 左相机图像列表
            right_images: 右相机图像列表
            pair_id: 相机对ID
            
        Returns:
            bool: 添加是否成功
        """
        if len(left_images) != len(right_images):
            logger.error("左右相机图像数量不匹配")
            return False
            
        try:
            left_points = []
            right_points = []
            obj_points = []
            
            # 处理每对图像
            for left_img, right_img in zip(left_images, right_images):
                left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
                right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
                
                # 查找角点
                ret_left, corners_left = cv2.findChessboardCorners(left_gray, self.chessboard_size, None)
                ret_right, corners_right = cv2.findChessboardCorners(right_gray, self.chessboard_size, None)
                
                if ret_left and ret_right:
                    # 精确化角点
                    corners_left = cv2.cornerSubPix(left_gray, corners_left, (11, 11), (-1, -1), self.criteria)
                    corners_right = cv2.cornerSubPix(right_gray, corners_right, (11, 11), (-1, -1), self.criteria)
                    
                    left_points.append(corners_left)
                    right_points.append(corners_right)
                    obj_points.append(self.objp)
            
            if len(obj_points) < 5:
                logger.error("有效标定图像不足，至少需要5对")
                return False
            
            # 保存标定数据
            self.stereo_pairs[pair_id] = {
                'object_points': obj_points,
                'left_points': left_points,
                'right_points': right_points,
                'image_size': left_images[0].shape[:2][::-1]  # (width, height)
            }
            
            logger.info(f"添加立体相机对 {pair_id}，共 {len(obj_points)} 对有效图像")
            return True
            
        except Exception as e:
            logger.error(f"添加立体图像对失败: {e}")
            return False
    
    def calibrate_stereo_pair(self, pair_id: str = "default") -> Optional[Dict]:
        """
        标定立体相机对外参
        
        Args:
            pair_id: 相机对ID
            
        Returns:
            Dict: 标定结果或None
        """
        if pair_id not in self.stereo_pairs:
            logger.error(f"未找到相机对 {pair_id}")
            return None
            
        try:
            pair_data = self.stereo_pairs[pair_id]
            obj_points = pair_data['object_points']
            left_points = pair_data['left_points']
            right_points = pair_data['right_points']
            image_size = pair_data['image_size']
            
            # 单目标定
            _, left_camera_matrix, left_dist, _, _ = cv2.calibrateCamera(
                obj_points, left_points, image_size, None, None
            )
            
            _, right_camera_matrix, right_dist, _, _ = cv2.calibrateCamera(
                obj_points, right_points, image_size, None, None
            )
            
            # 立体标定
            retval, cameraMatrix1, distCoeffs1, cameraMatrix2, distCoeffs2, \
            R, T, E, F = cv2.stereoCalibrate(
                obj_points, left_points, right_points,
                left_camera_matrix, left_dist,
                right_camera_matrix, right_dist,
                image_size,
                criteria=self.criteria_stereo,
                flags=cv2.CALIB_FIX_INTRINSIC
            )
            
            if not retval:
                logger.error("立体标定失败")
                return None
            
            # 计算重投影误差
            rms_error = self._calculate_stereo_reprojection_error(
                obj_points, left_points, right_points,
                cameraMatrix1, distCoeffs1, cameraMatrix2, distCoeffs2, R, T
            )
            
            # 保存标定结果
            calibration_result = {
                'left_camera_matrix': cameraMatrix1.tolist(),
                'left_distortion': distCoeffs1.tolist(),
                'right_camera_matrix': cameraMatrix2.tolist(),
                'right_distortion': distCoeffs2.tolist(),
                'rotation_matrix': R.tolist(),
                'translation_vector': T.tolist(),
                'essential_matrix': E.tolist(),
                'fundamental_matrix': F.tolist(),
                'rms_error': float(rms_error),
                'image_size': image_size,
                'sample_count': len(obj_points)
            }
            
            # 更新存储
            self.stereo_pairs[pair_id]['calibration_result'] = calibration_result
            
            logger.info(f"立体相机对 {pair_id} 标定完成，RMS误差: {rms_error:.6f}")
            return calibration_result
            
        except Exception as e:
            logger.error(f"立体标定异常: {e}")
            return None
    
    def _calculate_stereo_reprojection_error(self, obj_points: List[np.ndarray],
                                           left_points: List[np.ndarray],
                                           right_points: List[np.ndarray],
                                           cameraMatrix1: np.ndarray,
                                           distCoeffs1: np.ndarray,
                                           cameraMatrix2: np.ndarray,
                                           distCoeffs2: np.ndarray,
                                           R: np.ndarray,
                                           T: np.ndarray) -> float:
        """
        计算立体标定的重投影误差
        
        Returns:
            float: 平均重投影误差
        """
        total_error = 0
        total_points = 0
        
        for i, obj_pts in enumerate(obj_points):
            # 投影到左相机
            left_proj, _ = cv2.projectPoints(obj_pts, np.eye(3), np.zeros(3), 
                                           cameraMatrix1, distCoeffs1)
            # 投影到右相机
            right_proj, _ = cv2.projectPoints(obj_pts, R, T, cameraMatrix2, distCoeffs2)
            
            # 计算误差
            left_error = cv2.norm(left_points[i], left_proj, cv2.NORM_L2)
            right_error = cv2.norm(right_points[i], right_proj, cv2.NORM_L2)
            
            total_error += (left_error + right_error)
            total_points += 2 * len(obj_pts)
        
        return total_error / total_points
    
    def rectify_stereo_pair(self, pair_id: str = "default") -> Optional[Dict]:
        """
        立体矫正
        
        Args:
            pair_id: 相机对ID
            
        Returns:
            Dict: 矫正参数或None
        """
        if pair_id not in self.stereo_pairs or 'calibration_result' not in self.stereo_pairs[pair_id]:
            logger.error(f"相机对 {pair_id} 未标定")
            return None
            
        try:
            calib_result = self.stereo_pairs[pair_id]['calibration_result']
            image_size = tuple(calib_result['image_size'])
            
            cameraMatrix1 = np.array(calib_result['left_camera_matrix'])
            distCoeffs1 = np.array(calib_result['left_distortion'])
            cameraMatrix2 = np.array(calib_result['right_camera_matrix'])
            distCoeffs2 = np.array(calib_result['right_distortion'])
            R = np.array(calib_result['rotation_matrix'])
            T = np.array(calib_result['translation_vector'])
            
            # 计算矫正变换
            R1, R2, P1, P2, Q, validPixROI1, validPixROI2 = cv2.stereoRectify(
                cameraMatrix1, distCoeffs1,
                cameraMatrix2, distCoeffs2,
                image_size, R, T
            )
            
            # 计算矫正映射
            map1x, map1y = cv2.initUndistortRectifyMap(
                cameraMatrix1, distCoeffs1, R1, P1, image_size, cv2.CV_32FC1
            )
            map2x, map2y = cv2.initUndistortRectifyMap(
                cameraMatrix2, distCoeffs2, R2, P2, image_size, cv2.CV_32FC1
            )
            
            rectification_result = {
                'rectification_matrices': {
                    'R1': R1.tolist(),
                    'R2': R2.tolist(),
                    'P1': P1.tolist(),
                    'P2': P2.tolist(),
                    'Q': Q.tolist()
                },
                'remapping_maps': {
                    'map1x': map1x.tolist(),
                    'map1y': map1y.tolist(),
                    'map2x': map2x.tolist(),
                    'map2y': map2y.tolist()
                },
                'valid_roi': {
                    'left': validPixROI1,
                    'right': validPixROI2
                }
            }
            
            self.stereo_pairs[pair_id]['rectification_result'] = rectification_result
            logger.info(f"相机对 {pair_id} 矫正完成")
            return rectification_result
            
        except Exception as e:
            logger.error(f"立体矫正失败: {e}")
            return None
    
    def rectify_image_pair(self, left_image: np.ndarray, right_image: np.ndarray,
                          pair_id: str = "default") -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        对图像对进行矫正
        
        Args:
            left_image: 左图像
            right_image: 右图像
            pair_id: 相机对ID
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: 矫正后的左右图像对或None
        """
        if pair_id not in self.stereo_pairs or 'rectification_result' not in self.stereo_pairs[pair_id]:
            logger.error(f"相机对 {pair_id} 未矫正")
            return None
            
        try:
            rect_result = self.stereo_pairs[pair_id]['rectification_result']
            maps = rect_result['remapping_maps']
            
            map1x = np.array(maps['map1x'], dtype=np.float32)
            map1y = np.array(maps['map1y'], dtype=np.float32)
            map2x = np.array(maps['map2x'], dtype=np.float32)
            map2y = np.array(maps['map2y'], dtype=np.float32)
            
            # 应用矫正映射
            left_rectified = cv2.remap(left_image, map1x, map1y, cv2.INTER_LINEAR)
            right_rectified = cv2.remap(right_image, map2x, map2y, cv2.INTER_LINEAR)
            
            return left_rectified, right_rectified
            
        except Exception as e:
            logger.error(f"图像矫正失败: {e}")
            return None
    
    def save_calibration_data(self, filepath: str, pair_id: str = "default") -> bool:
        """
        保存标定数据
        
        Args:
            filepath: 保存路径
            pair_id: 相机对ID
            
        Returns:
            bool: 保存是否成功
        """
        if pair_id not in self.stereo_pairs:
            logger.error(f"未找到相机对 {pair_id}")
            return False
            
        try:
            data_to_save = {
                'pair_id': pair_id,
                'calibration_result': self.stereo_pairs[pair_id].get('calibration_result'),
                'rectification_result': self.stereo_pairs[pair_id].get('rectification_result')
            }
            
            with open(filepath, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            logger.info(f"标定数据已保存到 {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存标定数据失败: {e}")
            return False
    
    def get_extrinsics_summary(self, pair_id: str = "default") -> Dict:
        """
        获取外参标定摘要
        
        Args:
            pair_id: 相机对ID
            
        Returns:
            Dict: 外参摘要信息
        """
        if pair_id not in self.stereo_pairs:
            return {"status": "pair_not_found"}
            
        pair_data = self.stereo_pairs[pair_id]
        
        if 'calibration_result' not in pair_data:
            return {"status": "not_calibrated"}
            
        calib_result = pair_data['calibration_result']
        R = np.array(calib_result['rotation_matrix'])
        T = np.array(calib_result['translation_vector'])
        
        # 计算欧拉角
        euler_angles = self._rotation_matrix_to_euler(R)
        
        # 计算基线距离
        baseline = np.linalg.norm(T)
        
        return {
            "status": "calibrated",
            "rotation_angles_deg": {
                "roll": float(np.degrees(euler_angles[0])),
                "pitch": float(np.degrees(euler_angles[1])),
                "yaw": float(np.degrees(euler_angles[2]))
            },
            "translation_vector": {
                "x": float(T[0]),
                "y": float(T[1]),
                "z": float(T[2])
            },
            "baseline_distance": float(baseline),
            "rms_error": calib_result['rms_error'],
            "sample_count": calib_result['sample_count']
        }
    
    def _rotation_matrix_to_euler(self, R: np.ndarray) -> np.ndarray:
        """
        将旋转矩阵转换为欧拉角
        
        Args:
            R: 3x3旋转矩阵
            
        Returns:
            np.ndarray: 欧拉角 [roll, pitch, yaw]
        """
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0
            
        return np.array([x, y, z])


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建标定器
    calibrator = ExtrinsicsCalibrator(chessboard_size=(9, 6))
    
    # 模拟立体图像对（实际使用时应该是真实的棋盘格图像）
    left_images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
    right_images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
    
    # 添加图像对
    calibrator.add_stereo_pair_images(left_images, right_images, "stereo_pair_1")
    
    # 执行标定
    result = calibrator.calibrate_stereo_pair("stereo_pair_1")
    if result:
        print("立体标定成功!")
        summary = calibrator.get_extrinsics_summary("stereo_pair_1")
        print("外参摘要:", summary)
        
        # 保存标定数据
        calibrator.save_calibration_data("extrinsics_calibration.json", "stereo_pair_1")