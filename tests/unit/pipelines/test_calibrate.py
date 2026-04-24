# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 测试标定模块

import pytest
import json
import cv2
import numpy as np
from pathlib import Path

def generate_chessboard_images(tmp_path, count=10, pattern=(9,6), square_size=100):
    """生成模拟棋盘格图像用于测试"""
    import random
    img_dir = tmp_path / "calibration"
    img_dir.mkdir()
    board_width = (pattern[0] + 1) * square_size
    board_height = (pattern[1] + 1) * square_size
    
    for i in range(count):
        img = np.ones((board_height, board_width), dtype=np.uint8) * 255
        for row in range(pattern[1] + 1):
            for col in range(pattern[0] + 1):
                x0 = col * square_size
                y0 = row * square_size
                x1 = x0 + square_size
                y1 = y0 + square_size
                color = 0 if (row + col) % 2 == 0 else 255
                img[y0:y1, x0:x1] = color
        # 添加轻微噪声
        noise = np.random.randint(0, 10, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        cv2.imwrite(str(img_dir / f"chessboard_{i:02d}.jpg"), img)
    return img_dir

def test_calibrate_camera_success(temp_output_dir):
    """测试标定成功"""
    from core_workshop.pipelines.calibrate.algorithm.camera_calibrator import calibrate_camera
    
    # 生成测试图像
    img_dir = generate_chessboard_images(temp_output_dir, count=15)
    
    output_dir = temp_output_dir / "calib_out"
    result = calibrate_camera(str(img_dir), chessboard_size=(9,6), square_size=0.025, output_dir=str(output_dir))
    
    assert result is True
    # 检查输出文件
    intrinsics_path = output_dir / "intrinsics.json"
    report_path = output_dir / "calibration_report.json"
    assert intrinsics_path.exists()
    assert report_path.exists()
    
    with open(intrinsics_path) as f:
        intrinsics = json.load(f)
    assert "camera_matrix" in intrinsics
    assert "dist_coeffs" in intrinsics
    assert "reprojection_error" in intrinsics

def test_calibrate_camera_no_images(temp_output_dir):
    """测试没有图像的情况"""
    from core_workshop.pipelines.calibrate.algorithm.camera_calibrator import calibrate_camera
    
    empty_dir = temp_output_dir / "empty"
    empty_dir.mkdir()
    
    result = calibrate_camera(str(empty_dir), output_dir=str(temp_output_dir / "out"))
    assert result is False