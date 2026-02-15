# pipelines/01_quality/quality_report.py

import argparse
import json
import os
import cv2
import numpy as np
import pandas as pd
from blur_detector import detect_blurry_frames

def detect_exposure(video_path, over_threshold=240, under_threshold=30):
    """
    检测过曝/欠曝帧（基于平均亮度）
    返回过曝帧索引列表和欠曝帧索引列表
    """
    cap = cv2.VideoCapture(video_path)
    overexposed = []
    underexposed = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        if mean_brightness > over_threshold:
            overexposed.append(frame_idx)
        elif mean_brightness < under_threshold:
            underexposed.append(frame_idx)
        frame_idx += 1
    cap.release()
    return overexposed, underexposed

def check_dropped_frames(timestamp_csv, expected_fps=30):
    """
    基于时间戳检查丢帧情况
    返回丢帧数和最大间隔（毫秒）
    """
    df = pd.read_csv(timestamp_csv)
    timestamps = df['timestamp'].values
    if len(timestamps) < 2:
        return 0, 0.0
    intervals = np.diff(timestamps)  # 毫秒
    expected_interval = 1000.0 / expected_fps  # 毫秒
    # 如果间隔大于预期间隔的1.5倍，认为丢了一帧或多帧（简化处理）
    dropped = np.sum(intervals > expected_interval * 1.5)
    max_interval = np.max(intervals) if len(intervals) > 0 else 0.0
    return int(dropped), float(max_interval)

def generate_quality_report(scene_dir, output_dir, blur_threshold=100,
                            over_threshold=240, under_threshold=30, expected_fps=30):
    """
    生成场景的质检报告
    scene_dir: 场景目录（包含rgb.mp4, timestamps.csv等）
    output_dir: 报告输出目录
    """
    video_path = os.path.join(scene_dir, "rgb.mp4")
    timestamp_path = os.path.join(scene_dir, "timestamps.csv")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    if not os.path.exists(timestamp_path):
        raise FileNotFoundError(f"时间戳文件不存在: {timestamp_path}")

    # 模糊检测
    blurry_frames, blur_scores = detect_blurry_frames(video_path, threshold=blur_threshold)

    # 曝光检测
    overexposed, underexposed = detect_exposure(video_path, over_threshold, under_threshold)

    # 丢帧统计
    dropped_frames, max_interval_ms = check_dropped_frames(timestamp_path, expected_fps)

    # 总帧数（可通过视频或时间戳获得）
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # 构建报告
    report = {
        "scene_id": os.path.basename(scene_dir),
        "overall_pass": True,  # 可自定义规则，例如模糊帧比例<5%且丢帧<1%
        "timestamp": pd.Timestamp.now().isoformat(),
        "camera_reports": [
            {
                "camera_id": "cam0",  # 单相机，后续可扩展
                "total_frames": total_frames,
                "dropped_frames": dropped_frames,
                "blurry_frames": blurry_frames,
                "overexposed_frames": overexposed,
                "underexposed_frames": underexposed,
                "avg_sync_offset_ms": 0.0,  # 同步精度暂不测量
                "max_interval_ms": max_interval_ms,
                "blur_scores": blur_scores  # 可选，可用于可视化
            }
        ],
        "notes": ""
    }

    # 简单判断整体是否合格
    if len(blurry_frames) > total_frames * 0.05:  # 模糊帧超过5%
        report["overall_pass"] = False
        report["notes"] += "模糊帧比例过高; "
    if dropped_frames > 1:
        report["overall_pass"] = False
        report["notes"] += f"丢帧{dropped_frames}帧; "

    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "quality_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"质检报告已生成到 {report_path}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="质检模块")
    parser.add_argument("--input", required=True, help="场景目录（包含rgb.mp4等）")
    parser.add_argument("--output", required=True, help="报告输出目录")
    parser.add_argument("--blur_threshold", type=int, default=100, help="模糊阈值")
    parser.add_argument("--over_threshold", type=int, default=240, help="过曝阈值")
    parser.add_argument("--under_threshold", type=int, default=30, help="欠曝阈值")
    parser.add_argument("--fps", type=int, default=30, help="期望帧率")
    args = parser.parse_args()

    generate_quality_report(
        args.input,
        args.output,
        blur_threshold=args.blur_threshold,
        over_threshold=args.over_threshold,
        under_threshold=args.under_threshold,
        expected_fps=args.fps
    )