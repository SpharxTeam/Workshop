#!/usr/bin/env python3
"""
配置加载器：统一加载 YAML 配置文件，支持模块名和全局配置。
"""
import os
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = "/app/common/configs"

def load_config(config_path=None, module_name=None, config_dir=DEFAULT_CONFIG_DIR):
    """
    统一配置加载入口。
    优先使用 config_path 直接加载文件，否则使用 module_name 加载组合配置（全局+模块）。
    """
    if config_path and os.path.exists(config_path):
        return _load_yaml(config_path)

    if module_name:
        # 加载全局配置
        global_config = _load_yaml(os.path.join(config_dir, "pipeline_config.yaml"))
        # 加载模块配置
        module_config = _load_yaml(os.path.join(config_dir, "modules", f"{module_name}.yaml"))
        # 合并（模块配置优先）
        merged = global_config.copy()
        _deep_merge(merged, module_config)
        return merged

    return {}

def _load_yaml(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}
    except Exception as e:
        logger.error(f"加载配置文件失败 {path}: {e}")
        return {}

def _deep_merge(base, override):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v