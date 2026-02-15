#!/usr/bin/env python3
"""
质检模块：模拟生成质检报告。
"""
import argparse
import json
import os
import numpy as np
import pandas as pd

def generate_report(input_dir, output_dir, threshold=100):
    """模拟质检：从输入目录读取时间戳，生成虚假报告"""
    ts_path = os.path.join(input_dir, "timestamps.csv")
    if os.path.exists(ts_path):
        df = pd.read_csv(ts_path)
        total_frames = len(df)
        # 模拟丢帧
        dropped = np.random.randint(0, max(1, total_frames // 20))
    else:
        total_frames = 100
        dropped = 5

    report = {
        "scene_id": os.path.basename(input_dir),
        "overall_pass": True,
        "timestamp": pd.Timestamp.now().isoformat(),
        "camera_reports": [
            {
                "camera_id": "cam0",
                "total_frames": total_frames,
                "dropped_frames": dropped,
                "blurry_frames": [],
                "overexposed_frames": [],
                "underexposed_frames": [],
                "avg_sync_offset_ms": 0.02
            }
        ],
        "notes": "模拟质检报告"
    }
    
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "quality_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    # 创建完成标志
    with open(os.path.join(output_dir, "QUALITY_DONE"), "w") as f:
        f.write("done")
    
    print(f"质检报告已生成到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=int, default=100)
    args = parser.parse_args()
    
    generate_report(args.input, args.output, args.threshold)