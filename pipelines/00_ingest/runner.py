# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 数据导入模块主脚本。
# 00_ingest 模块运行器

import argparse
import os
import sys
import logging
from config_loader import load_config
from algorithm import parse_bag

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
    parser = argparse.ArgumentParser(description="解析 RealSense bag 文件")
    parser.add_argument("--input", required=True, help="输入 bag 文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(config_path=args.config) if args.config else {}
    logger.info(f"Python 版本: {sys.version}")
    logger.info(f"pyrealsense2 版本: {__import__('pyrealsense2').__version__ if hasattr(__import__('pyrealsense2'), '__version__') else 'unknown'}")

    try:
        success = parse_bag(args.input, args.output, config)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"未捕获的异常: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()