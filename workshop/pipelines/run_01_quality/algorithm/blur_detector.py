# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 模糊检测工具：从图像目录读取图像，使用 Laplacian 方差检测模糊

import cv2
import os

def detect_blurry_frames(image_dir, threshold=100.0):
    """
    检测图像目录中的模糊帧。
    参数:
        image_dir: 包含 frame_xxxxxx.jpg 的目录
        threshold: 方差阈值
    返回:
        blurry_indices: 模糊帧索引列表
        frame_scores: 每帧的方差值列表
    """
    blurry_indices = []
    frame_scores = []
    frame_idx = 0

    while True:
        img_path = os.path.join(image_dir, f"frame_{frame_idx:06d}.jpg")
        if not os.path.exists(img_path):
            break
        img = cv2.imread(img_path)
        if img is None:
            frame_scores.append(0)
            frame_idx += 1
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        frame_scores.append(laplacian_var)
        if laplacian_var < threshold:
            blurry_indices.append(frame_idx)
        frame_idx += 1

    return blurry_indices, frame_scores