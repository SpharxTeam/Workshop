"""
模型管理器：统一管理多个模型的加载和切换
"""
import logging
import yaml
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, config_path: str = "/app/configs/model_config.yaml"):
        self.config = self._load_config(config_path)
        self.adapters: Dict[str, Any] = {}
        self.active_adapter = None

    def _load_config(self, path: str) -> dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def load_adapter(self, model_name: str, version: str = "current"):
        """加载指定模型的适配器"""
        model_cfg = self.config['models'].get(model_name)
        if not model_cfg:
            raise ValueError(f"Model {model_name} not configured")

        if model_cfg['type'] == 'yolo':
            from .yolo_adapter import YOLOAdapter
            adapter = YOLOAdapter(model_cfg, version)
        else:
            raise ValueError(f"Unknown model type: {model_cfg['type']}")

        adapter.load()
        self.adapters[model_name] = adapter
        logger.info(f"Loaded {model_name} adapter (version: {version})")
        return adapter

    def get_adapter(self, model_name: str = None):
        if model_name is None:
            return self.active_adapter
        return self.adapters.get(model_name)

    def switch_to(self, model_name: str):
        if model_name not in self.adapters:
            self.load_adapter(model_name)
        self.active_adapter = self.adapters[model_name]
        logger.info(f"Switched active model to {model_name}")