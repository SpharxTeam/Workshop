#!/usr/bin/env python3
"""
打包模块（模拟版）：生成数据集清单和占位文件。
"""
import argparse
import os
import json
import shutil
import hashlib

def calculate_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def mock_pack(input_dir, output_dir, formats):
    os.makedirs(output_dir, exist_ok=True)

    if "ros" in formats:
        ros_dir = os.path.join(output_dir, "ros_bag")
        os.makedirs(ros_dir, exist_ok=True)
        with open(os.path.join(ros_dir, "mock_bag.bag"), "w") as f:
            f.write("mock ros bag content")

    if "coco" in formats:
        # 如果 enhance 模块已生成 annotations.json，直接复制
        enhanced_anno = os.path.join(input_dir, "enhanced", "annotations.json")
        if os.path.exists(enhanced_anno):
            shutil.copy(enhanced_anno, os.path.join(output_dir, "annotations.json"))
        else:
            with open(os.path.join(output_dir, "annotations.json"), "w") as f:
                json.dump({"images": [], "annotations": [], "categories": []}, f)

    # 生成 manifest
    manifest = {
        "scene_id": os.path.basename(input_dir),
        "created_at": "2026-02-15T12:00:00",
        "files": []
    }
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            relpath = os.path.relpath(os.path.join(root, file), output_dir)
            manifest["files"].append({
                "path": relpath,
                "size": os.path.getsize(os.path.join(root, file)),
                "sha256": calculate_file_hash(os.path.join(root, file))
            })
    with open(os.path.join(output_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"数据集已打包到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入场景目录")
    parser.add_argument("--output", required=True, help="输出数据集目录")
    parser.add_argument("--formats", default="ros,coco", help="格式列表，逗号分隔")
    args = parser.parse_args()

    formats = args.formats.split(",")
    mock_pack(args.input, args.output, formats)