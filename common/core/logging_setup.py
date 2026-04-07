# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 统一日志系统设置 - 参考 AgentOS 三层日志架构设计
# 提供高性能、线程安全的日志记录功能

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache


DEFAULT_LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_LOG_DIR = "/app/logs"


@lru_cache(maxsize=32)
def get_logger(name: str) -> logging.Logger:
    """
    获取 Logger 实例（带缓存）
    
    Args:
        name: Logger 名称
        
    Returns:
        logging.Logger: Logger 实例
    """
    return logging.getLogger(name)


def setup_logging(
    module_name: str,
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_color: bool = True
) -> logging.Logger:
    """
    配置统一的日志系统 - 参考 AgentOS 日志系统设计
    
    特性：
    - 支持控制台和文件双输出
    - 自动日志轮转
    - 彩色控制台输出（可选）
    - 模块化命名空间
    - 线程安全
    
    Args:
        module_name: 模块名称（用于 Logger 命名和文件名）
        log_dir: 日志目录（默认 /app/logs）
        level: 日志级别
        log_format: 日志格式
        date_format: 日期格式
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数
        use_color: 是否使用彩色输出
        
    Returns:
        logging.Logger: 配置好的 Logger 实例
        
    Example:
        >>> logger = setup_logging("01_quality")
        >>> logger.info("质检模块启动")
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_format = log_format or DEFAULT_LOG_FORMAT
    date_format = date_format or DEFAULT_DATE_FORMAT
    
    # 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 获取或创建 Logger
    logger_name = module_name if module_name else "workshop"
    logger = logging.getLogger(logger_name)
    
    # 避免重复添加 Handler
    if logger.handlers:
        logger.handlers.clear()
    
    logger.setLevel(level)
    
    # 格式化器
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 控制台 Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if use_color and _supports_color():
            color_formatter = _ColorFormatter(log_format, date_format)
            console_handler.setFormatter(color_formatter)
        else:
            console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    # 文件 Handler（带轮转）
    if file_output:
        log_file = os.path.join(log_dir, f"{module_name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志向上传播到 root logger（避免重复输出）
    logger.propagate = False
    
    logger.info(f"日志系统初始化完成: {module_name}")
    
    return logger


class _ColorFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # 调用父类的格式化方法
        formatted = super().format(record)
        
        # 重置（避免影响后续使用）
        record.levelname = levelname
        
        return formatted


def _supports_color() -> bool:
    """检测终端是否支持颜色"""
    plat = sys.platform
    supported_platform = plat != 'win32' or 'ANSICON' in os.environ
    
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    return supported_platform and is_a_tty


def get_log_files(log_dir: Optional[str] = None, pattern: str = "*.log") -> list:
    """
    获取日志文件列表
    
    Args:
        log_dir: 日志目录
        pattern: 文件匹配模式
        
    Returns:
        list: 日志文件路径列表
    """
    log_dir = Path(log_dir or DEFAULT_LOG_DIR)
    if not log_dir.exists():
        return []
    
    return sorted(log_dir.glob(pattern))


def clear_old_logs(
    log_dir: Optional[str] = None,
    max_age_days: int = 30,
    pattern: str = "*.log"
) -> int:
    """
    清理过期日志文件
    
    Args:
        log_dir: 日志目录
        max_age_days: 最大保留天数
        pattern: 文件匹配模式
        
    Returns:
        int: 删除的文件数量
    """
    import time
    
    log_dir = Path(log_dir or DEFAULT_LOG_DIR)
    if not log_dir.exists():
        return 0
    
    deleted_count = 0
    cutoff_time = time.time() - (max_age_days * 24 * 3600)
    
    for log_file in log_dir.glob(pattern):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                deleted_count += 1
            except OSError:
                pass
    
    return deleted_count


__all__ = [
    'setup_logging',
    'get_logger',
    'get_log_files',
    'clear_old_logs',
    'DEFAULT_LOG_FORMAT',
    'DEFAULT_LOG_DIR',
]
