"""
YOLO 模型适配器
"""
import os
import cv2
import numpy as np
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)

class YOLOAdapter:
    def __init__(self, config: dict, version: str = "current"):
        self.config = config
        self.version = version
        self.model = None
        self.model_path = self._resolve_weight_path()

    def _resolve_weight_path(self) -> str:
        base = self.config['weight_base']
        path = base.replace('{version}', self.version)
        if 'current' in path:
            real_path = os.path.realpath(path)
            logger.info(f"Resolved current symlink to: {real_path}")
            return real_path
        return path

    def load(self):
        logger.info(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)
        logger.info("YOLO model loaded successfully")

    def predict(self, image: np.ndarray, conf: float = 0.25):
        results = self.model(image, conf=conf, verbose=False)
        return results

    @property
    def names(self):
        return self.model.names