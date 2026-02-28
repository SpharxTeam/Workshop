#!/usr/bin/env python3

# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

"""
增强模块主脚本：使用 YOLOv8 对视频进行目标检测，生成 COCO 格式标注。
"""
import argparse
import os
import sys
import logging
from config_loader import load_config
from algorithm import process_video

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="场景目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--conf", type=float, help="置信度阈值（覆盖配置文件）")
    parser.add_argument("--model", help="模型路径（覆盖配置文件）")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(module_name="02_enhance") if not args.config else load_config(config_path=args.config)
    video_path = os.path.join(args.input, "rgb.mp4")
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        sys.exit(1)

    kwargs = {}
    if args.conf is not None:
        kwargs['conf'] = args.conf
    if args.model is not None:
        kwargs['model'] = args.model

    try:
        success = process_video(video_path, args.output, config=config, **kwargs)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"处理失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()