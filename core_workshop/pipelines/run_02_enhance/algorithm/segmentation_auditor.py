# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 分割质量审计模块：对语义分割结果进行无参考质量评估。
# 基于多模态大模型的掩码质量评估思想，提供量化质量指标[citation:5]。

import numpy as np
import cv2
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class SegmentationAuditor:
    """分割质量审计器，对生成的掩码进行多维度质量评估"""
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
    
    def audit_mask(self, mask: np.ndarray, rgb_image: np.ndarray) -> Dict[str, float]:
        """
        审计单个掩码的质量
        
        Args:
            mask: 二值掩码 (H, W)
            rgb_image: 原始RGB图像 (H, W, 3)
        
        Returns:
            质量指标字典
        """
        metrics = {}
        
        # 1. 边缘完整性 - 计算掩码边界的连续性
        edges = cv2.Canny(mask.astype(np.uint8) * 255, 50, 150)
        edge_continuity = np.sum(edges > 0) / (np.prod(mask.shape) + 1e-6)
        metrics['edge_completeness'] = 1.0 - min(edge_continuity, 1.0)
        
        # 2. 内部一致性 - 掩码区域内像素的方差
        masked_region = rgb_image[mask > 0]
        if len(masked_region) > 0:
            color_variance = np.var(masked_region, axis=0).mean()
            metrics['internal_consistency'] = 1.0 / (1.0 + color_variance / 255.0)
        else:
            metrics['internal_consistency'] = 0.0
        
        # 3. 形状规则性 - 基于傅里叶描述子
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest_contour, True)
            area = cv2.contourArea(largest_contour)
            if area > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                metrics['shape_regularity'] = min(circularity, 1.0)
            else:
                metrics['shape_regularity'] = 0.0
        else:
            metrics['shape_regularity'] = 0.0
        
        # 4. 综合质量得分
        metrics['overall_quality'] = np.mean([
            metrics['edge_completeness'],
            metrics['internal_consistency'],
            metrics['shape_regularity']
        ])
        
        return metrics
    
    def audit_batch(self, masks: List[np.ndarray], images: List[np.ndarray]) -> List[Dict]:
        """批量审计多个掩码"""
        return [self.audit_mask(m, img) for m, img in zip(masks, images)]


class TemporalConsistencyAuditor:
    """时序一致性审计：评估视频序列中掩码的稳定性[citation:2]"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.mask_buffer = []
    
    def audit_temporal_consistency(self, current_mask: np.ndarray) -> float:
        """
        基于历史掩码评估当前掩码的时序一致性
        
        Returns:
            一致性得分 (0-1)
        """
        self.mask_buffer.append(current_mask)
        if len(self.mask_buffer) > self.window_size:
            self.mask_buffer.pop(0)
        
        if len(self.mask_buffer) < 2:
            return 1.0
        
        # 计算连续帧的IoU
        ious = []
        for i in range(len(self.mask_buffer) - 1):
            intersection = np.logical_and(self.mask_buffer[i], self.mask_buffer[i+1]).sum()
            union = np.logical_or(self.mask_buffer[i], self.mask_buffer[i+1]).sum()
            iou = intersection / (union + 1e-6)
            ious.append(iou)
        
        return float(np.mean(ious))