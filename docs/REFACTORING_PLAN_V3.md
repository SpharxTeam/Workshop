# Workshop V3.0 深度重构计划

> 参考 AgentOS 和 Deepness 的项目架构，对 Workshop 进行全面深度重构

**重构日期**: 2026-04-07  
**目标版本**: V3.0.0  
**参考项目**: 
- AgentOS (微内核架构)
- Deepness (数据处理管道)

---

## 📋 重构背景

### 当前问题 (V2.0)

1. **层次不清晰**: `common/` 包含了核心模块、配置、工具、仪表板等多种功能
2. **职责不单一**: 核心基础设施与业务逻辑混合
3. **可观测性不足**: 监控、日志、追踪分散在各处
4. **服务抽象缺失**: 缺少统一的服务层
5. **文档结构松散**: 技术文档与项目文档混合

### AgentOS 架构优势

```
agentos/
├── agentos/              # 核心代码
│   ├── atoms/           # 原子模块 (核心内核、系统调用)
│   ├── commons/         # 通用工具平台
│   ├── cupolas/         # 顶层服务 (安全、审计)
│   ├── daemon/          # 守护进程服务
│   └── toolkit/         # 多语言工具包
├── docs/                # 完整文档体系
└── scripts/             # 构建和运维脚本
```

### Deepness 架构优势

```
deepness/
├── deepness/            # 核心代码
│   ├── core/           # 核心抽象和服务
│   │   ├── abstractions/  # 接口和抽象基类
│   │   ├── services/      # 配置、日志服务
│   │   ├── security/      # 安全服务
│   │   └── observability/ # 可观测性
│   ├── pipelines/      # 数据处理管道
│   └── orchestration/  # 编排层
└── docs/               # 技术文档
```

---

## 🎯 重构目标

### V3.0 架构设计

```
workshop/
├── workshop/                    # ★ 核心代码包 V3.0
│   ├── core/                    # 核心抽象和服务 (参考 Deepness)
│   │   ├── abstractions/        # 接口和抽象基类
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py      # BasePipeline ABC
│   │   │   ├── storage.py       # IStorageBackend ABC
│   │   │   ├── device.py        # IHardwareDevice ABC
│   │   │   └── models.py        # 数据模型
│   │   ├── services/            # 核心服务
│   │   │   ├── __init__.py
│   │   │   ├── config_service.py    # 配置服务
│   │   │   ├── logging_service.py   # 日志服务
│   │   │   └── metrics_service.py   # 指标服务
│   │   ├── security/            # 安全服务
│   │   │   ├── __init__.py
│   │   │   ├── validation_service.py  # 输入验证
│   │   │   └── security_service.py    # 安全审计
│   │   └── observability/       # 可观测性
│   │       ├── __init__.py
│   │       ├── tracing_service.py   # 追踪
│   │       └── metrics_service.py   # Prometheus 指标
│   │
│   ├── commons/                 # 通用工具和平台 (参考 AgentOS commons)
│   │   ├── utils/               # 通用工具
│   │   │   ├── __init__.py
│   │   │   ├── string_utils.py
│   │   │   ├── file_utils.py
│   │   │   └── io_utils.py
│   │   ├── config/              # 配置加载
│   │   ├── schemas/             # 数据模式
│   │   └── patches/             # 兼容性补丁
│   │
│   ├── pipelines/               # 数据处理管道 (标准化)
│   │   ├── __init__.py
│   │   ├── run_00_ingest/
│   │   ├── run_01_quality/
│   │   ├── run_02_enhance/
│   │   ├── run_03_calibrate/
│   │   ├── run_04_pack/
│   │   └── run_05_delivery/
│   │
│   ├── hardware/                # 硬件抽象层
│   │   ├── __init__.py
│   │   ├── devices/             # 设备实现
│   │   └── calibration/         # 校准工具
│   │
│   ├── orchestration/           # ★ 新增：任务编排层
│   │   ├── __init__.py
│   │   ├── scheduler.py         # 调度器
│   │   ├── task_queue.py        # 任务队列
│   │   └── workflow_engine.py   # 工作流引擎
│   │
│   └── scripts/                 # Python 脚本工具
│       ├── __init__.py
│       └── performance_benchmark.py
│
├── commons/                     # ★ 独立通用模块 (参考 AgentOS)
│   ├── platform/                # 平台适配层
│   ├── scripts/                 # Shell 脚本
│   └── tests/                   # 通用测试
│
├── services/                    # ★ 新增：服务层
│   ├── gateway/                 # API 网关
│   ├── monitor/                 # 监控服务
│   └── exporter/                # 数据导出服务
│
├── tests/                       # 测试套件 (重构)
│   ├── conftest.py
│   ├── fixtures/
│   ├── unit/
│   │   ├── core/
│   │   ├── commons/
│   │   └── pipelines/
│   ├── integration/
│   └── e2e/
│
├── docs/                        # 文档体系 (重构)
│   ├── api/                     # API 文档
│   ├── architecture/            # 架构文档
│   ├── development/             # 开发指南
│   ├── guides/                  # 使用指南
│   ├── operations/              # 运维指南
│   └── references/              # 参考资料
│
├── config/                      # 配置目录
│   ├── prometheus/
│   ├── grafana/
│   └── application/
│
├── scripts/                     # 根脚本目录
│   ├── ci/                      # CI/CD 脚本
│   ├── deploy/                  # 部署脚本
│   ├── init/                    # 初始化脚本
│   └── lib/                     # 库脚本
│
├── partdata/                    # 数据目录
├── produce/                     # 产出目录
└── base/                        # Docker 基础镜像
```

---

## 🔄 重构步骤

### Phase 1: 创建核心抽象层 (core/abstractions/)

**目标**: 提取所有抽象基类和接口定义

```bash
# 创建目录
mkdir -p workshop/core/abstractions

# 移动文件
mv common/core/base_pipeline.py workshop/core/abstractions/pipeline.py
mv common/core/io_abstraction.py workshop/core/abstractions/storage.py
```

**新增文件**:
- `workshop/core/abstractions/models.py` - 数据模型定义
- `workshop/core/abstractions/device.py` - 硬件设备接口

### Phase 2: 创建核心服务层 (core/services/)

**目标**: 提取配置、日志等核心服务

```bash
mkdir -p workshop/core/services

# 重构 ConfigManager → ConfigService
mv common/core/config_manager.py workshop/core/services/config_service.py

# 重构 logging_setup → LoggingService
mv common/core/logging_setup.py workshop/core/services/logging_service.py
```

### Phase 3: 创建安全服务层 (core/security/)

**目标**: 提取安全和验证服务

```bash
mkdir -p workshop/core/security

# 移动安全审计模块
mv common/core/security_audit.py workshop/core/security/security_service.py

# 移动输入验证模块
mv common/core/input_validator.py workshop/core/security/validation_service.py
```

### Phase 4: 创建可观测性层 (core/observability/)

**目标**: 提取监控和追踪服务

```bash
mkdir -p workshop/core/observability

# 移动指标模块
mv common/core/metrics.py workshop/core/observability/metrics_service.py

# 新增追踪服务
touch workshop/core/observability/tracing_service.py
```

### Phase 5: 重组通用模块 (commons/)

**目标**: 整理通用工具和配置

```bash
mkdir -p commons/utils
mkdir -p commons/config
mkdir -p commons/schemas

# 移动通用脚本
mv common/scripts/* commons/scripts/
mv common/schemas/* commons/schemas/
```

### Phase 6: 创建编排层 (orchestration/)

**目标**: 新增任务编排能力

```bash
mkdir -p workshop/orchestration

# 创建编排模块
touch workshop/orchestration/scheduler.py
touch workshop/orchestration/task_queue.py
touch workshop/orchestration/workflow_engine.py
```

### Phase 7: 标准化管道模块 (pipelines/)

**目标**: 统一管道结构和命名

```bash
# 每个管道标准化为:
pipelines/run_XX_name/
├── __init__.py
├── algorithm/
│   ├── __init__.py
│   └── processor.py      # 统一命名
├── model/
│   ├── __init__.py
│   └── loader.py         # 统一命名
├── config/
│   └── default.yaml      # 默认配置
├── runner.py             # V1 兼容
├── runner_v2.py          # V2 标准
├── Dockerfile
└── requirements.txt
```

### Phase 8: 重组测试套件 (tests/)

**目标**: 分层测试结构

```bash
tests/
├── unit/                 # 单元测试
│   ├── core/            # 核心层测试
│   ├── commons/         # 通用层测试
│   └── pipelines/       # 管道层测试
├── integration/          # 集成测试
│   ├── pipeline_flow/   # 管道流测试
│   └── hardware/        # 硬件集成测试
└── e2e/                 # 端到端测试
    └── full_workflow/   # 完整工作流测试
```

### Phase 9: 重组文档结构 (docs/)

**目标**: 分层文档体系

```bash
docs/
├── api/                 # API 参考
│   ├── core/
│   ├── commons/
│   └── pipelines/
├── architecture/        # 架构文档
│   ├── overview.md
│   ├── core_layer.md
│   └── security.md
├── development/         # 开发指南
│   ├── getting-started.md
│   └── coding-standards.md
├── guides/             # 使用指南
│   ├── configuration.md
│   └── deployment.md
├── operations/         # 运维指南
│   ├── monitoring.md
│   └── troubleshooting.md
└── references/         # 参考资料
    ├── changelog.md
    └── roadmap.md
```

---

## 📊 文件迁移映射表

### 核心模块迁移

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `common/core/base_pipeline.py` | `workshop/core/abstractions/pipeline.py` | Pipeline ABC |
| `common/core/config_manager.py` | `workshop/core/services/config_service.py` | 配置服务 |
| `common/core/logging_setup.py` | `workshop/core/services/logging_service.py` | 日志服务 |
| `common/core/input_validator.py` | `workshop/core/security/validation_service.py` | 验证服务 |
| `common/core/security_audit.py` | `workshop/core/security/security_service.py` | 安全审计 |
| `common/core/metrics.py` | `workshop/core/observability/metrics_service.py` | 指标服务 |
| `common/core/io_abstraction.py` | `workshop/core/abstractions/storage.py` | IO 抽象 |
| `common/core/exceptions.py` | `workshop/core/abstractions/models.py` | 异常模型 |
| `common/core/performance.py` | `workshop/core/observability/performance.py` | 性能工具 |

### 通用模块迁移

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `common/scripts/` | `commons/scripts/` | 通用脚本 |
| `common/schemas/` | `commons/schemas/` | 数据模式 |
| `common/dashboard/` | `services/dashboard/` | 仪表板服务 |
| `common/configs/` | `config/application/` | 应用配置 |

### 新增模块

| 新路径 | 说明 | 状态 |
|--------|--------|------|
| `workshop/orchestration/` | 任务编排层 | 新增 |
| `workshop/core/observability/tracing_service.py` | 追踪服务 | 新增 |
| `services/gateway/` | API 网关 | 新增 |
| `services/monitor/` | 监控服务 | 新增 |

---

## 🔧 向后兼容策略

### 1. 导入路径兼容

```python
# V2 导入 (仍然有效)
from common.core.base_pipeline import BasePipeline

# V3 推荐导入
from workshop.core.abstractions import BasePipeline

# 兼容层实现
# common/core/base_pipeline.py 重定向到 workshop/core/abstractions/pipeline.py
```

### 2. 配置兼容

```yaml
# V2 配置路径 (仍然有效)
common/configs/modules/01_quality.yaml

# V3 推荐配置路径
config/application/modules/01_quality.yaml
```

### 3. API 兼容

所有公共 API 保持向后兼容，废弃的 API 添加 `@deprecated` 标记。

---

## ✅ 验证清单

### 核心层验证

- [ ] 所有抽象基类可正常导入
- [ ] 所有服务可正常初始化
- [ ] 安全验证功能正常
- [ ] 监控指标正常上报

### 管道层验证

- [ ] 所有 Pipeline 可正常运行
- [ ] 配置文件可正常加载
- [ ] Docker 镜像可正常构建

### 测试验证

- [ ] 单元测试通过率 ≥95%
- [ ] 集成测试通过率 ≥90%
- [ ] 代码覆盖率 ≥80%

### 文档验证

- [ ] API 文档完整
- [ ] 架构文档清晰
- [ ] 开发指南完整
- [ ] 运维手册可用

---

## 📈 重构收益

### 架构清晰度

| 指标 | V2.0 | V3.0 | 改进 |
|------|------|------|------|
| 层次数量 | 3 层 | 5 层 | ⬆️ 更清晰 |
| 职责分离 | 中等 | 高 | ⬆️ 显著提升 |
| 模块耦合 | 高 | 低 | ⬇️ 显著降低 |

### 可维护性

| 指标 | V2.0 | V3.0 | 改进 |
|------|------|------|------|
| 新人上手 | 困难 | 容易 | ⬆️ 改善 |
| 代码复用 | 低 | 高 | ⬆️ 提升 |
| 测试覆盖 | 80% | 90%+ | ⬆️ 提升 |

### 可扩展性

- ✅ 新增管道模块更容易
- ✅ 新增服务层组件更规范
- ✅ 多后端支持更灵活

---

## 🚀 实施计划

### 第一阶段 (Week 1-2): 核心层重构

- [ ] 创建 `core/abstractions/`
- [ ] 创建 `core/services/`
- [ ] 创建 `core/security/`
- [ ] 创建 `core/observability/`

### 第二阶段 (Week 3): 通用层重组

- [ ] 创建 `commons/`
- [ ] 迁移通用工具
- [ ] 迁移配置和模式

### 第三阶段 (Week 4): 服务层和编排层

- [ ] 创建 `services/`
- [ ] 创建 `orchestration/`
- [ ] 实现编排引擎

### 第四阶段 (Week 5): 测试和文档

- [ ] 重组测试套件
- [ ] 重组文档结构
- [ ] 编写迁移指南

### 第五阶段 (Week 6): 验证和发布

- [ ] 完整测试验证
- [ ] 性能基准测试
- [ ] 发布 V3.0.0

---

## 📝 相关文档

- [AgentOS 架构](../AgentOS/README.md)
- [Deepness 架构](../Deepness/STRUCTURE.md)
- [Workshop V2.0 结构](docs/PROJECT_STRUCTURE.md)
- [迁移指南](docs/MIGRATION_V3.md) - 待创建

---

**重构负责人**: SPHARX DevTeam  
**开始日期**: 2026-04-07  
**预计完成**: 2026-05-15  
**版本目标**: V3.0.0

---

*From data intelligence emerges.*  
*始于数据，终于智能。*
