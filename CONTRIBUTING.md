# 贡献指南 - Workshop V2.0

感谢您考虑为 Workshop 项目做出贡献！本文档将帮助您了解如何参与项目开发。

---

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交 Pull Request](#提交-pull-request)
- [代码审查流程](#代码审查流程)

---

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们作为贡献者和维护者承诺：

- **尊重他人** - 无论经验水平、身份或背景
- **接受建设性批评** - 以改进工作为目的
- **专注于对社区最有利的事情** - 展现对他人的同理心

### 不可接受的行为

包括但不限于：

- 使用性化语言或图像
- 人身攻击或政治攻击
- 公开或私下骚扰
- 未经许可发布他人的私人信息

---

## 如何贡献

### 报告 Bug

发现 Bug？请通过 Issue 报告：

1. **搜索现有 Issues** - 避免重复报告
2. **使用 Bug 模板** - 提供完整信息
3. **包含复现步骤** - 最小化的可复现代码
4. **添加环境信息** - OS、Python 版本等

**Issue 标题格式**:
```
[Bug] 简短描述问题
```

**示例**:
```markdown
## 描述
ConfigManager 在加载不存在的模块时抛出意外异常

## 复现步骤
```python
config = ConfigManager(module_name='nonexistent')
```

## 期望行为
应该抛出 ConfigurationError(CONFIG_NOT_FOUND)

## 实际行为
抛出 FileNotFoundError

## 环境
- OS: Ubuntu 20.04
- Python: 3.10.6
- Workshop: 2.0.0
```

### 建议新功能

有好的想法？请提出 Feature Request：

1. **清晰描述功能** - 解决什么问题
2. **提供使用场景** - 为什么需要这个功能
3. **考虑 API 设计** - 建议的接口
4. **讨论实现方案** - 可选但推荐

**Issue 标题格式**:
```
[Feature] 功能简短描述
```

### 改进文档

文档是项目的重要组成部分！您可以：

- 修复错别字和语法错误
- 补充缺失的示例代码
- 改进说明的清晰度
- 添加新的教程或指南
- 翻译文档到其他语言

### 编写代码

#### 小改动（文档修复、小 bug 修复）

1. Fork 项目
2. 创建分支: `git checkout -b fix/typo-in-readme`
3. 进行修改
4. 提交 PR

#### 大改动（新功能、重大重构）

1. 先讨论 - 创建 Issue 或在现有 Issue 中讨论
2. 获得维护者认可后再开始编码
3. 遵循开发流程（见下文）

---

## 开发流程

### 1. Fork 和克隆

```bash
# 1. Fork 仓库 (在 GitHub/Gitee/AtomGit 上点击 Fork 按钮)

# 2. 克隆你的 Fork
git clone https://atomgit.com/<your-username>/workshop.git
cd workshop

# 3. 添加上游仓库
git remote add upstream https://atomgit.com/spharx/workshop.git

# 4. 确保主分支最新
git fetch upstream
git checkout main
git merge upstream/main
```

### 2. 创建分支

```bash
# 从 main 创建功能分支
git checkout -b feature/amazing-feature

# 或者修复分支
git checkout -b fix/solve-issue-123
```

**分支命名规范**:

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feature/` | `feature/add-augmentation-pipeline` |
| Bug 修复 | `fix/` | `fix/config-loading-error` | 
| 文档 | `docs/` | `docs/update-api-reference` |
| 重构 | `refactor/` | `refactor/optimize-io-layer` |
| 测试 | `test/` | `test/add-unit-tests-for-metrics` |
| CI/CD | `ci/` | `ci/add-lint-check` |

### 3. 开发和测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行 linting
ruff check .
black --check .
isort --check-only .

# 自动格式化
black .
isort .

# 运行测试
pytest tests/unit/ -v

# 运行完整测试套件
pytest -v --cov=workshop

# 运行类型检查 (可选)
mypy workshop/common/core/
```

### 4. 提交更改

```bash
# 查看更改
git status
git diff

# 暂存文件
git add modified_file.py

# 提交 (遵循 Conventional Commits 规范)
git commit -m "feat(pipelines): add data augmentation pipeline v2

- Implement ImageAugmentor with rotation and brightness adjustment
- Add AugmentPipeline based on BasePipeline ABC
- Include unit tests with 95%+ coverage

Closes #456"
```

**Commit Message 格式**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复  
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（不是新功能也不是修复）
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建过程或辅助工具变动
- `ci`: CI/CD 配置变更
- `revert`: 回滚提交

**Scope 范围** (可选):
- `core`, `pipelines`, `hardware`, `tests`, `docs`, `ci`, 等

**示例**:
```bash
feat(core): add async support to IOManager

Implement asynchronous file operations for better I/O performance.
Supports both sync and async modes via configuration switch.

- Add async_read() and async_write() methods
- Maintain backward compatibility with existing sync API
- Add integration tests for concurrent operations

Closes #789
```

### 5. 推送和更新

```bash
# 推送到你的 Fork
git push origin feature/amazing-feature

# 如果上游有更新，同步你的分支
git fetch upstream
git rebase upstream/main
git push origin feature/amazing-feature --force-with-lease
```

---

## 代码规范

### Python 风格

- **PEP 8**: 遵循 PEP 8 编码规范
- **Black**: 使用 Black 格式化代码 (配置见 pyproject.toml)
- **isort**: 导入排序 (与 Black 兼容模式)
- **类型注解**: 所有公共 API 必须有类型注解
- **Docstring**: Google 风格 docstring

### 代码质量要求

#### 必须通过的检查

```bash
# Linting (ruff)
ruff check workshop/

# 格式化 (Black + isort)
black --check .
isort --check-only .

# 测试
pytest tests/unit/ -v --cov=workshop --cov-fail-under=80
```

#### 代码复杂度

- 单个函数不超过 50 行
- 圈复杂度 ≤ 10
- 文件不超过 500 行 (核心模块除外)

#### 文档要求

- 所有公共类和函数必须有 docstring
- 复杂逻辑添加注释解释"为什么"
- 更新相关文档 (API Reference, README, etc.)

### 示例：符合规范的代码

```python
from typing import Dict, Any, List, Optional
from workshop import BasePipeline, PipelineResult, ConfigManager


class ExamplePipeline(BasePipeline):
    """示例管道 - 展示最佳实践。

    这个管道演示了 Workshop V2.0 的标准开发模式，
    包括完整的生命周期管理、错误处理和日志记录。

    Attributes:
        config: 配置管理器实例
        logger: 日志记录器
    """

    def _initialize(self) -> None:
        """初始化管道资源和配置。"""
        self.config = ConfigManager(
            module_name='example',
            auto_load=True
        )
        self.logger = get_logger('ExamplePipeline')

    def _execute(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> PipelineResult:
        """执行数据处理逻辑。

        Args:
            input_data: 输入数据字典，必须包含 'items' 键
            **kwargs: 额外参数

        Returns:
            PipelineResult: 包含处理结果和性能指标

        Raises:
            ValueError: 当输入数据缺少必需字段时
        """
        items = input_data.get('items', [])
        
        if not items:
            raise ValueError("输入数据不能为空")

        processed = []
        for item in items:
            result = self._process_single_item(item)
            processed.append(result)

        return PipelineResult(
            success=True,
            output={'results': processed},
            processed_count=len(processed),
            metrics={
                'input_count': len(items),
                'output_count': len(processed)
            }
        )

    def _cleanup(self) -> None:
        """清理资源并释放连接。"""
        if hasattr(self, '_connection'):
            self._connection.close()
```

---

## 提交 Pull Request

### PR 前检查清单

- [ ] 代码遵循项目风格指南
- [ ] 已通过所有 linting 检查 (`ruff check .`)
- [ ] 已通过格式化检查 (`black --check .`, `isort --check-only .`)
- [ ] 已添加/更新单元测试
- [ ] 测试全部通过 (`pytest tests/ -v`)
- [ ] 测试覆盖率 ≥ 80% (`--cov-fail-under=80`)
- [ ] 文档已更新 (docstring, API docs, etc.)
- [ ] Commit messages 符合规范
- [ ] 无合并冲突
- [ ] PR 标题清晰描述变更内容

### PR 模板

```markdown
## 变更描述
简要描述此 PR 的内容和目的

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 相关 Issue
Fixes #123 或 Closes #456

## 详细变更
- 变更点 1
- 变更点 2
- ...

## 测试计划
- [ ] 单元测试: 描述测试覆盖范围
- [ ] 集成测试: 如适用
- [ ] 手动测试步骤: 如适用

## 截图/演示 (如适用)
添加截图或 GIF 展示效果

## 检查清单
- [ ] 代码符合风格规范
- [ ] 自测通过
- [ ] 文档已更新
- [ ] 无破坏性变更 (如有请说明)
```

### PR 标题格式

```
<type>: 简短描述 (<issue number>)
```

**示例**:
```
feat: add image augmentation pipeline (#456)
fix: resolve config loading race condition (#789)
docs: update API reference for metrics module (#123)
```

---

## 代码审查流程

### 审查者指南

作为代码审查者，请关注：

#### ✅ 应该检查的

1. **正确性**: 代码是否正确实现了预期功能？
2. **设计**: 代码设计是否合理？是否有更好的方式？
3. **边界条件**: 是否处理了错误输入和边界情况？
4. **性能**: 是否存在明显的性能问题？
5. **安全性**: 是否引入安全风险？
6. **测试**: 测试是否充分？是否覆盖边界情况？
7. **文档**: 代码和文档是否一致？
8. **向后兼容**: 是否破坏现有 API？

#### ❌ 不应该关注的

- 代码风格（由工具自动处理）
- 个人偏好（除非影响可读性）
- 微小的优化（可以后续 PR）

### 审查评论格式

**建议修改**:
```markdown
**Question**: 这里为什么要用列表推导式而不是循环？
**Suggestion**: 可以考虑使用生成器表达式来节省内存。
```

**必须修改**:
```markdown
**Must Fix**: 这里缺少对 None 的检查，会导致 AttributeError。
请添加: `if value is not None:` 条件判断。
```

**赞赏**:
```markdown
**Nice**: 这里的错误处理很优雅，使用了自定义异常体系！👍
```

### 作者响应

- **感谢**所有反馈，即使是批评
- **及时回复**审查意见（目标: 24小时内）
- **礼貌讨论**不同观点
- **明确标记**哪些已修改，哪些待讨论

---

## 合并流程

### 自动检查

PR 必须通过以下自动检查才能合并：

- ✅ CI/CD 流水线成功 (linting + testing)
- ✅ 代码覆盖率达标 (≥80%)
- ✅ 至少 1 位维护者批准 (Approve)
- ✅ 无阻塞问题 (Request Changes)

### 合并策略

- **main 分支**: Squash and merge (保持历史整洁)
- **develop 分支**: Create merge commit (保留完整历史)
- **hotfix 分支**: 直接合并到 main 并 cherry-pick 到 develop

### 发布流程

维护者负责：

1. 更新版本号 (`pyproject.toml` 中的 version)
2. 更新 CHANGELOG.md
3. 创建 Git Tag
4. 发布到 PyPI (如果适用)
5. 更新文档网站

---

## 社区

### 沟通渠道

- **Issues**: Bug 报告和功能请求
- **Pull Requests**: 代码贡献
- **Discussions** (如果有): 一般性问题和技术讨论
- **邮件**: lidecheng@spharx.cn / wangliren@spharx.cn

### 认可贡献者

所有贡献者都会被添加到 [CONTRIBUTORS.md](CONTRIBUTORS.md) 文件中：

- Bug 报告者
- 功能建议者
- 代码贡献者
- 文档改进者
- 设计师

---

## 许可证

通过贡献代码，您同意您的贡献将在与项目相同的许可证下发布：
- **GPL-3.0** 用于开源版本
- **商业授权** 需联系 SPHARX

详见 [LICENSE-GPL-3.0](LICENSE-GPL-3.0) 和 [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL)。

---

## 致谢

感谢每一位为 Workshop 做出贡献的开发者！你们的努力让这个项目变得更好。

> "微微的灯火照不亮前路，但能指引我们前行的方向"

---

**最后更新**: 2026-04-07  
**维护团队**: SPHARX DevTeam
