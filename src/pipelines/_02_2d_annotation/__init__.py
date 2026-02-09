"""
2D自动标注模块
基于SAM进行自动分割，生成2D标注
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2
import json
import logging
from dataclasses import dataclass
from PIL import Image

# 尝试导入SAM相关库
try:
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False
    print("警告: segment-anything 未安装，2D标注功能将受限")

logger = logging.getLogger(__name__)

@dataclass
class AnnotationResult:
    """标注结果数据类"""
    image_id: str
    image_path: str
    masks: List[Dict[str, Any]]  # SAM原始掩码
    annotations: List[Dict[str, Any]]  # COCO格式标注
    quality_score: float
    processing_time: float

class SAMAnnotator:
    """基于SAM的2D自动标注器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.model = None
        self.mask_generator = None
        self.initialized = False
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """加载配置"""
        default_config = {
            'model_type': 'vit_h',
            'checkpoint_path': '/models/sam_vit_h_4b8939.pth',
            'device': 'cuda',
            'points_per_side': 32,
            'pred_iou_thresh': 0.88,
            'stability_score_thresh': 0.95,
            'crop_n_layers': 1,
            'crop_n_points_downscale_factor': 2,
            'min_mask_region_area': 100,
            'output_mode': 'coco_json',
            'save_visualization': True
        }
        
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config and 'sam' in user_config:
                    default_config.update(user_config['sam'])
        
        return default_config
    
    def initialize(self):
        """初始化SAM模型"""
        if not SAM_AVAILABLE:
            raise ImportError("segment-anything 库未安装，请运行: pip install segment-anything-py")
        
        if self.initialized:
            return
            
        try:
            import torch
            
            # 检查设备
            device = self.config['device']
            if device == 'cuda' and not torch.cuda.is_available():
                logger.warning("CUDA不可用，回退到CPU")
                device = 'cpu'
                self.config['device'] = device
            
            # 加载模型
            logger.info(f"正在加载SAM模型: {self.config['model_type']}")
            
            sam = sam_model_registry[self.config['model_type']](
                checkpoint=self.config['checkpoint_path']
            )
            sam.to(device=device)
            
            # 创建掩码生成器
            self.mask_generator = SamAutomaticMaskGenerator(
                model=sam,
                points_per_side=self.config['points_per_side'],
                pred_iou_thresh=self.config['pred_iou_thresh'],
                stability_score_thresh=self.config['stability_score_thresh'],
                crop_n_layers=self.config['crop_n_layers'],
                crop_n_points_downscale_factor=self.config['crop_n_points_downscale_factor'],
                min_mask_region_area=self.config['min_mask_region_area'],
            )
            
            self.model = sam
            self.initialized = True
            logger.info("SAM模型初始化完成")
            
        except Exception as e:
            logger.error(f"SAM模型初始化失败: {e}", exc_info=True)
            raise
    
    def annotate_image(self, image_path: Path) -> AnnotationResult:
        """标注单张图像"""
        if not self.initialized:
            self.initialize()
        
        import time
        start_time = time.time()
        
        try:
            # 读取图像
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"无法读取图像: {image_path}")
            
            # 转换颜色空间（SAM需要RGB）
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 生成掩码
            logger.info(f"正在为 {image_path.name} 生成标注...")
            masks = self.mask_generator.generate(image_rgb)
            
            # 转换为COCO格式
            annotations = self._masks_to_coco(image_path, image_rgb.shape, masks)
            
            # 计算质量分数
            quality_score = self._calculate_quality_score(masks, annotations)
            
            # 生成可视化结果（如果启用）
            if self.config.get('save_visualization', True):
                self._save_visualization(image_path, image_rgb, masks)
            
            processing_time = time.time() - start_time
            
            return AnnotationResult(
                image_id=image_path.stem,
                image_path=str(image_path),
                masks=masks,
                annotations=annotations,
                quality_score=quality_score,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"图像标注失败 {image_path}: {e}", exc_info=True)
            raise
    
    def _masks_to_coco(self, image_path: Path, image_shape: Tuple, masks: List) -> List[Dict]:
        """将SAM掩码转换为COCO格式"""
        annotations = []
        
        for i, mask_data in enumerate(masks):
            mask = mask_data['segmentation']
            
            # 计算边界框
            rows, cols = np.where(mask)
            if len(rows) == 0 or len(cols) == 0:
                continue
                
            x_min, x_max = np.min(cols), np.max(cols)
            y_min, y_max = np.min(rows), np.max(rows)
            width = x_max - x_min
            height = y_max - y_min
            
            # 计算多边形轮廓
            contours, _ = cv2.findContours(
                mask.astype(np.uint8), 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            segmentation = []
            for contour in contours:
                if contour.shape[0] >= 3:  # 至少需要3个点
                    contour = contour.flatten().tolist()
                    segmentation.append(contour)
            
            if not segmentation:
                continue
            
            # 创建标注对象
            annotation = {
                'id': i + 1,
                'image_id': image_path.stem,
                'category_id': 1,  # 默认类别，后续需要分类
                'bbox': [float(x_min), float(y_min), float(width), float(height)],
                'area': float(mask_data['area']),
                'segmentation': segmentation,
                'iscrowd': 0,
                'score': float(mask_data['predicted_iou']),
                'stability_score': float(mask_data['stability_score']),
                'crop_box': mask_data.get('crop_box', None)
            }
            
            annotations.append(annotation)
        
        return annotations
    
    def _calculate_quality_score(self, masks: List, annotations: List) -> float:
        """计算标注质量分数"""
        if not masks:
            return 0.0
        
        scores = []
        for mask_data, ann in zip(masks, annotations):
            # 基于预测IoU和稳定性分数
            iou_score = mask_data.get('predicted_iou', 0)
            stability_score = mask_data.get('stability_score', 0)
            
            # 基于掩码质量（面积、紧凑度）
            area = mask_data['area']
            bbox = ann['bbox']
            bbox_area = bbox[2] * bbox[3]
            
            if bbox_area > 0:
                compactness = area / bbox_area  # 越接近1越好
            else:
                compactness = 0
            
            # 综合分数
            score = (iou_score * 0.4 + stability_score * 0.3 + compactness * 0.3)
            scores.append(score)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _save_visualization(self, image_path: Path, image_rgb: np.ndarray, masks: List):
        """保存可视化结果"""
        try:
            import matplotlib.pyplot as plt
            
            # 创建可视化图像
            plt.figure(figsize=(20, 20))
            plt.imshow(image_rgb)
            
            # 绘制所有掩码
            for i, mask_data in enumerate(masks):
                mask = mask_data['segmentation']
                color = np.random.rand(3,)
                
                # 创建带透明度的掩码覆盖
                img_mask = np.zeros((*mask.shape, 4))
                img_mask[mask] = [*color, 0.35]
                
                plt.imshow(img_mask, alpha=0.5)
                
                # 绘制边界框
                y, x = np.where(mask)
                if len(x) > 0 and len(y) > 0:
                    bbox = [np.min(x), np.min(y), np.max(x), np.max(y)]
                    rect = plt.Rectangle(
                        (bbox[0], bbox[1]), 
                        bbox[2] - bbox[0], 
                        bbox[3] - bbox[1],
                        fill=False, 
                        edgecolor=color, 
                        linewidth=2
                    )
                    plt.gca().add_patch(rect)
            
            plt.axis('off')
            
            # 保存图像
            output_dir = Path(self.config.get('visualization_dir', '/tmp/sam_visualizations'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{image_path.stem}_annotated.png"
            plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=150)
            plt.close()
            
            logger.info(f"可视化结果已保存: {output_path}")
            
        except Exception as e:
            logger.warning(f"可视化保存失败: {e}")

class AnnotationPipeline:
    """2D标注流水线"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.annotator = SAMAnnotator()
        self.results = []
        
    def process_scene(self, scene_path: Path) -> Dict:
        """处理整个场景"""
        results = {
            'scene_id': scene_path.name,
            'images': [],
            'summary': {},
            'coco_format': None
        }
        
        # 检查图像目录
        images_dir = scene_path / 'images'
        if not images_dir.exists():
            raise ValueError(f"图像目录不存在: {images_dir}")
        
        # 获取所有图像文件
        image_files = list(images_dir.glob('*'))
        image_files = [f for f in image_files 
                      if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        
        if not image_files:
            raise ValueError(f"场景中没有图像文件: {scene_path}")
        
        logger.info(f"开始处理场景 {scene_path.name}, 共 {len(image_files)} 张图像")
        
        # 处理每张图像
        for img_path in image_files:
            try:
                result = self.annotator.annotate_image(img_path)
                self.results.append(result)
                results['images'].append({
                    'image_id': result.image_id,
                    'annotations_count': len(result.annotations),
                    'quality_score': result.quality_score,
                    'processing_time': result.processing_time
                })
                
                logger.info(f"完成标注 {img_path.name}: "
                           f"{len(result.annotations)} 个标注, "
                           f"质量分数 {result.quality_score:.3f}")
                
            except Exception as e:
                logger.error(f"处理图像失败 {img_path.name}: {e}")
                continue
        
        # 生成汇总统计
        if self.results:
            results['summary'] = self._generate_summary()
            results['coco_format'] = self._generate_coco_format(scene_path.name)
        
        return results
    
    def _generate_summary(self) -> Dict:
        """生成处理摘要"""
        if not self.results:
            return {}
        
        total_images = len(self.results)
        total_annotations = sum(len(r.annotations) for r in self.results)
        avg_quality = np.mean([r.quality_score for r in self.results])
        avg_time = np.mean([r.processing_time for r in self.results])
        
        return {
            'total_images': total_images,
            'total_annotations': total_annotations,
            'avg_annotations_per_image': total_annotations / total_images if total_images > 0 else 0,
            'avg_quality_score': float(avg_quality),
            'avg_processing_time_seconds': float(avg_time),
            'total_processing_time_seconds': sum(r.processing_time for r in self.results)
        }
    
    def _generate_coco_format(self, scene_id: str) -> Dict:
        """生成COCO格式的输出"""
        coco_data = {
            'info': {
                'description': f'Spharx 2D Annotations - {scene_id}',
                'version': '1.0',
                'year': 2024,
                'contributor': 'SpharxWorkshop',
                'date_created': '2024-01-01'
            },
            'images': [],
            'annotations': [],
            'categories': [
                {
                    'id': 1,
                    'name': 'object',
                    'supercategory': 'thing'
                }
            ]
        }
        
        # 添加图像信息
        for result in self.results:
            image_info = {
                'id': result.image_id,
                'file_name': Path(result.image_path).name,
                'width': 0,  # 需要从图像读取
                'height': 0,  # 需要从图像读取
                'license': 1,
                'flickr_url': '',
                'coco_url': '',
                'date_captured': '2024-01-01'
            }
            
            # 读取图像尺寸
            try:
                img = cv2.imread(result.image_path)
                if img is not None:
                    image_info['width'] = img.shape[1]
                    image_info['height'] = img.shape[0]
            except:
                pass
            
            coco_data['images'].append(image_info)
        
        # 添加标注信息
        annotation_id = 1
        for result in self.results:
            for ann in result.annotations:
                ann['id'] = annotation_id
                ann['image_id'] = result.image_id
                coco_data['annotations'].append(ann)
                annotation_id += 1
        
        return coco_data
    
    def save_results(self, output_path: Path):
        """保存标注结果"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存COCO格式标注
        if self.results:
            scene_id = Path(self.results[0].image_path).parent.parent.name
            coco_data = self._generate_coco_format(scene_id)
            
            coco_file = output_path / 'annotations.json'
            with open(coco_file, 'w', encoding='utf-8') as f:
                json.dump(coco_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"COCO标注已保存: {coco_file}")
        
        # 保存处理摘要
        summary = self._generate_summary()
        summary_file = output_path / 'summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"处理摘要已保存: {summary_file}")
        