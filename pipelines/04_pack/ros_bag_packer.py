#!/usr/bin/env python3
"""
打包模块：模拟生成 ROS bag、COCO 等格式数据集。
"""
import argparse
import os
import json
import shutil

def mock_pack(input_dir, output_dir, formats):
    """根据 formats 生成对应的数据集格式"""
    os.makedirs(output_dir, exist_ok=True)
    
    if "ros" in formats:
        # 模拟创建 ROS bag 目录
        ros_dir = os.path.join(output_dir, "ros_bag")
        os.makedirs(ros_dir, exist_ok=True)
        with open(os.path.join(ros_dir, "mock_bag.bag"), "w") as f:
            f.write("mock ros bag content")
    
    if "coco" in formats:
        # 模拟 COCO 标注文件
        coco_data = {
            "images": [],
            "annotations": [],
            "categories": []
        }
        with open(os.path.join(output_dir, "annotations.json"), "w") as f:
            json.dump(coco_data, f)
    
    # 生成 manifest
    manifest = {
        "scene_id": os.path.basename(input_dir),
        "created_at": "2026-02-15T12:00:00",
        "files": []
    }
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            relpath = os.path.relpath(os.path.join(root, file), output_dir)
            manifest["files"].append({"path": relpath, "size": 0})
    with open(os.path.join(output_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    with open(os.path.join(output_dir, "PACK_DONE"), "w") as f:
        f.write("done")
    
    print(f"数据集已打包到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--formats", default="ros,coco")
    args = parser.parse_args()
    
    formats = args.formats.split(",")
    mock_pack(args.input, args.output, formats)