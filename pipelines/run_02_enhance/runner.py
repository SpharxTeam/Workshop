# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 增强模块主脚本：基于图像序列进行目标检测

import argparse
import os
import sys
import logging
from config_loader import load_config
from algorithm import process_video  # 注意：函数名仍为 process_video，但实际处理图像

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
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--conf", type=float, help="置信度阈值")
    parser.add_argument("--model", help="模型路径")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(module_name="02_enhance") if not args.config else load_config(config_path=args.config)

    kwargs = {}
    if args.conf is not None:
        kwargs['conf'] = args.conf
    if args.model is not None:
        kwargs['model'] = args.model

    try:
        success = process_video(args.input, args.output, config=config, **kwargs)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"处理失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()