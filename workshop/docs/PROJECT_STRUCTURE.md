# Workshop V2.0 项目结构文档

本文档描述 Workshop V2.0 重构后的项目目录结构，参照 AgentOS 微内核架构模式组织。

---

## 📁 项目根目录结构

```
d:\SPHARX-CN\SpharxWorks\Workshop\
├── workshop/                          # 核心代码目录 (类似 agentos/)
│   ├── __init__.py                   # 包入口，导出公共 API
│   ├── common/                       # 通用模块 (类似 commons/)
│   │   ├── __init__.py
│   │   ├── core/                     # 核心基础设施 (类似 corekern/)
│   │   │   ├── __init__.py
│   │   │   ├── base_pipeline.py      # Pipeline ABC
│   │   │   ├── config_manager.py     # 配置管理器
│   │   │   ├── exceptions.py         # 异常体系
│   │   │   ├── logging_setup.py      # 日志系统
│   │   │   ├── input_validator.py    # 输入验证
│   │   │   ├── io_abstraction.py     # IO 抽象层
│   │   │   ├── metrics.py            # Prometheus 指标
│   │   │   ├── performance.py        # 性能测试
│   │   │   └── security_audit.py     # 安全审计
│   │   ├── configs/                  # 配置文件 (YAML)
│   │   │   ├── pipeline_config.yaml
│   │   │   ├── quality_thresholds.yaml
│   │   │   └── modules/              # 模块级配置
│   │   ├── schemas/                  # 数据模式定义
│   │   │   ├── dataset.py
│   │   │   ├── scene.py
│   │   │   └── sensor_stream.py
│   │   ├── dashboard/                # Web 监控仪表板
│   │   │   ├── app.py
│   │   │   └── pages/
│   │   └── scripts/                  # 通用脚本
│   ├── pipelines/                    # 数据处理管道 (类似 daemon/)
│   │   ├── __init__.py
│   │   ├── run_00_ingest/           # 数据摄入模块
│   │   │   ├── runner_v2.py         # V2 实现
│   │   │   ├── algorithm/           # 算法实现
│   │   │   └── model/               # 模型文件
│   │   ├── run_01_quality/          # 质量检测模块
│   │   ├── run_02_enhance/          # 增强模块
│   │   ├── run_03_calibrate/        # 校准模块
│   │   ├── run_04_pack/             # 打包模块
│   │   ├── run_05_delivery/         # 交付模块
│   │   └── streaming/               # 流式处理
│   ├── hardware/                     # 硬件抽象层
│   │   ├── __init__.py
│   │   ├── hardware_abstraction.py  # 设备 ABC
│   │   └── calibration/             # 校准工具
│   ├── tests/                        # 测试套件
│   │   ├── __init__.py
│   │   ├── unit/                    # 单元测试
│   │   ├── integration/             # 集成测试
│   │   └── framework/               # 测试框架
│   ├── scripts/                      # 运维脚本
│   │   ├── __init__.py
│   │   ├── load_tester.py          # 负载测试
│   │   ├── ops_toolkit.py          # 运维工具
│   │   ├── deploy_v2.py            # 部署工具
│   │   └── code_quality_checker.py # 质量检查
│   ├── config/                       # 配置文件
│   │   └── prometheus/             # Prometheus 配置
│   └── docs/                         # 文档
│       └── *.md                     # 技术文档
├── config/                           # 根配置目录 (保留向后兼容)
├── docs/                             # 根文档目录 (保留向后兼容)
├── docker-compose.yml                # Docker 编排
├── Dockerfile                        # Docker 构建
├── .github/workflows/                # CI/CD
└── README.md                         # 项目说明
```

---

## 🏗️ 架构对比：AgentOS vs Workshop

| AgentOS 模块 | Workshop 对应模块 | 功能说明 |
|-------------|------------------|---------|
| **atoms/corekern** | `workshop/common/core` | 核心基础设施层 |
| **daemon/** | `workshop/pipelines/` | 服务/管道模块 |
| **commons/** | `workshop/common/` | 通用工具库 |
| **cupolas/** | `workshop/common/core/security_audit.py` | 安全审计 |
| **heapstore/** | `workshop/common/core/io_abstraction.py` | 数据存储/IO |
| **manager/** | `workshop/common/core/config_manager.py` | 配置管理 |
| **gateway/** | `workshop/common/dashboard/` | Web 接口 |
| **toolkit/** | `workshop/scripts/` | 工具集 |
| **tests/** | `workshop/tests/` | 测试套件 |
| **docs/** | `workshop/docs/` + `docs/` | 文档 |

---

## 📦 核心模块详解

### 1. `workshop/common/core/` - 核心基础设施层

**类比**: AgentOS 的 `atoms/corekern/`

**文件结构**:
```
core/
├── __init__.py              # 导出所有公共 API
├── base_pipeline.py         # Pipeline 抽象基类 (K-2 接口契约)
├── config_manager.py        # 三级配置合并策略
├── exceptions.py            # 100+ 错误码体系
├── logging_setup.py         # 日志系统配置
├── input_validator.py       # 输入验证 (12 种预定义模式)
├── io_abstraction.py        # IO 抽象层 (IStorageBackend ABC)
├── metrics.py               # Prometheus 监控指标
├── performance.py           # 性能基准测试
└── security_audit.py        # SAST 安全审计
```

**关键类**:
- `BasePipeline`: 抽象基类，定义 `_initialize()`, `_execute()`, `_cleanup()` 生命周期
- `ConfigManager`: 配置加载与三级合并 (Global < Module < Runtime)
- `WorkshopError`: 统一异常基类，支持错误链追踪
- `InputValidator`: 类型/路径/正则表达式验证
- `IOManager`: 透明压缩/校验和/批量操作
- `WorkshopMetrics`: Prometheus 指标收集与导出

---

### 2. `workshop/pipelines/` - 数据处理管道模块

**类比**: AgentOS 的 `daemon/` 服务模块

**6 个标准阶段**:

| 模块 | 功能 | 关键算法 |
|------|------|---------|
| **run_00_ingest** | 数据摄入 | ROS bag 解析，图像压缩，隐私脱敏 |
| **run_01_quality** | 质量检测 | 模糊检测，曝光分析，帧丢弃检测 |
| **run_02_enhance** | 增强处理 | YOLO 目标检测，HDVS 分割 |
| **run_03_calibrate** | 相机校准 | 棋盘格校准，重投影误差评估 |
| **run_04_pack** | 数据集打包 | ROS/COCO/YOLO/VOC/KITTI 格式 |
| **run_05_delivery** | 交付上传 | OSS 上传，通知发送 |

**目录结构** (以 `run_00_ingest` 为例):
```
run_00_ingest/
├── runner_v2.py           # V2 实现 (基于 BasePipeline)
├── runner.py              # V1 实现 (保留向后兼容)
├── algorithm/             # 算法实现
│   ├── bag_parser.py
│   ├── image_compressor.py
│   └── privacy_desensitizer.py
├── model/                 # 模型文件 (.gitkeep)
├── requirements.txt       # 模块级依赖
└── Dockerfile            # 独立容器化配置
```

---

### 3. `workshop/hardware/` - 硬件抽象层

**功能**: 统一硬件设备接口，支持热插拔和健康检查

**关键类**:
- `IHardwareDevice`: 设备抽象基类
- `DeviceManager`: 单例设备管理器
- `RealSenseDeviceV2`: RealSense 相机实现

**使用示例**:
```python
from workshop.hardware import DeviceManager, RealSenseDeviceV2

device_mgr = DeviceManager()
camera = RealSenseDeviceV2(device_id='camera_001')
device_mgr.register('camera_001', camera)
device_mgr.initialize_all()

# 健康检查
status = device_mgr.health_check_all()
```

---

### 4. `workshop/tests/` - 测试套件

**类比**: AgentOS 的 `tests/`

**测试类型**:
```
tests/
├── unit/                      # 单元测试
│   ├── core/                  # 核心模块测试
│   │   ├── test_base_pipeline.py
│   │   ├── test_config_manager.py
│   │   ├── test_exceptions.py
│   │   └── test_input_validator.py
│   └── pipelines/             # Pipeline 模块测试
│       ├── test_ingest.py
│       ├── test_quality.py
│       └── ...
├── integration/               # 集成测试
│   ├── test_v2_integration.py
│   └── test_pipeline.py
└── framework/                 # 测试框架
    └── test_framework.py
```

**运行测试**:
```bash
# 单元测试
python -m pytest workshop/tests/unit/ -v

# 集成测试
python -m pytest workshop/tests/integration/ -v

# 完整测试套件
python -m pytest workshop/tests/ --cov=workshop
```

---

### 5. `workshop/scripts/` - 运维工具集

**类比**: AgentOS 的 `toolkit/` + `scripts/`

**核心工具**:

| 脚本 | 功能 | 使用示例 |
|------|------|---------|
| `load_tester.py` | 负载测试框架 | `--test-type load -c 20` |
| `ops_toolkit.py` | 运维自动化 | `--daily-maintenance` |
| `deploy_v2.py` | 部署工具 | `--check-env` |
| `code_quality_checker.py` | 代码质量检查 | `common/core` |
| `performance_benchmark_v1_vs_v2.py` | 性能对比 | 自动运行 |

---

## 🔧 导入路径指南

### 推荐导入方式

```python
# ✅ 推荐：使用 workshop 包导入
from workshop import BasePipeline, ConfigManager
from workshop.core import WorkshopMetrics
from workshop.pipelines.run_00_ingest.runner_v2 import IngestPipeline
from workshop.hardware import DeviceManager

# ⚠️ 旧方式 (保留向后兼容，但不推荐)
from common.core.base_pipeline import BasePipeline
from pipelines.run_00_ingest.runner_v2 import IngestPipeline
```

### 导入路径映射

| 旧路径 | 新路径 |
|--------|--------|
| `common.core.*` | `workshop.common.core.*` |
| `pipelines.*` | `workshop.pipelines.*` |
| `hardware.*` | `workshop.hardware.*` |
| `tests.*` | `workshop.tests.*` |
| `scripts.*` | `workshop.scripts.*` |

---

## 📊 代码组织原则

### 1. **模块化分离** (K-3 Service Isolation)
- 每个 Pipeline 模块独立目录
- 算法实现与 Runner 分离
- 模型文件使用 `.gitkeep` 占位

### 2. **接口标准化** (K-2 Interface Contract)
- 所有 Pipeline 继承 `BasePipeline`
- 硬件设备实现 `IHardwareDevice`
- 存储后端实现 `IStorageBackend`

### 3. **配置分层** (Three-level Merge)
```
Global Config (common/configs/pipeline_config.yaml)
    ↓
Module Config (pipelines/run_XX_module/config.yaml)
    ↓
Runtime Overrides (代码中动态传入)
```

### 4. **测试覆盖** (Testing Pyramid)
```
        /\
       /  \      E2E Tests (少量)
      /────\
     /      \    Integration Tests (中量)
    /────────\
   /          \  Unit Tests (大量)
  /────────────\
```

---

## 🐳 Docker 与部署

### 目录映射

```yaml
# docker-compose.yml
volumes:
  - ./workshop:/app/workshop          # 核心代码
  - ./config:/app/config              # 配置文件
  - workshop_data:/app/data           # 持久化数据
  - workshop_logs:/app/logs           # 日志文件
```

### Dockerfile 变更

```dockerfile
# 旧方式
COPY common/ ./common/
COPY pipelines/ ./pipelines/

# 新方式 (推荐)
COPY workshop/ ./workshop/
COPY config/ ./config/
```

---

## 📚 文档结构

### 技术文档 (`workshop/docs/`)

| 文档 | 用途 |
|------|------|
| `PHASE8_COMPLETION_REPORT.md` | Phase 8 完成报告 |
| `ARCHITECTURE_DECISION_RECORDS.md` | 9 条架构决策记录 |
| `V2_QUICKSTART.md` | 快速开始指南 |
| `DELIVERY_CHECKLIST_AND_MANUAL.md` | 交付手册 |

### 根目录文档 (`docs/`)

保留原有文档目录，用于 Sphinx 文档生成：
```
docs/
├── source/          # Sphinx 源文件
├── build/           # 生成的 HTML
└── *.md            # Markdown 文档
```

---

## 🎯 迁移检查清单

### 已完成迁移
- ✅ `common/core/` → `workshop/common/core/`
- ✅ `pipelines/` → `workshop/pipelines/`
- ✅ `hardware/` → `workshop/hardware/`
- ✅ `tests/` → `workshop/tests/`
- ✅ `scripts/` → `workshop/scripts/`
- ✅ `config/prometheus/` → `workshop/config/prometheus/`
- ✅ `docs/*.md` → `workshop/docs/` (复制)

### 向后兼容
- ✅ 保留原 `common/`, `pipelines/` 等目录
- ✅ 保留原 `config/`, `docs/` 根目录
- ✅ 新旧导入路径均有效

### 待更新 (可选)
- ⏳ 更新 `Dockerfile` 使用新路径
- ⏳ 更新 `.github/workflows/ci-cd-pipeline.yml`
- ⏳ 更新 `README.md` 导入示例

---

## 🚀 快速开始

### 安装与导入

```bash
# 克隆项目
git clone https://github.com/spharx-cn/workshop.git
cd workshop

# 安装依赖
pip install -r requirements.txt

# 验证导入
python -c "from workshop import BasePipeline; print('✅ 导入成功')"
```

### 运行第一个 Pipeline

```python
from workshop import BasePipeline, ConfigManager
from workshop.pipelines.run_00_ingest.runner_v2 import IngestPipeline

# 创建并运行 Pipeline
with IngestPipeline() as pipeline:
    result = pipeline.run(input_data={'path': 'data/sample.bag'})
    print(f"处理完成：{result.success}")
    print(f"耗时：{result.duration_ms:.2f}ms")
```

---

## 📞 技术支持

- 📘 完整文档：[workshop/docs/](file:///d:/SPHARX-CN/SpharxWorks/Workshop/workshop/docs/)
- 🚀 快速开始：[V2_QUICKSTART.md](file:///d:/SPHARX-CN/SpharxWorks/Workshop/docs/V2_QUICKSTART.md)
- 🏗️ 架构决策：[ARCHITECTURE_DECISION_RECORDS.md](file:///d:/SPHARX-CN/SpharxWorks/Workshop/docs/ARCHITECTURE_DECISION_RECORDS.md)
- 📦 交付手册：[DELIVERY_CHECKLIST_AND_MANUAL.md](file:///d:/SPHARX-CN/SpharxWorks/Workshop/docs/DELIVERY_CHECKLIST_AND_MANUAL.md)

---

*文档版本*: v2.0.0  
*最后更新*: 2026-04-07  
*维护者*: SPHARX DevTeam
