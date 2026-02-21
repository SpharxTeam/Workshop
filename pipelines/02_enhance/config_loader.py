#!/usr/bin/env python3
"""
配置加载工具：读取 YAML 配置文件，合并命令行参数。
"""
import os
import yaml
import argparse

DEFAULT_CONFIG_PATH = "/configs/pipeline_config.yaml"

def load_config(config_path=None, module_name=None):
    """
    加载配置文件，返回模块对应的配置字典。
    如果 config_path 为 None，尝试从环境变量 CONFIG_PATH 获取。
    如果文件不存在，返回空字典。
    """
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        full_config = yaml.safe_load(f)
    if module_name and module_name in full_config:
        return full_config[module_name]
    elif module_name:
        return {}
    else:
        return full_config