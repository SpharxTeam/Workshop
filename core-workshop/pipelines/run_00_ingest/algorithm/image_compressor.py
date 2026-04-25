# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 图像压缩模块：根据配置自动选择合适的压缩格式

import cv2
import numpy as np
import os
from PIL import Image
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class ImageCompressor:
    """自适应图像压缩器，支持多种格式"""
    
    def __init__(self, quality_preset: str = 'production'):
        """
        Args:
            quality_preset: 'production' (高质量), 'development' (快速), 'archive' (无损)
        """
        self.preset = quality_preset
        self._configure_preset()
    
    def _configure_preset(self):
        """根据预设配置压缩参数"""
        if self.preset == 'production':
            self.rgb_format = 'webp'
            self.rgb_params = {
                'quality': 95,           # WebP质量95
                'method': 6               # 压缩速度-质量平衡
            }
            self.depth_format = 'png'
            self.depth_params = {
                'compress_level': 3        # PNG压缩级别1-9
            }
        elif self.preset == 'development':
            self.rgb_format = 'jpg'
            self.rgb_params = {
                'quality': 85,
                'optimize': True
            }
            self.depth_format = 'png'
            self.depth_params = {
                'compress_level': 1
            }
        elif self.preset == 'archive':
            self.rgb_format = 'png'
            self.rgb_params = {}           # PNG无损
            self.depth_format = 'png'
            self.depth_params = {
                'compress_level': 9
            }
    
    def save_rgb(self, image: np.ndarray, path: str) -> Tuple[bool, int]:
        """
        保存RGB图像，返回(成功标志, 文件大小)
        """
        # 根据格式调整实际文件扩展名
        base, ext = os.path.splitext(path)
        if self.rgb_format == 'webp':
            actual_path = base + '.webp'
            success = cv2.imwrite(actual_path, image, [
                cv2.IMWRITE_WEBP_QUALITY, self.rgb_params['quality']
            ])
        elif self.rgb_format == 'jpg':
            actual_path = base + '.jpg'
            success = cv2.imwrite(actual_path, image, [
                cv2.IMWRITE_JPEG_QUALITY, self.rgb_params['quality']
            ])
        else:  # png
            actual_path = base + '.png'
            success = cv2.imwrite(actual_path, image)
        
        if success and os.path.exists(actual_path):
            size = os.path.getsize(actual_path)
            logger.debug(f"保存图像 {actual_path}，大小: {size} 字节，格式: {self.rgb_format}")
            return True, size
        return False, 0
    
    def save_depth(self, depth: np.ndarray, path: str) -> Tuple[bool, int]:
        """
        保存深度图，使用16-bit PNG保留精度
        """
        # 确保深度图为16位
        if depth.dtype != np.uint16:
            if depth.max() < 65535:
                depth = depth.astype(np.uint16)
            else:
                depth = (depth / depth.max() * 65535).astype(np.uint16)
        
        # PIL保存16-bit PNG
        img = Image.fromarray(depth)
        img.save(path, compress_level=self.depth_params['compress_level'])
        
        if os.path.exists(path):
            size = os.path.getsize(path)
            return True, size
        return False, 0


class StreamCompressor:
    """流式压缩器，支持渐进式处理"""
    
    def __init__(self, target_bitrate: Optional[int] = None):
        self.target_bitrate = target_bitrate
    
    def compress_video(self, frame_dir: str, output_path: str, fps: int = 30, image_pattern: str = "*.jpg"):
        """
        将图像序列压缩为视频（H.264）
        Args:
            frame_dir: 图像目录
            output_path: 输出视频路径
            fps: 帧率
            image_pattern: 图像文件匹配模式，如 "*.jpg"
        """
        import subprocess
        # 构建输入文件模式
        input_pattern = os.path.join(frame_dir, image_pattern)
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-pattern_type', 'glob',
            '-i', input_pattern,
            '-c:v', 'libx264',      # H.264编码
            '-preset', 'medium',
            '-crf', '23',            # 质量参数（越小质量越高）
            '-pix_fmt', 'yuv420p',
            output_path
        ]
        if self.target_bitrate:
            cmd.extend(['-b:v', self.target_bitrate])
        
        logger.debug(f"执行 ffmpeg 命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"视频压缩失败: {result.stderr}")
            return False
        return True