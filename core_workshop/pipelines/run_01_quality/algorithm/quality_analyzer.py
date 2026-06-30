# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 算法：基于图像序列进行模糊检测、曝光检测等。

import json
import os
import cv2
import numpy as np
import pandas as pd
import logging
from .blur_detector import detect_blurry_frames

logger = logging.getLogger(__name__)

def detect_exposure_on_images(rgb_dir, over_threshold=240, under_threshold=30):
    """遍历 RGB 图像目录，检测过曝和欠曝帧"""
    over = []
    under = []
    frame_idx = 0
    while True:
        img_path = os.path.join(rgb_dir, f"frame_{frame_idx:06d}.jpg")
        if not os.path.exists(img_path):
            break
        img = cv2.imread(img_path)
        if img is None:
            logger.warning(f"无法读取图像: {img_path}")
            frame_idx += 1
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean = np.mean(gray)
        if mean > over_threshold:
            over.append(frame_idx)
        elif mean < under_threshold:
            under.append(frame_idx)
        frame_idx += 1
    return over, under

def generate_quality_report(scene_dir, output_dir, config=None, **kwargs):
    rgb_dir = os.path.join(scene_dir, "rgb")
    timestamp_path = os.path.join(scene_dir, "timestamps.csv")
    if not os.path.exists(rgb_dir):
        raise FileNotFoundError(f"RGB 图像目录不存在: {rgb_dir}")
    if not os.path.exists(timestamp_path):
        raise FileNotFoundError(f"时间戳不存在: {timestamp_path}")

    if config is None:
        config = {}
    hardware = config.get('hardware', {})
    blur_threshold = kwargs.get('blur_threshold', hardware.get('blur_threshold', 100))
    over_threshold = kwargs.get('over_threshold', hardware.get('over_threshold', 240))
    under_threshold = kwargs.get('under_threshold', hardware.get('under_threshold', 30))
    expected_fps = kwargs.get('expected_fps', hardware.get('expected_fps', 30))

    blurry_frames, blur_scores = detect_blurry_frames(rgb_dir, threshold=blur_threshold)
    overexposed, underexposed = detect_exposure_on_images(rgb_dir, over_threshold, under_threshold)
    # 丢帧统计（基于时间戳）
    df = pd.read_csv(timestamp_path)
    timestamps = df['timestamp'].values
    total_frames = len(timestamps)
    if total_frames < 2:
        dropped_frames = 0
        max_interval_ms = 0.0
    else:
        intervals = np.diff(timestamps)
        expected_interval = 1000.0 / expected_fps
        dropped_frames = np.sum(intervals > expected_interval * 1.5)
        max_interval_ms = np.max(intervals) if len(intervals) > 0 else 0.0

    report = {
        "scene_id": os.path.basename(scene_dir),
        "overall_pass": True,
        "timestamp": pd.Timestamp.now().isoformat(),
        "camera_reports": [{
            "camera_id": "cam0",
            "total_frames": total_frames,
            "dropped_frames": int(dropped_frames),
            "blurry_frames": blurry_frames,
            "overexposed_frames": overexposed,
            "underexposed_frames": underexposed,
            "avg_sync_offset_ms": 0.0,
            "max_interval_ms": float(max_interval_ms),
            "blur_scores": blur_scores
        }],
        "notes": ""
    }

    if len(blurry_frames) > total_frames * 0.05:
        report["overall_pass"] = False
        report["notes"] += "模糊帧比例过高; "
    if dropped_frames > 1:
        report["overall_pass"] = False
        report["notes"] += f"丢帧{dropped_frames}帧; "

    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "quality_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"质检报告已生成: {report_path}")
    return report