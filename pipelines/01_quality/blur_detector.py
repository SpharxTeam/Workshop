# pipelines/01_quality/blur_detector.py

import cv2
import numpy as np

def detect_blurry_frames(video_path, threshold=100.0):
    """
    使用Laplacian方差检测视频中的模糊帧。
    参数:
        video_path: 输入视频文件路径
        threshold: 方差阈值，低于此值判定为模糊（默认100，可根据实际情况调整）
    返回:
        blurry_indices: 模糊帧的索引列表（0-based）
        frame_scores: 每帧的方差值列表（可用于调试）
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