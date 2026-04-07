# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 输入验证器 - 参考 AgentOS InputValidator 和安全穹顶设计
# 提供参数验证和类型检查功能

import re
import os
from pathlib import Path
from typing import Any, Optional, Union, List, Type
from dataclasses import dataclass

from .exceptions import ValidationError, ErrorCode


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    value: Any = None
    
    @classmethod
    def success(cls, value: Any = None) -> 'ValidationResult':
        return cls(valid=True, errors=[], warnings=[], value=value)
    
    @classmethod
    def failure(cls, errors: List[str], warnings: List[str] = None) -> 'ValidationResult':
        return cls(valid=False, errors=errors, warnings=warnings or [])


class InputValidator:
    """
    输入验证器 - 参考 AgentOS 安全机制设计
    
    提供全面的输入验证功能：
    - 类型检查
    - 范围验证
    - 正则表达式匹配
    - 文件/路径安全性检查
    - 自定义验证规则
    
    Example:
        >>> validator = InputValidator()
        >>> result = validator.validate_path("/app/data/input", must_exist=True)
        >>> if not result.valid:
        ...     raise ValidationError(result.errors)
    """
    
    # 常用的正则表达式模式
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'filename': r'^[a-zA-Z0-9_\-\.]+$',
        'module_name': r'^[a-z][a-z0-9_]*$',
        'semver': r'^\d+\.\d+\.\d+$',
    }
    
    def __init__(self):
        self._custom_rules = {}
    
    def validate_required(self, value: Any, name: str = "value") -> ValidationResult:
        """
        验证必填参数
        
        Args:
            value: 要验证的值
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        if value is None:
            return ValidationResult.failure([f"'{name}' 是必填参数"])
        
        if isinstance(value, str) and not value.strip():
            return ValidationResult.failure([f"'{name}' 不能为空字符串"])
        
        return ValidationResult.success(value)
    
    def validate_type(
        self,
        value: Any,
        expected_type: Type,
        name: str = "value",
        allow_none: bool = False
    ) -> ValidationResult:
        """
        验证类型
        
        Args:
            value: 要验证的值
            expected_type: 期望的类型
            name: 参数名称
            allow_none: 是否允许 None 值
            
        Returns:
            ValidationResult: 验证结果
        """
        if allow_none and value is None:
            return ValidationResult.success(value)
        
        if not isinstance(value, expected_type):
            type_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)
            actual_name = type(value).__name__
            return ValidationResult.failure([
                f"'{name}' 类型错误: 期望 {type_name}, 实际 {actual_name}"
            ])
        
        return ValidationResult.success(value)
    
    def validate_range(
        self,
        value: Union[int, float],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        name: str = "value"
    ) -> ValidationResult:
        """
        验证数值范围
        
        Args:
            value: 要验证的数值
            min_val: 最小值
            max_val: 最大值
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        
        if min_val is not None and value < min_val:
            errors.append(f"'{name}' 值 {value} 小于最小允许值 {min_val}")
        
        if max_val is not None and value > max_val:
            errors.append(f"'{name}' 值 {value} 大于最大允许值 {max_val}")
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success(value)
    
    def validate_string_length(
        self,
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        name: str = "value"
    ) -> ValidationResult:
        """
        验证字符串长度
        
        Args:
            value: 字符串值
            min_length: 最小长度
            max_length: 最大长度
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        length = len(value)
        errors = []
        
        if min_length is not None and length < min_length:
            errors.append(f"'{name}' 长度 {length} 小于最小长度 {min_length}")
        
        if max_length is not None and length > max_length:
            errors.append(f"'{name}' 长度 {length} 大于最大长度 {max_length}")
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success(value)
    
    def validate_regex(
        self,
        value: str,
        pattern: str,
        name: str = "value",
        pattern_name: Optional[str] = None
    ) -> ValidationResult:
        """
        使用正则表达式验证
        
        Args:
            value: 字符串值
            pattern: 正则表达式
            name: 参数名称
            pattern_name: 模式名称（用于错误消息）
            
        Returns:
            ValidationResult: 验证结果
        """
        if not re.match(pattern, value):
            desc = pattern_name or pattern
            return ValidationResult.failure([
                f"'{name}' 不符合格式要求: {desc}"
            ])
        
        return ValidationResult.success(value)
    
    def validate_pattern(self, value: str, pattern_name: str, name: str = "value") -> ValidationResult:
        """
        使用预定义模式验证
        
        Args:
            value: 字符串值
            pattern_name: 预定义模式名称
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        pattern = self.PATTERNS.get(pattern_name)
        if not pattern:
            return ValidationResult.failure([f"未知的模式名称: {pattern_name}"])
        
        return self.validate_regex(value, pattern, name, pattern_name)
    
    def validate_path(
        self,
        path: str,
        must_exist: bool = False,
        should_be_file: bool = False,
        should_be_dir: bool = False,
        allowed_extensions: Optional[List[str]] = None,
        name: str = "path"
    ) -> ValidationResult:
        """
        验证路径安全性 - 参考 AgentOS 安全穹顶 L3 (输入净化)
        
        Args:
            path: 路径字符串
            must_exist: 路径是否必须存在
            should_be_file: 是否必须是文件
            should_be_dir: 是否必须是目录
            allowed_extensions: 允许的扩展名列表
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        # 安全性检查：防止路径遍历攻击
        if '..' in path:
            errors.append(f"'{name}' 包含不安全的路径遍历序列 '..'")
        
        # 检查是否存在
        path_obj = Path(path)
        if must_exist and not path_obj.exists():
            errors.append(f"'{name}' 路径不存在: {path}")
        
        if path_obj.exists():
            if should_be_file and not path_obj.is_file():
                errors.append(f"'{name}' 应该是文件但实际是目录: {path}")
            
            if should_be_dir and not path_obj.is_dir():
                errors.append(f"'{name}' 应该是目录但实际是文件: {path}")
            
            # 检查扩展名
            if allowed_extensions and path_obj.is_file():
                ext = path_obj.suffix.lower()
                if ext not in allowed_extensions:
                    warnings.append(
                        f"'{name}' 扩展名 '{ext}' 不在允许列表中: {allowed_extensions}"
                    )
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        
        return ValidationResult.success(path, warnings=warnings)
    
    def validate_file_readable(self, file_path: str, name: str = "file") -> ValidationResult:
        """
        验证文件是否可读
        
        Args:
            file_path: 文件路径
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        path_result = self.validate_path(file_path, must_exist=True, should_be_file=True, name=name)
        if not path_result.valid:
            return path_result
        
        if not os.access(file_path, os.R_OK):
            return ValidationResult.failure([f"'{name}' 文件不可读: {file_path}"])
        
        return ValidationResult.success(file_path)
    
    def validate_directory_writable(self, dir_path: str, name: str = "directory") -> ValidationResult:
        """
        验证目录是否可写
        
        Args:
            dir_path: 目录路径
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        path_obj = Path(dir_path)
        
        if path_obj.exists():
            if not path_obj.is_dir():
                return ValidationResult.failure([f"'{name}' 不是目录: {dir_path}"])
            if not os.access(dir_path, os.W_OK):
                return ValidationResult.failure([f"'{name}' 目录不可写: {dir_path}"])
        else:
            # 尝试创建目录
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return ValidationResult.failure([f"'{name}' 无法创建目录: {dir_path} ({e})"])
        
        return ValidationResult.success(dir_path)
    
    def validate_list_items(
        self,
        items: List[Any],
        item_validator=None,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        name: str = "items"
    ) -> ValidationResult:
        """
        验证列表项
        
        Args:
            items: 列表
            item_validator: 单项验证器（可调用对象）
            min_items: 最少项数
            max_items: 最多项数
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        
        if min_items is not None and len(items) < min_items:
            errors.append(f"'{name}' 项数 {len(items)} 少于最少项数 {min_items}")
        
        if max_items is not None and len(items) > max_items:
            errors.append(f"'{name}' 项数 {len(items)} 多于最多项数 {max_items}")
        
        if item_validator and errors:
            for idx, item in enumerate(items):
                result = item_validator(item)
                if not result.valid:
                    errors.extend([f"{name}[{idx}]: {err}" for err in result.errors])
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success(items)
    
    def add_custom_rule(self, name: str, rule_func) -> None:
        """
        添加自定义验证规则
        
        Args:
            name: 规则名称
            rule_func: 验证函数（接受 value，返回 ValidationResult）
        """
        self._custom_rules[name] = rule_func
    
    def validate_custom(self, value: Any, rule_name: str, name: str = "value") -> ValidationResult:
        """
        使用自定义规则验证
        
        Args:
            value: 要验证的值
            rule_name: 规则名称
            name: 参数名称
            
        Returns:
            ValidationResult: 验证结果
        """
        rule_func = self._custom_rules.get(rule_name)
        if not rule_func:
            return ValidationResult.failure([f"未知的自定义规则: {rule_name}"])
        
        return rule_func(value, name)
    
    def validate_all(self, validations: List[tuple]) -> ValidationResult:
        """
        批量验证
        
        Args:
            validations: 验证元组列表 [(validator_method, args, kwargs), ...]
            
        Returns:
            ValidationResult: 合并后的验证结果
        """
        all_errors = []
        all_warnings = []
        
        for item in validations:
            method, args, kwargs = item
            result = method(*args, **kwargs)
            if not result.valid:
                all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        if all_errors:
            return ValidationResult.failure(all_errors, all_warnings)
        
        return ValidationResult.success(warnings=all_warnings)


__all__ = ['InputValidator', 'ValidationResult']
