"""
数据预处理模块
负责原始数据的清洗、格式转换和元数据提取
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import exifread
import json

class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff']
    
    def preprocess_scene(self, scene_path: Path) -> Dict:
        """
        预处理整个场景
        
        Args:
            scene_path: 场景路径
            
        Returns:
            预处理结果字典
        """
        results = {
            'scene_id': scene_path.name,
            'images': [],
            'metadata': {},
            'issues': []
        }
        
        # 检查目录结构
        images_dir = scene_path / 'images'
        if not images_dir.exists():
            results['issues'].append(f"图像目录不存在: {images_dir}")
            return results
        
        # 处理每张图像
        image_files = list(images_dir.glob('*'))
        image_files = [f for f in image_files if f.suffix.lower() in self.supported_formats]
        
        for img_path in image_files:
            try:
                img_result = self._preprocess_image(img_path, scene_path)
                results['images'].append(img_result)
            except Exception as e:
                results['issues'].append(f"处理图像失败 {img_path.name}: {str(e)}")
        
        # 提取场景元数据
        metadata_file = scene_path / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                results['metadata'] = json.load(f)
        
        return results
    
    def _preprocess_image(self, image_path: Path, scene_path: Path) -> Dict:
        """预处理单张图像"""
        result = {
            'filename': image_path.name,
            'path': str(image_path.relative_to(scene_path)),
            'original_size': None,
            'processed_size': None,
            'exif_data': {},
            'checksum': None,
            'issues': []
        }
        
        # 读取图像
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        result['original_size'] = {
            'width': img.shape[1],
            'height': img.shape[0],
            'channels': img.shape[2] if len(img.shape) > 2 else 1
        }
        
        # 检查图像质量
        quality_issues = self._check_image_quality(img, image_path)
        result['issues'].extend(quality_issues)
        
        # 提取EXIF数据
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                result['exif_data'] = {
                    str(tag): str(value) 
                    for tag, value in tags.items() 
                    if not tag.startswith('Thumbnail')
                }
        except Exception as e:
            result['issues'].append(f"EXIF提取失败: {str(e)}")
        
        # 计算校验和
        result['checksum'] = self._calculate_checksum(img)
        
        # 应用预处理（缩放、去噪等）
        if self.config.get('resize_images', False):
            max_size = self.config.get('max_image_size', 1600)
            img_processed = self._resize_image(img, max_size)
            result['processed_size'] = {
                'width': img_processed.shape[1],
                'height': img_processed.shape[0]
            }
        
        return result
    
    def _check_image_quality(self, image: np.ndarray, image_path: Path) -> List[str]:
        """检查图像质量"""
        issues = []
        
        # 检查尺寸
        min_size = self.config.get('min_image_size', 480)
        if image.shape[0] < min_size or image.shape[1] < min_size:
            issues.append(f"图像尺寸过小: {image.shape[1]}x{image.shape[0]}")
        
        # 检查模糊度（拉普拉斯方差）
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        if fm < 100:  # 阈值可调整
            issues.append(f"图像可能模糊: 拉普拉斯方差={fm:.1f}")
        
        # 检查曝光
        brightness = np.mean(gray)
        if brightness < 30 or brightness > 220:
            issues.append(f"曝光异常: 平均亮度={brightness:.1f}")
        
        return issues
    
    def _resize_image(self, image: np.ndarray, max_size: int) -> np.ndarray:
        """缩放图像，保持宽高比"""
        h, w = image.shape[:2]
        
        if max(h, w) <= max_size:
            return image
        
        if h > w:
            new_h = max_size
            new_w = int(w * max_size / h)
        else:
            new_w = max_size
            new_h = int(h * max_size / w)
        
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    def _calculate_checksum(self, image: np.ndarray) -> str:
        """计算图像校验和"""
        import hashlib
        # 使用灰度图计算校验和，避免颜色变化影响
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        return hashlib.md5(gray.tobytes()).hexdigest()
        