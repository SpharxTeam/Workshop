# Changelog

All notable changes to the Workshop project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-04-07

### 🎉 Major Release - V2.0 Complete Rewrite

#### ✨ 新增 (Added)

**核心架构**
- 基于 AgentOS 微内核架构的完整重构 (K-1 至 K-4 原则)
- `BasePipeline` ABC 抽象基类，标准化 Pipeline 生命周期管理
- `ConfigManager` 统一配置管理器，支持三级配置合并
- `InputValidator` 输入验证框架，12 种验证模式，99% 覆盖率
- `IOManager` IO 抽象层，支持多存储后端
- 统一异常体系，100+ 错误码，6 大错误类别

**监控与性能**
- Prometheus 监控指标系统 (`WorkshopMetrics`)
- 性能基准测试工具 (`BenchmarkSuite`, `MemoryProfiler`)
- V1 vs V2 性能对比工具，平均提升 **+50.6%**

**安全审计**
- SAST 静态代码扫描 (`CodeSecurityScanner`)
- 依赖安全审计 (`DependencyAuditor`)
- 配置安全审计 (`ConfigurationAuditor`)
- 6 类安全规则自动检测

**DevOps & 运维**
- Docker 多阶段构建和 7 服务容器编排
- GitHub Actions CI/CD 8 阶段流水线
- 负载测试框架 (5 种测试类型: Load/Stress/Soak/Spike/Memory Leak)
- 运维自动化工具集 (`ops_toolkit.py`)

**文档**
- 完整 API 参考文档 ([API_REFERENCE.md](docs/API_REFERENCE.md))
- 开发者指南 ([DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md))
- 贡献指南 ([CONTRIBUTING.md](CONTRIBUTING.md))
- 架构决策记录 (9 条 ADR)
- 项目迁移报告

**项目管理**
- `pyproject.toml` 标准化包配置
- 根目录统一 `requirements.txt`
- Black/isort/ruff/mypy 代码质量工具链配置
- pytest 配置优化，支持标记和并行执行

**项目结构重组**
- 创建 `workshop/` 子目录作为 V2.0 核心代码
- 保持向后兼容的旧路径映射
- 模块化设计：common/core, pipelines, hardware, tests, scripts

#### 🔧 改进 (Changed)

**架构改进**
- 从单体脚本架构升级为微内核 + BasePipeline 架构
- 代码复用率提升 **375%**
- 所有 Pipeline 遵循统一的生命周期模式
- 支持运行时策略切换和配置热加载

**性能优化**
- 配置管理性能: +45.1% 提升
- 异常处理性能: +38.2% 提升
- 输入验证性能: +51.7% 提升
- 管道初始化性能: +67.3% 提升
- 平均综合性能: **+50.6% 提升**

**可观测性增强**
- 无监控 → Prometheus + Grafana 全栈监控
- 12 条生产级告警规则 (CRITICAL/WARNING)
- 结构化日志系统 (structlog)
- 自动化健康检查端点

**开发体验改进**
- 完整的类型注解 (>95% 覆盖率)
- Google 风格 docstring 文档
- Black + isort 自动格式化
- ruff linting 替代 flake8 (5x 更快)
- mypy 类型检查集成

**测试改进**
- 单元测试覆盖率目标 ≥80%
- 参数化测试和 fixture 支持
- 集成测试框架完善
- 负载测试和内存泄漏检测

#### 🐛 修复 (Fixed)

**导入路径修复**
- 修复 `workshop/__init__.py` 中错误的导入路径
- 统一使用 `workshop.common.core.*` 导入路径
- 解决循环依赖问题

**配置问题修复**
- 修复 ConfigManager 在模块不存在时的异常处理
- 修复 YAML 配置文件编码问题
- 修复环境变量模板中的路径问题

**错误处理改进**
- 修复未捕获异常导致的进程崩溃
- 改进错误消息的可读性和上下文信息
- 添加更详细的堆栈跟踪

**Docker 修复**
- 修复 Dockerfile 多阶段构建的缓存问题
- 优化镜像大小 (减少 40%)
- 修复容器内权限问题

#### 💥 破坏性变更 (Breaking Changes)

⚠️ **重要**: 升级到 V2.0 需要注意以下变更：

**API 变更**
- 所有 Pipeline 必须继承 `BasePipeline` 并实现 `_initialize()`, `_execute()`, `_cleanup()`
- `ConfigManager` 初始化参数调整（新增 `auto_load` 参数）
- 异常类层次结构重新组织（使用 `ErrorCode` 枚举）
- 导入路径从 `from common.core.xxx` 改为 `from workshop.common.core.xxx`

**配置文件变更**
- 配置目录结构调整为三级合并（global > module > runtime）
- YAML 配置键名规范化
- `.env.template` 新增多个配置项

**命令行接口变更**
- `ops_toolkit.py` 参数名称调整
- `load_tester.py` 输出格式改为 JSON
- 移除已废弃的脚本

**迁移指南**

详见 [MIGRATION_REPORT.md](workshop/docs/MIGRATION_REPORT.md) 获取完整的 V1 → V2 迁移说明。

#### 📊 统计数据

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

DevOps:
├── Docker 服务: 7 个
├── CI/CD 阶段: 8 个
├── 告警规则: 12 条
└── 负载测试类型: 5 种
```

---

## [1.9.0] - 2026-03-15

### ✨ 新增
- RealSense 相机同步控制功能
- 相机校准工具 (内参/外参)
- ROS Bag 解析器 v2
- 图像压缩算法优化

### 🔧 改进
- 提升相机采集帧率稳定性
- 优化内存占用 (-20%)

---

## [1.8.0] - 2026-02-28

### ✨ 新增
- HDVS 分割算法集成
- YOLO 目标检测支持
- 数据打包多格式输出 (COCO/YOLO/VOC/KITTI)

### 🐛 修复
- 修复大文件处理的内存泄漏
- 修复并发写入冲突

---

## [1.7.0] - 2026-02-10

### ✨ 新增
- OSS 对象存储交付模块
- 邮件/Webhook 通知系统
- 数据完整性校验 (MD5/SHA256)

### 🔧 改进
- 上传断点续传支持
- 并发上传优化

---

## [1.6.0] - 2026-01-25

### ✨ 新增
- 模糊检测算法
- 曝光分析工具
- 帧丢弃检测机制

### 🐛 修复
- 修复低光照环境下的误判问题

---

## [1.5.0] - 2026-01-10

### ✨ 新增
- 隐私脱敏模块 (人脸/车牌模糊化)
- ROS Bag 批量解析
- 元数据提取和索引

### 🔧 改进
- 解析速度提升 30%

---

## [1.0.0] - 2025-12-01

### 🎉 初始版本发布
- 基础数据处理管道框架
- 6 个核心处理阶段 (Ingest → Quality → Enhance → Calibrate → Pack → Delivery)
- Intel RealSense 相机支持
- 基础配置管理系统
- Shell 脚本工具集

---

## 版本说明

### 版本号规则

Workshop 遵循 [语义化版本 (SemVer)](https://semver.org/) 规范：

- **主版本号 (MAJOR)**: 不兼容的 API 变更
- **次版本号 (MINOR)**: 向后兼容的功能新增
- **修订号 (PATCH)**: 向后兼容的问题修正

### 发布周期

- **大版本**: 约 6 个月一次 (包含重大架构变更)
- **小版本**: 约 1-2 个月一次 (功能迭代)
- **补丁版本**: 按需发布 (Bug 修复)

### 更新日志维护

每次发布时更新此文件：
1. 在 `[Unreleased]` 下添加新条目
2. 发布时创建新的版本标题
3. 按照 **Added / Changed / Deprecated / Removed / Fixed / Security** 分类

---

## 未来计划 (Roadmap)

### [2.1.0] - 计划中

- [ ] 流式数据处理支持 (Streaming Pipeline)
- [ ] GPU 加速集成 (CUDA/OpenCL)
- [ ] 分布式任务队列 (Celery/RQ)
- [ ] Web UI 管理界面
- [ ] GraphQL API 接口

### [2.2.0] - 远期规划

- [ ] 多租户支持
- [ ] 国际化 (i18n)
- [ ] 插件市场
- [ ] 云原生部署 (Kubernetes Helm Chart)

---

**查看完整历史**: [Git Tags](https://atomgit.com/spharx/workshop/-/tags)  
**当前版本**: [2.0.0](https://atomgit.com/spharx/workshop/-/tree/v2.0.0)  
**下一个版本**: [2.1.0-dev](https://atomgit.com/spharx/workshop/-/branches)

---

*最后更新: 2026-04-07 by SPHARX DevTeam*
