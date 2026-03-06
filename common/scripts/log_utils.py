#!/usr/bin/env python3
"""
统一日志工具模块
"""
import logging
import sys

# 设置第三方库的日志级别为 WARNING，减少干扰
logging.getLogger("ultralytics").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("cv2").setLevel(logging.WARNING)

# 自定义日志格式
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%H:%M:%S'

def setup_logger(name, level=logging.INFO):
    """设置一个控制台日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

# 初始化根日志器
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT, handlers=[logging.StreamHandler(sys.stdout)])