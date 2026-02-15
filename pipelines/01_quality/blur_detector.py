"""图像模糊检测器"""
import cv2
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BlurDetector:
    def __init__(self, threshold: float = 100.0):
        self.threshold = threshold
    
    def detect_blur(self, image: np.ndarray) -> Dict:
        """检测图像模糊程度"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            return {
                'laplacian_variance': float(laplacian_var),
                'is_blurry': laplacian_var < self.threshold,
                'quality_score': min(1.0, laplacian_var / self.threshold)
            }
        except Exception as e:
            logger.error(f"模糊检测失败: {e}")
            return {'error': str(e)}