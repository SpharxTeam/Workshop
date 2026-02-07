# Spharx Toolchain - 空间智能数据生产线

## 项目简介

Spharx Toolchain 是一个面向空间智能的数据处理流水线系统，采用"先2D后3D"的设计理念，通过配置驱动的方式实现数据处理的标准化和自动化。

## 核心特性

- 🔄 **流水线架构**: 模块化设计，支持灵活的阶段组合
- 🎯 **先2D后3D**: 优先处理2D标注，再提升至3D空间
- ⚙️ **配置驱动**: 通过环境变量和配置文件控制行为
- 🐳 **容器化部署**: Docker化服务，便于复制和扩展
- 📊 **产品导向**: 输出标准化的数据产品而非原始数据

## 快速开始

### 环境要求
- Docker & Docker Compose
- NVIDIA GPU (推荐)
- Windows/Linux/macOS

### 最小化部署 (仅2D服务)
```bash
# 1. 克隆项目
git clone <repository-url>
cd toolchain

# 2. 配置环境变量
cp .env.template .env
# 编辑 .env 文件设置必要参数

# 3. 启动2D服务栈
make deploy-2d

# 4. 运行流水线
make run-pipeline INPUT_PATH=./data/sample
```

### 完整部署 (2D+3D服务)
```bash
# 启动完整服务栈
make deploy-full

# 运行包含3D重建的流水线
make run-pipeline-3d INPUT_PATH=./data/sample
```

## 项目结构

```
toolchain/
├── .env.template          # 环境变量模板
├── docker-compose.yml     # 完整服务编排
├── docker-compose.2d.yml  # 最小2D栈
├── Makefile              # 常用命令
├── src/                  # 源代码
│   ├── main.py          # 主入口
│   ├── pipeline/        # 流水线引擎
│   ├── services/        # 外部服务封装
│   ├── products/        # 产品定义
│   └── utils/           # 通用工具
├── config/              # 配置模板
├── docker/              # Docker定义
├── scripts/             # 部署脚本
├── tests/               # 测试套件
└── docs/                # 项目文档
```

## 核心组件

### 流水线阶段
1. **输入验证** - 数据完整性检查
2. **2D自动标注** - 基于SAM的像素级标注
3. **2D产品打包** - COCO/YOLO格式输出
4. **3D重建** - COLMAP几何重建
5. **2D到3D提升** - 标签空间映射
6. **物理属性生成** - Blender物理仿真
7. **3D产品打包** - 标准化3D数据集
8. **输出导出** - OSS上传/本地存储

### 支持的产品
- **Spharx 2D**: 2D图像标注数据集
- **Spharx 3D Geo**: 3D几何数据集
- **Spharx 3D Physics**: 3D物理事实数据集

## 开发指南

### 本地开发环境
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
make test

# 代码格式化
make format

# 静态检查
make lint
```

### 添加新阶段
1. 继承 `stage_base.py` 中的基类
2. 实现 `validate()` 和 `execute()` 方法
3. 在 `pipeline_default.yaml` 中注册
4. 添加相应的测试用例

## 部署运维

### 服务器初始化
```bash
# 在新服务器上运行
./scripts/01_init_workshop.sh
```

### 健康检查
```bash
# 检查所有服务状态
./scripts/health_check.sh
```

### 监控告警
- CPU/内存使用率监控
- GPU利用率跟踪
- 磁盘空间预警
- 服务可用性检测

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: Spharx Team
- 邮箱: contact@spharx.cn
- 官网: https://www.spharx.cn

---
*最后更新: 2026-02-07*