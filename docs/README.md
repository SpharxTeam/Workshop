# Workshop - 物理世界数据工厂

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](#)

**SpharxHub 核心子系统 - 从传感器到标准化数据集的自动化流水线**

</div>

## 📋 项目概述

Workshop 是 SpharxHub 平台的数据采集和预处理子系统，采用模块化、容器化的设计理念，通过六个核心处理管道实现从原始传感器数据到标准化高质量数据集的完整转换链路。

### 🎯 核心功能

- **数据导入** (`00_ingest`): 解析 RealSense 数据，隐私脱敏处理
- **质量检测** (`01_quality`): 多层次质量评估和异常检测
- **数据增强** (`02_enhance`): YOLOv8 目标检测和图像增强
- **相机标定** (`03_calibrate`): 内外参标定和参数优化
- **数据打包** (`04_pack`): 标准格式打包和完整性验证
- **数据交付** (`05_delivery`): 多种存储协议的数据交付

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Workshop 系统架构                         │
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

## 🚀 快速开始

### 环境要求

- **操作系统**: Ubuntu 22.04 / Windows 10+
- **Docker**: 20.10+
- **内存**: 16GB+ RAM
- **存储**: 100GB+ 可用空间

### 安装部署

```bash
# 克隆项目
git clone https://gitee.com/spharx/spharxhub.git
cd spharxhub/workshop

# 构建基础镜像
docker-compose build base

# 构建所有服务
./scripts/build_all.sh

# 启动完整流水线
docker-compose up -d
```

### 使用示例

```bash
# 处理单个数据文件
./scripts/pipeline/run_full.sh /path/to/your/recording.bag

# 启动监控面板
streamlit run dashboard/app.py
```

## 📁 目录结构

```
workshop/
├── base/                    # 基础 Docker 镜像
├── common/                  # 公共组件
│   ├── configs/            # 配置文件
│   │   ├── modules/        # 模块级配置
│   │   └── pipeline_config.yaml  # 全局配置
│   ├── schemas/            # 数据模型
│   ├── scripts/            # 公共脚本
│   └── tests/              # 测试框架
├── hardware/                # 硬件控制模块
├── pipelines/               # 处理管道
│   ├── 00_ingest/          # 数据导入
│   ├── 01_quality/         # 质量检测
│   ├── 02_enhance/         # 数据增强
│   ├── 03_calibrate/       # 相机标定
│   ├── 04_pack/            # 数据打包
│   └── 05_delivery/        # 数据交付
├── dashboard/               # Web 监控面板
├── partdata/                # 数据目录
│   ├── raw/                # 原始数据
│   ├── workshop_output/    # 处理结果
│   ├── datasets/           # 最终数据集
│   └── docs/               # 文档资料
└── scripts/                 # 构建和部署脚本
```

## ⚙️ 配置管理

### 全局配置
```yaml
# common/configs/pipeline_config.yaml
global:
  data_root: /data
  log_dir: /logs

modules:
  ingest:
    enabled: true
    method: "realsense"
  # ... 其他模块配置
```

### 模块配置示例
```yaml
# common/configs/modules/00_ingest.yaml
privacy:
  enable_blur: true
  blur_kernel_size: 15

data_format:
  output_structure: "standard"
  compression_level: 6
```

## 🛠️ 开发指南

### 本地开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements.dev.txt

# 运行测试
pytest tests/

# 代码格式化
black .
flake8 .
```

### 添加新模块

1. 在 `pipelines/` 目录下创建新模块目录
2. 编写 `Dockerfile` 和 `runner.py`
3. 添加模块配置文件
4. 更新 `docker-compose.yml`

## 📊 监控与日志

### 日志级别
- **DEBUG**: 详细调试信息
- **INFO**: 一般运行信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息

### 监控面板
访问 `http://localhost:8501` 查看实时监控信息

## 🔧 故障排除

### 常见问题

1. **Docker 构建失败**
   ```bash
   # 清理缓存重新构建
   docker-compose build --no-cache
   ```

2. **权限问题**
   ```bash
   # 确保数据目录权限正确
   sudo chown -R $(id -u):$(id -g) partdata/
   ```

3. **GPU 支持**
   ```bash
   # 启用 GPU 支持
   export GPU_ENABLED=true
   ```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

### 代码规范
- 遵循 PEP 8 编码规范
- 编写单元测试
- 更新相关文档

## 📚 相关文档

- [📘 架构设计文档](partdata/docs/WORKSHOP_ARCH.md)
- [📈 项目进度报告](PROGRESS.md)
- [⚙️ 配置文件说明](common/configs/)

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](../LICENSE) 文件。

---

<div align="center">

**Workshop** —— 构建 AI 时代的物理世界数据基础设施

*SpharxHub 核心子系统*

</div>