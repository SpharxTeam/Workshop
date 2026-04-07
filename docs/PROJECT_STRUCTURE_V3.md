# Workshop V3.0 项目结构

> 参考 AgentOS 和 Deepness 架构，深度重构后的完整项目结构

**版本**: V3.0.0  
**更新日期**: 2026-04-07  
**架构参考**: AgentOS, Deepness

---

## 📁 完整目录结构

```
Workshop/                              # 项目根目录
│
├── 📘 核心文档
│   ├── README.md                      # 项目总览
│   ├── CONTRIBUTING.md                # 贡献指南
│   ├── CHANGELOG.md                   # 版本历史
│   ├── LICENSE                        # GPL-3.0 许可证
│   ├── LICENSE-COMMERCIAL             # 商业许可证
│   └── LICENSE-GPL-3.0                # GPL 许可证副本
│
├── ⚙️ 项目配置
│   ├── pyproject.toml                 # Python 包配置
│   ├── requirements.txt               # 依赖列表
│   ├── Makefile                       # 开发命令
│   ├── .gitignore                     # Git 忽略规则
│   ├── .env.template                  # 环境变量模板
│   ├── Dockerfile                     # Docker 构建
│   ├── docker-compose.yml             # 容器编排
│   └── docker-entrypoint.sh           # 入口脚本
│
├── 🏗️ CI/CD
│   └── .github/
│       └── workflows/
│           └── ci-cd-pipeline.yml     # CI/CD流水线
│
├── 🔧 核心代码包 V3.0
│   └── workshop/
│       │
│       ├── __init__.py                # 包入口
│       │
│       ├── core/                      # ★ 核心层
│       │   ├── __init__.py
│       │   │
│       │   ├── abstractions/          # 抽象基类
│       │   │   ├── __init__.py
│       │   │   ├── pipeline.py        # BasePipeline ABC
│       │   │   ├── storage.py         # IStorageBackend ABC
│       │   │   ├── device.py          # IHardwareDevice ABC
│       │   │   └── models.py          # ErrorCode, 异常类
│       │   │
│       │   ├── services/              # ★ 核心服务
│       │   │   ├── __init__.py
│       │   │   ├── config_service.py  # 配置管理服务
│       │   │   ├── logging_service.py # 日志服务
│       │   │   └── metrics_service.py # 指标服务
│       │   │
│       │   ├── security/              # ★ 安全服务
│       │   │   ├── __init__.py
│       │   │   ├── validation_service.py  # 输入验证
│       │   │   └── security_service.py    # 安全审计
│       │   │
│       │   └── observability/         # ★ 可观测性
│       │       ├── __init__.py
│       │       ├── tracing_service.py # 分布式追踪
│       │       ├── performance.py     # 性能监控
│       │       └── health_service.py  # 健康检查
│       │
│       └── orchestration/             # ★ 编排层
│           ├── __init__.py
│           ├── scheduler.py           # 任务调度器
│           ├── task_queue.py          # 任务队列
│           └── workflow_engine.py     # 工作流引擎
│
├── 🛠️ 通用层
│   └── commons/
│       ├── __init__.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logging_utils.py       # 日志工具
│       │   ├── decorators.py          # 装饰器
│       │   ├── data_utils.py          # 数据处理
│       │   └── functional.py          # 函数式工具
│       └── schemas/
│           ├── __init__.py
│           ├── base.py                # 基础模式
│           ├── dataset.py             # 数据集模式
│           ├── scene.py               # 场景模式
│           └── sensor_stream.py       # 传感器流模式
│
├── 🛠️ 服务层
│   └── services/
│       ├── __init__.py
│       ├── gateway.py                 # API 网关
│       ├── monitor.py                 # 监控服务
│       └── exporter.py                # 数据导出
│
├── 📦 向后兼容层
│   └── common/
│       ├── __init__.py                # 兼容导入
│       ├── core/
│       │   └── __init__.py            # 重定向到 workshop.core
│       ├── configs/
│       │   ├── __init__.py            # 重定向
│       │   ├── modules/               # 模块配置
│       │   ├── logging.yaml
│       │   ├── pipeline_config.yaml
│       │   └── quality_thresholds.yaml
│       ├── schemas/
│       │   └── __init__.py            # 重定向到 commons.schemas
│       └── scripts/
│           └── __init__.py            # 重定向到 commons.utils
│
├── 🧪 测试套件
│   └── tests/
│       ├── conftest.py
│       ├── pytest.ini
│       ├── fixtures/
│       │   └── sample_frames/
│       ├── framework/
│       │   └── test_framework.py
│       ├── unit/
│       │   ├── core/
│       │   │   ├── test_base_pipeline.py
│       │   │   ├── test_config_manager.py
│       │   │   ├── test_exceptions.py
│       │   │   └── test_input_validator.py
│       │   ├── pipelines/
│       │   │   ├── test_calibrate.py
│       │   │   ├── test_delivery.py
│       │   │   ├── test_enhance.py
│       │   │   ├── test_ingest.py
│       │   │   ├── test_pack.py
│       │   │   ├── test_pipelines_v2.py
│       │   │   └── test_quality.py
│       │   └── test_v3_imports.py
│       └── integration/
│           ├── test_pipeline.py
│           └── test_v2_integration.py
│
├── 📚 文档体系
│   └── docs/
│       ├── source/                    # Sphinx 源码
│       │   ├── _static/
│       │   ├── api/
│       │   ├── development/
│       │   ├── getting-started/
│       │   ├── user-guide/
│       │   ├── conf.py
│       │   └── index.rst
│       ├── API_REFERENCE.md           # API 参考
│       ├── ARCHITECTURE_DECISION_RECORDS.md
│       ├── CONTRIBUTING.md
│       ├── DELIVERY_CHECKLIST_AND_MANUAL.md
│       ├── DEVELOPER_GUIDE.md         # 开发者指南
│       ├── PROJECT_STRUCTURE.md       # 项目结构 V2
│       ├── PROJECT_STRUCTURE_V3.md    # 本文档
│       ├── REFACTORING_PLAN_V3.md     # 重构计划
│       ├── REFACTORING_V3_COMPLETION_REPORT.md  # 重构完成报告
│       ├── V2_QUICKSTART.md
│       ├── WORKSHOP_ARCH.md
│       ├── Makefile
│       └── make.bat
│
├── ⚙️ 配置目录
│   └── config/
│       └── prometheus/
│           ├── prometheus.yml
│           └── alert_rules.yml
│
├── 🔌 硬件层
│   └── hardware/
│       ├── hardware_abstraction.py
│       ├── calibration/
│       │   ├── extrinsics_calib.py
│       │   └── intrinsics_calib.py
│       ├── camera/
│       │   ├── realSense_manager.py
│       │   ├── sync_controller.py
│       │   └── sync_validator.py
│       └── scripts/
│           ├── install_drivers.sh
│           └── test_sync.sh
│
├── 🔄 管道层
│   └── pipelines/
│       ├── __init__.py
│       ├── run_00_ingest/
│       ├── run_01_quality/
│       ├── run_02_enhance/
│       ├── run_03_calibrate/
│       ├── run_04_pack/
│       ├── run_05_delivery/
│       └── streaming/
│
├── 💾 数据目录
│   ├── partdata/
│   │   ├── deps/
│   │   ├── logs/
│   │   └── models/
│   └── produce/
│       ├── input/
│       │   ├── calibration/
│       │   └── raw/
│       └── output/
│           ├── datasets/
│           └── processed/
│
├── 🛠️ 辅助脚本
│   └── scripts/
│       ├── deploy/
│       ├── dispose/
│       ├── download/
│       ├── init/
│       ├── lib/
│       ├── pipeline/
│       ├── streaming/
│       ├── test/
│       ├── utils/
│       ├── code_quality_checker.py
│       ├── demo_v2_full_pipeline.py
│       ├── deploy_v2.py
│       ├── load_tester.py
│       ├── ops_toolkit.py
│       ├── performance_benchmark_v1_vs_v2.py
│       ├── quality_check.py
│       ├── refactor_v3.py
│       └── requirements-dev.txt
│
├── 🐳 Docker
│   └── base/
│       └── Dockerfile
│
└── 📊 Dashboard
    └── common/dashboard/
        ├── app.py
        └── pages/
            ├── 01_capture.py
            ├── 02_monitor.py
            └── 03_data.py
```

---

## 🎯 架构层次说明

### 1. Core Layer (核心层)

**职责**: 提供核心抽象、服务和基础设施

```
workshop/core/
├── abstractions/      # 接口和抽象基类
├── services/          # 核心服务 (配置、日志、指标)
├── security/          # 安全服务 (验证、审计)
└── observability/     # 可观测性 (监控、追踪、性能)
```

**关键特性**:
- ✅ 统一的抽象基类 (BasePipeline, IStorageBackend, etc.)
- ✅ 集中化的服务管理
- ✅ 内建的安全和验证
- ✅ 完整的可观测性支持

### 2. Commons Layer (通用层)

**职责**: 提供通用工具、数据模式

```
commons/
├── utils/            # 通用工具函数
│   ├── logging_utils.py
│   ├── decorators.py
│   ├── data_utils.py
│   └── functional.py
└── schemas/          # 数据模式定义
    ├── dataset.py
    ├── scene.py
    └── sensor_stream.py
```

### 3. Orchestration Layer (编排层)

**职责**: 任务调度、队列管理、工作流编排

```
workshop/orchestration/
├── scheduler.py          # 任务调度器
├── task_queue.py         # 任务队列
└── workflow_engine.py    # 工作流引擎
```

### 4. Services Layer (服务层)

**职责**: 提供对外的服务接口

```
services/
├── gateway.py            # API 网关
├── monitor.py            # 监控服务
└── exporter.py           # 数据导出
```

### 5. Backward Compatibility Layer (向后兼容层)

**职责**: 提供 V2.0 到 V3.0 的平滑迁移

```
common/
├── __init__.py           # 兼容导入
├── core/__init__.py      # 重定向到 workshop.core
├── configs/              # 配置文件
├── schemas/__init__.py   # 重定向到 commons.schemas
└── scripts/__init__.py   # 重定向到 commons.utils
```

---

## 📊 模块统计

### 代码模块

| 层次 | 目录数 | 文件数 | 说明 |
|------|--------|--------|------|
| Core | 4 | 16 | 核心抽象和服务 |
| Commons | 2 | 9 | 通用工具和模式 |
| Orchestration | 1 | 4 | 编排层 |
| Services | 1 | 4 | 服务层 |
| Hardware | 3 | 8 | 硬件抽象 |
| Pipelines | 7 | 40+ | 管道模块 |
| Tests | 4 | 20+ | 测试套件 |
| **总计** | **22** | **100+** | - |

---

## 🔄 导入路径指南

### V3.0 推荐导入

```python
# 核心抽象
from workshop.core.abstractions import BasePipeline, PipelineResult

# 核心服务
from workshop.core.services import ConfigService, LoggingService

# 安全服务
from workshop.core.security import ValidationService, SecurityService

# 可观测性
from workshop.core.observability import TracingService, PerformanceMonitor

# 通用工具
from commons.utils import get_logger, deep_merge, retry

# 数据模式
from commons.schemas import DatasetSchema, SceneSchema

# 编排层
from workshop.orchestration import Scheduler, TaskQueue, WorkflowEngine

# 服务层
from services import Gateway, Monitor, Exporter
```

### V2.0 兼容导入

```python
# 仍然有效，但会显示 DeprecationWarning
from common.core import BasePipeline, ConfigService
from common.schemas import DatasetSchema
```

---

## 📝 相关文档

- [REFACTORING_PLAN_V3.md](REFACTORING_PLAN_V3.md) - 重构计划
- [REFACTORING_V3_COMPLETION_REPORT.md](REFACTORING_V3_COMPLETION_REPORT.md) - 重构完成报告
- [API_REFERENCE.md](API_REFERENCE.md) - API 参考
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - 开发者指南

---

**版本**: V3.0.0  
**更新日期**: 2026-04-07  
**维护者**: SPHARX DevTeam
