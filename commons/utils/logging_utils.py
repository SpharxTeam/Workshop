"""
日志工具

提供统一的日志配置和管理功能。
"""

from __future__ import annotations

import logging
import logging.config
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColorFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，支持额外上下文"""

    def process(
        self,
        msg: str,
        kwargs: Dict[str, Any],
    ) -> tuple:
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


_loggers: Dict[str, logging.Logger] = {}
_loggers_lock = threading.Lock()
_default_level = logging.INFO
_configured = False


def setup_logging(
    level: Union[str, int] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    log_dir: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    colorize: bool = True,
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    global _default_level, _configured

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    _default_level = level

    format_str = format_string or LOG_FORMAT
    date_fmt = date_format or LOG_DATE_FORMAT

    handlers: list = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if colorize and sys.stdout.isatty() and not json_format:
        console_formatter = ColorFormatter(format_str, datefmt=date_fmt)
    else:
        console_formatter = logging.Formatter(format_str, datefmt=date_fmt)

    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str, datefmt=date_fmt))
        handlers.append(file_handler)

    if log_dir:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)

        from logging.handlers import RotatingFileHandler

        timestamp = datetime.now().strftime("%Y%m%d")
        log_path = log_dir_path / f"workshop_{timestamp}.log"

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str, datefmt=date_fmt))
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    for handler in handlers:
        root_logger.addHandler(handler)

    _configured = True


def get_logger(
    name: str,
    level: Optional[Union[str, int]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Union[logging.Logger, LoggerAdapter]:
    if not _configured:
        setup_logging()

    with _loggers_lock:
        if name not in _loggers:
            logger = logging.getLogger(name)
            if level is not None:
                if isinstance(level, str):
                    level = getattr(logging, level.upper(), _default_level)
                logger.setLevel(level)
            _loggers[name] = logger

        logger = _loggers[name]

    if extra:
        return LoggerAdapter(logger, extra)

    return logger


def set_log_level(level: Union[str, int]) -> None:
    global _default_level

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    _default_level = level
    logging.getLogger().setLevel(level)

    with _loggers_lock:
        for logger in _loggers.values():
            logger.setLevel(level)


def get_log_level() -> int:
    return _default_level


def add_handler(handler: logging.Handler) -> None:
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)


def remove_handler(handler: logging.Handler) -> None:
    root_logger = logging.getLogger()
    root_logger.removeHandler(handler)


def log_exception(
    logger: logging.Logger,
    message: str = "发生异常",
    exc_info: bool = True,
) -> None:
    logger.exception(message, exc_info=exc_info)


class LoggingContext:
    """日志上下文管理器"""

    def __init__(
        self,
        logger: logging.Logger,
        level: int,
    ):
        self.logger = logger
        self.level = level
        self.original_level: Optional[int] = None

    def __enter__(self) -> logging.Logger:
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.original_level is not None:
            self.logger.setLevel(self.original_level)
