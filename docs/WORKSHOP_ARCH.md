# Workshop 架构设计文档

## 1. 概述

Workshop 是 SpharxHub 平台的数据采集和预处理子系统，负责将原始传感器数据转化为标准化的高质量数据集。系统采用模块化、容器化的设计理念，通过六个核心处理管道实现从数据采集到数据交付的完整处理链路。

## 2. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                       Workshop 系统架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │   输入层     │───▶│  处理层       │───▶│    输出层        │   │
│  │             │    │              │    │                 │   │
│  │ ▪ 原始数据   │    │ ▪ 数据导入    │    │ ▪ 标准数据集     │   │
│  │ ▪ 传感器流   │    │ ▪ 质量检测    │    │ ▪ 交付服务      │   │
│  │ ▪ 标定数据   │    │ ▪ 增强处理    │    │ ▪ 监控面板      │   │
│  └─────────────┘    │ ▪ 相机标定    │    └─────────────────┘   │
│                     │ ▪ 数据打包    │                          │
│                     └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 核心模块详解

### 00_ingest - 数据导入模块 ▶

#### 模块职责
接收和解析原始传感器数据，进行隐私脱敏处理，生成标准化的数据结构。

#### 技术栈
- **数据格式**: ROS Bag, RealSense SDK
- **隐私处理**: 人脸模糊、敏感信息过滤
- **输出格式**: 标准化目录结构

#### 配置参数
```yaml
# common/configs/modules/00_ingest.yaml
privacy:
  enable_blur: true
  blur_kernel_size: 15
  face_detection: true

data_format:
  output_structure: "standard"
  compression_level: 6
```

#### 输入输出规范
- **输入**: `/data/input/*.bag`
- **输出**: `/data/workshop/scene_xxx/`
  - `rgb/` - 彩色图像序列
  - `depth/` - 深度图像序列
  - `timestamps.csv` - 时间戳信息
  - `manifest.json` - 场景元数据

---

### 01_quality - 质量检测模块 ▶

#### 模块职责
对采集的数据进行多层次质量评估，包括硬件层面和语义层面的质量检测。

#### 技术特性
- **硬件层检测**: 模糊度、过曝、欠曝、帧率稳定性
- **动作语义层**: (预留) 动作完整性和语义质量
- **任务完成层**: (预留) 任务目标达成度评估

#### 配置参数
```yaml
# common/configs/modules/01_quality.yaml
hardware:
  blur_threshold: 100
  over_threshold: 240
  under_threshold: 30
  expected_fps: 30

quality_check:
  enable_real_time: true
  save_reports: true
  report_format: "json"
```

#### 输出产物
- `quality_report.json` - 质量评估报告
- `quality_metrics/` - 详细指标数据

---

### 02_enhance - 数据增强模块 ▶

#### 模块职责
基于目标检测和图像处理技术，对数据进行增强和标注。

#### 技术组成
- **目标检测**: YOLOv8 实时目标检测
- **图像增强**: 去噪、对比度调整、亮度校正
- **标注生成**: COCO 格式标注文件

#### 配置参数
```yaml
# common/configs/modules/02_enhance.yaml
yolo:
  model: "yolov8n.pt"
  conf_threshold: 0.25
  iou_threshold: 0.45

enhancement:
  enable_denoising: true
  noise_reduction_strength: 0.3
```

#### 输出产物
- `annotations.json` - 目标标注数据
- `enhanced_images/` - 增强后的图像
- `detection_results/` - 检测中间结果

---

### 03_calibrate - 相机标定模块 ▶

#### 模块职责
执行相机内外参标定，生成精确的相机参数文件。

#### 标定方法
- **内参标定**: 棋盘格标定法
- **外参标定**: (预留) 多相机相对位置标定

#### 配置参数
```yaml
# common/configs/modules/03_calibrate.yaml
chessboard:
  pattern_size: [9, 6]
  square_size: 0.025

calibration:
  max_images: 30
  reprojection_error_threshold: 0.5
```

#### 输出产物
- `intrinsics.json` - 内参矩阵
- `extrinsics.json` - 外参矩阵
- `calibration_report.json` - 标定报告

---

### 04_pack - 数据打包模块 ▶

#### 模块职责
将处理完成的数据打包成标准格式，便于后续使用和分发。

#### 支持格式
- **ROS Bag**: 机器人操作系统标准格式
- **COCO**: 计算机视觉标准格式
- **自定义格式**: 可扩展的打包接口

#### 配置参数
```yaml
# common/configs/modules/04_pack.yaml
formats:
  ros:
    enabled: true
    compression: "bz2"
  coco:
    enabled: true
    split_ratios: [0.7, 0.2, 0.1]

validation:
  verify_integrity: true
  check_annotations: true
```

#### 输出产物
- `/data/datasets/scene_xxx/` - 标准化数据集
- `dataset.json` - 数据集元数据
- `checksums.txt` - 文件完整性校验

---

### 05_delivery - 数据交付模块 ▶

#### 模块职责
将处理完成的数据集上传到指定存储位置，并发送通知。

#### 交付方式
- **OSS 存储**: 阿里云对象存储
- **SFTP**: 安全文件传输协议
- **本地存储**: 直接保存到本地目录

#### 配置参数
```yaml
# common/configs/modules/05_delivery.yaml
oss:
  endpoint: ""
  bucket: ""
  region: "cn-hangzhou"

delivery:
  enable_notification: true
  notification_channels: ["email", "webhook"]
  retry_attempts: 3
```

---

## 4. 容器化架构 ▶

### 基础镜像设计
```dockerfile
# base/Dockerfile
FROM python:3.10-slim
# 安装系统依赖和Python基础包
# 创建标准目录结构
```

### 服务编排 (docker-compose.yml)
```yaml
version: '3.8'
services:
  ingest:       # 数据导入服务
    build: pipelines/00_ingest/Dockerfile
    depends_on: []
    
  quality:      # 质量检测服务
    build: pipelines/01_quality/Dockerfile
    depends_on: [ingest]
    
  enhance:      # 数据增强服务
    build: pipelines/02_enhance/Dockerfile
    depends_on: [quality]
    
  calibrate:    # 相机标定服务
    build: pipelines/03_calibrate/Dockerfile
    depends_on: [enhance]
    
  pack:         # 数据打包服务
    build: pipelines/04_pack/Dockerfile
    depends_on: [calibrate]
    
  delivery:     # 数据交付服务
    build: pipelines/05_delivery/Dockerfile
    depends_on: [pack]
    profiles: ["delivery"]  # 默认禁用
```

### 数据卷挂载策略
```yaml
volumes:
  - ./partdata/workshop_output:/data/workshop    # 处理中间结果
  - ./partdata/datasets:/data/datasets           # 最终数据集
  - ./partdata/raw:/data/input:ro               # 原始输入数据
  - ./common/configs:/app/common/configs:ro     # 配置文件共享
```

---

## 5. 数据流设计 ▶

### 标准数据流
```
Raw Data Input (L1)
        ↓
┌─────────────────┐
│   00_ingest     │  # 数据导入和标准化
└─────────────────┘
        ↓
┌─────────────────┐
│   01_quality    │  # 质量检测和评估
└─────────────────┘
        ↓
┌─────────────────┐
│   02_enhance    │  # 目标检测和增强
└─────────────────┘
        ↓
┌─────────────────┐
│   03_calibrate  │  # 相机标定
└─────────────────┘
        ↓
┌─────────────────┐
│   04_pack       │  # 数据打包
└─────────────────┘
        ↓
┌─────────────────┐
│   05_delivery   │  # 数据交付 (可选)
└─────────────────┘
        ↓
Standard Dataset (L2)
```

### 错误处理机制
- **模块隔离**: 各模块独立容器，故障不相互影响
- **数据校验**: 每个环节都有输入输出校验
- **重试机制**: 支持配置化的失败重试策略
- **日志追踪**: 统一日志格式，便于问题定位

---

## 6. 配置管理系统 ▶

### 配置层次结构
```
common/configs/
├── pipeline_config.yaml        # 全局流水线配置
├── modules/                    # 模块级配置
│   ├── 00_ingest.yaml         # 数据导入配置
│   ├── 01_quality.yaml        # 质量检测配置
│   ├── 02_enhance.yaml        # 数据增强配置
│   ├── 03_calibrate.yaml      # 相机标定配置
│   ├── 04_pack.yaml           # 数据打包配置
│   └── 05_delivery.yaml       # 数据交付配置
└── global.yaml                # 全局参数（预留）
```

### 配置加载机制
```python
# common/scripts/config_loader.py
def load_global_config():      # 加载全局配置
def load_module_config(name):  # 加载模块配置
def load_combined_config():    # 加载组合配置
```

---

## 7. 公共组件库 ▶

### 数据模型定义
```
common/schemas/
├── __init__.py
├── dataset.py      # 数据集模型
├── scene.py        # 场景元数据
├── sensor_stream.py # 传感器流模型
```

### IO 工具集
```python
# common/scripts/data_io/data_io.py
def load_scene_data(scene_dir):  # 场景数据加载
def save_processed_data():       # 处理结果保存
def validate_data_integrity():   # 数据完整性校验
```

---

## 8. 部署运维 ▶

### 构建脚本
```bash
# scripts/build_all.sh
#!/bin/bash
# 一键构建所有 Workshop 镜像
docker-compose build
```

### 启动服务
```bash
# 启动基础处理流程
docker-compose up -d ingest quality enhance calibrate pack

# 启动包括交付在内的完整流程
docker-compose --profile delivery up -d
```

### 监控面板
```bash
# 启动监控面板
streamlit run dashboard/app.py
```

---

## 9. 性能优化策略 ▶

### 资源管理
- **CPU优化**: 多进程并行处理
- **内存优化**: 分批处理大数据集
- **I/O优化**: 异步文件读写

### 缓存机制
- **配置缓存**: 配置文件预加载
- **模型缓存**: 检测模型常驻内存
- **中间结果缓存**: 避免重复计算

---

## 10. 安全与合规 ▶

### 数据保护
- **隐私处理**: 自动人脸模糊和敏感信息过滤
- **访问控制**: 容器内最小权限原则
- **数据加密**: 敏感配置文件加密存储

### 合规性
- **数据完整性**: 校验和验证机制
- **审计日志**: 完整的操作日志记录
- **版本控制**: 配置和代码版本管理

---

## 11. 开发路线图 ▶

### 当前状态
- ✅ 基础架构搭建完成
- ✅ Docker 容器化配置
- ✅ 各模块核心功能开发中 (80%)
- ⏳ 端到端集成测试
- ⏳ 性能基准测试

### 里程碑规划
```
v0.1 (当前)  - 架构原型和基础功能
v0.2         - 完整流水线实现
v0.3         - 性能优化和监控完善
v1.0         - 生产就绪版本
v1.5         - 高级功能和扩展支持
```

---

## 12. 集成接口 ▶

### 与 Deepness 集成
- **数据输出**: 生成 Deepness 兼容的输入格式
- **触发机制**: 文件系统事件监听或API调用
- **状态同步**: 处理进度回调通知

### API 接口规范
```python
# 标准化输入输出接口
class PipelineModule:
    def process(self, input_path: str, output_path: str) -> bool:
        """处理数据的主要接口"""
        pass
    
    def validate_input(self, input_path: str) -> bool:
        """验证输入数据完整性"""
        pass
    
    def generate_report(self) -> Dict:
        """生成处理报告"""
        pass
```

---

*文档版本: v1.0*
*最后更新: 2026年2月22日*