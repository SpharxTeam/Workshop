# Spharx 数据产品规格说明书

## 产品概述

Spharx Toolchain 输出三种标准化的数据产品，分别针对不同的应用场景和需求：

1. **Spharx 2D** - 2D图像标注数据集
2. **Spharx 3D Geo** - 3D几何数据集  
3. **Spharx 3D Physics** - 3D物理事实数据集

## Spharx 2D 标注数据集

### 产品描述
高质量的2D图像标注数据集，适用于计算机视觉训练和评估。

### 数据格式
支持多种标准格式：
- **COCO格式** (推荐)
- **YOLO格式** 
- **Pascal VOC格式**

### COCO格式规范
```json
{
  "info": {
    "description": "Spharx 2D标注数据集",
    "version": "1.0",
    "year": 2024,
    "contributor": "Spharx Team",
    "date_created": "2024-01-01"
  },
  "licenses": [...],
  "images": [
    {
      "id": 1,
      "file_name": "image_001.jpg",
      "width": 1920,
      "height": 1080,
      "date_captured": "2024-01-01 10:00:00"
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [100, 150, 200, 300],
      "area": 60000,
      "segmentation": [[100, 150, 300, 150, 300, 450, 100, 450]],
      "iscrowd": 0,
      "score": 0.95,
      "attributes": {
        "material": "wood",
        "condition": "good"
      }
    }
  ],
  "categories": [
    {
      "id": 1,
      "name": "家具",
      "supercategory": "室内物品"
    }
  ]
}
```

### 质量标准
- **标注精度**: IoU ≥ 0.85
- **类别准确性**: ≥ 95%
- **边界框完整性**: 100%覆盖目标
- **最小标注面积**: 100像素

### 目录结构
```
spharx_2d_dataset/
├── annotations/
│   ├── instances_train.json
│   ├── instances_val.json
│   └── instances_test.json
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── licenses/
└── README.md
```

## Spharx 3D Geo 几何数据集

### 产品描述
精确的3D几何重建数据，包含点云、网格和相机参数。

### 数据组成
1. **稠密点云** (PLY格式)
2. **三角网格** (OBJ格式)
3. **相机参数** (TXT格式)
4. **纹理贴图** (PNG格式)

### 点云格式 (PLY)
```ply
ply
format ascii 1.0
element vertex 10000
property float x
property float y  
property float z
property uchar red
property uchar green
property uchar blue
end_header
1.23 4.56 7.89 255 128 64
...
```

### 相机参数格式
```
# Camera list (COLMAP format)
# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]
1 PINHOLE 1920 1080 1440.0 1440.0 960.0 540.0
```

### 质量指标
- **重建精度**: ≤ 5mm RMS误差
- **点云密度**: ≥ 100 points/m²
- **纹理分辨率**: ≥ 1024×1024
- **覆盖完整性**: ≥ 90%场景覆盖

### 目录结构
```
spharx_3d_geo_dataset/
├── pointclouds/
│   ├── scene_001.ply
│   └── scene_001_meta.json
├── meshes/
│   ├── scene_001.obj
│   └── scene_001.mtl
├── cameras/
│   └── cameras.txt
├── textures/
│   └── scene_001_texture.png
└── metadata.json
```

## Spharx 3D Physics 物理事实数据集

### 产品描述
包含物理属性和仿真数据的增强3D数据集。

### 数据扩展
在3D Geo基础上增加：
- **物理材质属性**
- **质量分布信息**
- **碰撞体定义**
- **力学仿真轨迹**

### 物理属性定义
```json
{
  "physical_properties": {
    "material": {
      "type": "wood",
      "density": 0.65,
      "young_modulus": 10000000000,
      "poisson_ratio": 0.3
    },
    "mass": {
      "value": 2.5,
      "unit": "kg",
      "center_of_mass": [0.5, 0.3, 0.4]
    },
    "collision": {
      "shape": "box",
      "dimensions": [1.2, 0.8, 0.6],
      "friction": 0.5,
      "restitution": 0.3
    }
  },
  "simulation_data": {
    "trajectories": [...],
    "forces": [...],
    "constraints": [...]
  }
}
```

### 仿真格式支持
- **Blender Physics** (.blend)
- **Unity Physics** (.unitypackage)
- **USD Physics** (.usd)

### 质量保证
- **物理合理性**: 符合现实世界物理规律
- **仿真准确性**: 与真实运动轨迹偏差≤10%
- **材质真实性**: 光学和力学属性准确
- **交互一致性**: 多物体交互符合预期

### 目录结构
```
spharx_3d_physics_dataset/
├── geometry/              # 3D Geo数据
├── physics/
│   ├── materials.json
│   ├── masses.json
│   └── collisions.json
├── simulations/
│   ├── falling_test.blend
│   └── interaction_test.usd
├── validations/
│   └── physics_verification.json
└── spharx_3d_physics.json
```

## 产品质量验证

### 自动验证流程
```python
class DatasetValidator:
    def validate_2d_dataset(self, dataset_path):
        """验证2D数据集质量"""
        checks = [
            self.check_annotation_format(),
            self.check_image_integrity(),
            self.check_category_coverage(),
            self.check_bbox_quality()
        ]
        return all(checks)
        
    def validate_3d_dataset(self, dataset_path):
        """验证3D数据集质量"""
        checks = [
            self.check_pointcloud_density(),
            self.check_mesh_manifoldness(),
            self.check_texture_alignment(),
            self.check_camera_calibration()
        ]
        return all(checks)
```

### 质量报告格式
```json
{
  "validation_summary": {
    "overall_status": "pass",
    "total_objects": 1000,
    "quality_score": 95.5,
    "validation_date": "2024-01-01T10:30:00Z"
  },
  "detailed_metrics": {
    "annotation_accuracy": 96.2,
    "completeness": 98.1,
    "consistency": 94.8,
    "usability": 97.3
  },
  "issues": [
    {
      "severity": "warning",
      "description": "Low confidence annotations detected",
      "count": 15,
      "recommendation": "Manual review suggested"
    }
  ]
}
```

## 产品交付标准

### 交付清单
每个产品交付包含：
1. **数据文件** - 核心数据内容
2. **元数据** - 描述性信息
3. **验证报告** - 质量检查结果
4. **使用说明** - 格式说明和加载示例
5. **许可证** - 使用条款和限制

### 版本控制
```
产品名称_版本号_时间戳_质量等级
例如: spharx_2d_v1.0_20240101_high
```

### 兼容性保证
- 向后兼容性承诺
- 格式稳定性和迁移路径
- API版本管理
- 文档同步更新

---
*最后更新: 2026-02-07*
*版本: 1.0*