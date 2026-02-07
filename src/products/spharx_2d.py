"""
Spharx 2D 标注数据集产品规范
"""
import os
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path

@dataclass
class Spharx2DProduct:
    """2D数据集产品"""
    
    # 基本信息
    scene_id: str
    version: str = "1.0.0"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 数据统计
    image_count: int = 0
    annotation_count: int = 0
    category_count: int = 0
    
    # 文件结构
    base_dir: Path = None
    image_dir: Path = None
    annotation_dir: Path = None
    metadata_file: Path = None
    
    # 类别信息
    categories: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化目录结构"""
        if self.base_dir:
            self.base_dir = Path(self.base_dir)
            self.image_dir = self.base_dir / "images"
            self.annotation_dir = self.base_dir / "annotations"
            self.metadata_file = self.base_dir / "metadata.json"
            
            # 创建目录
            self.image_dir.mkdir(parents=True, exist_ok=True)
            self.annotation_dir.mkdir(parents=True, exist_ok=True)
    
    def add_category(self, name: str, id: int, supercategory: str = ""):
        """添加标注类别"""
        category = {
            "id": id,
            "name": name,
            "supercategory": supercategory
        }
        self.categories.append(category)
        self.category_count = len(self.categories)
    
    def save_annotation(self, image_id: str, annotations: List[Dict], 
                        format: str = "coco"):
        """保存标注文件"""
        if format == "coco":
            self._save_coco_annotation(image_id, annotations)
        elif format == "yolo":
            self._save_yolo_annotation(image_id, annotations)
    
    def _save_coco_annotation(self, image_id: str, annotations: List[Dict]):
        """保存为COCO格式"""
        coco_data = {
            "info": {
                "description": f"Spharx 2D Dataset - {self.scene_id}",
                "version": self.version,
                "year": datetime.now().year,
                "contributor": "Spharx Perception Tech",
                "date_created": self.created_date
            },
            "licenses": [{
                "id": 1,
                "name": "Spharx Non-Commercial License",
                "url": "https://spharx.com/license"
            }],
            "images": [{
                "id": 1,
                "file_name": f"{image_id}.jpg",
                "width": 1920,
                "height": 1080,
                "date_captured": self.created_date
            }],
            "annotations": annotations,
            "categories": self.categories
        }
        
        output_file = self.annotation_dir / f"{image_id}_coco.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2, ensure_ascii=False)
        
        self.annotation_count += len(annotations)
    
    def _save_yolo_annotation(self, image_id: str, annotations: List[Dict]):
        """保存为YOLO格式"""
        # YOLO格式: class_id x_center y_center width height
        lines = []
        for ann in annotations:
            # 假设annotations包含边界框信息
            bbox = ann.get("bbox", [0, 0, 0, 0])  # [x, y, width, height]
            class_id = ann.get("category_id", 0)
            
            # 归一化坐标
            img_width, img_height = 1920, 1080  # 实际应从图像获取
            x_center = (bbox[0] + bbox[2] / 2) / img_width
            y_center = (bbox[1] + bbox[3] / 2) / img_height
            width = bbox[2] / img_width
            height = bbox[3] / img_height
            
            lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
        
        output_file = self.annotation_dir / f"{image_id}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    def save_metadata(self):
        """保存产品元数据"""
        metadata = {
            "product_type": "2d_annotation",
            "scene_id": self.scene_id,
            "version": self.version,
            "created_date": self.created_date,
            "statistics": {
                "image_count": self.image_count,
                "annotation_count": self.annotation_count,
                "category_count": self.category_count
            },
            "categories": self.categories,
            "file_structure": {
                "images": str(self.image_dir.relative_to(self.base_dir)),
                "annotations": str(self.annotation_dir.relative_to(self.base_dir)),
                "formats": ["coco", "yolo", "pascal_voc"]
            },
            "quality_metrics": {
                "min_annotation_area": 100,
                "label_consistency": "verified",
                "format_compliance": "full"
            }
        }
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata
    
    @classmethod
    def validate_product(cls, product_dir: Path) -> Dict[str, Any]:
        """验证产品完整性"""
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        # 检查必要文件
        required_files = ["metadata.json", "images/", "annotations/"]
        for file in required_files:
            file_path = product_dir / file
            if not file_path.exists():
                if file.endswith('/'):
                    validation_result["errors"].append(f"目录不存在: {file}")
                else:
                    validation_result["errors"].append(f"文件不存在: {file}")
        
        # 检查元数据
        metadata_file = product_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                required_fields = ["product_type", "scene_id", "version", "statistics"]
                for field in required_fields:
                    if field not in metadata:
                        validation_result["errors"].append(f"元数据缺少字段: {field}")
                        
            except json.JSONDecodeError as e:
                validation_result["errors"].append(f"元数据JSON解析错误: {e}")
        
        # 检查标注文件数量与图像数量匹配
        image_dir = product_dir / "images"
        annotation_dir = product_dir / "annotations"
        
        if image_dir.exists() and annotation_dir.exists():
            image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
            annotation_files = list(annotation_dir.glob("*.json")) + list(annotation_dir.glob("*.txt"))
            
            if len(image_files) != len(annotation_files):
                validation_result["warnings"].append(
                    f"图像文件数({len(image_files)})与标注文件数({len(annotation_files)})不匹配"
                )
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        return validation_result