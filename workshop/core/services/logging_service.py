"""
Logging Service - V3.0
=====================

日志服务 - 结构化日志、分级输出、多处理器

参考:
    - AgentOS Logging 模块
    - Deepness LoggingService
"""

from typing import Any, Dict, Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
import logging.config
import sys
import json
from datetime import datetime
from functools import wraps


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """日志格式"""
    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LogConfig:
    """日志配置"""
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.TEXT
    output_dir: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    include_timestamp: bool = True
    include_module: bool = True
    include_function: bool = True
    include_line: bool = True
    sanitize_sensitive: bool = True
    sensitive_keys: List[str] = field(default_factory=lambda: [
        'password', 'token', 'secret', 'key', 'credential',
        'api_key', 'access_token', 'private_key',
    ])


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器
    
    输出格式化的结构化日志
    """

    def __init__(self, config: LogConfig):
        super().__init__()
        self._config = config

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        if self._config.include_module:
            log_data['module'] = record.module

        if self._config.include_function:
            log_data['function'] = record.funcName

        if self._config.include_line:
            log_data['line'] = record.lineno

        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        # 异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class SanitizingFilter(logging.Filter):
    """
    日志净化过滤器
    
    过滤敏感信息
    """

    def __init__(self, sensitive_keys: List[str]):
        super().__init__()
        self._sensitive_keys = set(key.lower() for key in sensitive_keys)

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录"""
        msg = record.getMessage()
        
        # 检查是否包含敏感键
        msg_lower = msg.lower()
        for key in self._sensitive_keys:
            if key in msg_lower:
                # 替换敏感值
                record.msg = self._sanitize_message(msg, key)
        
        return True

    def _sanitize_message(self, message: str, key: str) -> str:
        """净化消息"""
        import re
        pattern = rf'{key}["\s:=]+["\']?([^"\s,}}]+)'
        return re.sub(pattern, f'{key}=***REDACTED***', message, flags=re.IGNORECASE)


class LoggingService:
    """
    日志服务 - V3.0
    
    特性:
    - 结构化日志
    - 多处理器支持
    - 敏感信息过滤
    - 日志轮转
    - 性能追踪
    """

    _instance: Optional['LoggingService'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[LogConfig] = None):
        """
        初始化日志服务
        
        Args:
            config: 日志配置
        """
        if self._initialized:
            return

        self._config = config or LogConfig()
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        
        self._setup_root_logger()
        self._initialized = True

    def _setup_root_logger(self) -> None:
        """设置根日志记录器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self._config.level.value)

        # 清除现有处理器
        root_logger.handlers.clear()

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._config.level.value)
        
        if self._config.format == LogFormat.JSON:
            formatter = StructuredFormatter(self._config)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        self._handlers['console'] = console_handler

        # 文件处理器
        if self._config.output_dir:
            self._add_file_handler()

        # 敏感信息过滤器
        if self._config.sanitize_sensitive:
            sanitizing_filter = SanitizingFilter(self._config.sensitive_keys)
            root_logger.addFilter(sanitizing_filter)

    def _add_file_handler(self) -> None:
        """添加文件处理器"""
        from logging.handlers import RotatingFileHandler

        log_file = self._config.output_dir / "workshop.log"
        self._config.output_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self._config.max_file_size,
            backupCount=self._config.backup_count,
            encoding='utf-8',
        )
        
        file_handler.setLevel(self._config.level.value)
        
        if self._config.format == LogFormat.JSON:
            formatter = StructuredFormatter(self._config)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
        self._handlers['file'] = file_handler

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def set_level(self, level: LogLevel) -> None:
        """
        设置日志级别
        
        Args:
            level: 日志级别
        """
        self._config.level = level
        logging.getLogger().setLevel(level.value)
        
        for handler in self._handlers.values():
            handler.setLevel(level.value)

    def add_handler(self, name: str, handler: logging.Handler) -> None:
        """
        添加处理器
        
        Args:
            name: 处理器名称
            handler: 处理器实例
        """
        self._handlers[name] = handler
        logging.getLogger().addHandler(handler)

    def remove_handler(self, name: str) -> bool:
        """
        移除处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            bool: 是否成功
        """
        if name in self._handlers:
            handler = self._handlers.pop(name)
            logging.getLogger().removeHandler(handler)
            return True
        return False


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return LoggingService().get_logger(name)


def setup_logging(
    level: str = "INFO",
    format_type: str = "text",
    output_dir: Optional[str] = None,
    **kwargs
) -> LoggingService:
    """
    设置日志的便捷函数
    
    Args:
        level: 日志级别
        format_type: 格式类型
        output_dir: 输出目录
        **kwargs: 其他配置
        
    Returns:
        LoggingService: 日志服务实例
    """
    config = LogConfig(
        level=LogLevel[level.upper()],
        format=LogFormat[format_type.upper()],
        output_dir=Path(output_dir) if output_dir else None,
        **kwargs
    )
    return LoggingService(config)


def log_performance(func: Callable) -> Callable:
    """
    性能日志装饰器
    
    记录函数执行时间
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(
                f"{func.__name__} 执行完成: {duration:.3f}s",
                extra={'duration': duration, 'function': func.__name__}
            )
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"{func.__name__} 执行失败: {e}",
                extra={'duration': duration, 'function': func.__name__, 'error': str(e)}
            )
            raise
    
    return wrapper
