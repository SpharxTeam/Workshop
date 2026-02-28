#!/usr/bin/env python3
"""
交付模块（预留）：将打包好的数据集上传至 OSS 并发送通知。
"""
import argparse
import os
import sys
import logging
from pathlib import Path
from config_loader import load_config
from .oss_uploader import upload_to_oss
from .notifier import send_notification

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

def upload_dataset(dataset_path, oss_config):
    if not os.path.isdir(dataset_path):
        logger.error(f"数据集目录不存在: {dataset_path}")
        return False

    success = True
    for root, _, files in os.walk(dataset_path):
        for file in files:
            local = os.path.join(root, file)
            rel = os.path.relpath(local, dataset_path)
            remote = f"datasets/{os.path.basename(dataset_path)}/{rel}"
            if not upload_to_oss(local, remote, **oss_config):
                logger.error(f"上传失败: {local}")
                success = False
    return success

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入数据集目录")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(module_name="05_delivery") if not args.config else load_config(config_path=args.config)
    oss_config = config.get("oss", {})

    # 从环境变量补充
    for key in ["endpoint", "bucket", "access_key_id", "access_key_secret"]:
        if not oss_config.get(key):
            oss_config[key] = os.environ.get(f"OSS_{key.upper()}")

    required = ["endpoint", "bucket", "access_key_id", "access_key_secret"]
    if not all(oss_config.get(k) for k in required):
        logger.warning("OSS 配置不完整，将执行模拟上传")

    try:
        success = upload_dataset(args.input, oss_config)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"交付失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()