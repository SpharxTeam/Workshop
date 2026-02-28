# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

"""
模糊检测工具：使用 Laplacian 方差检测视频中的模糊帧。
"""
import cv2

def detect_blurry_frames(video_path, threshold=100.0):
    """
    检测视频中的模糊帧。
    参数:
        video_path: 输入视频文件路径
        threshold: 方差阈值，低于此值判定为模糊
    返回:
        blurry_indices: 模糊帧索引列表
        frame_scores: 每帧的方差值列表
    """
    cap = cv2.VideoCapture(video_path)
    blurry_indices = []
    frame_scores = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        frame_scores.append(laplacian_var)
        if laplacian_var < threshold:
            blurry_indices.append(frame_idx)
        frame_idx += 1

    cap.release()
    return blurry_indices, frame_scores