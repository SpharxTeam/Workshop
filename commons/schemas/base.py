"""
基础模式定义

提供模式验证的基础类和字段定义。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union


@dataclass
class ValidationError:
    """验证错误"""
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
    data: Optional[Dict[str, Any]] = None

    def add_error(
        self,
        field: str,
        message: str,
        code: str,
        value: Any = None,
        **constraints,
    ) -> None:
        self.errors.append(ValidationError(
            field=field,
            message=message,
            code=code,
            value=value,
            constraints=constraints,
        ))
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False


@dataclass
class Field:
    """字段定义"""

    name: str
    field_type: Type
    required: bool = True
    default: Any = None
    description: str = ""
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    choices: Optional[List[Any]] = None
    custom_validator: Optional[Callable[[Any], bool]] = None
    serializer: Optional[Callable[[Any], Any]] = None
    deserializer: Optional[Callable[[Any], Any]] = None

    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True)

        if value is None:
            if self.required:
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 是必需的",
                    code="REQUIRED_FIELD_MISSING",
                )
            return result

        if not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except (ValueError, TypeError):
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 类型错误，期望 {self.field_type.__name__}",
                    code="TYPE_ERROR",
                    value=value,
                )
                return result

        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 值不能小于 {self.min_value}",
                    code="MIN_VALUE_VIOLATION",
                    value=value,
                )

            if self.max_value is not None and value > self.max_value:
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 值不能大于 {self.max_value}",
                    code="MAX_VALUE_VIOLATION",
                    value=value,
                )

        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 长度不能少于 {self.min_length}",
                    code="MIN_LENGTH_VIOLATION",
                    value=value,
                )

            if self.max_length is not None and len(value) > self.max_length:
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 长度不能超过 {self.max_length}",
                    code="MAX_LENGTH_VIOLATION",
                    value=value,
                )

            if self.pattern:
                import re
                if not re.match(self.pattern, value):
                    result.add_error(
                        field=self.name,
                        message=f"字段 '{self.name}' 格式不正确",
                        code="PATTERN_MISMATCH",
                        value=value,
                    )

        if self.choices is not None and value not in self.choices:
            result.add_error(
                field=self.name,
                message=f"字段 '{self.name}' 值不在允许的选项中",
                code="INVALID_CHOICE",
                value=value,
            )

        if self.custom_validator:
            try:
                if not self.custom_validator(value):
                    result.add_error(
                        field=self.name,
                        message=f"字段 '{self.name}' 自定义验证失败",
                        code="CUSTOM_VALIDATION_FAILED",
                        value=value,
                    )
            except Exception as e:
                result.add_error(
                    field=self.name,
                    message=f"字段 '{self.name}' 验证异常: {str(e)}",
                    code="VALIDATION_EXCEPTION",
                    value=value,
                )

        return result

    def serialize(self, value: Any) -> Any:
        if self.serializer:
            return self.serializer(value)
        return value

    def deserialize(self, value: Any) -> Any:
        if self.deserializer:
            return self.deserializer(value)
        if isinstance(value, self.field_type):
            return value
        return self.field_type(value)


class BaseSchema(ABC):
    """基础模式抽象类"""

    def __init__(self):
        self._fields: Dict[str, Field] = {}
        self._setup_fields()

    @abstractmethod
    def _setup_fields(self) -> None:
        pass

    def add_field(self, field: Field) -> None:
        self._fields[field.name] = field

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, data={})

        for field_name, field_def in self._fields.items():
            value = data.get(field_name)
            field_result = field_def.validate(value)
            result.merge(field_result)

            if field_result.is_valid and value is not None:
                result.data[field_name] = value
            elif field_def.default is not None:
                result.data[field_name] = field_def.default

        return result

    def serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}

        for field_name, field_def in self._fields.items():
            if field_name in data:
                result[field_name] = field_def.serialize(data[field_name])
            elif field_def.default is not None:
                result[field_name] = field_def.default

        return result

    def deserialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}

        for field_name, field_def in self._fields.items():
            if field_name in data:
                result[field_name] = field_def.deserialize(data[field_name])

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fields": {
                name: {
                    "type": field.field_type.__name__,
                    "required": field.required,
                    "default": field.default,
                    "description": field.description,
                }
                for name, field in self._fields.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseSchema":
        schema = cls()
        for name, field_data in data.get("fields", {}).items():
            field_type = getattr(__builtins__, field_data.get("type", "str"), str)
            schema.add_field(Field(
                name=name,
                field_type=field_type,
                required=field_data.get("required", True),
                default=field_data.get("default"),
                description=field_data.get("description", ""),
            ))
        return schema
