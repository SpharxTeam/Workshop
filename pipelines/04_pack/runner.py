# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 打包模块主脚本：将处理后的场景数据整理成数据集包，生成 manifest.json

import argparse
import os
import sys
import logging
from config_loader import load_config
from algorithm import pack_scene

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

if __name__ == "__main__":
    main()