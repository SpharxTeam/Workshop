#!/usr/bin/env python3
"""
质检模块：模糊检测、曝光检测、丢帧统计，生成 JSON 报告。
"""
import argparse
import json
import os
import cv2
import numpy as np
import pandas as pd
from blur_detector import detect_blurry_frames
import logging
import sys
from config_loader import load_config

MODULE_NAME = os.path.basename(__file__).replace('.py', '')
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, f"{MODULE_NAME}.log"))
    ]
)
logger = logging.getLogger(MODULE_NAME)

def detect_exposure(video_path, over_threshold=240, under_threshold=30):
    cap = cv2.VideoCapture(video_path)
    over = []
    under = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean = np.mean(gray)
        if mean > over_threshold:
            over.append(idx)
        elif mean < under_threshold:
            under.append(idx)
        idx += 1
    cap.release()
    return over, under

def check_dropped_frames(timestamp_csv, expected_fps=30):
    df = pd.read_csv(timestamp_csv)
    timestamps = df['timestamp'].values
    if len(timestamps) < 2:
        return 0, 0.0
    intervals = np.diff(timestamps)
    expected_interval = 1000.0 / expected_fps
    dropped = np.sum(intervals > expected_interval * 1.5)
    max_interval = np.max(intervals) if len(intervals) > 0 else 0.0
    return int(dropped), float(max_interval)

def generate_quality_report(scene_dir, output_dir, config=None, **kwargs):
    video_path = os.path.join(scene_dir, "rgb.mp4")
    timestamp_path = os.path.join(scene_dir, "timestamps.csv")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频不存在: {video_path}")
    if not os.path.exists(timestamp_path):
        raise FileNotFoundError(f"时间戳不存在: {timestamp_path}")

    if config is None:
        config = {}
    hardware = config.get('hardware', {})
    blur_threshold = kwargs.get('blur_threshold', hardware.get('blur_threshold', 100))
    over_threshold = kwargs.get('over_threshold', hardware.get('over_threshold', 240))
    under_threshold = kwargs.get('under_threshold', hardware.get('under_threshold', 30))
    expected_fps = kwargs.get('expected_fps', hardware.get('expected_fps', 30))

    blurry_frames, blur_scores = detect_blurry_frames(video_path, threshold=blur_threshold)
    overexposed, underexposed = detect_exposure(video_path, over_threshold, under_threshold)
    dropped_frames, max_interval_ms = check_dropped_frames(timestamp_path, expected_fps)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    report = {
        "scene_id": os.path.basename(scene_dir),
        "overall_pass": True,
        "timestamp": pd.Timestamp.now().isoformat(),
        "camera_reports": [{
            "camera_id": "cam0",
            "total_frames": total_frames,
            "dropped_frames": dropped_frames,
            "blurry_frames": blurry_frames,
            "overexposed_frames": overexposed,
            "underexposed_frames": underexposed,
            "avg_sync_offset_ms": 0.0,
            "max_interval_ms": max_interval_ms,
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="场景目录")
    parser.add_argument("--output", required=True, help="报告输出目录")
    parser.add_argument("--blur_threshold", type=int)
    parser.add_argument("--over_threshold", type=int)
    parser.add_argument("--under_threshold", type=int)
    parser.add_argument("--fps", type=int)
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(module_name="01_quality") if not args.config else load_config(config_path=args.config)

    kwargs = {}
    if args.blur_threshold is not None:
        kwargs['blur_threshold'] = args.blur_threshold
    if args.over_threshold is not None:
        kwargs['over_threshold'] = args.over_threshold
    if args.under_threshold is not None:
        kwargs['under_threshold'] = args.under_threshold
    if args.fps is not None:
        kwargs['expected_fps'] = args.fps

    try:
        generate_quality_report(args.input, args.output, config=config, **kwargs)
    except Exception as e:
        logger.critical(f"质检失败: {e}", exc_info=True)
        sys.exit(1)