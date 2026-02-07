# Spharx Toolchain 架构设计

## 系统概述

Spharx Toolchain 是一个模块化的空间智能数据处理流水线系统，采用"先2D后3D"的设计理念，通过配置驱动的方式实现数据处理的标准化和自动化。

## 核心架构

### 1. 流水线引擎 (Pipeline Engine)
- **职责**: 阶段调度、状态管理、错误处理
- **组件**: `src/pipeline/engine.py`
- **特点**: 插件化设计，支持动态阶段注册

### 2. 处理阶段 (Processing Stages)
按顺序编号的处理模块：
- `00_input_validation.py`: 输入数据验证
- `01_2d_annotation.py`: 2D自动标注
- `02_2d_product_assembly.py`: 2D产品打包
- `03_3d_reconstruction.py`: 3D几何重建
- `04_2d_to_3d_lift.py`: 2D到3D标签提升
- `05_physics_generation.py`: 物理属性生成
- `06_3d_product_assembly.py`: 3D产品打包
- `99_output_export.py`: 输出导出

### 3. 服务封装层 (Services Layer)
对外部工具和服务的统一封装：
- CVAT客户端
- SAM自动标注器
- COLMAP重建工具
- SA3D提升工具
- Blender物理引擎

### 4. 产品定义 (Products)
标准化的数据产品输出：
- Spharx 2D标注数据集
- Spharx 3D几何数据集
- Spharx 3D物理事实数据集

## 数据流向

```
输入数据 → 验证 → 2D标注 → 2D产品 → [3D重建] → [标签提升] → [物理生成] → 3D产品 → 输出
```

## 配置管理

系统采用分层配置：
- **环境变量**: 基础运行参数
- **YAML配置**: 流水线阶段参数
- **INI模板**: 工具特定配置
- **JSON Schema**: 产品规范定义

## 部署架构

### 容器化设计
- 每个核心组件独立Docker化
- 支持GPU加速
- 资源隔离和限制

### 服务编排
- Docker Compose管理多服务
- 支持最小2D部署和完整3D部署
- 健康检查和自动重启

## 扩展机制

### 插件化阶段
新的处理阶段只需继承`PipelineStage`基类并实现相应接口。

### 服务适配器
外部工具通过服务封装层集成，保持接口一致性。

### 配置驱动
所有行为通过配置文件控制，无需修改代码。