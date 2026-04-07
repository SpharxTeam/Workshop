# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 配置管理器 - 参考 AgentOS BaseManager 和配置管理模式设计
# 遵循 ARCHITECTURAL_PRINCIPLES.md E-3 (资源确定性)

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from copy import deepcopy

from .exceptions import (
    WorkshopError,
    ConfigurationError,
    ErrorCode,
    error_code_manager
)


class ConfigManager:
    """
    统一配置管理器 - 参考 AgentOS Manager 模式
    
    特性：
    - 支持多层级配置合并（全局 > 模块 > 运行时）
    - 配置验证和类型检查
    - 配置变更监听
    - 热重载支持
    
    Example:
        >>> config = ConfigManager(config_dir="/app/config")
        >>> config.load_module_config("01_quality")
        >>> blur_threshold = config.get("blur_threshold", default=100)
    """
    
    DEFAULT_CONFIG_DIR = "/app/common/configs"
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        module_name: Optional[str] = None,
        auto_load: bool = True
    ):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录路径
            module_name: 模块名称（用于加载模块特定配置）
            auto_load: 是否自动加载配置
        """
        self._config_dir = Path(config_dir or self.DEFAULT_CONFIG_DIR)
        self._module_name = module_name
        self._logger = logging.getLogger(f"ConfigManager.{module_name or 'global'}")
        self._config: Dict[str, Any] = {}
        self._global_config: Dict[str, Any] = {}
        self._module_config: Dict[str, Any] = {}
        self._runtime_overrides: Dict[str, Any] = {}
        self._config_schema: Optional[Dict[str, Any]] = None
        self._loaded = False
        
        if auto_load:
            self.load()
    
    def load(self) -> None:
        """加载配置"""
        try:
            self._load_global_config()
            
            if self._module_name:
                self._load_module_config(self._module_name)
            
            self._merge_configs()
            self._loaded = True
            self._logger.info(f"配置加载成功: {self._module_name or 'global'}")
            
        except Exception as e:
            error_code_manager.record_error(
                ConfigurationError(ErrorCode.CONFIG_LOAD_ERROR, str(e), cause=e)
            )
            raise ConfigurationError(
                ErrorCode.CONFIG_LOAD_ERROR,
                f"配置加载失败: {e}",
                cause=e
            )
    
    def load_from_file(self, config_path: str) -> None:
        """
        从指定文件加载配置
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(
                ErrorCode.CONFIG_NOT_FOUND,
                f"配置文件不存在: {config_path}"
            )
        
        try:
            self._config = self._load_yaml_or_json(path)
            self._loaded = True
            self._logger.info(f"从文件加载配置成功: {config_path}")
        except Exception as e:
            raise ConfigurationError(
                ErrorCode.CONFIG_PARSE_ERROR,
                f"解析配置文件失败: {e}",
                cause=e
            )
    
    def _load_global_config(self) -> None:
        """加载全局配置"""
        pipeline_config_path = self._config_dir / "pipeline_config.yaml"
        if pipeline_config_path.exists():
            self._global_config = self._load_yaml_or_json(pipeline_config_path)
            self._logger.debug(f"加载全局配置: {pipeline_config_path}")
    
    def _load_module_config(self, module_name: str) -> None:
        """
        加载模块配置
        
        Args:
            module_name: 模块名称
        """
        module_config_path = self._config_dir / "modules" / f"{module_name}.yaml"
        if module_config_path.exists():
            self._module_config = self._load_yaml_or_json(module_config_path)
            self._logger.debug(f"加载模块配置: {module_config_path}")
    
    def _merge_configs(self) -> None:
        """合并配置（优先级：运行时覆盖 > 模块配置 > 全局配置）"""
        merged = deepcopy(self._global_config)
        
        if self._module_config:
            self._deep_merge(merged, self._module_config)
        
        if self._runtime_overrides:
            self._deep_merge(merged, self._runtime_overrides)
        
        self._config = merged
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> None:
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value
    
    @staticmethod
    def _load_yaml_or_json(path: Path) -> Dict[str, Any]:
        """
        加载 YAML 或 JSON 文件
        
        Args:
            path: 文件路径
            
        Returns:
            解析后的字典
        """
        suffix = path.suffix.lower()
        
        with open(path, 'r', encoding='utf-8') as f:
            if suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif suffix == '.json':
                data = json.load(f)
            else:
                raise ConfigurationError(
                    ErrorCode.CONFIG_INVALID_FORMAT,
                    f"不支持的配置文件格式: {suffix}"
                )
        
        return data if data is not None else {}
    
    def get(
        self,
        key: str,
        default: Any = None,
        required: bool = False,
        expected_type: Optional[type] = None
    ) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套访问，如 "quality.blur_threshold"）
            default: 默认值
            required: 是否为必填项
            expected_type: 期望的类型
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                if required:
                    raise ConfigurationError(
                        ErrorCode.CONFIG_MISSING_REQUIRED,
                        f"缺少必需的配置项: {key}"
                    )
                return default
        
        if expected_type is not None and value is not None:
            if not isinstance(value, expected_type):
                try:
                    value = expected_type(value)
                except (ValueError, TypeError):
                    raise ConfigurationError(
                        ErrorCode.CONFIG_VALIDATION_ERROR,
                        f"配置项 '{key}' 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
                    )
        
        return value
    
    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """
        设置配置值（运行时覆盖）
        
        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化到文件
        """
        keys = key.split('.')
        target = self._runtime_overrides
        
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
        self._merge_configs()
        
        self._logger.debug(f"更新配置: {key} = {value}")
        
        if persist:
            self._persist_runtime_overrides()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            配置段字典
        """
        return self.get(section, default={})
    
    def validate_schema(self, schema: Dict[str, Any]) -> List[str]:
        """
        根据 Schema 验证配置
        
        Args:
            schema: 配置 Schema 定义
            
        Returns:
            验证错误列表
        """
        errors = []
        
        for key, rules in schema.items():
            value = self.get(key)
            
            if rules.get('required', False) and value is None:
                errors.append(f"缺少必需字段: {key}")
                continue
            
            if value is not None:
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"字段 '{key}' 类型错误: 期望 {expected_type.__name__}")
                
                min_val = rules.get('min')
                max_val = rules.get('max')
                if isinstance(value, (int, float)):
                    if min_val is not None and value < min_val:
                        errors.append(f"字段 '{key}' 值 {value} 小于最小值 {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"字段 '{key}' 值 {value} 大于最大值 {max_val}")
                
                allowed_values = rules.get('allowed')
                if allowed_values and value not in allowed_values:
                    errors.append(f"字段 '{key}' 值 {value} 不在允许值列表中: {allowed_values}")
        
        return errors
    
    def reload(self) -> None:
        """重新加载配置"""
        self._logger.info("重新加载配置...")
        self.load()
    
    def _persist_runtime_overrides(self) -> None:
        """持久化运行时覆盖"""
        overrides_path = self._config_dir / "runtime_overrides.yaml"
        try:
            with open(overrides_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._runtime_overrides, f, default_flow_style=False, allow_unicode=True)
            self._logger.info(f"运行时配置已持久化: {overrides_path}")
        except Exception as e:
            self._logger.error(f"持久化配置失败: {e}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()
    
    @property
    def is_loaded(self) -> bool:
        """配置是否已加载"""
        return self._loaded
    
    @property
    def config_dir(self) -> Path:
        """获取配置目录"""
        return self._config_dir
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            'config': self._config,
            'global_config': self._global_config,
            'module_config': self._module_config,
            'runtime_overrides': self._runtime_overrides,
            'loaded': self._loaded
        }
    
    def __repr__(self) -> str:
        return (
            f"ConfigManager("
            f"module={self._module_name!r}, "
            f"loaded={self._loaded})"
        )


# 向后兼容的便捷函数
def load_config(
    config_path: Optional[str] = None,
    module_name: Optional[str] = None,
    config_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：加载配置
    
    Args:
        config_path: 配置文件路径
        module_name: 模块名称
        config_dir: 配置目录
        
    Returns:
        配置字典
    """
    manager = ConfigManager(
        config_dir=config_dir,
        module_name=module_name,
        auto_load=False
    )
    
    if config_path:
        manager.load_from_file(config_path)
    else:
        manager.load()
    
    return manager.config


__all__ = ['ConfigManager', 'load_config']
