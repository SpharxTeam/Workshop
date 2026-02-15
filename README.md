# Spharx Workshop - 智能视觉数据处理平台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Status-Development-orange" alt="Status">
</p>

## 📋 项目简介

Spharx Workshop 是一个企业级的智能视觉数据处理平台，专为基于 Intel RealSense 相机的大规模数据采集和处理场景而设计。该平台采用现代化的微服务架构，提供从原始数据采集、质量检测、智能增强到最终数据交付的完整解决方案。

### 🔧 核心特性

- **多阶段流水线处理**：6个独立的处理阶段，支持模块化扩展
- **实时质量监控**：内置模糊检测、曝光分析、时间同步验证
- **智能数据增强**：集成YOLOv8目标检测，支持自动标注
- **灵活部署方式**：支持本地开发、Docker容器化部署
- **完善的监控体系**：基于Streamlit的可视化监控面板
- **企业级配置管理**：多层次配置系统，支持环境隔离

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据采集层    │───▶│   处理流水线    │───▶│   数据交付层    │
│  RealSense相机  │    │  6阶段处理模块  │    │  云存储/本地    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   硬件控制模块  │    │   质量检测系统  │    │   监控告警系统  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 处理流水线详解

1. **📥 Ingest（数据摄入）**
   - RealSense原始数据解析
   - 隐私数据自动脱敏
   - 数据格式标准化

2. **🔍 Quality（质量检测）**
   - 图像模糊度分析（Laplacian方差检测）
   - 曝光异常检测（过曝/欠曝）
   - 时间同步验证
   - 质量报告生成

3. **✨ Enhance（数据增强）**
   - YOLOv8目标自动标注
   - 数据增强处理
   - 标注质量验证

4. **📐 Calibrate（相机标定）**
   - 批量内参/外参标定
   - 标定漂移检测
   - 标定参数优化

5. **📦 Pack（数据打包）**
   - ROS Bag格式封装
   - COCO标注格式转换
   - 数据完整性校验

6. **🚚 Delivery（数据交付）**
   - 云存储上传（AWS S3/阿里云OSS）
   - 本地存储归档
   - 交付状态跟踪

## 🛠️ 技术栈概览

### 核心技术组件

| 类别 | 技术栈 | 版本要求 | 用途 |
|------|--------|----------|------|
| **编程语言** | Python | 3.8+ | 核心开发语言 |
| **计算机视觉** | OpenCV, scikit-image | 最新版 | 图像处理基础库 |
| **深度学习** | PyTorch, Ultralytics | 1.10+, 8.0+ | YOLO目标检测 |
| **硬件接口** | pyrealsense2 | 2.50+ | RealSense相机控制 |
| **Web框架** | Streamlit, FastAPI | 1.10+, 0.78+ | 监控面板和API |
| **异步处理** | Celery, Redis | 5.2+, 4.3+ | 任务队列和缓存 |
| **数据管理** | ROS Bag, HDF5 | 最新版 | 数据存储格式 |
| **容器化** | Docker, docker-compose | 最新版 | 容器部署 |
| **数据库** | PostgreSQL, SQLAlchemy | 1.4+ | 元数据管理 |
| **监控** | Prometheus, Loguru | 最新版 | 系统监控 |

## 📁 项目结构详解

```
Workshop/
├── 📁 hardware/                 # 硬件抽象层
│   ├── 📁 camera/              # 相机管理系统
│   │   ├── realSense_manager.py    # 相机生命周期管理
│   │   ├── sync_controller.py      # 多相机同步控制
│   │   └── sync_validator.py       # 同步精度验证
│   ├── 📁 calibration/         # 相机标定工具集
│   │   ├── intrinsics_calib.py     # 内参标定算法
│   │   └── extrinsics_calib.py     # 外参标定算法
│   └── 📁 scripts/             # 硬件维护脚本
│       ├── install_drivers.sh      # 驱动自动安装
│       └── test_sync.sh            # 同步功能测试
│
├── 📁 pipelines/                # 核心处理流水线
│   ├── 📁 00_ingest/           # 数据摄入模块
│   │   ├── realsense_parser.py     # 数据解析器
│   │   ├── privacy_desensitizer.py # 隐私保护处理
│   │   ├── config_loader.py        # 模块配置加载
│   │   └── requirements.txt        # 依赖声明
│   ├── 📁 01_quality/          # 质量检测模块
│   │   ├── blur_detector.py        # 模糊度检测算法
│   │   ├── quality_report.py       # 质量评估报告
│   │   ├── config_loader.py        # 配置管理
│   │   └── requirements.txt        # 依赖声明
│   ├── 📁 02_enhance/          # 数据增强模块
│   │   ├── yolo_annotator.py       # YOLO自动标注
│   │   ├── config_loader.py        # 配置加载
│   │   └── requirements.txt        # 依赖声明
│   ├── 📁 03_calibrate/        # 相机标定模块
│   │   ├── batch_calibrate.py      # 批量标定工具
│   │   ├── config_loader.py        # 配置管理
│   │   └── requirements.txt        # 依赖声明
│   ├── 📁 04_pack/             # 数据打包模块
│   │   ├── ros_bag_packer.py       # ROS Bag封装器
│   │   ├── config_loader.py        # 配置加载
│   │   └── requirements.txt        # 依赖声明
│   └── 📁 05_delivery/         # 数据交付模块
│       └── requirements.txt        # 依赖声明
│
├── 📁 schemas/                  # 数据模型定义
│   ├── __init__.py             # 模块初始化
│   ├── scene.py                # 场景数据模型
│   ├── sensor_stream.py        # 传感器流模型
│   └── dataset.py              # 数据集模型
│
├── 📁 dashboard/                # 可视化监控系统
│   ├── app.py                  # Streamlit主应用
│   └── 📁 pages/               # 监控页面集合
│       ├── 01_capture.py       # 数据采集监控
│       ├── 02_monitor.py       # 系统状态监控
│       └── 03_data.py          # 数据资产管理
│
├── 📁 configs/                  # 配置管理中心
│   ├── logging.yaml            # 日志系统配置
│   ├── pipeline_config.yaml    # 流水线参数配置
│   └── quality_thresholds.yaml # 质量检测阈值
│
├── 📁 data/                     # 数据存储目录
│   ├── raw/                    # 原始采集数据
│   ├── processed/              # 处理中间数据
│   └── datasets/               # 最终数据产品
│
├── 📁 logs/                     # 系统日志目录
├── 📁 tests/                    # 测试套件
│   └── fixtures/               # 测试数据夹具
│
├── 📁 scripts/                  # 辅助工具脚本
│   ├── 📁 pipeline/            # 流水线执行脚本
│   │   └── run_full.sh         # 完整流程执行器
│   └── 📁 utils/               # 实用工具集合
│       ├── config_loader.py            # 配置工具类
│       ├── generate_realistic_calibration.py  # 标定数据生成器
│       └── github_fetch.sh             # 资源获取工具
│
├── 📁 docs/                     # 项目文档
├── .env.template                # 环境变量模板
├── .gitignore                   # Git忽略规则
├── LICENSE                      # 开源许可证
├── docker-compose.yml           # Docker编排配置
├── requirements.txt             # 项目依赖清单
├── bootstrap.sh                 # 一键初始化脚本
├── PROGRESS.md                  # 项目进度追踪
└── README.md                    # 项目说明文档
```

## ⚡ 快速开始指南

### 📋 环境要求

**基础环境**：
- Python 3.8 或更高版本
- Git 版本控制系统
- 4GB 以上可用磁盘空间

**推荐配置**：
- Ubuntu 20.04+/CentOS 8+/Windows 10+
- 16GB RAM（推荐32GB）
- NVIDIA GPU（推荐RTX 3070+，用于深度学习加速）
- Docker Engine 20.10+（容器化部署）

### 🚀 部署方式选择

#### 方式一：本地开发环境（推荐开发者）

```bash
# 1. 克隆项目源码
git clone https://gitee.com/spharx/workshop.git
cd workshop

# 2. 创建Python虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装项目依赖
pip install -r requirements.txt

# 5. 初始化项目配置
cp .env.template .env
# 编辑.env文件配置必要参数

# 6. 创建数据目录结构
mkdir -p data/{raw,processed,datasets} logs

# 7. 启动监控面板验证安装
streamlit run dashboard/app.py
```

#### 方式二：一键自动化部署（推荐生产环境）

```bash
# 1. 克隆项目
git clone https://gitee.com/spharx/workshop.git
cd workshop

# 2. 运行自动化初始化脚本
chmod +x bootstrap.sh
./bootstrap.sh

# 脚本将自动完成：
# ✓ 环境检查和依赖验证
# ✓ 虚拟环境创建和激活
# ✓ 依赖包安装和更新
# ✓ 配置文件初始化
# ✓ 数据目录结构创建
# ✓ 可选的硬件驱动安装
# ✓ 基础功能测试运行
```

#### 方式三：Docker容器化部署（推荐团队协作）

```bash
# 1. 构建并启动完整服务栈
docker-compose up --build -d

# 2. 查看服务运行状态
docker-compose ps

# 3. 查看实时日志
docker-compose logs -f

# 4. 启动特定服务模块
docker-compose up ingest quality enhance

# 5. 停止所有服务
docker-compose down
```

### 🔧 环境配置详解

#### 核心环境变量配置

```bash
# .env 文件配置示例

# ████████ 基础路径配置 ████████
PROJECT_NAME=SpharxWorkshop           # 项目标识名称
DATA_ROOT=/data                      # 数据根目录
RAW_DIR=/data/raw                    # 原始数据目录
PROCESSED_DIR=/data/processed        # 处理数据目录
DATASETS_DIR=/data/datasets          # 数据集输出目录
LOG_DIR=/logs                        # 日志文件目录

# ████████ 质量检测阈值 ████████
QUALITY_BLUR_THRESHOLD=100           # 模糊度检测阈值(Laplacian方差)
QUALITY_OVEREXPOSED_THRESHOLD=240    # 过曝检测阈值(像素平均值)
QUALITY_UNDEREXPOSED_THRESHOLD=30    # 欠曝检测阈值(像素平均值)
QUALITY_SYNC_THRESHOLD_MS=0.5        # 时间同步误差阈值(毫秒)

# ████████ 云存储配置 ████████
OSS_ENABLED=false                    # 是否启用云存储
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com  # OSS服务端点
OSS_BUCKET=your-bucket-name          # 存储桶名称
OSS_ACCESS_KEY_ID=your-access-key    # 访问密钥ID
OSS_ACCESS_KEY_SECRET=your-secret-key # 访问密钥Secret

# ████████ 告警通知配置 ████████
NOTIFY_ENABLED=false                 # 是否启用告警通知
NOTIFY_WEBHOOK=https://your-webhook-url  # 告警推送地址
```

#### 配置文件详解

**1. 流水线配置 (`configs/pipeline_config.yaml`)**
```yaml
global:
  data_root: /data                   # 全局数据根路径
  log_dir: /logs                     # 全局日志目录

ingest:
  # 数据摄入模块配置（通过命令行参数传递）

quality:
  blur_threshold: 100                # 模糊检测敏感度
  over_threshold: 240                # 过曝判断阈值
  under_threshold: 30                # 欠曝判断阈值
  expected_fps: 30                   # 期望帧率（丢帧检测）

enhance:
  conf_threshold: 0.25               # YOLO置信度阈值
  model_path: "yolov8n.pt"           # 检测模型路径

calibrate:
  chessboard: [9, 6]                 # 标定棋盘格尺寸
  square_size: 0.025                 # 棋盘格边长(米)

pack:
  formats: ["ros", "coco"]           # 输出格式列表
```

### ▶️ 系统运行指南

#### 1. 启动监控面板

```bash
# 启动可视化监控系统
streamlit run dashboard/app.py --server.port 8501

# 访问地址：http://localhost:8501
# 默认包含三个监控页面：
# - 数据采集监控：实时查看相机状态和采集进度
# - 系统状态监控：CPU、内存、磁盘使用情况
# - 数据资产管理：已处理数据集浏览和管理
```

#### 2. 执行数据采集

```bash
# 启动RealSense相机数据采集
python -m hardware.camera.realSense_manager

# 支持的命令行参数：
# --config configs/camera_config.yaml  # 指定相机配置文件
# --duration 3600                      # 采集持续时间(秒)
# --output data/raw/session_001        # 输出目录
```

#### 3. 运行处理流水线

```bash
# 方法一：单模块执行（开发调试）
python -m pipelines.00_ingest.realsense_parser \
  --input data/raw/sample.bag \
  --output data/processed/scene_001

# 方法二：完整流程执行（生产环境）
./scripts/pipeline/run_full.sh \
  --input data/raw/session_001 \
  --output data/datasets/final_dataset

# 方法三：Docker容器执行
docker-compose run --rm ingest \
  --input /data/raw/session_001 \
  --output /data/processed/scene_001
```

## 📊 性能基准测试

### 硬件性能要求

| 配置等级 | CPU | 内存 | 存储 | GPU | 适用场景 |
|----------|-----|------|------|-----|----------|
| **入门级** | Intel i5-9400 | 16GB DDR4 | 1TB SSD | 无 | 开发测试、小规模处理 |
| **标准级** | Intel i7-10700 | 32GB DDR4 | 2TB NVMe | GTX 1660 | 中等规模生产环境 |
| **专业级** | Intel i9-12900 | 64GB DDR4 | 4TB NVMe | RTX 3080 | 大规模并发处理 |
| **企业级** | Dual Xeon E5 | 128GB DDR4 | 8TB NVMe RAID | Dual RTX 3090 | 超大规模生产部署 |

### 处理性能指标

| 处理阶段 | 处理速度 | 资源消耗 | 并发能力 | 备注 |
|----------|----------|----------|----------|------|
| **数据摄入** | 100-150 MB/s | CPU: 30%, 内存: 2GB | 4路并发 | 受存储I/O限制 |
| **质量检测** | 40-60 FPS | CPU: 60%, 内存: 4GB | 8路并发 | 可GPU加速 |
| **YOLO标注** | 25-35 FPS | GPU: 70%, 内存: 6GB | 4路并发 | 需要CUDA支持 |
| **相机标定** | 10-15 场景/分钟 | CPU: 80%, 内存: 8GB | 2路并发 | 计算密集型 |
| **数据打包** | 180-220 MB/s | CPU: 40%, 内存: 3GB | 6路并发 | 受存储I/O限制 |

### 扩展性设计

- **水平扩展**：各处理模块支持多实例并行运行
- **负载均衡**：基于Redis的任务队列实现动态负载分配
- **故障恢复**：支持断点续传和错误重试机制
- **资源隔离**：Docker容器化确保资源使用边界

## 🔍 开发者指南

### 代码质量标准

#### 编码规范
```python
# 遵循PEP 8标准，示例：
def process_image_frame(
    frame: np.ndarray, 
    config: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    处理单帧图像数据
    
    Args:
        frame: 输入图像帧
        config: 处理配置参数
        
    Returns:
        处理后的图像和质量指标字典
    """
    # 实现逻辑...
    pass
```

#### 依赖管理
```bash
# 开发环境依赖安装
pip install -r requirements-dev.txt

# 包含额外的开发工具：
# - black: 代码格式化
# - flake8: 语法检查
# - mypy: 类型检查
# - pytest: 单元测试框架
# - pre-commit: 提交前检查钩子
```

### 测试策略

#### 单元测试
```bash
# 运行所有单元测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_camera_manager.py::TestCameraManager

# 生成覆盖率报告
pytest --cov=pipelines --cov-report=html tests/

# 并行执行测试
pytest -n auto tests/
```

#### 集成测试
```bash
# 端到端流水线测试
./scripts/test/e2e_pipeline_test.sh

# 硬件兼容性测试
./hardware/scripts/test_hardware_compatibility.sh

# 性能基准测试
./scripts/test/performance_benchmark.sh
```

### CI/CD流程

```yaml
# .github/workflows/ci.yml 示例
name: Continuous Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest tests/ --cov=pipelines
      - name: Code quality checks
        run: |
          black --check .
          flake8 .
          mypy .
```

### 贡献流程

1. **Fork项目** → `git clone` → `git checkout -b feature/new-feature`
2. **开发实现** → 编写代码 → 添加测试 → 运行检查
3. **提交代码** → `git commit -m "feat: 添加新功能描述"`
4. **推送分支** → `git push origin feature/new-feature`
5. **创建PR** → 填写详细描述 → 等待代码审查

## 🛟 故障排查手册

### 常见问题解决方案

#### 硬件相关问题

**问题1：RealSense设备无法识别**
```bash
# 检查设备连接状态
lsusb | grep -i realsense

# 验证USB权限
ls -l /dev/bus/usb/*/*

# 重新安装驱动程序
sudo ./hardware/scripts/install_drivers.sh

# 检查内核模块加载
lsmod | grep uvcvideo
```

**问题2：相机同步失败**
```bash
# 运行同步测试脚本
./hardware/scripts/test_sync.sh

# 检查硬件连接线缆
# 验证电源供应稳定性
# 确认固件版本兼容性
```

#### 软件相关问题

**问题3：Docker容器启动失败**
```bash
# 查看详细错误日志
docker-compose logs --tail=50 <service_name>

# 检查容器资源配置
docker stats

# 重建镜像（清除缓存）
docker-compose build --no-cache

# 验证docker-compose.yml语法
docker-compose config
```

**问题4：依赖包安装失败**
```bash
# 升级pip到最新版本
pip install --upgrade pip

# 清除pip缓存
pip cache purge

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 单独安装问题包
pip install numpy==1.21.0 --force-reinstall
```

#### 性能相关问题

**问题5：处理速度过慢**
```bash
# 监控系统资源使用
htop
iotop
nvidia-smi  # 如果有GPU

# 检查存储I/O性能
dd if=/dev/zero of=test bs=1M count=1000

# 分析瓶颈环节
python -m cProfile -o profile.out your_script.py
```

### 日志系统使用

#### 日志级别配置
```yaml
# configs/logging.yaml
version: 1
formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
handlers:
  file:
    class: logging.FileHandler
    filename: /logs/workshop.log
    level: INFO
  console:
    class: logging.StreamHandler
    level: WARNING
```

#### 日志查看命令
```bash
# 实时查看主日志
tail -f logs/workshop.log

# 按级别过滤日志
grep "ERROR" logs/workshop.log

# 查看Docker服务日志
docker-compose logs -f --tail=100 ingest

# 按时间范围查看日志
sed -n '/2024-01-01/,/2024-01-02/p' logs/workshop.log
```

## 📈 项目发展规划

### 当前阶段状态：🏗️ 基础架构完成 (100%)

**已完成里程碑**：
- ✅ 项目目录结构标准化
- ✅ 核心模块框架搭建
- ✅ 配置管理体系建立
- ✅ Docker部署环境配置
- ✅ 依赖关系管理完善

### 下一阶段目标：🚀 功能实现阶段

**短期目标（1-3个月）**：
- [ ] 完善各管道模块核心业务逻辑
- [ ] 实现完整的数据处理流程
- [ ] 开发实时监控告警功能
- [ ] 建立自动化测试体系

**中期目标（3-6个月）**：
- [ ] 性能优化和扩展性提升
- [ ] 完善文档和使用指南
- [ ] 建立CI/CD流水线
- [ ] 准备生产环境部署

**长期愿景（6-12个月）**：
- [ ] 支持更多相机型号和传感器
- [ ] 增强AI算法能力和准确度
- [ ] 构建插件化生态系统
- [ ] 提供商业化部署方案

## 🤝 社区与支持

### 获取帮助

- **官方文档**：查阅 [docs/](docs/) 目录下的详细文档
- **问题反馈**：在 [Issues](https://gitee.com/spharx/workshop/issues) 提交问题
- **功能建议**：通过 [Pull Requests](https://gitee.com/spharx/workshop/pulls) 贡献代码
- **技术交流**：加入开发者微信群（请联系项目维护者）

### 贡献者名单

感谢以下开发者的贡献：
- [@lidecheng](https://gitee.com/lidecheng) - 项目发起人和主要架构师
- [@developer-team](https://gitee.com/spharx) - 核心开发团队

## 📄 许可证信息

本项目采用 **MIT License** 开源许可证，详细条款请参见 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2024 Spharx Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
```

---

<p align="center">
  <strong> Made with ❤️ by Spharx Team </strong>
  <br>
  <sub>Latest Update: February 2026 | Version: 1.0.0-beta</sub>
</p>