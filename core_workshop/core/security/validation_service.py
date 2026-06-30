"""
输入验证服务

提供统一的输入验证机制，支持字段验证、模式验证、路径验证等。
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Pattern, Type, Union


@dataclass
class ValidationError:
    """验证错误详情"""
    field: str
    message: str
    code: str
    value: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_data: Optional[Dict[str, Any]] = None

    def add_error(self, field: str, message: str, code: str, value: Any = None, **constraints) -> None:
        self.errors.append(ValidationError(
            field=field,
            message=message,
            code=code,
            value=value,
            constraints=constraints
        ))
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
        if other.sanitized_data and self.sanitized_data:
            self.sanitized_data.update(other.sanitized_data)


class BaseValidator(ABC):
    """验证器基类"""

    @abstractmethod
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        pass

    def __call__(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        return self.validate(value, context)


class FieldValidator(BaseValidator):
    """字段验证器"""

    DANGEROUS_PATTERNS = [
        re.compile(r'\.\./', re.IGNORECASE),
        re.compile(r'\.\.\\', re.IGNORECASE),
        re.compile(r'[<>"|?*]'),
        re.compile(r'[\x00-\x1f]'),
    ]

    SQL_INJECTION_PATTERNS = [
        re.compile(r"('|\")(;|--|\)|union|select|insert|delete|update|drop|exec)", re.IGNORECASE),
        re.compile(r"(union.+select|select.+from)", re.IGNORECASE),
        re.compile(r"(insert.+into|delete.+from)", re.IGNORECASE),
        re.compile(r"(drop\s+table|drop\s+database)", re.IGNORECASE),
    ]

    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>', re.IGNORECASE),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
    ]

    def __init__(
        self,
        field_name: str,
        required: bool = True,
        field_type: Optional[Type] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        pattern: Optional[Union[str, Pattern]] = None,
        choices: Optional[List[Any]] = None,
        custom_validator: Optional[Callable[[Any], bool]] = None,
        sanitizer: Optional[Callable[[Any], Any]] = None,
        allow_empty: bool = False,
    ):
        self.field_name = field_name
        self.required = required
        self.field_type = field_type
        self.min_length = min_length
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.choices = choices
        self.custom_validator = custom_validator
        self.sanitizer = sanitizer
        self.allow_empty = allow_empty

    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True, sanitized_data={})

        if value is None:
            if self.required:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 是必需的",
                    code="REQUIRED_FIELD_MISSING"
                )
            return result

        if not self.allow_empty and value == "":
            if self.required:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 不能为空",
                    code="EMPTY_FIELD"
                )
            return result

        if self.field_type and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except (ValueError, TypeError):
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 类型错误，期望 {self.field_type.__name__}",
                    code="TYPE_ERROR",
                    value=value
                )
                return result

        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 长度不能少于 {self.min_length}",
                    code="MIN_LENGTH_VIOLATION",
                    value=value,
                    min_length=self.min_length
                )

            if self.max_length is not None and len(value) > self.max_length:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 长度不能超过 {self.max_length}",
                    code="MAX_LENGTH_VIOLATION",
                    value=value,
                    max_length=self.max_length
                )

            if self.pattern and not self.pattern.match(value):
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 格式不正确",
                    code="PATTERN_MISMATCH",
                    value=value,
                    pattern=self.pattern.pattern
                )

        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 值不能小于 {self.min_value}",
                    code="MIN_VALUE_VIOLATION",
                    value=value,
                    min_value=self.min_value
                )

            if self.max_value is not None and value > self.max_value:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 值不能大于 {self.max_value}",
                    code="MAX_VALUE_VIOLATION",
                    value=value,
                    max_value=self.max_value
                )

        if self.choices is not None and value not in self.choices:
            result.add_error(
                field=self.field_name,
                message=f"字段 '{self.field_name}' 值不在允许的选项中",
                code="INVALID_CHOICE",
                value=value,
                choices=self.choices
            )

        if self.custom_validator:
            try:
                if not self.custom_validator(value):
                    result.add_error(
                        field=self.field_name,
                        message=f"字段 '{self.field_name}' 自定义验证失败",
                        code="CUSTOM_VALIDATION_FAILED",
                        value=value
                    )
            except Exception as e:
                result.add_error(
                    field=self.field_name,
                    message=f"字段 '{self.field_name}' 验证异常: {str(e)}",
                    code="VALIDATION_EXCEPTION",
                    value=value
                )

        if result.is_valid and self.sanitizer:
            try:
                value = self.sanitizer(value)
            except Exception as e:
                result.add_warning(f"字段 '{self.field_name}' 清理失败: {str(e)}")

        if result.is_valid:
            result.sanitized_data = {self.field_name: value}

        return result

    def check_sql_injection(self, value: str) -> bool:
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def check_xss(self, value: str) -> bool:
        for pattern in self.XSS_PATTERNS:
            if pattern.search(value):
                return True
        return False


class SchemaValidator(BaseValidator):
    """模式验证器"""

    def __init__(
        self,
        schema: Dict[str, FieldValidator],
        allow_extra_fields: bool = False,
        extra_fields_validator: Optional[Callable[[str, Any], bool]] = None,
    ):
        self.schema = schema
        self.allow_extra_fields = allow_extra_fields
        self.extra_fields_validator = extra_fields_validator

    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True, sanitized_data={})

        if not isinstance(value, dict):
            result.add_error(
                field="_schema",
                message="输入值必须是字典类型",
                code="SCHEMA_TYPE_ERROR",
                value=value
            )
            return result

        for field_name, validator in self.schema.items():
            field_value = value.get(field_name)
            field_result = validator.validate(field_value, context)
            result.merge(field_result)

        if not self.allow_extra_fields:
            schema_fields = set(self.schema.keys())
            input_fields = set(value.keys())
            extra_fields = input_fields - schema_fields

            if extra_fields:
                for extra_field in extra_fields:
                    if self.extra_fields_validator:
                        try:
                            if not self.extra_fields_validator(extra_field, value[extra_field]):
                                result.add_warning(f"未知字段 '{extra_field}' 被忽略")
                        except Exception as e:
                            result.add_warning(f"验证额外字段 '{extra_field}' 时出错: {str(e)}")
                    else:
                        result.add_warning(f"未知字段 '{extra_field}' 被忽略")

        if result.is_valid and result.sanitized_data:
            for key, val in value.items():
                if key not in result.sanitized_data and self.allow_extra_fields:
                    result.sanitized_data[key] = val

        return result


class PathValidator(BaseValidator):
    """路径验证器"""

    DANGEROUS_PATTERNS = [
        re.compile(r'\.\./', re.IGNORECASE),
        re.compile(r'\.\.\\', re.IGNORECASE),
        re.compile(r'[\x00-\x1f]'),
        re.compile(r'^/dev/'),
        re.compile(r'^/proc/'),
        re.compile(r'^/sys/'),
    ]

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        allow_absolute: bool = True,
        allow_relative: bool = True,
        allowed_extensions: Optional[List[str]] = None,
        max_path_length: int = 260,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_directory: bool = False,
    ):
        self.base_path = Path(base_path) if base_path else None
        self.allow_absolute = allow_absolute
        self.allow_relative = allow_relative
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else None
        self.max_path_length = max_path_length
        self.must_exist = must_exist
        self.must_be_file = must_be_file
        self.must_be_directory = must_be_directory

    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True, sanitized_data={})
        field_name = context.get("field_name", "path") if context else "path"

        if not isinstance(value, (str, Path)):
            result.add_error(
                field=field_name,
                message="路径必须是字符串或 Path 对象",
                code="PATH_TYPE_ERROR",
                value=value
            )
            return result

        path_str = str(value)

        if len(path_str) > self.max_path_length:
            result.add_error(
                field=field_name,
                message=f"路径长度超过最大限制 {self.max_path_length}",
                code="PATH_TOO_LONG",
                value=value
            )
            return result

        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(path_str):
                result.add_error(
                    field=field_name,
                    message="路径包含危险字符或模式",
                    code="DANGEROUS_PATH_PATTERN",
                    value=value
                )
                return result

        try:
            path = Path(path_str)
        except Exception as e:
            result.add_error(
                field=field_name,
                message=f"无效的路径格式: {str(e)}",
                code="INVALID_PATH_FORMAT",
                value=value
            )
            return result

        if path.is_absolute() and not self.allow_absolute:
            result.add_error(
                field=field_name,
                message="不允许使用绝对路径",
                code="ABSOLUTE_PATH_NOT_ALLOWED",
                value=value
            )
            return result

        if not path.is_absolute() and not self.allow_relative:
            result.add_error(
                field=field_name,
                message="不允许使用相对路径",
                code="RELATIVE_PATH_NOT_ALLOWED",
                value=value
            )
            return result

        if self.allowed_extensions:
            ext = path.suffix.lower()
            if ext and ext not in self.allowed_extensions:
                result.add_error(
                    field=field_name,
                    message=f"不允许的文件扩展名 '{ext}'",
                    code="INVALID_EXTENSION",
                    value=value,
                    allowed_extensions=self.allowed_extensions
                )
                return result

        if self.base_path:
            try:
                resolved_path = (self.base_path / path).resolve()
                base_resolved = self.base_path.resolve()
                try:
                    resolved_path.relative_to(base_resolved)
                except ValueError:
                    result.add_error(
                        field=field_name,
                        message="路径超出允许的基础目录范围",
                        code="PATH_TRAVERSAL_DETECTED",
                        value=value
                    )
                    return result
            except Exception as e:
                result.add_error(
                    field=field_name,
                    message=f"路径解析失败: {str(e)}",
                    code="PATH_RESOLUTION_ERROR",
                    value=value
                )
                return result

        if self.must_exist and not path.exists():
            result.add_error(
                field=field_name,
                message="路径不存在",
                code="PATH_NOT_FOUND",
                value=value
            )
            return result

        if self.must_be_file and path.exists() and not path.is_file():
            result.add_error(
                field=field_name,
                message="路径不是文件",
                code="NOT_A_FILE",
                value=value
            )
            return result

        if self.must_be_directory and path.exists() and not path.is_dir():
            result.add_error(
                field=field_name,
                message="路径不是目录",
                code="NOT_A_DIRECTORY",
                value=value
            )
            return result

        if result.is_valid:
            result.sanitized_data = {field_name: str(path)}

        return result


class FileValidator(BaseValidator):
    """文件验证器"""

    MAGIC_NUMBERS = {
        b'\xff\xd8\xff': 'jpeg',
        b'\x89PNG\r\n\x1a\n': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'%PDF': 'pdf',
        b'PK\x03\x04': 'zip',
        b'\x50\x4b\x03\x04': 'zip',
        b'Rar!': 'rar',
        b'\x1f\x8b': 'gzip',
        b'BZ': 'bzip2',
        b'\x00\x00\x01\x00': 'ico',
        b'BM': 'bmp',
        b'II*\x00': 'tiff',
        b'MM\x00*': 'tiff',
    }

    def __init__(
        self,
        max_size: Optional[int] = None,
        allowed_mime_types: Optional[List[str]] = None,
        allowed_extensions: Optional[List[str]] = None,
        check_content: bool = False,
        scan_for_malware: bool = False,
    ):
        self.max_size = max_size
        self.allowed_mime_types = allowed_mime_types
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else None
        self.check_content = check_content
        self.scan_for_malware = scan_for_malware

    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        field_name = context.get("field_name", "file") if context else "file"

        if isinstance(value, dict):
            file_path = value.get("path") or value.get("tmp_name")
            file_size = value.get("size")
            file_name = value.get("name") or value.get("filename")
        elif isinstance(value, (str, Path)):
            file_path = value
            file_size = None
            file_name = None
        else:
            result.add_error(
                field=field_name,
                message="无效的文件输入格式",
                code="INVALID_FILE_INPUT",
                value=type(value).__name__
            )
            return result

        if not file_path:
            result.add_error(
                field=field_name,
                message="缺少文件路径",
                code="FILE_PATH_MISSING"
            )
            return result

        path = Path(file_path)

        if not path.exists():
            result.add_error(
                field=field_name,
                message="文件不存在",
                code="FILE_NOT_FOUND",
                value=file_path
            )
            return result

        if not path.is_file():
            result.add_error(
                field=field_name,
                message="路径不是文件",
                code="NOT_A_FILE",
                value=file_path
            )
            return result

        if self.allowed_extensions:
            ext = path.suffix.lower()
            if ext and ext not in self.allowed_extensions:
                result.add_error(
                    field=field_name,
                    message=f"不允许的文件扩展名 '{ext}'",
                    code="INVALID_FILE_EXTENSION",
                    value=file_name or file_path,
                    allowed_extensions=self.allowed_extensions
                )
                return result

        actual_size = path.stat().st_size
        if file_size is not None and file_size != actual_size:
            result.add_warning(f"声明的文件大小 ({file_size}) 与实际大小 ({actual_size}) 不一致")

        if self.max_size is not None and actual_size > self.max_size:
            result.add_error(
                field=field_name,
                message=f"文件大小 ({actual_size}) 超过限制 ({self.max_size})",
                code="FILE_TOO_LARGE",
                value=file_name or file_path,
                actual_size=actual_size,
                max_size=self.max_size
            )
            return result

        if self.check_content:
            detected_type = self._detect_file_type(path)
            if detected_type and self.allowed_mime_types:
                if detected_type not in self.allowed_mime_types:
                    result.add_error(
                        field=field_name,
                        message=f"检测到的文件类型 '{detected_type}' 不在允许列表中",
                        code="INVALID_FILE_TYPE",
                        value=file_name or file_path,
                        detected_type=detected_type,
                        allowed_types=self.allowed_mime_types
                    )
                    return result

        return result

    def _detect_file_type(self, path: Path) -> Optional[str]:
        try:
            with open(path, 'rb') as f:
                header = f.read(16)

            for magic, file_type in self.MAGIC_NUMBERS.items():
                if header.startswith(magic):
                    return file_type

            return None
        except Exception:
            return None


class ValidationService:
    """验证服务"""

    _instance: Optional[ValidationService] = None

    def __new__(cls) -> ValidationService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._validators: Dict[str, BaseValidator] = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    def register_validator(self, name: str, validator: BaseValidator) -> None:
        self._validators[name] = validator

    def get_validator(self, name: str) -> Optional[BaseValidator]:
        return self._validators.get(name)

    def validate(
        self,
        data: Any,
        validator: Union[str, BaseValidator],
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        if isinstance(validator, str):
            v = self.get_validator(validator)
            if v is None:
                result = ValidationResult(is_valid=False)
                result.add_error(
                    field="_validator",
                    message=f"未找到验证器 '{validator}'",
                    code="VALIDATOR_NOT_FOUND"
                )
                return result
            validator = v

        return validator.validate(data, context)

    def validate_field(
        self,
        value: Any,
        field_name: str,
        **kwargs,
    ) -> ValidationResult:
        validator = FieldValidator(field_name=field_name, **kwargs)
        return validator.validate(value)

    def validate_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Dict[str, Any]],
        allow_extra_fields: bool = False,
    ) -> ValidationResult:
        validators = {}
        for field_name, config in schema.items():
            validators[field_name] = FieldValidator(field_name=field_name, **config)

        schema_validator = SchemaValidator(
            schema=validators,
            allow_extra_fields=allow_extra_fields
        )
        return schema_validator.validate(data)

    def validate_path(
        self,
        path: Union[str, Path],
        **kwargs,
    ) -> ValidationResult:
        validator = PathValidator(**kwargs)
        return validator.validate(path)

    def validate_file(
        self,
        file: Any,
        **kwargs,
    ) -> ValidationResult:
        validator = FileValidator(**kwargs)
        return validator.validate(file)

    def sanitize_string(self, value: str, max_length: Optional[int] = None) -> str:
        sanitized = value.strip()

        for pattern in FieldValidator.DANGEROUS_PATTERNS:
            sanitized = pattern.sub('', sanitized)

        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    def sanitize_html(self, value: str) -> str:
        import html
        return html.escape(value)

    def sanitize_sql(self, value: str) -> str:
        return value.replace("'", "''").replace("\\", "\\\\")


def get_validation_service() -> ValidationService:
    return ValidationService()
