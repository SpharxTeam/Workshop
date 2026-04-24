"""
Models and Exceptions - V3.0
============================

数据模型和异常定义

参考:
    - AgentOS Error 模块
    - Deepness Abstractions
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import traceback
from datetime import datetime


class ErrorCode(Enum):
    """
    错误码枚举 - V3.0
    
    错误码范围:
        - 1000-1099: 通用错误
        - 1100-1199: 配置错误
        - 1200-1299: 管道错误
        - 1300-1399: 验证错误
        - 1400-1499: 硬件错误
        - 1500-1599: IO错误
        - 1600-1699: 安全错误
        - 1700-1799: 网络错误
        - 1800-1899: 存储错误
    """
    
    # 通用错误 (1000-1099)
    UNKNOWN_ERROR = (1000, "未知错误")
    INVALID_INPUT = (1001, "无效输入")
    OPERATION_TIMEOUT = (1002, "操作超时")
    RESOURCE_UNAVAILABLE = (1003, "资源不可用")
    PERMISSION_DENIED = (1004, "权限拒绝")
    
    # 配置错误 (1100-1199)
    CONFIG_LOAD_ERROR = (1100, "配置加载失败")
    CONFIG_VALIDATION_ERROR = (1101, "配置验证失败")
    CONFIG_NOT_FOUND = (1102, "配置不存在")
    CONFIG_PARSE_ERROR = (1103, "配置解析错误")
    CONFIG_TYPE_ERROR = (1104, "配置类型错误")
    
    # 管道错误 (1200-1299)
    PIPELINE_INIT_FAILED = (1200, "管道初始化失败")
    PIPELINE_EXECUTION_ERROR = (1201, "管道执行错误")
    PIPELINE_TIMEOUT = (1202, "管道超时")
    PIPELINE_NOT_FOUND = (1203, "管道不存在")
    PIPELINE_INVALID_STATE = (1204, "管道状态无效")
    PIPELINE_DEPENDENCY_ERROR = (1205, "管道依赖错误")
    
    # 验证错误 (1300-1399)
    VALIDATION_ERROR = (1300, "验证失败")
    PATH_TRAVERSAL_DETECTED = (1301, "检测到路径遍历攻击")
    SQL_INJECTION_DETECTED = (1302, "检测到SQL注入")
    XSS_DETECTED = (1303, "检测到XSS攻击")
    INVALID_FILE_TYPE = (1304, "无效的文件类型")
    INVALID_FILE_SIZE = (1305, "无效的文件大小")
    
    # 硬件错误 (1400-1499)
    DEVICE_NOT_FOUND = (1400, "设备未找到")
    DEVICE_CONNECTION_FAILED = (1401, "设备连接失败")
    CALIBRATION_FAILED = (1402, "校准失败")
    DEVICE_TIMEOUT = (1403, "设备超时")
    DEVICE_BUSY = (1404, "设备忙碌")
    DEVICE_ERROR = (1405, "设备错误")
    
    # IO错误 (1500-1599)
    FILE_NOT_FOUND = (1500, "文件未找到")
    FILE_READ_ERROR = (1501, "文件读取错误")
    FILE_WRITE_ERROR = (1502, "文件写入错误")
    FILE_DELETE_ERROR = (1503, "文件删除错误")
    DIRECTORY_NOT_FOUND = (1504, "目录不存在")
    PERMISSION_ERROR = (1505, "权限错误")
    
    # 安全错误 (1600-1699)
    SECURITY_VIOLATION = (1600, "安全违规")
    AUTHENTICATION_FAILED = (1601, "认证失败")
    AUTHORIZATION_FAILED = (1602, "授权失败")
    TOKEN_EXPIRED = (1603, "令牌过期")
    INVALID_CREDENTIALS = (1604, "无效凭据")
    
    # 网络错误 (1700-1799)
    NETWORK_ERROR = (1700, "网络错误")
    CONNECTION_REFUSED = (1701, "连接被拒绝")
    HOST_UNREACHABLE = (1702, "主机不可达")
    DNS_ERROR = (1703, "DNS解析错误")
    
    # 存储错误 (1800-1899)
    STORAGE_ERROR = (1800, "存储错误")
    UPLOAD_FAILED = (1801, "上传失败")
    DOWNLOAD_FAILED = (1802, "下载失败")
    STORAGE_QUOTA_EXCEEDED = (1803, "存储配额超限")

    def __init__(self, code: int, message: str):
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        return self._code

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return f"[{self._code}] {self._message}"


class ErrorSeverity(Enum):
    """错误严重级别"""
    CRITICAL = "CRITICAL"    # 严重：系统无法继续运行
    ERROR = "ERROR"          # 错误：当前操作失败
    WARNING = "WARNING"      # 警告：可继续但需关注
    INFO = "INFO"            # 信息：正常提示
    DEBUG = "DEBUG"          # 调试：调试信息


@dataclass
class ErrorContext:
    """错误上下文"""
    timestamp: datetime = field(default_factory=datetime.now)
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'module': self.module,
            'function': self.function,
            'line_number': self.line_number,
            'stack_trace': self.stack_trace,
            'additional_info': self.additional_info,
        }


class WorkshopError(Exception):
    """
    Workshop 基础异常类 - V3.0
    
    所有 Workshop 异常的基类
    """

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            code: 错误码
            message: 错误消息（默认使用错误码消息）
            severity: 严重级别
            cause: 原始异常
            context: 上下文信息
        """
        self._code = code
        self._severity = severity
        self._cause = cause
        self._context = ErrorContext(
            additional_info=context or {}
        )
        
        # 设置消息
        self._message = message or code.message
        
        # 获取调用栈信息
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            self._context.module = frame.f_back.f_globals.get('__name__')
            self._context.function = frame.f_back.f_code.co_name
            self._context.line_number = frame.f_back.f_lineno
        
        # 获取堆栈跟踪
        if cause:
            self._context.stack_trace = ''.join(traceback.format_exception(
                type(cause), cause, cause.__traceback__
            ))
        
        super().__init__(str(self))

    @property
    def code(self) -> ErrorCode:
        return self._code

    @property
    def severity(self) -> ErrorSeverity:
        return self._severity

    @property
    def message(self) -> str:
        return self._message

    @property
    def cause(self) -> Optional[Exception]:
        return self._cause

    @property
    def context(self) -> ErrorContext:
        return self._context

    def to_dict(self, include_stack_trace: bool = False) -> Dict[str, Any]:
        """
        转换为字典
        
        Args:
            include_stack_trace: 是否包含堆栈跟踪
            
        Returns:
            Dict: 字典表示
        """
        result = {
            'error': True,
            'code': self._code.code,
            'code_name': self._code.name,
            'message': self._message,
            'severity': self._severity.value,
            'context': self._context.to_dict(),
        }
        
        if include_stack_trace and self._context.stack_trace:
            result['stack_trace'] = self._context.stack_trace
        
        if self._cause:
            result['cause'] = str(self._cause)
        
        return result

    def __str__(self) -> str:
        return f"[{self._code.code}] {self._message}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} code={self._code.name} severity={self._severity.value}>"


class ConfigurationError(WorkshopError):
    """配置错误"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.CONFIG_LOAD_ERROR,
        message: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if config_key:
            context['config_key'] = config_key
        super().__init__(code, message, context=context, **kwargs)


class PipelineError(WorkshopError):
    """管道错误"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.PIPELINE_EXECUTION_ERROR,
        message: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if pipeline_name:
            context['pipeline_name'] = pipeline_name
        if pipeline_stage:
            context['pipeline_stage'] = pipeline_stage
        super().__init__(code, message, context=context, **kwargs)


class ValidationError(WorkshopError):
    """验证错误"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        message: Optional[str] = None,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if field_name:
            context['field_name'] = field_name
        if field_value is not None:
            context['field_value'] = str(field_value)[:100]  # 限制长度
        super().__init__(code, message, context=context, **kwargs)


class HardwareError(WorkshopError):
    """硬件错误"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.DEVICE_ERROR,
        message: Optional[str] = None,
        device_id: Optional[str] = None,
        device_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if device_id:
            context['device_id'] = device_id
        if device_type:
            context['device_type'] = device_type
        super().__init__(code, message, context=context, **kwargs)


class DataIOError(WorkshopError):
    """数据IO错误"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.FILE_READ_ERROR,
        message: Optional[str] = None,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        super().__init__(code, message, context=context, **kwargs)


class SecurityError(WorkshopError):
    """安全错误"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.SECURITY_VIOLATION,
        message: Optional[str] = None,
        security_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if security_type:
            context['security_type'] = security_type
        super().__init__(code, message, severity=ErrorSeverity.CRITICAL, context=context, **kwargs)


class ErrorCodeManager:
    """
    错误码管理器 - V3.0
    
    管理错误码的注册、查询和统计
    """

    def __init__(self):
        self._error_stats: Dict[str, int] = {}
        self._error_history: List[WorkshopError] = []
        self._max_history = 1000

    def record_error(self, error: WorkshopError) -> None:
        """
        记录错误
        
        Args:
            error: 错误实例
        """
        error_name = error.code.name
        self._error_stats[error_name] = self._error_stats.get(error_name, 0) + 1
        
        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            'total_errors': sum(self._error_stats.values()),
            'by_code': dict(self._error_stats),
            'unique_codes': len(self._error_stats),
        }

    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        return [
            error.to_dict() 
            for error in self._error_history[-count:]
        ]

    def clear_stats(self) -> None:
        """清除统计"""
        self._error_stats.clear()
        self._error_history.clear()


# 全局错误码管理器实例
error_code_manager = ErrorCodeManager()
