"""
标注数据模型
"""

from typing import List, Tuple, Optional, Dict, Any
from pydantic import Field, validator
import numpy as np
from .base import BaseSpharxModel


class BoundingBox2D(BaseSpharxModel):
    """2D边界框"""
    x: float = Field(..., ge=0, description="左上角x坐标")
    y: float = Field(..., ge=0, description="左上角y坐标")
    width: float = Field(..., gt=0, description="宽度")
    height: float = Field(..., gt=0, description="高度")
    
    @property
    def area(self) -> float:
        """计算面积"""
        return self.width * self.height
    
    @property
    def corners(self) -> List[Tuple[float, float]]:
        """获取四个角点坐标"""
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        if v <= 0:
            raise ValueError('宽度和高度必须大于0')
        return v


class AnnotationObject(BaseSpharxModel):
    """标注对象"""
    object_id: str = Field(..., description="物体ID")
    category: str = Field(..., description="类别名称")
    bbox: List[float] = Field(..., min_items=4, max_items=4, description="边界框[x, y, width, height]")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="属性")
    segmentation: Optional[List[List[float]]] = Field(None, description="多边形坐标")
    
    @validator('bbox')
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError('bbox必须包含4个值: [x, y, width, height]')
        if v[2] <= 0 or v[3] <= 0:
            raise ValueError('宽度和高度必须大于0')
        return v
    
    @property
    def bbox_object(self) -> BoundingBox2D:
        """获取BoundingBox2D对象"""
        v = self.bbox
        return BoundingBox2D(id=f"bbox_{self.object_id}", x=v[0], y=v[1], width=v[2], height=v[3])


class ImageAnnotation(BaseSpharxModel):
    """单张图像的标注"""
    image_id: str = Field(..., description="图像ID")
    image_path: str = Field(..., description="图像路径")
    width: int = Field(..., gt=0, description="图像宽度")
    height: int = Field(..., gt=0, description="图像高度")
    objects: List[AnnotationObject] = Field(default_factory=list, description="标注物体列表")
    camera_params: Optional[Dict[str, Any]] = Field(None, description="相机参数")


class COCOAnnotation(BaseSpharxModel):
    """COCO格式标注"""
    info: Dict[str, Any] = Field(default_factory=dict)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    annotations: List[Dict[str, Any]] = Field(default_factory=list)
    categories: List[Dict[str, Any]] = Field(default_factory=list)