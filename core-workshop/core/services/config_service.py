"""
Configuration Service - V3.0
============================

配置管理服务 - 支持多级配置合并、热重载、验证

参考:
    - AgentOS Config 模块
    - Deepness ConfigService
"""

from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import os
import threading
import logging
from datetime import datetime

from core_workshop.core.abstractions.models import (
    ConfigurationError,
    ErrorCode,
)


class ConfigSource(Enum):
    """配置来源"""
    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    RUNTIME = "runtime"
    CLI = "cli"


@dataclass
class ConfigEntry:
    """配置项"""
    key: str
    value: Any
    source: ConfigSource
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """
    配置加载器
    
    支持多种配置格式: YAML, JSON, TOML, INI
    """

    SUPPORTED_FORMATS = {'.yaml', '.yml', '.json', '.toml', '.ini'}

    @staticmethod
    def load_file(file_path: Path) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            Dict: 配置字典
            
        Raises:
            ConfigurationError: 加载失败
        """
        if not file_path.exists():
            raise ConfigurationError(
                ErrorCode.CONFIG_NOT_FOUND,
                f"配置文件不存在: {file_path}",
                context={'file_path': str(file_path)}
            )

        suffix = file_path.suffix.lower()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if suffix in {'.yaml', '.yml'}:
                    return yaml.safe_load(f) or {}
                elif suffix == '.json':
                    return json.load(f)
                elif suffix == '.toml':
                    try:
                        import tomli
                        return tomli.load(f)
                    except ImportError:
                        raise ConfigurationError(
                            ErrorCode.CONFIG_PARSE_ERROR,
                            "TOML 支持需要安装 tomli 包",
                        )
                elif suffix == '.ini':
                    import configparser
                    config = configparser.ConfigParser()
                    config.read_file(f)
                    return {s: dict(config.items(s)) for s in config.sections()}
                else:
                    raise ConfigurationError(
                        ErrorCode.CONFIG_PARSE_ERROR,
                        f"不支持的配置格式: {suffix}",
                    )
        except Exception as e:
            raise ConfigurationError(
                ErrorCode.CONFIG_LOAD_ERROR,
                f"加载配置文件失败: {e}",
                context={'file_path': str(file_path)}
            )

    @staticmethod
    def load_directory(dir_path: Path, pattern: str = "*.yaml") -> Dict[str, Any]:
        """
        加载目录下所有配置文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件模式
            
        Returns:
            Dict: 合并后的配置
        """
        config = {}
        
        if not dir_path.exists():
            return config

        for file_path in sorted(dir_path.glob(pattern)):
            if file_path.is_file():
                file_config = ConfigLoader.load_file(file_path)
                config = ConfigLoader.merge_configs(config, file_config)

        return config

    @staticmethod
    def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并配置
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            Dict: 合并后的配置
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader.merge_configs(result[key], value)
            else:
                result[key] = value

        return result


class ConfigValidator:
    """
    配置验证器
    
    验证配置的完整性和正确性
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        初始化验证器
        
        Args:
            schema: 验证模式
        """
        self._schema = schema or {}
        self._validators: Dict[str, Callable] = {}

    def register_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """
        注册验证器
        
        Args:
            key: 配置键
            validator: 验证函数
        """
        self._validators[key] = validator

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """
        验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 错误消息列表
        """
        errors = []

        # 验证必需字段
        required_fields = self._schema.get('required', [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")

        # 验证字段类型
        field_types = self._schema.get('types', {})
        for field, expected_type in field_types.items():
            if field in config:
                if not isinstance(config[field], expected_type):
                    errors.append(
                        f"字段 {field} 类型错误: 期望 {expected_type.__name__}, "
                        f"实际 {type(config[field]).__name__}"
                    )

        # 运行自定义验证器
        for key, validator in self._validators.items():
            if key in config:
                try:
                    if not validator(config[key]):
                        errors.append(f"字段 {key} 验证失败")
                except Exception as e:
                    errors.append(f"字段 {key} 验证异常: {e}")

        return errors


class ConfigService:
    """
    配置管理服务 - V3.0
    
    特性:
    - 多级配置合并 (默认 < 文件 < 环境变量 < 运行时)
    - 热重载支持
    - 配置验证
    - 变更监听
    """

    DEFAULT_CONFIG_DIR = Path("config")

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        module_name: Optional[str] = None,
        auto_load: bool = True,
        enable_hot_reload: bool = False,
    ):
        """
        初始化配置服务
        
        Args:
            config_dir: 配置目录
            module_name: 模块名称
            auto_load: 是否自动加载
            enable_hot_reload: 是否启用热重载
        """
        self._config_dir = Path(config_dir) if config_dir else self.DEFAULT_CONFIG_DIR
        self._module_name = module_name
        self._enable_hot_reload = enable_hot_reload
        
        self._config: Dict[str, Any] = {}
        self._entries: Dict[str, ConfigEntry] = {}
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        self._lock = threading.RLock()
        self._logger = logging.getLogger("ConfigService")
        
        self._loader = ConfigLoader()
        self._validator = ConfigValidator()

        if auto_load:
            self.load()

    def load(self) -> None:
        """加载所有配置"""
        with self._lock:
            # 1. 加载默认配置
            self._load_defaults()

            # 2. 加载全局配置
            self._load_global_config()

            # 3. 加载模块配置
            if self._module_name:
                self._load_module_config()

            # 4. 加载环境变量
            self._load_environment()

            self._logger.info(
                f"配置加载完成: {len(self._config)} 项, "
                f"模块: {self._module_name or '全局'}"
            )

    def _load_defaults(self) -> None:
        """加载默认配置"""
        defaults = {
            'log_level': 'INFO',
            'max_workers': 4,
            'timeout': 300,
            'retry_count': 3,
            'enable_metrics': True,
            'enable_tracing': False,
        }
        
        for key, value in defaults.items():
            self._set(key, value, ConfigSource.DEFAULT)

    def _load_global_config(self) -> None:
        """加载全局配置"""
        global_config_path = self._config_dir / "global.yaml"
        
        if global_config_path.exists():
            config = self._loader.load_file(global_config_path)
            for key, value in self._flatten(config).items():
                self._set(key, value, ConfigSource.FILE)

    def _load_module_config(self) -> None:
        """加载模块配置"""
        module_config_path = self._config_dir / "modules" / f"{self._module_name}.yaml"
        
        if module_config_path.exists():
            config = self._loader.load_file(module_config_path)
            for key, value in self._flatten(config).items():
                self._set(key, value, ConfigSource.FILE)

    def _load_environment(self) -> None:
        """加载环境变量"""
        prefix = "WORKSHOP_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                self._set(config_key, self._parse_env_value(value), ConfigSource.ENVIRONMENT)

    def _parse_env_value(self, value: str) -> Any:
        """解析环境变量值"""
        # 尝试解析为 JSON
        try:
            return json.loads(value)
        except:
            pass

        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except:
            pass

        return value

    def _flatten(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """展平嵌套配置"""
        result = {}
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten(value, full_key))
            else:
                result[full_key] = value

        return result

    def _set(self, key: str, value: Any, source: ConfigSource) -> None:
        """设置配置项"""
        old_value = self._config.get(key)
        
        self._config[key] = value
        self._entries[key] = ConfigEntry(
            key=key,
            value=value,
            source=source,
        )

        # 触发监听器
        if old_value != value:
            self._notify_listeners(key, old_value, value)

    def get(
        self,
        key: str,
        default: Any = None,
        required: bool = False,
    ) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键 (支持点号分隔)
            default: 默认值
            required: 是否必需
            
        Returns:
            Any: 配置值
            
        Raises:
            ConfigurationError: 当 required=True 且键不存在时
        """
        with self._lock:
            if key not in self._config:
                if required:
                    raise ConfigurationError(
                        ErrorCode.CONFIG_NOT_FOUND,
                        f"必需的配置项不存在: {key}",
                        config_key=key,
                    )
                return default

            return self._config[key]

    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """
        设置运行时配置
        
        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化
        """
        with self._lock:
            self._set(key, value, ConfigSource.RUNTIME)

            if persist:
                self._persist_runtime_config()

    def _persist_runtime_config(self) -> None:
        """持久化运行时配置"""
        runtime_config = {
            k: e.value
            for k, e in self._entries.items()
            if e.source == ConfigSource.RUNTIME
        }
        
        if runtime_config:
            runtime_path = self._config_dir / "runtime.yaml"
            with open(runtime_path, 'w', encoding='utf-8') as f:
                yaml.dump(runtime_config, f)

    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return key in self._config

    def get_section(self, prefix: str) -> Dict[str, Any]:
        """
        获取配置段
        
        Args:
            prefix: 前缀
            
        Returns:
            Dict: 配置段
        """
        with self._lock:
            return {
                k: v
                for k, v in self._config.items()
                if k.startswith(prefix)
            }

    def reload(self) -> None:
        """重新加载配置"""
        self._logger.info("重新加载配置...")
        self.load()

    def add_listener(
        self,
        listener: Callable[[str, Any, Any], None]
    ) -> None:
        """
        添加配置变更监听器
        
        Args:
            listener: 监听函数 (key, old_value, new_value)
        """
        self._listeners.append(listener)

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                self._logger.error(f"配置监听器错误: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        with self._lock:
            return dict(self._config)

    def get_entry(self, key: str) -> Optional[ConfigEntry]:
        """获取配置项详情"""
        return self._entries.get(key)

    def __repr__(self) -> str:
        return f"<ConfigService module={self._module_name} entries={len(self._config)}>"
