# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 数据打包核心算法（适配图像序列结构）

import os
import json
import shutil
import hashlib
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

def pack_scene(input_dir, output_dir, formats=None, config=None):
    if config is None:
        config = {}
    if formats is None:
        formats = config.get('formats', ['ros', 'coco'])

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    required = [("timestamps.csv", "timestamps.csv")]
    optional = [
        ("imu.csv", "imu.csv"),
        ("rgb", "rgb"),
        ("depth", "depth"),
        ("quality/quality_report.json", "quality_report.json"),
        ("enhanced/annotations.json", "annotations.json"),
        ("calib/intrinsics.json", "intrinsics.json")
    ]

    for src_name, dst_name in required:
        src = input_dir / src_name
        if not src.exists():
            raise FileNotFoundError(f"必需文件缺失: {src_name}")
        copy_file(src, output_dir / dst_name)

    for src_name, dst_name in optional:
        src = input_dir / src_name
        if src.exists():
            dst = output_dir / dst_name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                copy_file(src, dst)
            logger.info(f"复制: {src_name}")
        else:
            logger.info(f"可选文件 {src_name} 不存在，跳过")

    manifest = {
        "scene_id": input_dir.name,
        "created_at": pd.Timestamp.now().isoformat(),
        "files": []
    }
    for root, _, files in os.walk(output_dir):
        for file in files:
            full = os.path.join(root, file)
            rel = os.path.relpath(full, output_dir)
            manifest["files"].append({
                "path": rel,
                "size": os.path.getsize(full),
                "sha256": file_hash(full)
            })

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"manifest 已生成，共 {len(manifest['files'])} 个文件")
    return True