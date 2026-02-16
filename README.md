# Spharx Workshop 3.1
## 物理世界数据工厂 · 从传感器到数据集的端到端自动化流水线

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen)
![Intel RealSense](https://img.shields.io/badge/Intel%20RealSense-D455-orange)

> 我们不训练模型，我们只生产数据 —— 成为人工智能时代的"数据台积电"

Spharx Workshop 是一套面向封闭物理空间的自动化数据采集与处理工具链。它将真实物理世界中的物体运动、人机交互、环境变化，变成干净、同步、可用的传感器数据，交付给所有需要理解物理世界的 AI 公司。

---

## 📖 目录

- [为什么需要 Spharx Workshop？](#为什么需要-spharx-workshop)
- [核心理念](#核心理念)
- [技术架构](#技术架构)
- [当前成果](#当前成果)
- [快速开始](#快速开始)
- [模块详解](#模块详解)
- [项目结构](#项目结构)
- [路线图](#路线图)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 🤔 为什么需要 Spharx Workshop？

当前具身智能发展的核心瓶颈是真实物理世界数据的稀缺。现有数据集多为互联网图片或仿真生成，无法满足机器人在真实环境中感知、交互的需求。各大 AI 实验室和机器人公司正在争夺高质量、多模态的物理世界数据，但数据的采集、清洗、标定、打包过程极度依赖人工，效率低下且不可重复。

Spharx Workshop 的目标是将数据生产工业化。我们提供一套从硬件同步到数据集交付的全自动化工具链，让数据生产像芯片制造一样，可扩展、可重复、可验证。我们相信，未来的 AI 竞争，归根结底是数据基础设施的竞争。Spharx 就是为这场竞争准备的"数据工厂"。

---

## 🧠 核心理念

- **物理世界优先**：直接从真实传感器（RGB-D、IMU、环境传感器）采集，确保数据反映真实物理规律。
- **自动化闭环**：从采集、质检、增强、标定到打包，全流程无人干预，保证数据一致性与可追溯性。
- **模块化与可扩展**：每个处理阶段独立容器化，可单独升级或替换，支持第三方算法集成。
- **生产就绪**：代码经过实际数据测试，具备日志、异常处理、配置分离等工业级特性，可直接部署于云服务器或边缘节点。
- **数据即产品**：产出的数据集附带完整元数据（质检报告、标定参数、文件哈希），客户开箱即用，无需二次处理。

---

## 🏗️ 技术架构

```
[硬件层] 3×RealSense D455（硬件同步） + IMU/环境传感器（可选）
    ↓
[采集层] 本地录制 → 原始.bag文件
    ↓
[处理层] 云服务器Docker容器化流水线
    ├── 00_ingest    # 数据导入与解析（真实bag → RGB视频、深度图、IMU、时间戳）
    ├── 01_quality   # 自动化质检（模糊/曝光/丢帧检测，生成质检报告）
    ├── 02_enhance   # 语义标注（YOLOv8）+ 预留SLAM轨迹
    ├── 03_calibrate # 批量标定（棋盘格内参，输出相机矩阵）
    ├── 04_pack      # 数据集打包（复制文件，生成manifest.json含SHA256）
    └── 05_delivery  # 交付模块（OSS上传、通知，预留）
    ↓
[存储层] 本地归档 / L1里云OSS
    ↓
[交付层] 标准化L0/L1/L2数据集（含完整元数据）

```

### 数据分级
```
| 等级     | 内容                                      | 典型客户             |
|----------|------------------------------------------|----------------------|
| L0 基础版 | 原始RGB-D + IMU + 基础质检                | 初创AI团队、科研院所  |
| L1 增强版 | L0 + 语义标注（COCO格式）+ SLAM轨迹       | 商用机器人厂商        |
| L2 定制版 | L1 + 客户定制格式 + 专属交付服务          | 大型科技公司、车企     |

---
```
## 🎯 当前成果

截至2026年2月，Spharx Workshop 已完成以下核心功能，并通过真实 RealSense D435i 数据的测试验证：

✅ 硬件同步方案：完成3×D455硬件同步的软件配置代码（GPIO连接 + pyrealsense2 同步模式设置）。  
✅ 真实数据解析：ingest 模块可读取任意 RealSense .bag 文件，提取 RGB 视频（H.264）、深度图（16-bit PNG）、IMU 数据和时间戳。  
✅ 自动化质检：quality 模块基于 OpenCV 实现模糊检测、曝光检测、丢帧统计，生成 JSON 报告，并可自定义阈值。  
✅ 语义标注：enhance 模块集成 YOLOv8，对视频逐帧进行目标检测，输出 COCO 格式标注文件（支持置信度阈值设置）。  
✅ 相机标定：calibrate 模块基于棋盘格实现内参标定，重投影误差可达亚像素级，并提供虚拟棋盘格生成工具用于测试。  
✅ 数据集打包：pack 模块将所有处理后的文件（视频、深度图、质检报告、标注、标定参数）收集至统一目录，生成包含 SHA256 哈希的 manifest.json，确保数据完整性。  
✅ 配置分离：所有可调参数（阈值、模型路径、棋盘格尺寸等）集中管理于 configs/pipeline_config.yaml，支持通过命令行或环境变量覆盖。  
✅ 统一日志与异常处理：每个模块均使用 Python logging，同时输出到控制台和 /logs 下的独立文件，并捕获所有已知异常。  
✅ Docker 优化：采用多阶段构建、国内 pip 镜像源，显著减小镜像体积，构建速度提升 30% 以上。  
✅ 自动化脚本：提供 run_full.sh 一键处理指定 bag，自动生成场景 ID，串联所有模块。

**已验证的输入**：Intel RealSense D435i 官方示例 bag（D435i_Walking.bag，约 700MB，518 帧）。  
**输出示例**：最终数据集包含 rgb.mp4、518 张深度图、timestamps.csv、quality_report.json、annotations.json（YOLO 检测 591 个目标）、intrinsics.json（标定结果）及 manifest.json。

---

## 🚀 快速开始

### 环境要求

- **操作系统**：Ubuntu 22.04 / [Gitee](https://gitee.com)，或 Windows + WSL2
- **Docker**：20.10+，并启用 WSL2 后端（Windows）
- **内存**：至少 8GB（建议 16GB）
- **磁盘**：50GB 可用空间（用于存放数据和镜像）

### 安装步骤

1. **克隆仓库**

git clone https://gitee.com/spharx/workshop.git
cd workshop
git checkout workshop3.3.1  # 当前稳定分支

2. **创建环境变量文件**

cp .env.template .env
# 根据需要编辑 .env（如 OSS 配置，暂不需要）

3. **构建所有镜像**（首次构建约 30 分钟，取决于网络）

docker-compose build

4. **准备测试数据**

将任意 RealSense .bag 文件放入 `data/raw/` 目录。如果没有，可使用我们提供的示例下载脚本（需网络）：

wget -O data/raw/D435i_Walking.bag https://github.com/IntelRealSense/librealsense/raw/development/unit-tests/data/d435i_sample.bag

若下载失败，可先用模拟模式（见下文）。

5. **运行全流程**

./scripts/pipeline/run_full.sh /data/raw/你的文件.bag

脚本会自动生成场景 ID（如 `scene_20260215_123456`），并在 `data/datasets/` 下创建最终数据集。

6. **验证运行**

# 查看生成的 manifest
cat data/datasets/scene_*/manifest.json | jq .  # 需安装 jq

# 查看日志
tail -f logs/*.log

### 模拟模式（无硬件或数据时）

只需创建一个空 .bag 文件，ingest 模块会自动生成模拟数据（随机 RGB 视频、深度图等），方便测试流水线逻辑。

touch data/raw/sample.bag
./scripts/pipeline/run_full.sh /data/raw/sample.bag

---

## 🔍 模块详解

### 00_ingest：数据导入

- **输入**：.bag 文件（RealSense 格式）
- **输出**：rgb.mp4、depth/（PNG 序列）、timestamps.csv、imu.csv（若存在）
- **核心逻辑**：使用 pyrealsense2 读取 bag，禁用实时播放，逐帧提取彩色、深度和 IMU 数据。彩色帧编码为 H.264 视频，深度帧保存为 16-bit PNG，时间戳和 IMU 保存为 CSV。
- **异常处理**：若文件不存在或为空，输出错误并退出；若 bag 无 IMU，记录 info 但不报错。

### 01_quality：质检

- **模糊检测**：cv2.Laplacian 方差，低于 `blur_threshold` 记为模糊。
- **曝光检测**：平均亮度，高于 `over_threshold` 为过曝，低于 `under_threshold` 为欠曝。
- **丢帧统计**：比较相邻时间戳间隔，超过 1.5 倍帧间隔记为丢帧。
- **输出**：quality_report.json，包含各帧索引和整体合格判断。

### 02_enhance：增强

- **语义标注**：使用 ultralytics YOLOv8 对视频逐帧检测，生成 COCO 格式的 annotations.json。
- **模型下载**：模型在容器启动时由 Ultralytics 自动下载（已安装 curl 确保下载工具可用），文件约 6MB。
- **预留接口**：orb_slam_runner.py 占位，供后续集成 SLAM。

### 03_calibrate：标定

- **棋盘格检测**：cv2.findChessboardCorners 带自适应阈值标志，提高检测率。
- **标定**：使用 cv2.calibrateCamera，输出相机矩阵、畸变系数、重投影误差。
- **辅助工具**：scripts/utils/generate_realistic_calibration.py 可生成带棋盘格的虚拟图像，用于无硬件时测试。

### 04_pack：打包

- **必需文件**：rgb.mp4、timestamps.csv，缺失则报错。
- **可选文件**：imu.csv、depth/、质检报告、标注、标定结果，缺失仅记录 info。
- **哈希计算**：对每个输出文件计算 SHA256，存入 manifest.json，便于后续验证。

---

## 📁 项目结构
```
.
├── .env.template                # 环境变量模板
├── .gitignore                   # Git忽略规则
├── README.md                    # 本文件
├── docker-compose.yml           # 开发环境编排
├── bootstrap.sh                 # 服务器部署脚本（待完善）
├── hardware/                    # 硬件控制代码
│   ├── camera/                  # 相机同步、管理
│   ├── calibration/             # 标定函数
│   └── scripts/                 # 驱动安装、测试
├── pipelines/                   # 数据处理流水线（各模块子目录）
│   ├── 00_ingest/
│   ├── 01_quality/
│   ├── 02_enhance/
│   ├── 03_calibrate/
│   ├── 04_pack/
│   └── 05_delivery/             # 预留
├── schemas/                     # Pydantic 数据模型
├── configs/                     # 配置文件
├── scripts/                     # 运维与工具脚本
│   ├── deploy/                  # 部署脚本
│   ├── pipeline/                # 流水线执行脚本
│   └── utils/                   # 辅助工具
├── docs/                        # 文档（待填充）
├── tests/                       # 单元测试（预留）
├── data/                        # 数据目录（git忽略）
└── logs/                        # 日志目录（git忽略）
```
---

## 🗺️ 路线图

### 已完成（v3.1）

- 硬件同步软件框架
- 真实 bag 解析
- 质检模块（模糊/曝光/丢帧）
- YOLOv8 语义标注
- 棋盘格内参标定
- 数据集打包与哈希验证
- 配置分离与日志统一
- Docker 镜像优化

### 进行中（v3.2）

- 多相机同步采集脚本
- 外参标定（多相机相对位姿）
- 集成 ORB-SLAM3 生成相机轨迹
- 交付模块（OSS 上传 + 微信通知）

### 未来规划

- 硬件扩展：支持 LiDAR、热成像传感器
- 算法扩展：集成 SAM 大模型进行实例分割
- 平台化：提供 Web 仪表盘管理采集任务和数据集
- 云原生：迁移至 K3s，实现自动扩缩容和监控
- 数据服务：为客户提供私有化部署和数据定制

---

## 🤝 贡献指南

我们欢迎任何形式的贡献，包括但不限于：

- 报告 Bug 或提出功能需求
- 提交代码优化或新模块
- 改进文档

请通过 GitHub Issues 或 Pull Request 与我们联系。开发流程：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'feat: add something'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

**代码规范**：PEP 8，需通过 flake8 检查；Dockerfile 应遵循最佳实践。

---

## 📄 许可证

本项目采用 MIT 许可证，详情见 [LICENSE](LICENSE) 文件。

---

## 🌟 致谢

感谢 Intel RealSense 团队提供的优秀 SDK 和示例数据，感谢 Ultralytics 开源的 YOLOv8 模型，感谢所有开源社区的支持。

---

> **Spharx Workshop** —— 始于数据，终于智能。  
> 期待与您一起，构建 AI 时代的物理世界数据基础设施。

_"数据是新的石油，但石油需要炼油厂。Spharx 就是你的数据炼油厂。"_
