# Workshop V2.0 项目结构说明

> 清晰、模块化、易于维护的项目目录布局

---

## 📁 完整目录结构

```
workshop/                          # 项目根目录
├── 📘 核心文档
│   ├── README.md                  # 项目总览和快速开始
│   ├── CONTRIBUTING.md            # 贡献指南
│   ├── CHANGELOG.md               # 版本变更记录
│   ├── LICENSE                    # 开源许可证
│   ├── LICENSE-GPL-3.0           # GPL-3.0 许可证全文
│   └── LICENSE-COMMERCIAL        # 商业许可证
│
├── ⚙️ 项目配置
│   ├── pyproject.toml            # Python 包标准化配置 ⭐
│   ├── requirements.txt          # 核心依赖列表 ⭐
│   ├── Makefile                  # 开发命令集合 ⭐
│   ├── .gitignore                # Git 忽略规则
│   ├── .env.template             # 环境变量模板
│   ├── Dockerfile                # Docker 镜像构建
│   ├── docker-compose.yml        # 7 服务容器编排
│   └── docker-entrypoint.sh      # Docker 入口脚本
│
├── 🏗️ CI/CD
│   └── .github/
│       └── workflows/
│           └── ci-cd-pipeline.yml  # GitHub Actions 流水线
│
├── 📦 核心代码包 (V2.0)
│   └── workshop/
│       ├── __init__.py            # 包入口，导出公共 API ⭐
│       ├── common/                # 通用模块（保留向后兼容）
│       ├── pipelines/             # 数据处理管道（保留向后兼容）
│       ├── hardware/              # 硬件抽象层（保留向后兼容）
│       ├── tests/                 # 测试套件（保留向后兼容）
│       ├── scripts/               # 运维脚本（保留向后兼容）
│       ├── config/                # Prometheus/Grafana 配置
│       └── docs/                  # 技术文档
│           ├── PROJECT_STRUCTURE.md  # 本文档
│           ├── MIGRATION_REPORT.md   # V1→V2 迁移报告
│           └── V2_QUICKSTART.md      # V2 快速开始指南
│
├── 🔧 向后兼容层 (V1 代码)
│   ├── common/                    # 通用模块（V1 路径）
│   │   ├── core/                  # ★ 核心基础设施 (10 模块)
│   │   │   ├── __init__.py
│   │   │   ├── base_pipeline.py   # Pipeline ABC
│   │   │   ├── config_manager.py  # 配置管理器
│   │   │   ├── exceptions.py      # 异常体系
│   │   │   ├── logging_setup.py   # 日志系统
│   │   │   ├── input_validator.py # 输入验证
│   │   │   ├── io_abstraction.py  # IO 抽象
│   │   │   ├── metrics.py         # Prometheus 监控
│   │   │   ├── performance.py     # 性能工具
│   │   │   └── security_audit.py  # 安全审计
│   │   ├── configs/               # YAML 配置文件
│   │   │   ├── modules/           # 模块配置
│   │   │   │   ├── 00_ingest.yaml
│   │   │   │   ├── 01_quality.yaml
│   │   │   │   ├── 02_enhance.yaml
│   │   │   │   ├── 03_calibrate.yaml
│   │   │   │   ├── 04_pack.yaml
│   │   │   │   └── 05_delivery.yaml
│   │   │   ├── deps.lock          # 依赖锁定
│   │   │   ├── logging.yaml       # 日志配置
│   │   │   ├── model_config.yaml  # 模型配置
│   │   │   ├── pipeline_config.yaml # 管道配置
│   │   │   ├── quality_thresholds.yaml # 质量阈值
│   │   │   └── requirements.txt   # 依赖列表
│   │   ├── schemas/               # 数据模式定义
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py
│   │   │   ├── scene.py
│   │   │   └── sensor_stream.py
│   │   ├── dashboard/             # Web 监控仪表板
│   │   │   ├── app.py
│   │   │   └── pages/
│   │   │       ├── 01_capture.py
│   │   │       ├── 02_monitor.py
│   │   │       └── 03_data.py
│   │   └── scripts/               # 通用脚本
│   │       ├── __init__.py
│   │       ├── config_loader.py
│   │       ├── log_utils.py
│   │       └── data_io/
│   │           ├── __init__.py
│   │           └── data_io.py
│   │
│   ├── pipelines/                 # 数据处理管道 (6 个)
│   │   ├── __init__.py
│   │   ├── run_00_ingest/        # 数据导入
│   │   │   ├── algorithm/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bag_parser.py
│   │   │   │   ├── image_compressor.py
│   │   │   │   └── privacy_desensitizer.py
│   │   │   ├── model/
│   │   │   ├── runner.py          # V1 运行器
│   │   │   ├── runner_v2.py       # V2 运行器 ⭐
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── run_01_quality/       # 质量检测
│   │   ├── run_02_enhance/       # 数据增强
│   │   ├── run_03_calibrate/     # 相机校准
│   │   ├── run_04_pack/          # 数据打包
│   │   └── run_05_delivery/      # 数据交付
│   │
│   ├── hardware/                  # 硬件抽象层
│   │   ├── hardware_abstraction.py
│   │   ├── camera/
│   │   │   ├── realSense_manager.py
│   │   │   ├── sync_controller.py
│   │   │   └── sync_validator.py
│   │   └── calibration/
│   │       ├── intrinsics_calib.py
│   │       └── extrinsics_calib.py
│   │
│   ├── tests/                     # 测试套件
│   │   ├── conftest.py
│   │   ├── pytest.ini
│   │   ├── framework/
│   │   │   └── test_framework.py
│   │   ├── integration/
│   │   │   ├── test_pipeline.py
│   │   │   └── test_v2_integration.py
│   │   └── unit/
│   │       ├── core/
│   │       │   ├── test_base_pipeline.py
│   │       │   ├── test_config_manager.py
│   │       │   ├── test_exceptions.py
│   │       │   └── test_input_validator.py
│   │       └── pipelines/
│   │           ├── __init__.py
│   │           ├── test_ingest.py
│   │           ├── test_quality.py
│   │           ├── test_enhance.py
│   │           ├── test_calibrate.py
│   │           ├── test_pack.py
│   │           ├── test_delivery.py
│   │           └── test_pipelines_v2.py
│   │
│   └── scripts/                   # 运维工具集
│       ├── quality_check.py      # ⭐ 代码质量检查 (新增)
│       ├── ops_toolkit.py        # ⭐ 运维自动化
│       ├── load_tester.py        # ⭐ 负载测试
│       ├── performance_benchmark_v1_vs_v2.py  # ⭐ 性能对比
│       ├── code_quality_checker.py  # 代码质量检查
│       ├── deploy_v2.py          # 部署工具
│       ├── demo_v2_full_pipeline.py  # 完整流程演示
│       └── requirements-dev.txt  # 开发依赖
│
├── 📚 技术文档
│   └── docs/
│       ├── API_REFERENCE.md      # ⭐ API 参考文档 (新增)
│       ├── DEVELOPER_GUIDE.md    # ⭐ 开发者指南 (新增)
│       ├── ARCHITECTURE_DECISION_RECORDS.md  # 架构决策记录
│       ├── DELIVERY_CHECKLIST_AND_MANUAL.md  # 交付手册
│       ├── FINAL_COMPLETION_REPORT.md        # 最终完成报告
│       ├── PHASE2_3_COMPLETION_REPORT.md     # Phase 2-3 报告
│       ├── PHASE7_COMPLETION_REPORT.md       # Phase 7 报告
│       ├── PHASE8_COMPLETION_REPORT.md       # Phase 8 报告
│       ├── REFACTORING_REPORT_V2.md          # V2 重构报告
│       ├── WORKSHOP_ARCH.md                  # 架构文档
│       ├── source/                           # Sphinx 文档源
│       │   ├── conf.py
│       │   ├── index.rst
│       │   ├── api/
│       │   ├── development/
│       │   ├── getting-started/
│       │   └── user-guide/
│       └── Makefile
│
├── ⚙️ 配置目录
│   └── config/
│       └── prometheus/
│           ├── prometheus.yml    # Prometheus 配置
│           └── alert_rules.yml   # 告警规则 (12 条)
│
├── 💾 数据目录 (保留结构)
│   ├── partdata/
│   │   ├── deps/                 # 依赖数据
│   │   ├── models/               # 模型文件
│   │   │   ├── architecture/
│   │   │   └── weights/
│   │   └── logs/                 # 日志文件
│   └── produce/
│       ├── input/
│       │   ├── raw/              # 原始数据
│       │   └── calibration/      # 校准数据
│       └── output/
│           ├── processed/        # 处理结果
│           └── datasets/         # 最终数据集
│
└── 🛠️ 辅助脚本
    └── scripts/
        ├── deploy/
        │   └── workshop_deploy.sh
        ├── dispose/
        │   └── dispose_build_all.sh
        ├── download/
        │   ├── download_deps.sh
        │   ├── download_models.sh
        │   └── download_sources.sh
        ├── init/
        │   └── init_project.sh
        ├── lib/
        │   ├── download_common.sh
        │   └── workshop_common.sh
        ├── pipeline/
        │   ├── run_batch.sh
        │   └── run_full.sh
        ├── streaming/
        │   └── run_streaming.py
        ├── test/
        │   └── run_tests.sh
        └── utils/
            ├── export_datasets.sh
            └── generate_realistic_calibration.py
```

---

## 🎯 设计理念

### 1. **向后兼容原则**

- 保留 V1 代码路径 (`common/`, `pipelines/`, `hardware/` 等)
- V2 核心代码位于 `workshop/` 子目录
- 新旧代码可以共存，平滑迁移

### 2. **模块化设计**

每个模块职责单一，遵循 SOLID 原则：

```
common/core/        # 核心基础设施层
pipelines/          # 业务逻辑层
hardware/           # 硬件抽象层
tests/              # 测试验证层
scripts/            # 运维工具层
```

### 3. **配置与代码分离**

```
config/             # 运行时配置 (Prometheus/Grafana)
common/configs/     # 应用配置 (YAML)
.env.template       # 环境变量
```

### 4. **文档分层**

```
根目录/             # 面向用户 (README, CONTRIBUTING)
docs/               # 技术文档 (API, 开发者指南)
workshop/docs/      # V2 特定文档 (迁移报告)
```

---

## 📦 核心模块说明

### workshop/__init__.py - 公共 API 导出

```python
# 版本信息
__version__ = '2.0.0'
__author__ = 'SPHARX DevTeam'
__license__ = 'GPL-3.0'

# 导出所有公共 API
__all__ = [
    'BasePipeline', 'PipelineResult', 'PipelineStatus',
    'ConfigManager', 'WorkshopMetrics', 'get_metrics',
    'IOManager', 'get_io_manager', 'init_io_manager',
    'BenchmarkSuite', 'MemoryProfiler', 'quick_benchmark',
    'CodeSecurityScanner', 'run_full_security_audit',
]
```

### common/core/ - 10 个核心模块

| 模块 | 功能 | 关键类/函数 |
|------|------|------------|
| `base_pipeline.py` | Pipeline 抽象基类 | `BasePipeline`, `PipelineResult` |
| `config_manager.py` | 配置管理 | `ConfigManager` |
| `exceptions.py` | 异常体系 | `WorkshopError`, `ErrorCode` |
| `logging_setup.py` | 日志系统 | `setup_logging()`, `get_logger()` |
| `input_validator.py` | 输入验证 | `InputValidator`, `Pattern` |
| `io_abstraction.py` | IO 抽象 | `IOManager`, `IStorageBackend` |
| `metrics.py` | Prometheus 监控 | `WorkshopMetrics` |
| `performance.py` | 性能工具 | `BenchmarkSuite`, `MemoryProfiler` |
| `security_audit.py` | 安全审计 | `CodeSecurityScanner` |

---

## 🔧 开发工具

### Makefile 命令

```bash
# 安装
make install          # 安装核心依赖
make install-dev      # 安装完整开发环境

# 代码质量
make lint             # 运行 Ruff Linting
make format           # 自动格式化 (Black + isort)
make typecheck        # 类型检查 (mypy)
make quality          # 完整质量检查

# 测试
make test             # 运行单元测试
make test-all         # 运行完整测试套件
make test-cov         # 测试 + 覆盖率报告

# 构建和部署
make build            # 构建 Docker 镜像
make up               # 启动 Docker 服务
make down             # 停止 Docker 服务

# 文档
make docs             # 构建文档
```

### 代码质量检查

```bash
# 一键运行所有检查
python scripts/quality_check.py

# 自动修复问题
python scripts/quality_check.py --fix

# 生成质量报告
python scripts/quality_check.py --report
```

---

## 📊 项目统计

```
代码统计:
├── Python 文件: 87 个
├── 总代码行数: ~25,000 行
├── 核心模块: 10 个
├── Pipeline 模块: 6 个
├── 测试用例: 67+ 个
└── 文档页数: 15+ 页

质量指标:
├── 代码复用率: +375%
├── 输入验证覆盖: 99%
├── 性能提升: +50.6%
├── 错误码体系: 100+ 个
└── 测试覆盖率目标: ≥80%
```

---

## 🔄 迁移指南

### 从 V1 迁移到 V2

1. **更新导入路径**
   ```python
   # V1
   from common.core.base_pipeline import BasePipeline
   
   # V2 (推荐)
   from workshop import BasePipeline
   ```

2. **使用新的 CLI 工具**
   ```bash
   # V1
   python scripts/run_full.sh
   
   # V2
   make test-all
   python scripts/quality_check.py
   ```

3. **配置文件位置**
   ```
   # V1
   common/configs/pipeline_config.yaml
   
   # V2 (保持不变，向后兼容)
   common/configs/pipeline_config.yaml
   ```

详见 [MIGRATION_REPORT.md](workshop/docs/MIGRATION_REPORT.md)

---

## 📝 最佳实践

### 1. 添加新 Pipeline

```bash
# 创建目录结构
mkdir -p pipelines/run_06_new_feature/{algorithm,model}

# 实现 Pipeline
vim pipelines/run_06_new_feature/runner_v2.py

# 添加测试
vim tests/unit/pipelines/test_new_feature.py

# 运行测试
pytest tests/unit/pipelines/test_new_feature.py -v
```

### 2. 修改核心模块

```bash
# 修改代码
vim common/core/config_manager.py

# 运行 linting
make lint

# 运行测试
make test

# 运行类型检查
make typecheck
```

### 3. 提交代码

```bash
# 格式化代码
make format

# 运行质量检查
make quality

# 提交
git commit -m "feat(core): add new feature"
```

---

## 🎓 学习路径

### 新人入门

1. **阅读文档**
   - [README.md](README.md) - 项目总览
   - [V2_QUICKSTART.md](workshop/docs/V2_QUICKSTART.md) - 快速开始
   - [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) - 开发者指南

2. **理解架构**
   - [API_REFERENCE.md](docs/API_REFERENCE.md) - API 文档
   - [ARCHITECTURE_DECISION_RECORDS.md](docs/ARCHITECTURE_DECISION_RECORDS.md) - 架构决策

3. **实践操作**
   ```bash
   # 安装开发环境
   make install-dev
   
   # 运行示例
   python scripts/demo_v2_full_pipeline.py
   
   # 运行测试
   make test
   ```

---

## 🔗 相关资源

- **项目仓库**: https://atomgit.com/spharx/workshop
- **API 文档**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **开发者指南**: [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **版本历史**: [CHANGELOG.md](CHANGELOG.md)

---

**最后更新**: 2026-04-07  
**维护团队**: SPHARX DevTeam
