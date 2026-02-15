#!/usr/bin/env python3
"""
增强模块：模拟语义标注和 SLAM 轨迹生成。
"""
import argparse
import os
import json
import numpy as np

def mock_enhance(input_dir, output_dir):
    """生成模拟的语义标签和轨迹文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 模拟 COCO 格式标注
    coco_output = {
        "images": [{"id": 0, "file_name": "rgb.mp4", "width": 1920, "height": 1080}],
        "annotations": [],
        "categories": [{"id": 0, "name": "person"}]
    }
    with open(os.path.join(output_dir, "annotations.json"), "w") as f:
        json.dump(coco_output, f)
    
    # 模拟 SLAM 轨迹
    trajectory = []
    for i in range(100):
        trajectory.append({
            "frame": i,
            "position": [np.random.randn() * 0.1, np.random.randn() * 0.1, np.random.randn() * 0.1],
            "rotation": list(np.random.randn(3, 3).flatten())
        })
    with open(os.path.join(output_dir, "trajectory.json"), "w") as f:
        json.dump(trajectory, f, indent=2)
    
    with open(os.path.join(output_dir, "ENHANCE_DONE"), "w") as f:
        f.write("done")
    
    print(f"增强数据已生成到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    mock_enhance(args.input, args.output)