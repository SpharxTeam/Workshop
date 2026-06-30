"""
Models and Exceptions - V3.0 (Unified ErrorCode v4.0)
=====================================================

数据模型和异常定义 - 第四套统一 ErrorCode 体系

本模块定义了 Workshop 的统一错误码体系，覆盖七大域：
    - 1xxx: 配置域 (Configuration)
    - 2xxx: Pipeline 域
    - 3xxx: 验证域 (Validation)
    - 4xxx: 硬件域 (Hardware)
    - 5xxx: IO 域
    - 6xxx: 模块域 (Module)
    - 7xxx: 安全域 (Security)
    - 8xxx: 网络/存储域 (Network/Storage)
    - 9xxx: 系统域 (System)

设计原则：
    1. 覆盖七大域，每域 1000 个码值，便于扩展
    2. SUCCESS=0 表示成功
    3. IntEnum 实现，支持数值比较
    4. 提供别名兼容 V2/V3 历史代码
    5. 语义化命名（VALIDATION_ERROR 而非 VALIDATION_FAILED）

参考:
    - AgentOS Error 模块
    - Deepness Abstractions
    - SpharxTools 工程标准规范手册 v24.3
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from enum import IntEnum
import traceback
from datetime import datetime


# =============================================================================
# 第四套统一 ErrorCode 体系
# =============================================================================

class ErrorCode(IntEnum):
    """
    统一错误码枚举 - 第四套 (v4.0)

    覆盖七大域，千位分段：
        - 1xxx: 配置域
        - 2xxx: Pipeline 域
        - 3xxx: 验证域
        - 4xxx: 硬件域
        - 5xxx: IO 域
        - 6xxx: 模块域
        - 7xxx: 安全域
        - 8xxx: 网络/存储域
        - 9xxx: 系统域

    兼容性：
        - V3 models.py: 保留所有原有 ErrorCode 名称（部分作为别名）
        - V2 runner_v2.py: 新增 V2 期望的 ErrorCode（MODULE_LOAD_FAILED 等）
        - test_v3_imports.py: 通过别名兼容部分期望值
    """

    SUCCESS = 0

    # === 1xxx: 配置域 (Configuration) ===
    CONFIG_NOT_FOUND = 1001
    CONFIG_PARSE_ERROR = 1002
    CONFIG_MISSING_REQUIRED = 1003
    CONFIG_INVALID_FORMAT = 1004
    CONFIG_FILE_NOT_FOUND = 1005  # 兼容 test_v3_imports.py 期望
    CONFIG_LOAD_ERROR = 1006      # 兼容 V3 models.py
    CONFIG_VALIDATION_ERROR = 1007  # 兼容 V3 models.py
    CONFIG_TYPE_ERROR = 1008       # 兼容 V3 models.py

    # === 2xxx: Pipeline 域 ===
    PIPELINE_INIT_FAILED = 2001
    PIPELINE_EXECUTION_FAILED = 2002
    PIPELINE_EXECUTION_ERROR = 2002  # 别名，兼容 V3 models.py
    PIPELINE_DEPENDENCY_MISSING = 2003
    PIPELINE_DEPENDENCY_ERROR = 2003  # 别名，兼容 V3 models.py
    PIPELINE_NOT_SUPPORTED = 2004
    PIPELINE_CANCELED = 2005
    PIPELINE_TIMEOUT = 2006
    PIPELINE_NOT_FOUND = 2007
    PIPELINE_INVALID_STATE = 2008
    ALGORITHM_EXECUTION_FAILED = 2009  # V2 runner_v2.py 期望

    # === 3xxx: 验证域 (Validation) ===
    VALIDATION_ERROR = 3001
    VALIDATION_FAILED = 3001  # 别名，兼容 V2 runner_v2.py
    INVALID_PARAMETER = 3002
    INVALID_DATA_FORMAT = 3003
    VALUE_OUT_OF_RANGE = 3004
    INVALID_INPUT = 3005  # 兼容 V3 models.py（移至验证域）
    PATH_TRAVERSAL_DETECTED = 3006
    SQL_INJECTION_DETECTED = 3007
    XSS_DETECTED = 3008
    INVALID_FILE_TYPE = 3009
    INVALID_FILE_SIZE = 3010

    # === 4xxx: 硬件域 (Hardware) ===
    HARDWARE_NOT_CONNECTED = 4001  # 兼容 test_v3_imports.py 期望
    HARDWARE_INIT_FAILED = 4002   # V2 runner_v2.py 期望
    DEVICE_NOT_FOUND = 4003
    DEVICE_NOT_READY = 4004
    DEVICE_CONNECTION_FAILED = 4005  # 兼容 V3 models.py
    CALIBRATION_FAILED = 4006
    DEVICE_TIMEOUT = 4007
    DEVICE_BUSY = 4008
    DEVICE_ERROR = 4009

    # === 5xxx: IO 域 ===
    IO_FILE_NOT_FOUND = 5001  # 兼容 test_v3_imports.py 期望
    FILE_NOT_FOUND = 5001  # 别名，兼容 V3 models.py
    IO_ERROR = 5002  # V2 runner_v2.py 期望
    IO_PERMISSION_DENIED = 5003
    PERMISSION_ERROR = 5003  # 别名，兼容 V3 models.py
    FILE_READ_ERROR = 5004
    FILE_WRITE_ERROR = 5005
    FILE_DELETE_ERROR = 5006
    DIRECTORY_NOT_FOUND = 5007
    READ_ERROR = 5004  # 别名，兼容 test_exceptions.py（READ_ERROR=6000 调整为 IO 域）

    # === 6xxx: 模块域 (Module) ===
    MODULE_LOAD_FAILED = 6001  # V2 runner_v2.py 期望
    MODULE_NOT_FOUND = 6002
    MODULE_DEPENDENCY_MISSING = 6003
    NOT_SUPPORTED = 6004  # V2 runner_v2.py 期望

    # === 7xxx: 安全域 (Security) ===
    SECURITY_VIOLATION = 7001
    AUTHENTICATION_FAILED = 7002
    AUTHORIZATION_FAILED = 7003
    TOKEN_EXPIRED = 7004
    INVALID_CREDENTIALS = 7005

    # === 8xxx: 网络/存储域 (Network/Storage) ===
    NETWORK_ERROR = 8001
    CONNECTION_REFUSED = 8002
    HOST_UNREACHABLE = 8003
    DNS_ERROR = 8004
    STORAGE_ERROR = 8101
    UPLOAD_FAILED = 8102
    DOWNLOAD_FAILED = 8103
    STORAGE_QUOTA_EXCEEDED = 8104

    # === 9xxx: 系统域 (System) ===
    UNKNOWN_ERROR = 9000
    OPERATION_TIMEOUT = 9001  # 兼容 V3 models.py
    TIMEOUT = 9001  # 别名
    RESOURCE_UNAVAILABLE = 9002
    PERMISSION_DENIED = 9003
    OUT_OF_MEMORY = 9004
    CANCELED = 9005
    NOT_IMPLEMENTED = 9006

    @property
    def code(self) -> int:
        """错误码数字（兼容 V3 调用方式 `ErrorCode.X.code`）"""
        return int(self)

    @property
    def message(self) -> str:
        """错误码中文描述"""
        return _ERROR_MESSAGES.get(int(self), "未知错误")

    def __str__(self) -> str:
        return f"[{int(self)}] {self.message}"


# =============================================================================
# 错误码中文描述映射表
# =============================================================================

_ERROR_MESSAGES: Dict[int, str] = {
    # 通用
    0: "成功",

    # 1xxx: 配置域
    1001: "配置不存在",
    1002: "配置解析错误",
    1003: "配置缺少必需项",
    1004: "配置格式无效",
    1005: "配置文件未找到",
    1006: "配置加载失败",
    1007: "配置验证失败",
    1008: "配置类型错误",

    # 2xxx: Pipeline 域
    2001: "管道初始化失败",
    2002: "管道执行失败",
    2003: "管道依赖缺失",
    2004: "管道不支持",
    2005: "管道已取消",
    2006: "管道超时",
    2007: "管道不存在",
    2008: "管道状态无效",
    2009: "算法执行失败",

    # 3xxx: 验证域
    3001: "验证失败",
    3002: "无效参数",
    3003: "无效数据格式",
    3004: "值超出范围",
    3005: "无效输入",
    3006: "检测到路径遍历攻击",
    3007: "检测到SQL注入",
    3008: "检测到XSS攻击",
    3009: "无效的文件类型",
    3010: "无效的文件大小",

    # 4xxx: 硬件域
    4001: "硬件未连接",
    4002: "硬件初始化失败",
    4003: "设备未找到",
    4004: "设备未就绪",
    4005: "设备连接失败",
    4006: "校准失败",
    4007: "设备超时",
    4008: "设备忙碌",
    4009: "设备错误",

    # 5xxx: IO 域
    5001: "文件未找到",
    5002: "IO 错误",
    5003: "权限错误",
    5004: "文件读取错误",
    5005: "文件写入错误",
    5006: "文件删除错误",
    5007: "目录不存在",

    # 6xxx: 模块域
    6001: "模块加载失败",
    6002: "模块未找到",
    6003: "模块依赖缺失",
    6004: "不支持的操作",

    # 7xxx: 安全域
    7001: "安全违规",
    7002: "认证失败",
    7003: "授权失败",
    7004: "令牌过期",
    7005: "无效凭据",

    # 8xxx: 网络/存储域
    8001: "网络错误",
    8002: "连接被拒绝",
    8003: "主机不可达",
    8004: "DNS解析错误",
    8101: "存储错误",
    8102: "上传失败",
    8103: "下载失败",
    8104: "存储配额超限",

    # 9xxx: 系统域
    9000: "未知错误",
    9001: "操作超时",
    9002: "资源不可用",
    9003: "权限拒绝",
    9004: "内存不足",
    9005: "操作已取消",
    9006: "未实现",
}


# =============================================================================
# ErrorSeverity - 错误严重级别
# =============================================================================

class ErrorSeverity(IntEnum):
    """
    错误严重级别 - IntEnum 实现

    主流值：
        - DEBUG = 0
        - INFO = 1
        - WARNING = 2
        - ERROR = 3
        - CRITICAL = 4

    兼容别名：
        - LOW = WARNING (2)
        - MEDIUM = ERROR (3)
        - HIGH = CRITICAL (4)
    """

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

    # 兼容别名（V2/V3 历史代码使用 LOW/MEDIUM/HIGH）
    LOW = WARNING       # test_exceptions.py 期望 LOW=1，统一为 WARNING=2
    MEDIUM = ERROR      # test_exceptions.py 期望 MEDIUM=2，统一为 ERROR=3
    HIGH = CRITICAL     # test_exceptions.py 期望 HIGH=3，统一为 CRITICAL=4

    @property
    def label(self) -> str:
        """严重级别中文标签"""
        return _SEVERITY_LABELS.get(int(self), "未知")

    def __str__(self) -> str:
        return self.name


_SEVERITY_LABELS: Dict[int, str] = {
    0: "调试",
    1: "信息",
    2: "警告",
    3: "错误",
    4: "严重",
}


# =============================================================================
# ErrorContext - 错误上下文
# =============================================================================

@dataclass
class ErrorContext:
    """
    错误上下文 - 记录错误发生时的环境信息

    用于在错误传播链中携带诊断信息，支持错误追溯和调试。
    """

    timestamp: datetime = field(default_factory=datetime.now)
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'module': self.module,
            'function': self.function,
            'line_number': self.line_number,
            'stack_trace': self.stack_trace,
            'additional_info': self.additional_info,
        }


# =============================================================================
# WorkshopError - 基础异常类
# =============================================================================

class WorkshopError(Exception):
    """
    Workshop 基础异常类 - V3.0

    所有 Workshop 异常的基类，提供统一的错误信息格式、上下文携带和序列化能力。

    Attributes:
        code: 错误码 (ErrorCode 枚举)
        message: 错误消息（默认使用错误码消息）
        severity: 严重级别 (ErrorSeverity 枚举)
        cause: 原始异常（可选）
        context: 错误上下文 (ErrorContext)

    Example:
        >>> raise PipelineError(
        ...     code=ErrorCode.PIPELINE_INIT_FAILED,
        ...     message="无法初始化 ingest pipeline",
        ...     pipeline_name="ingest"
        ... )
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
            'severity': self._severity.name,
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
        return f"<{self.__class__.__name__} code={self._code.name} severity={self._severity.name}>"


# =============================================================================
# 具体异常类 - 按域分类
# =============================================================================

class ConfigurationError(WorkshopError):
    """配置错误 - 1xxx 域"""

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
    """管道错误 - 2xxx 域"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.PIPELINE_EXECUTION_FAILED,
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
    """验证错误 - 3xxx 域"""

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
    """硬件错误 - 4xxx 域"""

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
    """数据IO错误 - 5xxx 域"""

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
    """安全错误 - 7xxx 域（默认 CRITICAL 级别）"""

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


# =============================================================================
# ErrorCodeManager - 错误码管理器
# =============================================================================

class ErrorCodeManager:
    """
    错误码管理器 - V3.0

    提供错误码的注册、查询、统计、域名分类和重试判断功能。

    职责：
        1. 错误统计：记录错误发生次数
        2. 错误历史：保留最近 N 条错误
        3. 域名分类：根据错误码判断所属域
        4. 重试判断：根据错误码判断是否可重试
    """

    # 域名映射：千位 -> 域名
    DOMAIN_MAP: Dict[int, str] = {
        0: "Success",
        1: "Configuration",
        2: "Pipeline",
        3: "Validation",
        4: "Hardware",
        5: "IO",
        6: "Module",
        7: "Security",
        8: "Network/Storage",
        9: "System",
    }

    # 可重试错误码集合
    RETRIABLE_CODES: frozenset = frozenset({
        ErrorCode.TIMEOUT,
        ErrorCode.OPERATION_TIMEOUT,
        ErrorCode.DEVICE_NOT_READY,
        ErrorCode.HARDWARE_NOT_CONNECTED,
        ErrorCode.DEVICE_BUSY,
        ErrorCode.RESOURCE_UNAVAILABLE,
        ErrorCode.PIPELINE_TIMEOUT,
        ErrorCode.DEVICE_TIMEOUT,
        ErrorCode.NETWORK_ERROR,
        ErrorCode.CONNECTION_REFUSED,
        ErrorCode.HOST_UNREACHABLE,
    })

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

    def get_domain(self, code: ErrorCode) -> str:
        """
        获取错误码所属域

        Args:
            code: 错误码

        Returns:
            str: 域名（如 "Configuration"、"Pipeline"）

        Example:
            >>> error_code_manager.get_domain(ErrorCode.CONFIG_NOT_FOUND)
            'Configuration'
        """
        domain_prefix = int(code) // 1000
        return self.DOMAIN_MAP.get(domain_prefix, "Unknown")

    def is_retriable(self, code: ErrorCode) -> bool:
        """
        判断错误码是否可重试

        Args:
            code: 错误码

        Returns:
            bool: True 表示可重试，False 表示不可重试

        Example:
            >>> error_code_manager.is_retriable(ErrorCode.TIMEOUT)
            True
            >>> error_code_manager.is_retriable(ErrorCode.CONFIG_NOT_FOUND)
            False
        """
        return code in self.RETRIABLE_CODES

    def get_all_error_codes(self) -> List[ErrorCode]:
        """获取所有已定义的错误码"""
        return list(ErrorCode)

    def get_codes_by_domain(self, domain_prefix: int) -> List[ErrorCode]:
        """
        获取指定域的所有错误码

        Args:
            domain_prefix: 域前缀（1-9）

        Returns:
            List[ErrorCode]: 该域的所有错误码
        """
        return [
            code for code in ErrorCode
            if int(code) // 1000 == domain_prefix
        ]


# 全局错误码管理器实例
error_code_manager = ErrorCodeManager()
