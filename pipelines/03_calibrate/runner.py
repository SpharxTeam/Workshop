#!/usr/bin/env python3

# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

"""
标定模块主脚本：基于棋盘格图像进行相机内参标定。
"""
import argparse
import os
import sys
import logging
from config_loader import load_config
from algorithm import calibrate_camera

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
    parser.add_argument("--input", required=True, help="标定图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--chessboard", help="棋盘格内角点，如 9,6")
    parser.add_argument("--square_size", type=float, help="方格尺寸（米）")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        logger.error(f"输入目录不存在: {args.input}")
        sys.exit(1)

    config = load_config(module_name="03_calibrate") if not args.config else load_config(config_path=args.config)

    chessboard = args.chessboard if args.chessboard else config.get('chessboard', '9,6')
    if isinstance(chessboard, str):
        chessboard = tuple(map(int, chessboard.split(',')))
    square_size = args.square_size if args.square_size is not None else config.get('square_size', 0.025)

    try:
        success = calibrate_camera(args.input, chessboard_size=chessboard, square_size=square_size, output_dir=args.output)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"标定失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()