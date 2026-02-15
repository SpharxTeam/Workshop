#!/usr/bin/env python3
"""
标定模块：模拟生成相机内外参文件。
"""
import argparse
import os
import json
import numpy as np

def mock_calibrate(input_dir, output_dir):
    """生成模拟的标定参数"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 模拟相机内参
    intrinsics = {
        "camera_matrix": [
            [1400.0, 0.0, 960.0],
            [0.0, 1400.0, 540.0],
            [0.0, 0.0, 1.0]
        ],
        "dist_coeffs": [0.1, -0.2, 0.0, 0.0, 0.0],
        "reprojection_error": 0.25
    }
    with open(os.path.join(output_dir, "intrinsics.json"), "w") as f:
        json.dump(intrinsics, f, indent=2)
    
    # 模拟外参（相对于参考相机）
    extrinsics = {
        "rotation": list(np.eye(3).flatten()),
        "translation": [0.1, 0.0, 0.0]
    }
    with open(os.path.join(output_dir, "extrinsics.json"), "w") as f:
        json.dump(extrinsics, f, indent=2)
    
    with open(os.path.join(output_dir, "CALIBRATE_DONE"), "w") as f:
        f.write("done")
    
    print(f"标定参数已生成到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    mock_calibrate(args.input, args.output)