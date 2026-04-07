# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 统一异常处理体系 - 参考 AgentOS 错误处理机制设计
# 遵循 ARCHITECTURAL_PRINCIPLES.md E-6 (错误可追溯)

from enum import Enum, IntEnum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import traceback
import time


class ErrorCode(IntEnum):
    """
    统一错误码定义 - 参考 AgentOS agentos_error_t 设计
    
    分类：
    - 1xxx: 基础/通用错误
    - 2xxx: 配置相关错误
    - 3xxx: Pipeline 执行错误
    - 4xxx: 数据验证错误
    - 5xxx: 硬件设备错误
    - 6xxx: 数据IO错误
    """
    
    # 成功
    SUCCESS = 0
    
    # 基础错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    INVALID_PARAMETER = 1001
    NULL_POINTER = 1002
    OUT_OF_MEMORY = 1003
    TIMEOUT = 1004
    NOT_SUPPORTED = 1005
    PERMISSION_DENIED = 1006
    IO_ERROR = 1007
    PARSE_ERROR = 1008
    STATE_ERROR = 1009
    CANCELED = 1010
    
    # 配置错误 (2000-2999)
    CONFIG_NOT_FOUND = 2000
    CONFIG_PARSE_ERROR = 2001
    CONFIG_VALIDATION_ERROR = 2002
    CONFIG_MISSING_REQUIRED = 2003
    CONFIG_INVALID_FORMAT = 2004
    CONFIG_LOAD_ERROR = 2005
    
    # Pipeline 错误 (3000-3999)
    PIPELINE_INIT_FAILED = 3000
    PIPELINE_EXECUTION_FAILED = 3001
    PIPELINE_TIMEOUT = 3002
    PIPELINE_DEPENDENCY_MISSING = 3003
    MODULE_NOT_FOUND = 3004
    MODULE_LOAD_FAILED = 3005
    ALGORITHM_EXECUTION_FAILED = 3006
    
    # 验证错误 (4000-4999)
    VALIDATION_FAILED = 4000
    DATA_INTEGRITY_ERROR = 4001
    FILE_NOT_FOUND = 4002
    INVALID_DATA_FORMAT = 4003
    MISSING_REQUIRED_FIELD = 4004
    VALUE_OUT_OF_RANGE = 4005
    
    # 硬件错误 (5000-5999)
    HARDWARE_INIT_FAILED = 5000
    DEVICE_NOT_FOUND = 5001
    DEVICE_DISCONNECTED = 5002
    CALIBRATION_FAILED = 5003
    SYNC_ERROR = 5004
    FRAME_CAPTURE_FAILED = 5005
    
    # 数据IO错误 (6000-6999)
    READ_ERROR = 6000
    WRITE_ERROR = 6001
    ENCODE_ERROR = 6002
    DECODE_ERROR = 6003
    COMPRESSION_ERROR = 6004
    STORAGE_FULL = 6005


class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    file: str = ""
    line: int = 0
    function: str = ""
    message: str = ""
    error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR
    timestamp_ns: int = field(default_factory=lambda: int(time.time() * 1e9))


@dataclass
class ErrorChain:
    """错误链 - 支持多层错误追踪"""
    code: ErrorCode = ErrorCode.SUCCESS
    contexts: List[ErrorContext] = field(default_factory=list)
    
    def add_context(self, context: ErrorContext) -> None:
        """添加错误上下文"""
        if len(self.contexts) >= 10:
            self.contexts.pop(0)
        self.contexts.append(context)
        self.code = context.error_code
    
    @property
    def depth(self) -> int:
        return len(self.contexts)


class WorkshopError(Exception):
    """
    Workshop 基础异常类 - 参考 AgentOS 异常设计
    
    特性：
    - 统一错误码
    - 多语言描述
    - 错误链追踪
    - 上下文信息保留
    """
    
    _error_descriptions: Dict[ErrorCode, Dict[str, str]] = {
        # 成功
        ErrorCode.SUCCESS: {"en": "Success", "zh_cn": "成功"},
        
        # 基础错误
        ErrorCode.UNKNOWN_ERROR: {"en": "Unknown error", "zh_cn": "未知错误"},
        ErrorCode.INVALID_PARAMETER: {"en": "Invalid parameter", "zh_cn": "无效参数"},
        ErrorCode.NULL_POINTER: {"en": "Null pointer", "zh_cn": "空指针"},
        ErrorCode.OUT_OF_MEMORY: {"en": "Out of memory", "zh_cn": "内存不足"},
        ErrorCode.TIMEOUT: {"en": "Operation timeout", "zh_cn": "操作超时"},
        ErrorCode.NOT_SUPPORTED: {"en": "Not supported", "zh_cn": "不支持"},
        ErrorCode.PERMISSION_DENIED: {"en": "Permission denied", "zh_cn": "权限不足"},
        ErrorCode.IO_ERROR: {"en": "I/O error", "zh_cn": "I/O 错误"},
        ErrorCode.PARSE_ERROR: {"en": "Parse error", "zh_cn": "解析错误"},
        ErrorCode.STATE_ERROR: {"en": "State error", "zh_cn": "状态错误"},
        ErrorCode.CANCELED: {"en": "Canceled", "zh_cn": "已取消"},
        
        # 配置错误
        ErrorCode.CONFIG_NOT_FOUND: {"en": "Configuration not found", "zh_cn": "配置文件未找到"},
        ErrorCode.CONFIG_PARSE_ERROR: {"en": "Configuration parse error", "zh_cn": "配置解析错误"},
        ErrorCode.CONFIG_VALIDATION_ERROR: {"en": "Configuration validation failed", "zh_cn": "配置验证失败"},
        ErrorCode.CONFIG_MISSING_REQUIRED: {"en": "Missing required configuration", "zh_cn": "缺少必需配置项"},
        ErrorCode.CONFIG_INVALID_FORMAT: {"en": "Invalid configuration format", "zh_cn": "无效的配置格式"},
        
        # Pipeline 错误
        ErrorCode.PIPELINE_INIT_FAILED: {"en": "Pipeline initialization failed", "zh_cn": "Pipeline 初始化失败"},
        ErrorCode.PIPELINE_EXECUTION_FAILED: {"en": "Pipeline execution failed", "zh_cn": "Pipeline 执行失败"},
        ErrorCode.PIPELINE_TIMEOUT: {"en": "Pipeline execution timeout", "zh_cn": "Pipeline 执行超时"},
        ErrorCode.PIPELINE_DEPENDENCY_MISSING: {"en": "Missing pipeline dependency", "zh_cn": "缺少 Pipeline 依赖"},
        ErrorCode.MODULE_NOT_FOUND: {"en": "Module not found", "zh_cn": "模块未找到"},
        ErrorCode.MODULE_LOAD_FAILED: {"en": "Module load failed", "zh_cn": "模块加载失败"},
        ErrorCode.ALGORITHM_EXECUTION_FAILED: {"en": "Algorithm execution failed", "zh_cn": "算法执行失败"},
        
        # 验证错误
        ErrorCode.VALIDATION_FAILED: {"en": "Validation failed", "zh_cn": "验证失败"},
        ErrorCode.DATA_INTEGRITY_ERROR: {"en": "Data integrity error", "zh_cn": "数据完整性错误"},
        ErrorCode.FILE_NOT_FOUND: {"en": "File not found", "zh_cn": "文件未找到"},
        ErrorCode.INVALID_DATA_FORMAT: {"en": "Invalid data format", "zh_cn": "无效的数据格式"},
        ErrorCode.MISSING_REQUIRED_FIELD: {"en": "Missing required field", "zh_cn": "缺少必需字段"},
        ErrorCode.VALUE_OUT_OF_RANGE: {"en": "Value out of range", "zh_cn": "值超出范围"},
        
        # 硬件错误
        ErrorCode.HARDWARE_INIT_FAILED: {"en": "Hardware initialization failed", "zh_cn": "硬件初始化失败"},
        ErrorCode.DEVICE_NOT_FOUND: {"en": "Device not found", "zh_cn": "设备未找到"},
        ErrorCode.DEVICE_DISCONNECTED: {"en": "Device disconnected", "zh_cn": "设备已断开"},
        ErrorCode.CALIBRATION_FAILED: {"en": "Calibration failed", "zh_cn": "校准失败"},
        ErrorCode.SYNC_ERROR: {"en": "Synchronization error", "zh_cn": "同步错误"},
        ErrorCode.FRAME_CAPTURE_FAILED: {"en": "Frame capture failed", "zh_cn": "帧捕获失败"},
        
        # 数据IO错误
        ErrorCode.READ_ERROR: {"en": "Read error", "zh_cn": "读取错误"},
        ErrorCode.WRITE_ERROR: {"en": "Write error", "zh_cn": "写入错误"},
        ErrorCode.ENCODE_ERROR: {"en": "Encode error", "zh_cn": "编码错误"},
        ErrorCode.DECODE_ERROR: {"en": "Decode error", "zh_cn": "解码错误"},
        ErrorCode.COMPRESSION_ERROR: {"en": "Compression error", "zh_cn": "压缩错误"},
        ErrorCode.STORAGE_FULL: {"en": "Storage full", "zh_cn": "存储空间不足"},
    }
    
    def __init__(
        self,
        code: ErrorCode,
        message: str = "",
        cause: Optional[Exception] = None,
        **context_data
    ):
        super().__init__(message or self._get_description(code))
        self.code = code
        self._cause = cause
        self._context_data = context_data
        self._error_chain = ErrorChain()
        
        stack = traceback.extract_stack()
        if len(stack) >= 3:
            frame_info = stack[-3]
            ctx = ErrorContext(
                file=frame_info.filename,
                line=frame_info.lineno,
                function=frame_info.name,
                message=message or self._get_description(code),
                error_code=code
            )
            self._error_chain.add_context(ctx)
    
    @classmethod
    def _get_description(cls, code: ErrorCode, lang: str = "zh_cn") -> str:
        """获取错误描述"""
        desc_map = cls._error_descriptions.get(code, {})
        return desc_map.get(lang, desc_map.get("en", f"Unknown error ({code})"))
    
    @property
    def description_zh(self) -> str:
        return self._get_description(self.code, "zh_cn")
    
    @property
    def description_en(self) -> str:
        return self._get_description(self.code, "en")
    
    @property
    def severity(self) -> ErrorSeverity:
        """获取错误严重程度"""
        critical_codes = {
            ErrorCode.OUT_OF_MEMORY,
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.HARDWARE_INIT_FAILED,
            ErrorCode.STORAGE_FULL
        }
        if self.code in critical_codes:
            return ErrorSeverity.CRITICAL
        
        warning_codes = {
            ErrorCode.TIMEOUT,
            ErrorCode.CANCELED,
            ErrorCode.CALIBRATION_FAILED,
        }
        if self.code in warning_codes:
            return ErrorSeverity.WARNING
        
        return ErrorSeverity.ERROR
    
    @property
    def cause(self) -> Optional[Exception]:
        return self._cause
    
    @property
    def error_chain(self) -> ErrorChain:
        return self._error_chain
    
    @property
    def context_data(self) -> Dict[str, Any]:
        return self._context_data
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"code={self.code.name}, "
            f"message={str(self)!r}, "
            f"severity={self.severity.value})"
        )


class ConfigurationError(WorkshopError):
    """配置相关错误"""
    def __init__(self, code: ErrorCode, message: str = "", cause: Exception = None, **kwargs):
        super().__init__(code, message, cause, **kwargs)


class PipelineError(WorkshopError):
    """Pipeline 执行错误"""
    def __init__(self, code: ErrorCode, message: str = "", cause: Exception = None, **kwargs):
        super().__init__(code, message, cause, **kwargs)


class ValidationError(WorkshopError):
    """数据验证错误"""
    def __init__(self, code: ErrorCode, message: str = "", cause: Exception = None, **kwargs):
        super().__init__(code, message, cause, **kwargs)


class HardwareError(WorkshopError):
    """硬件设备错误"""
    def __init__(self, code: ErrorCode, message: str = "", cause: Exception = None, **kwargs):
        super().__init__(code, message, cause, **kwargs)


class DataIOError(WorkshopError):
    """数据IO错误"""
    def __init__(self, code: ErrorCode, message: str = "", cause: Exception = None, **kwargs):
        super().__init__(code, message, cause, **kwargs)


class ErrorCodeManager:
    """
    错误码管理器 - 参考 AgentOS 错误统计功能
    
    功能：
    - 错误计数统计
    - 按类别汇总
    - 最近错误记录
    """
    
    def __init__(self):
        self._stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'last_error': None,
            'last_error_time': 0
        }
    
    def record_error(self, error: WorkshopError) -> None:
        """记录错误"""
        category = error.__class__.__name__
        self._stats['total_errors'] += 1
        self._stats['errors_by_category'][category] = \
            self._stats['errors_by_category'].get(category, 0) + 1
        self._stats['last_error'] = error
        self._stats['last_error_time'] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'last_error': None,
            'last_error_time': 0
        }


# 全局错误码管理器实例
error_code_manager = ErrorCodeManager()


__all__ = [
    'ErrorCode',
    'ErrorSeverity',
    'ErrorContext',
    'ErrorChain',
    'WorkshopError',
    'ConfigurationError',
    'PipelineError',
    'ValidationError',
    'HardwareError',
    'DataIOError',
    'ErrorCodeManager',
    'error_code_manager',
]
