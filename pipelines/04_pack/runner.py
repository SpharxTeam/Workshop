#!/usr/bin/env python3
"""
打包模块：将处理后的场景数据整理成数据集包，生成 manifest.json。
"""
import argparse
import os
import json
import shutil
import hashlib
import pandas as pd
from pathlib import Path
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

    required = [("rgb.mp4", "rgb.mp4"), ("timestamps.csv", "timestamps.csv")]
    optional = [
        ("imu.csv", "imu.csv"),
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入场景目录")
    parser.add_argument("--output", required=True, help="输出数据集目录")
    parser.add_argument("--formats", help="格式列表，逗号分隔")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        logger.error(f"输入目录不存在: {args.input}")
        sys.exit(1)

    config = load_config(module_name="04_pack") if not args.config else load_config(config_path=args.config)
    formats = args.formats.split(',') if args.formats else config.get('formats', ['ros', 'coco'])

    try:
        success = pack_scene(args.input, args.output, formats, config=config)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"打包失败: {e}", exc_info=True)
        sys.exit(1)