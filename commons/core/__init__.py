"""
Core-Workshop V3.0 向后兼容层
================================

提供 V2.0 到 V3.0 的导入重定向，确保旧代码可以正常工作。

V2 兼容符号：
    - ConfigManager: ConfigService 的 V2 别名
    - setup_logging / get_logger: 从 logging_service 重导出
    - InputValidator: V2 兼容验证器（包装 V3 PathValidator / FileValidator）
    - error_code_manager: 从 models 重导出

迁移建议:
    请逐步将 `from common.core import ...` 替换为
    `from core_workshop.core.abstractions import ...` 等直接导入。
"""

import warnings

warnings.warn(
    "从 'common.core' 导入已废弃，请使用 'core_workshop.core' 代替",
    DeprecationWarning,
    stacklevel=2,
)

# =============================================================================
# V3 核心抽象层符号（直接重导出）
# =============================================================================
from core_workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    PipelineStatus,
    PipelineContext,
    PipelineConfig,
    IStorageBackend,
    LocalStorageBackend,
    FileMetadata,
    IOResult,
    IHardwareDevice,
    DeviceInfo,
    DeviceStatus,
    ErrorCode,
    ErrorSeverity,
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
    error_code_manager,
)

# =============================================================================
# V3 核心服务层符号（直接重导出）
# =============================================================================
from core_workshop.core.services import (
    ConfigService,
    LoggingService,
    MetricsService,
)
from core_workshop.core.services.logging_service import (
    setup_logging,
    get_logger,
)

# =============================================================================
# V3 安全服务层符号（直接重导出）
# =============================================================================
from core_workshop.core.security import (
    ValidationService,
    ValidationResult,
    SecurityService,
    SecurityContext,
)

# =============================================================================
# V3 可观测性层符号（直接重导出）
# =============================================================================
from core_workshop.core.observability import (
    TracingService,
    PerformanceMonitor,
    HealthService,
)


# =============================================================================
# V2 兼容包装类
# =============================================================================

class ConfigManager(ConfigService):
    """
    V2 兼容配置管理器

    V2 的 ConfigManager 与 V3 的 ConfigService 接口基本一致，
    此类作为别名保留，便于 V2 代码平滑迁移。
    """

    def __init__(self, config_dir=None, module_name=None, **kwargs):
        """V2 兼容构造函数"""
        super().__init__(
            config_dir=config_dir,
            module_name=module_name,
            auto_load=kwargs.get('auto_load', True),
            enable_hot_reload=kwargs.get('enable_hot_reload', False),
        )


class InputValidator:
    """
    V2 兼容输入验证器

    V2 API:
        validator = InputValidator()
        validation = validator.validate_all([
            (validator.validate_file_readable, (path,), {'name': 'input'}),
            (validator.validate_directory_writable, (dir,), {'name': 'output'})
        ])
        if not validation.valid:
            errors = validation.errors  # list of str

    V3 等价:
        使用 ValidationService + PathValidator / FileValidator
    """

    def __init__(self):
        from core_workshop.core.security.validation_service import (
            PathValidator,
            FileValidator,
            ValidationResult as V3ValidationResult,
        )
        self._path_validator = PathValidator
        self._file_validator = FileValidator
        self._v3_result_class = V3ValidationResult
        self._last_result = None

    def validate_file_readable(self, path, name='file'):
        """验证文件可读"""
        from pathlib import Path

        result = self._v3_result_class(is_valid=True, sanitized_data={})

        if not path:
            result.add_error(field=name, message=f"字段 '{name}' 不能为空", code="EMPTY_FIELD")
            return _V2ValidationResult(result)

        path_obj = Path(path)
        if not path_obj.exists():
            result.add_error(
                field=name, message=f"文件不存在: {path}", code="FILE_NOT_FOUND", value=path
            )
            return _V2ValidationResult(result)

        if not path_obj.is_file():
            result.add_error(
                field=name, message=f"路径不是文件: {path}", code="NOT_A_FILE", value=path
            )
            return _V2ValidationResult(result)

        if not path_obj.stat().st_size > 0:
            result.add_warning(f"文件为空: {path}")

        return _V2ValidationResult(result)

    def validate_directory_writable(self, path, name='directory'):
        """验证目录可写"""
        from pathlib import Path

        result = self._v3_result_class(is_valid=True, sanitized_data={})

        if not path:
            result.add_error(field=name, message=f"字段 '{name}' 不能为空", code="EMPTY_FIELD")
            return _V2ValidationResult(result)

        path_obj = Path(path)

        if path_obj.exists():
            if not path_obj.is_dir():
                result.add_error(
                    field=name, message=f"路径不是目录: {path}", code="NOT_A_DIRECTORY", value=path
                )
                return _V2ValidationResult(result)
        else:
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                result.add_error(
                    field=name,
                    message=f"目录不存在且无法创建: {path} ({e})",
                    code="DIR_CREATE_FAILED",
                    value=path,
                )
                return _V2ValidationResult(result)

        return _V2ValidationResult(result)

    def validate_all(self, tasks):
        """
        批量验证

        Args:
            tasks: [(callable, args, kwargs), ...]

        Returns:
            _V2ValidationResult: 合并后的验证结果
        """
        merged = self._v3_result_class(is_valid=True, sanitized_data={})

        for func, args, kwargs in tasks:
            result = func(*args, **kwargs)
            if hasattr(result, '_v3_result'):
                merged.merge(result._v3_result)
            else:
                if not getattr(result, 'is_valid', True):
                    merged.is_valid = False

        self._last_result = _V2ValidationResult(merged)
        return self._last_result


class _V2ValidationResult:
    """
    V2 兼容验证结果包装器

    V2 API:
        result.valid -> bool
        result.errors -> list of str
    """

    def __init__(self, v3_result):
        self._v3_result = v3_result

    @property
    def valid(self) -> bool:
        """V2 兼容属性（V3 使用 is_valid）"""
        return self._v3_result.is_valid

    @property
    def is_valid(self) -> bool:
        """V3 属性"""
        return self._v3_result.is_valid

    @property
    def errors(self):
        """V2 兼容：返回错误消息字符串列表（V3 返回 ValidationError 对象列表）"""
        return [e.message for e in self._v3_result.errors]

    @property
    def warnings(self):
        """警告消息列表"""
        return self._v3_result.warnings

    @property
    def sanitized_data(self):
        """清理后的数据"""
        return self._v3_result.sanitized_data

    def add_error(self, field, message, code, value=None, **constraints):
        """添加错误"""
        self._v3_result.add_error(field, message, code, value, **constraints)

    def add_warning(self, message):
        """添加警告"""
        self._v3_result.add_warning(message)

    def merge(self, other):
        """合并另一个结果"""
        if hasattr(other, '_v3_result'):
            self._v3_result.merge(other._v3_result)
        else:
            self._v3_result.merge(other)


# =============================================================================
# 导出清单
# =============================================================================

__all__ = [
    # V3 核心抽象
    "BasePipeline",
    "PipelineResult",
    "PipelineStatus",
    "PipelineContext",
    "PipelineConfig",
    "IStorageBackend",
    "LocalStorageBackend",
    "FileMetadata",
    "IOResult",
    "IHardwareDevice",
    "DeviceInfo",
    "DeviceStatus",
    "ErrorCode",
    "ErrorSeverity",
    "WorkshopError",
    "ConfigurationError",
    "PipelineError",
    "ValidationError",
    "HardwareError",
    "DataIOError",
    "error_code_manager",
    # V3 核心服务
    "ConfigService",
    "LoggingService",
    "MetricsService",
    "setup_logging",
    "get_logger",
    # V3 安全服务
    "ValidationService",
    "ValidationResult",
    "SecurityService",
    "SecurityContext",
    # V3 可观测性
    "TracingService",
    "PerformanceMonitor",
    "HealthService",
    # V2 兼容包装
    "ConfigManager",
    "InputValidator",
]
