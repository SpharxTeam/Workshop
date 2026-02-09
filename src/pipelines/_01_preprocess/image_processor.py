"""
图像预处理模块
负责图像的标准化、格式转换和质量检查
"""
import cv2
import numpy as np
from pathlib import Path
import os
import json
from PIL import Image
from typing import Dict, Any, Optional, List
from loguru import logger
from dataclasses import dataclass

from ...schemas import SceneMetadata


@dataclass
class PreprocessResult:
    """预处理结果"""
    success: bool
    image_count: int = 0
    error: Optional[str] = None
    metadata: Optional[SceneMetadata] = None
    processed_images: List[str] = []


class ImagePreprocessor:
    """图像预处理器"""
    
    def __init__(self):
        self.input_dir = Path(os.getenv("SPHARX_INPUT_DIR", "."))
        self.workspace_dir = Path(os.getenv("SPHARX_WORKSPACE_DIR", "."))
        
    def process_scene(self, scene_id: str) -> PreprocessResult:
        """处理整个场景的图像"""
        logger.info(f"开始预处理场景: {scene_id}")
        
        scene_dir = self.input_dir / scene_id / "images"
        if not scene_dir.exists():
            return PreprocessResult(
                success=False,
                error=f"场景图像目录不存在: {scene_dir}"
            )
        
        # 获取所有图像文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        image_files = []
        for ext in image_extensions:
            image_files.extend(scene_dir.glob(f"*{ext}"))
        
        if not image_files:
            return PreprocessResult(
                success=False,
                error=f"场景目录中没有发现图像文件: {scene_dir}"
            )
        
        logger.info(f"发现 {len(image_files)} 张图像")
        
        processed_images = []
        total_size = 0
        
        # 创建处理输出目录
        output_dir = self.workspace_dir / "processing" / scene_id / "preprocessed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理每张图像
        for i, img_path in enumerate(sorted(image_files)):
            try:
                result = self._process_single_image(img_path, output_dir, i)
                if result:
                    processed_images.append(result["filename"])
                    total_size += result["file_size"]
                    
                if (i + 1) % 10 == 0:
                    logger.debug(f"已处理 {i + 1}/{len(image_files)} 张图像")
                    
            except Exception as e:
                logger.error(f"处理图像失败 {img_path}: {str(e)}")
                continue
        
        # 生成场景元数据
        metadata = self._generate_scene_metadata(
            scene_id, processed_images, total_size
        )
        
        # 保存元数据
        metadata_path = output_dir / "scene_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.dict(), f, indent=2, ensure_ascii=False)
        
        logger.success(f"场景预处理完成: {len(processed_images)} 张图像")
        
        return PreprocessResult(
            success=True,
            image_count=len(processed_images),
            metadata=metadata,
            processed_images=processed_images
        )
    
    def _process_single_image(self, img_path: Path, output_dir: Path, index: int) -> Optional[Dict[str, Any]]:
        """处理单张图像"""
        # 读取图像
        img = cv2.imread(str(img_path))
        if img is None:
            logger.warning(f"无法读取图像: {img_path}")
            return None
        
        # 获取原始信息
        original_height, original_width = img.shape[:2]
        
        # 调整图像大小（可选，根据配置）
        max_size = int(os.getenv("COLMAP_MAX_IMAGE_SIZE", "1600"))
        if max(original_width, original_height) > max_size:
            scale = max_size / max(original_width, original_height)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # 生成输出文件名
        output_filename = f"frame_{index:06d}.jpg"
        output_path = output_dir / output_filename
        
        # 保存处理后的图像
        cv2.imwrite(str(output_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # 获取文件大小
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        
        return {
            "filename": output_filename,
            "original_path": str(img_path),
            "width": img.shape[1],
            "height": img.shape[0],
            "file_size": file_size,
            "channels": img.shape[2] if len(img.shape) > 2 else 1
        }
    
    def _generate_scene_metadata(self, scene_id: str, images: List[str], total_size: float) -> SceneMetadata:
        """生成场景元数据"""
        return SceneMetadata(
            scene_id=scene_id,
            name=f"Scene_{scene_id}",
            image_count=len(images),
            file_size_mb=total_size,
            tags=["preprocessed", "standardized"]
        )
    
    def validate_images(self, scene_id: str) -> Dict[str, Any]:
        """验证图像质量"""
        # TODO: 实现图像质量验证
        return {"status": "pending"}