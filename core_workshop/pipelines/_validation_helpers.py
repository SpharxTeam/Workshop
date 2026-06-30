"""Pipeline 验证工具 — V3 验证器便捷封装

提供 V2 InputValidator 的 V3 等价功能,供 runner_v2.py 迁移使用。

本模块封装 core_workshop.core.security.validation_service 中的
PathValidator / FileValidator / FieldValidator,提供与 V2 InputValidator
方法签名兼容的便捷函数。

迁移指南:
    V2: validator = InputValidator()
        validation = validator.validate_all([...])
        if not validation.valid: errors = validation.errors

    V3: from core_workshop.pipelines._validation_helpers import (
            validate_file_readable, validate_directory_writable,
            validate_path_exists_dir, validate_range, collect_errors,
        )
        errors = collect_errors(
            validate_file_readable(input_path, 'input'),
            validate_directory_writable(output_dir, 'output'),
        )
        if errors: ...
"""

from pathlib import Path
from typing import Any, List, Union

from core_workshop.core.security.validation_service import (
    FieldValidator,
    FileValidator,
    PathValidator,
    ValidationResult,
)


def validate_file_readable(path: str, name: str = "file") -> ValidationResult:
    """验证文件可读(存在且是文件)

    V3 等价于 V2 InputValidator.validate_file_readable
    """
    return FileValidator().validate(path)


def validate_directory_writable(path: str, name: str = "directory") -> ValidationResult:
    """验证目录可写(不存在则创建)

    V3 等价于 V2 InputValidator.validate_directory_writable

    注意:V3 PathValidator 仅验证不创建,此函数保留 V2 行为(自动创建目录)
    """
    result = ValidationResult(is_valid=True, sanitized_data={})
    path_obj = Path(path)

    if not path_obj.exists():
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            result.add_error(
                field=name,
                message=f"目录不存在且无法创建: {path} ({e})",
                code="DIR_CREATE_FAILED",
                value=path,
            )
    elif not path_obj.is_dir():
        result.add_error(
            field=name,
            message=f"路径不是目录: {path}",
            code="NOT_A_DIRECTORY",
            value=path,
        )

    return result


def validate_path_exists_dir(path: str, name: str = "path") -> ValidationResult:
    """验证路径存在且是目录

    V3 等价于 V2 InputValidator.validate_path(path, must_exist=True, should_be_dir=True)
    """
    return PathValidator(must_exist=True, must_be_directory=True).validate(path)


def validate_range(
    value: Any,
    min_val: Union[int, float, None] = None,
    max_val: Union[int, float, None] = None,
    name: str = "value",
) -> ValidationResult:
    """验证数值在指定范围内

    V3 等价于 V2 InputValidator.validate_range
    """
    return FieldValidator(
        field_name=name,
        min_value=min_val,
        max_value=max_val,
    ).validate(value)


def collect_errors(*results: ValidationResult) -> List[str]:
    """收集所有验证结果的错误消息

    Args:
        *results: 多个 ValidationResult 对象

    Returns:
        List[str]: 所有错误消息字符串列表(空列表表示全部通过)
    """
    errors: List[str] = []
    for r in results:
        if not r.is_valid:
            errors.extend(e.message for e in r.errors)
    return errors


__all__ = [
    "validate_file_readable",
    "validate_directory_writable",
    "validate_path_exists_dir",
    "validate_range",
    "collect_errors",
]
