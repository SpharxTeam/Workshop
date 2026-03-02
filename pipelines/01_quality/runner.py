# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 质检模块主脚本：模糊检测、曝光检测、丢帧统计，生成 JSON 报告

import argparse
import os
import sys
import logging
from config_loader import load_config
from algorithm import generate_quality_report

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
    parser.add_argument("--input", required=True, help="场景目录（包含 rgb/ 子目录）")
    parser.add_argument("--output", required=True, help="报告输出目录")
    parser.add_argument("--blur_threshold", type=int)
    parser.add_argument("--over_threshold", type=int)
    parser.add_argument("--under_threshold", type=int)
    parser.add_argument("--fps", type=int)
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(module_name="01_quality") if not args.config else load_config(config_path=args.config)

    kwargs = {}
    if args.blur_threshold is not None:
        kwargs['blur_threshold'] = args.blur_threshold
    if args.over_threshold is not None:
        kwargs['over_threshold'] = args.over_threshold
    if args.under_threshold is not None:
        kwargs['under_threshold'] = args.under_threshold
    if args.fps is not None:
        kwargs['expected_fps'] = args.fps

    try:
        generate_quality_report(args.input, args.output, config=config, **kwargs)
    except Exception as e:
        logger.critical(f"质检失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()