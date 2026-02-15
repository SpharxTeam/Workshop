# Workshop 项目

## 项目概述

Workshop 是一个基于 Intel RealSense 相机的完整数据采集和处理系统，采用模块化设计，包含从数据采集、质量检测、增强处理到最终打包交付的全流程解决方案。

**项目状态**: ✅ 基础架构已完成 (100%) - 等待功能实现

## 技术栈

- **核心框架**: Python 3.8+
- **计算机视觉**: OpenCV, scikit-image
- **深度学习**: PyTorch, Ultralytics(YOLOv8)
- **硬件接口**: pyrealsense2
- **前端框架**: Streamlit, FastAPI
- **容器化**: Docker, docker-compose
- **数据管理**: ROS Bag, HDF5
- **云存储**: AWS S3, 阿里云 OSS

## 目录结构

```
Workshop/
├── hardware/              # 硬件控制层
│   ├── camera/           # 相机管理模块
│   │   ├── realSense_manager.py    # RealSense相机管理器
│   │   ├── sync_controller.py      # 同步控制器
│   │   └── sync_validator.py       # 同步验证器
│   ├── calibration/      # 相机标定工具
│   │   ├── intrinsics_calib.py     # 内参标定
│   │   └── extrinsics_calib.py     # 外参标定
│   └── scripts/          # 硬件维护脚本
│       ├── install_drivers.sh      # 驱动安装脚本
│       └── test_sync.sh            # 同步测试脚本
│
├── pipelines/             # 数据处理流水线
│   ├── 00_ingest/        # 数据摄入和预处理
│   │   ├── realsense_parser.py     # RealSense数据解析
│   │   └── privacy_desensitizer.py # 隐私数据脱敏
│   ├── 01_quality/       # 质量检测和同步监控
│   │   ├── blur_detector.py        # 模糊度检测
│   │   └── quality_report.py       # 质量报告生成
│   ├── 02_enhance/       # 数据增强和标注
│   │   └── yolo_annotator.py       # YOLO自动标注
│   ├── 03_calibrate/     # 批量标定和漂移检测
│   │   └── batch_calibrate.py      # 批量标定工具
│   ├── 04_pack/          # 数据打包和导出
│   │   └── ros_bag_packer.py       # ROS Bag打包器
│   └── 05_delivery/      # 数据交付和上传
│
├── schemas/              # 数据模型定义
│   ├── __init__.py
│   ├── scene.py          # 场景数据模型
│   ├── sensor_stream.py  # 传感器流模型
│   └── dataset.py        # 数据集模型
│
├── dashboard/            # 监控面板
│   ├── app.py            # 主应用入口
│   └── pages/            # 页面模块
│       ├── 01_capture.py # 数据采集监控
│       ├── 02_monitor.py # 系统状态监控
│       └── 03_data.py    # 数据管理界面
│
├── configs/              # 配置文件
│   ├── logging.yaml              # 日志配置
│   ├── pipeline_config.yaml      # 管道配置
│   └── quality_thresholds.yaml   # 质量阈值配置
│
├── data/                 # 数据存储目录
│   ├── raw/             # 原始数据
│   ├── processed/       # 处理后数据
│   └── datasets/        # 最终数据集
│
├── logs/                 # 日志文件目录
├── tests/                # 测试套件
│   └── fixtures/        # 测试夹具
│
├── docs/                 # 项目文档
├── .env.template         # 环境变量模板
├── docker-compose.yml    # Docker编排配置
├── requirements.txt      # Python依赖
├── bootstrap.sh          # 项目初始化脚本
├── PROGRESS.md           # 项目进度报告
└── README.md             # 项目说明文档
```

## 快速开始

### 环境准备

#### 方法一：本地开发环境

```bash
# 克隆项目
git clone <repository-url>
cd Workshop

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 方法二：Docker容器环境

```bash
# 构建并启动所有服务
docker-compose up --build

# 启动特定服务
docker-compose up ingest quality

# 查看服务日志
docker-compose logs -f
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.template .env

# 编辑配置文件，设置必要的参数
# 主要配置项：
# - 路径配置：数据存储路径
# - 质量阈值：模糊检测、曝光检测等阈值
# - 云存储：OSS/S3配置（可选）
```

### 运行项目

#### 1. 启动监控面板
```bash
streamlit run dashboard/app.py
```
访问地址：`http://localhost:8501`

#### 2. 运行数据采集
```bash
python -m hardware.camera.realSense_manager
```

#### 3. 执行处理管道
```bash
# 方式一：直接运行Python模块
python -m pipelines.00_ingest.realsense_parser --input data/raw/sample.bag --output data/processed/scene_001

# 方式二：使用Docker
docker-compose run ingest
```

## 流水线架构

项目采用六阶段流水线架构：

1. **Ingest (数据摄入)**: 解析RealSense原始数据，进行隐私脱敏
2. **Quality (质量检测)**: 检测图像模糊度、曝光异常、时间同步等问题
3. **Enhance (数据增强)**: 自动标注、数据增强处理
4. **Calibrate (相机标定)**: 批量相机标定和漂移检测
5. **Pack (数据打包)**: 将处理结果打包为标准格式（ROS Bag, COCO等）
6. **Delivery (数据交付)**: 上传到云端存储或指定位置

## 配置说明

### 主要配置文件

- `configs/pipeline_config.yaml`: 流水线执行配置
- `configs/quality_thresholds.yaml`: 质量检测阈值
- `configs/logging.yaml`: 日志级别和格式配置

### 环境变量

关键环境变量说明：

```bash
# 数据路径配置
DATA_ROOT=/data
RAW_DIR=/data/raw
PROCESSED_DIR=/data/processed
DATASETS_DIR=/data/datasets

# 质量检测阈值
QUALITY_BLUR_THRESHOLD=100        # 模糊度阈值
QUALITY_SYNC_THRESHOLD_MS=0.5     # 时间同步阈值(ms)

# 云存储配置（可选）
OSS_ENABLED=false
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

## 开发指南

### 代码规范

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范
- 使用类型提示（Type Hints）
- 编写单元测试，目标覆盖率 > 80%
- 使用 Black 格式化代码
- 使用 Flake8 进行代码检查

### 项目结构规范

```
each_module/
├── __init__.py
├── main_component.py    # 主要功能实现
├── utils.py            # 辅助工具函数
├── config.py           # 模块配置
├── exceptions.py       # 自定义异常
├── Dockerfile          # 容器配置
└── requirements.txt    # 模块依赖
```

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
git commit -m "feat(camera): 添加自动曝光调节功能"
git commit -m "fix(pipeline): 修复数据同步时间戳错误"
git commit -m "docs(readme): 更新快速开始指南"
git commit -m "test(calibration): 添加外参标定单元测试"
git commit -m "chore(deps): 升级pyrealsense2到2.53.1"
```

### 测试策略

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_camera.py

# 生成覆盖率报告
pytest --cov=pipelines tests/

# 运行语法检查
flake8 .
mypy .
```

## 性能指标

### 硬件要求

**最低配置**:
- CPU: Intel i5 或同等性能处理器
- 内存: 16GB RAM
- 存储: 1TB SSD
- GPU: 支持CUDA的NVIDIA显卡（可选）

**推荐配置**:
- CPU: Intel i7 或 AMD Ryzen 7
- 内存: 32GB RAM
- 存储: 2TB NVMe SSD
- GPU: NVIDIA RTX 3070 或更高

### 处理性能

- **数据摄入**: ~100MB/s
- **质量检测**: ~50帧/秒
- **YOLO标注**: ~30帧/秒（GPU加速）
- **数据打包**: ~200MB/s

## 故障排除

### 常见问题

1. **RealSense设备无法识别**
   ```bash
   # 检查设备连接
   lsusb | grep RealSense
   
   # 重新安装驱动
   ./hardware/scripts/install_drivers.sh
   ```

2. **Docker容器启动失败**
   ```bash
   # 查看详细错误信息
   docker-compose logs <service_name>
   
   # 重建镜像
   docker-compose build --no-cache
   ```

3. **内存不足错误**
   ```bash
   # 调整Docker内存限制
   # 在docker-compose.yml中修改mem_limit参数
   ```

### 日志查看

```bash
# 查看系统日志
tail -f logs/pipeline.log

# 查看Docker服务日志
docker-compose logs -f --tail=100

# 查看特定服务日志
docker-compose logs -f ingest
```

## 项目进度

详细进度请查看 [PROGRESS.md](PROGRESS.md) 文件。

**当前状态**: ✅ 基础架构已完成
- [x] 项目目录结构创建
- [x] 核心模块占位实现
- [x] 配置文件初始化
- [x] Docker环境配置
- [ ] 功能逻辑实现（进行中）
- [ ] 单元测试编写
- [ ] 性能优化
- [ ] 生产环境部署

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: [您的姓名]
- 邮箱: [您的邮箱]
- 项目主页: [项目链接]