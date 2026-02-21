#!/usr/bin/env python3
"""
打包模块：将处理后的场景数据整理成数据集包。
- 复制 RGB 视频、深度图、IMU、质检报告、标注文件等到数据集目录。
- 生成 manifest.json，包含每个文件的 SHA256 哈希。
- 支持按格式输出（如 COCO 格式的标注）。
增强版：统一日志、异常处理、支持配置文件、区分必需/可选文件。
"""
import argparse
import os
import json
import shutil
import hashlib
import pandas as pd
from pathlib import Path

# 本地配置加载模块
import config_loader

import logging
import sys
MODULE_NAME = os.path.basename(__file__).replace('.py', '')
LOG_DIR = "/logs"
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

def calculate_file_hash(filepath):
    """计算文件的 SHA256 哈希"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def copy_file(src, dst):
    """复制文件，自动创建目录"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    logger.debug(f"复制 {src} -> {dst}")

def pack_scene(input_dir, output_dir, formats=None, config=None):
    """
    打包场景数据
    input_dir: 场景目录（由 ingest 生成，并包含 quality/ enhanced/ calib/ 等子目录）
    output_dir: 数据集输出目录
    formats: 列表，如 ['ros', 'coco']（目前仅用于占位）
    config: 配置字典（可选）
    """
    if config is None:
        config = {}
    if formats is None and 'formats' in config:
        formats = config['formats']
    if formats is None:
        formats = ['ros', 'coco']

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 必需文件列表（缺失则终止）
    required_files = [
        ("rgb.mp4", "rgb.mp4"),
        ("timestamps.csv", "timestamps.csv")
    ]
    # 可选文件列表（缺失仅记录 info）
    optional_files = [
        ("imu.csv", "imu.csv"),
        ("depth", "depth"),           # 整个目录
        ("quality/quality_report.json", "quality_report.json"),
        ("enhanced/annotations.json", "annotations.json"),
        ("calib/intrinsics.json", "intrinsics.json")
    ]

    # 检查必需文件
    for src_name, dst_name in required_files:
        src_path = input_dir / src_name
        if not src_path.exists():
            raise FileNotFoundError(f"必需文件缺失: {src_name}，打包终止")
        dst_path = output_dir / dst_name
        copy_file(src_path, dst_path)

    # 处理可选文件
    for src_name, dst_name in optional_files:
        src_path = input_dir / src_name
        if src_path.exists():
            if src_path.is_dir():
                dst_path = output_dir / dst_name
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                logger.info(f"复制目录 {src_path} -> {dst_path}")
            else:
                dst_path = output_dir / dst_name
                copy_file(src_path, dst_path)
        else:
            logger.info(f"可选文件 {src_name} 不存在，跳过")

    # 生成 manifest.json
    manifest = {
        "scene_id": input_dir.name,
        "created_at": pd.Timestamp.now().isoformat(),
        "files": []
    }

    # 遍历输出目录中所有文件，计算哈希
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, output_dir)
            file_size = os.path.getsize(full_path)
            file_hash = calculate_file_hash(full_path)
            manifest["files"].append({
                "path": rel_path,
                "size": file_size,
                "sha256": file_hash
            })

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"manifest 已生成: {manifest_path}")

    logger.info(f"数据集打包完成，共 {len(manifest['files'])} 个文件")
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
        exit(1)

    config = config_loader.load_config(args.config, "pack")
    formats = args.formats.split(',') if args.formats else config.get('formats', ['ros', 'coco'])

    try:
        success = pack_scene(args.input, args.output, formats, config=config)
        exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"打包失败: {e}", exc_info=True)
        exit(1)