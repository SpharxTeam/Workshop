# 🏭 SpharxWorkshop - 空间智能数据生产线

> 全自动、开源、云原生的空间智能数据集生产平台

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-555555.svg)]()

## ✨ 项目亮点

- **🤖 全自动化**：从原始图像到多模态数据集，全流程无人化处理
- **📦 容器化部署**：基于Docker，一键部署，环境一致
- **🔓 完全开源**：工具链100%开源，无供应商锁定
- **🌐 云原生设计**：支持本地、云端、混合部署
- **📈 可扩展架构**：模块化设计，轻松添加新处理模块
- **🔧 低技术门槛**：面向非技术用户，简单配置即可运行

## 🎯 应用场景

- **自动驾驶**：生成3D标注训练数据
- **机器人视觉**：生产机器人操作场景数据集
- **AR/VR/MR**：创建室内外3D环境资产
- **智慧城市**：大规模城市场景数字化
- **工业检测**：生成缺陷检测训练数据

## 📁 项目结构

toolchain/
├── .env.template              # 环境配置模板（复制为.env）
├── docker-compose.yml         # 服务编排核心
├── Dockerfile                 # 主控制器镜像构建
├── requirements.txt           # Python依赖列表
│
├── deploy/                    # 部署脚本
│   ├── 01-init-server.sh     # 服务器初始化
│   ├── 02-clone-repos.sh     # 仓库克隆
│   └── 03-setup-directories.sh # 目录创建
│
├── src/                       # 源代码
│   ├── main.py               # 主程序入口
│   ├── pipelines/            # 双轨流水线
│   │   ├── 01_preprocess/    # 预处理
│   │   ├── 02_2d_annotation/ # 2D自动标注
│   │   ├── 03_3d_reconstruction/ # 3D重建
│   │   ├── 04_2d_to_3d_lifting/ # 2D转3D提升
│   │   ├── 05_physics_generation/ # 物理事实生成
│   │   └── 06_dataset_assembly/ # 数据集打包
│   │
│   ├── agents/               # 智能体模块（阶段二）
│   ├── utils/                # 工具函数
│   └── schemas/              # 数据模型（Pydantic）
│
├── configs/                  # 配置文件
│   ├── logging.yaml          # 日志配置
│   ├── 2d_annotation/        # SAM、CVAT配置
│   ├── 3d_reconstruction/    # COLMAP、Open3D配置
│   └── physics/              # Blender仿真模板
│
├── docker/                   # 各工具Docker镜像
│   ├── cvat/                 # CVAT标注平台
│   ├── colmap/               # COLMAP 3D重建
│   ├── sam/                  # Segment Anything
│   └── base/                 # Python基础镜像
│
├── scripts/                  # 运维脚本
│   ├── run_2d_pipeline.sh    # 运行2D流水线
│   ├── run_full_pipeline.sh  # 运行完整流水线
│   └── health_check.sh       # 健康检查
│
└── docs/                     # 项目文档
    ├── ARCHITECTURE_V2.md    # 架构说明
    ├── DEPLOYMENT.md         # 部署指南
    └── API.md                # API接口文档

## 🚀 快速开始

### 前提条件

- **Docker 20.10+** 和 **Docker Compose 2.20+**
- **Git** 版本控制
- **阿里云账号**（用于OSS存储）
- **至少8GB内存**，建议16GB+
- **50GB可用磁盘空间**

### 1. 本地开发环境设置

# 克隆仓库（如果从Gitee获取）
git clone git@gitee.com:spharx/toolchain.git
cd toolchain

# 复制环境配置模板
cp .env.template .env

# 编辑环境变量（重要！）
# 使用文本编辑器打开 .env 文件，至少修改以下配置：
# - OSS_ENDPOINT: 阿里云OSS节点
# - OSS_BUCKET: 存储桶名称
# - OSS_ACCESS_KEY_ID: 访问密钥ID
# - OSS_ACCESS_KEY_SECRET: 访问密钥
nano .env  # 或使用其他编辑器

### 2. 构建并启动服务

# 构建Docker镜像（首次运行或更新后）
docker-compose build

# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f spharx-controller

### 3. 验证安装

# 进入控制器容器
docker-compose exec spharx-controller bash

# 运行健康检查
python src/main.py --health-check

# 测试环境变量加载
python -c "import os; print('PROJECT_NAME:', os.getenv('PROJECT_NAME'))"

# 退出容器
exit

### 4. 运行第一个数据处理任务

# 准备示例数据
mkdir -p /home/SpharxWorkshop/data/input/scenes/demo_scene_001/images

# 放入一些测试图像（JPEG格式）
# cp /path/to/your/images/*.jpg /home/SpharxWorkshop/data/input/scenes/demo_scene_001/images/

# 运行2D标注流水线
docker-compose exec spharx-controller python src/main.py --pipeline 2d --scene demo_scene_001

# 或使用脚本
./scripts/run_2d_pipeline.sh demo_scene_001

## 📊 数据处理流程

graph TD
    A[原始图像数据] --> B[预处理模块]
    B --> C{选择流水线}
    
    C -->|2D优先| D[2D自动标注]
    D --> E[人工审核/修正]
    E --> F[2D标注数据集 L1]
    
    C -->|3D重建| G[多视图几何重建]
    G --> H[点云生成]
    H --> I[网格化与纹理]
    I --> J[3D几何数据集 L2]
    
    F --> K[2D转3D标签提升]
    J --> K
    
    K --> L[物理事实生成]
    L --> M[物理仿真验证]
    M --> N[物理事实数据集 L3]
    
    F --> O[数据集组装]
    J --> O
    N --> O
    
    O --> P[质量检验]
    P --> Q[格式标准化]
    Q --> R[上传OSS]
    
    R --> S[✔️ 成品数据集]

## ⚙️ 配置说明

### 环境变量（.env文件）

关键配置项：

| 变量 | 说明 | 示例值 |
|------|------|--------|
| PROJECT_STAGE | 运行环境 | DEVELOPMENT |
| SPHARX_INPUT_DIR | 原始数据目录 | /home/SpharxWorkshop/data/input/scenes |
| OSS_ENDPOINT | 阿里云OSS节点 | oss-cn-hangzhou.aliyuncs.com |
| OSS_BUCKET | OSS存储桶 | spharx-datasets |
| ENABLE_2D_PIPELINE | 启用2D流水线 | true |
| ENABLE_3D_PIPELINE | 启用3D流水线 | false |

### 流水线开关

在 `.env` 中控制流水线模块：

# 基础配置（建议从2D开始）
ENABLE_2D_PIPELINE=true      # 2D标注流水线
ENABLE_3D_PIPELINE=false     # 3D重建流水线（较耗时）
ENABLE_PHYSICS_PIPELINE=false # 物理事实生成

# 高级配置
ENABLE_AUTO_QUALITY_CHECK=true
ENABLE_CLOUD_SYNC=true
MAX_CONCURRENT_TASKS=4

## 🔧 运维管理

### 常用命令

# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f [服务名]

# 进入容器
docker-compose exec spharx-controller bash

# 备份数据
./scripts/backup_data.sh

# 系统健康检查
./scripts/health_check.sh

### 监控与日志

- 服务日志：`docker-compose logs -f`
- 流水线日志：`workspace/logs/pipeline/`
- 访问统计：默认端口8081（可在.env中修改）

## 🐛 故障排除

### 常见问题

**Q1: Docker构建失败，提示内存不足**

# 增加Docker内存限制（Docker Desktop）
# 或使用交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

**Q2: 阿里云OSS连接失败**

1. 检查 .env 中的OSS配置
2. 验证网络连接：curl oss-cn-hangzhou.aliyuncs.com
3. 检查防火墙设置

**Q3: 权限错误**

# 修复目录权限
sudo chown -R $USER:$USER /home/SpharxWorkshop
sudo chmod -R 755 /home/SpharxWorkshop

### 调试模式

# 启用详细日志
export LOG_LEVEL=DEBUG
docker-compose up

# 单步调试流水线
docker-compose exec spharx-controller python -m pdb src/main.py --pipeline test

## 📈 性能优化

### 硬件建议

| 场景 | CPU | 内存 | 存储 | GPU |
|------|-----|------|------|-----|
| 开发测试 | 4核+ | 8GB+ | 100GB SSD | 可选 |
| 生产小规模 | 8核+ | 16GB+ | 500GB NVMe | RTX 3060+ |
| 生产大规模 | 16核+ | 32GB+ | 2TB NVMe | RTX 4090+ |

### 配置调优

# .env 中的性能相关配置
COLMAP_MAX_IMAGE_SIZE=1600    # 图像最大尺寸
COLMAP_MAX_FEATURES=8192      # 特征点数量
MAX_CONCURRENT_TASKS=4        # 并发任务数
TASK_TIMEOUT_SECONDS=7200     # 任务超时时间

## 🤝 贡献指南

欢迎贡献代码！请阅读 `CONTRIBUTING.md` 了解详情。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 Apache License 2.0 开源许可证。详见 `LICENSE` 文件。

## 📞 支持与联系

- 项目文档：https://gitee.com/spharx/toolchain/wikis
- 问题反馈：https://gitee.com/spharx/toolchain/issues
- 讨论区：https://gitee.com/spharx/toolchain/issues

## 🙏 致谢

感谢以下开源项目的支持：

- [COLMAP](https://colmap.github.io/) - 3D重建
- [Open3D](http://www.open3d.org/) - 3D数据处理
- [Segment Anything](https://segment-anything.com/) - 2D分割
- [Docker](https://www.docker.com/) - 容器化平台
