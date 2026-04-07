# Workshop V2.0 重构 - 快速入门指南

## 🚀 5分钟上手新架构

### 核心概念

Workshop V2.0 采用 **AgentOS 微内核架构思想**进行了全面重构。核心改进：

- **BasePipeline**: 统一的 Pipeline 基类，消除重复代码
- **ConfigManager**: 三级配置合并 + Schema 验证
- **Exception System**: 100+ 错误码 + 错误链追踪
- **InputValidator**: 全面输入验证和安全防护
- **Logging Setup**: 彩色日志 + 自动轮转

---

## 📦 新增文件清单

### 核心基础设施 (`common/core/`)

```
common/core/
├── __init__.py              # 包导出（一键导入所有组件）
├── base_pipeline.py         # Pipeline 抽象基类 ⭐ 核心
├── exceptions.py            # 统一异常体系 ⭐ 核心
├── config_manager.py        # 配置管理器 ⭐ 核心
├── logging_setup.py         # 日志系统设置 ⭐ 实用
└── input_validator.py       # 输入验证器 ⭐ 安全
```

### 重构后的 Pipeline

```
pipelines/run_00_ingest/runner_v2.py    # 数据导入 (已重构)
pipelines/run_01_quality/runner_v2.py   # 质量检测 (已重构)
```

### 测试体系 (`tests/`)

```
tests/
├── framework/test_framework.py          # 测试运行器
└── unit/core/
    ├── test_exceptions.py              # 异常测试 (10用例)
    ├── test_config_manager.py          # 配置测试 (9用例)
    ├── test_base_pipeline.py           # Pipeline测试 (11用例)
    └── test_input_validator.py         # 验证器测试 (11用例)
```

---

## 💻 使用示例

### 1️⃣ 创建新的 Pipeline（推荐方式）

```python
# my_new_pipeline.py
from common.core import (
    BasePipeline,
    PipelineResult,
    ConfigManager,
    setup_logging,
    InputValidator,
    ErrorCode
)
import logging

class MyNewPipeline(BasePipeline):
    """我的新处理模块"""
    
    MODULE_NAME = "06_my_module"  # 模块名称
    VERSION = "1.0.0"             # 版本号
    
    def _initialize(self):
        """初始化资源"""
        self.logger.info("初始化模型/连接硬件...")
        
        # 加载配置
        self.threshold = self.config.get('threshold', default=0.5)
        self.model_path = self.config.get('model_path')
        
        # 初始化资源
        # self.model = load_model(self.model_path)
        
        self.logger.info("✓ 初始化完成")
    
    def _execute(self, input_data=None, **kwargs):
        """执行核心逻辑"""
        validator = InputValidator()
        
        # 验证输入参数
        validation = validator.validate_required(
            kwargs.get('input_file'),
            name='input_file'
        )
        if not validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(validation.errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        input_file = kwargs['input_file']
        self.logger.info(f"开始处理: {input_file}")
        
        try:
            # 你的业务逻辑
            result_data = {
                'input': input_file,
                'output': '/app/output/result.json',
                'items_processed': 42
            }
            
            self._increment_processed(1)  # 更新计数器
            
            return PipelineResult(
                success=True,
                output=result_data,
                metrics={'processing_time': 1.23}
            )
            
        except Exception as e:
            self.logger.error(f"处理失败: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=str(e),
                error_code=ErrorCode.ALGORITHM_EXECUTION_FAILED
            )
    
    def _cleanup(self):
        """清理资源"""
        self.logger.info("释放资源...")
        # if hasattr(self, 'model'):
        #     del self.model


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="My New Module v2.0")
    parser.add_argument("--input", required=True, help="输入文件")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging("06_my_module")
    
    # 运行 Pipeline
    pipeline = MyNewPipeline(config_path=args.config)
    result = pipeline.run(input_file=args.input, output=args.output)
    
    if result.success:
        logger.info("✓ 处理成功!")
        import sys; sys.exit(0)
    else:
        logger.error(f"✗ 处理失败: {result.error}")
        import sys; sys.exit(1)


if __name__ == "__main__":
    main()
```

**对比旧代码（runner.py）的改进**：
- ❌ 旧版：~40行重复的日志/配置/异常处理代码
- ✅ 新版：只需关注 `_initialize()` / `_execute()` / `_cleanup()` 业务逻辑
- **代码量减少：60%+**

---

### 2️⃣ 使用 ConfigManager

```python
from common.core import ConfigManager

# 方式1：自动加载模块配置
config = ConfigManager(module_name="01_quality")

# 获取配置值（带默认值和类型检查）
threshold = config.get('blur_threshold', default=100, expected_type=int)
mode = config.get('mode', default='strict')

# 嵌套访问（点号分隔）
depth_config = config.get('quality.depth.enabled', default=False)

# 运行时覆盖（不修改原文件）
config.set('blur_threshold', 150)

# 获取完整配置字典
all_config = config.config

# Schema 验证
errors = config.validate_schema({
    'threshold': {'type': int, 'min': 0, 'max': 255, 'required': True},
    'mode': {'type': str, 'allowed': ['strict', 'relaxed'], 'required': True}
})
if errors:
    print(f"配置错误: {errors}")

# 热重载
config.reload()
```

---

### 3️⃣ 使用统一异常体系

```python
from common.core import (
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    ErrorCode
)

# 抛出异常（自动记录上下文信息）
try:
    raise ValidationError(
        ErrorCode.INVALID_DATA_FORMAT,
        "图像格式不支持",
        expected_format=["jpg", "png"],
        actual_format="bmp"
    )
except WorkshopError as e:
    print(f"错误码: {e.code.name}")           # INVALID_DATA_FORMAT
    print(f"中文描述: {e.description_zh}")     # 无效的数据格式
    print(f"英文描述: {e.description_en}")     # Invalid data format
    print(f"严重程度: {e.severity.value}")      # error
    print(f"上下文数据: {e.context_data}")      # {'expected_format': [...], ...}
    print(f"错误链深度: {e.error_chain.depth}") # 1

# 错误统计
from common.core import error_code_manager
stats = error_code_manager.get_stats()
print(f"总错误数: {stats['total_errors']}")
```

---

### 4️⃣ 使用 InputValidator 进行安全验证

```python
from common.core import InputValidator

validator = InputValidator()

# 单项验证
result = validator.validate_type(42, int, name="age")
assert result.valid is True

result = validator.validate_range(
    value=75,
    min_val=0,
    max_val=100,
    name="score"
)
assert result.valid is True

# 路径安全检查（防止 ../../../etc/passwd 攻击）
result = validator.validate_path(
    path=user_input,
    must_exist=True,
    should_be_file=True,
    allowed_extensions=['.jpg', '.png'],
    name="image_file"
)
if not result.valid:
    raise ValueError(result.errors)

# 批量验证
validation = validator.validate_all([
    (validator.validate_file_readable, (input_path,), {}),
    (validator.validate_directory_writable, (output_dir,), {}),
    (validator.validate_regex, (email, r'^[\w.-]+@[\w.-]+$'), {'name': 'email'}),
])

if not validation.valid:
    print(f"验证失败:\n" + "\n".join(validation.errors))
```

---

### 5️⃣ 设置日志系统

```python
from common.core import setup_logging

# 基础用法
logger = setup_logging(module_name="my_module")

# 高级配置
logger = setup_logging(
    module_name="my_module",
    log_dir="/app/logs",
    level=logging.DEBUG,              # 日志级别
    use_color=True,                    # 彩色控制台输出
    max_bytes=20*1024*1024,           # 单文件最大20MB
    backup_count=10                    # 保留10个备份
)

# 使用
logger.debug("调试信息")               # 开发环境
logger.info("常规信息")                 # 生产环境默认级别
logger.warning("警告: 内存使用率 > 80%")
logger.error("错误: 连接数据库失败")
logger.critical("致命错误: 磁盘空间不足")

# 清理过期日志（可选）
from common.core import clear_old_logs
deleted_count = clear_old_logs(log_dir="/app/logs", max_age_days=30)
print(f"已清理 {deleted_count} 个过期日志文件")
```

**日志输出示例**：
```
2026-04-07 14:30:45 | INFO     | Pipeline.my_module | 模块启动
2026-04-07 14:30:46 | WARNING  | Pipeline.my_module | 警告: 内存使用率 > 80%
2026-04-07 14:30:47 | ERROR    | Pipeline.my_module | 错误: 处理失败
```

---

## 🔧 运行测试

```bash
# 运行全部测试
cd Workshop
python tests/framework/test_framework.py

# 运行单个测试模块
python tests/unit/core/test_exceptions.py
python tests/unit/core/test_config_manager.py
python tests/unit/core/test_base_pipeline.py
python tests/unit/core/test_input_validator.py

# 预期输出：
# ✓ All exception system tests passed!
# ✓ All Config Manager tests passed!
# ✓ All BasePipeline tests passed!
# ✓ All InputValidator tests passed!
#
# Results: 41/41 passed (100.0%) in 2.345s
```

---

## 📖 从旧版本迁移指南

### 步骤 1：保留旧文件（零风险）

```bash
# 旧的 runner.py 保持不变（向后兼容）
cp pipelines/run_XX_xxx/runner.py pipelines/run_XX_xxx/runner_legacy.py
```

### 步骤 2：创建 v2 版本

参考上面的"创建新的 Pipeline"示例，将业务逻辑迁移到 `runner_v2.py`

### 步骤 3：逐步切换

```bash
# 测试阶段：同时运行两个版本进行对比
python pipelines/run_00_ingest/runner.py --input data.bag --output out_v1
python pipelines/run_00_ingest/runner_v2.py --input data.bag --output out_v2

# 对比结果后，逐步替换
```

### 主要改动点对照表

| 功能 | 旧代码 (runner.py) | 新代码 (runner_v2.py) |
|------|-------------------|---------------------|
| **日志设置** | 手动配置 logging.basicConfig() | `setup_logging("module_name")` |
| **配置加载** | 直接调用 load_config() | `ConfigManager(module_name=...)` |
| **异常处理** | 简单 try-except | 统一异常体系 + 错误码 |
| **输入验证** | 几乎没有 | `InputValidator` 全面验证 |
| **生命周期** | 无 | `_initialize()` → `_execute()` → `_cleanup()` |
| **性能指标** | 手动计时 | 自动收集（execution_time, processed_count）|
| **回调机制** | 无 | `on_start()` / `on_complete()` / `on_error()` |
| **健康检查** | 无 | `health_check()` 接口 |

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **始终继承 BasePipeline**
   - 获得完整的生命周期管理和指标收集
   
2. **使用 ConfigManager 管理配置**
   - 支持多层级合并、类型检查、Schema验证
   
3. **全面使用 InputValidator**
   - 在 `_execute()` 入口处验证所有外部输入
   
4. **抛出具体的异常子类**
   - 不要直接抛出 Exception，使用 PipelineError/ValidationError 等
   
5. **利用回调函数**
   - 用于通知、监控、日志记录等横切关注点

### ❌ 应避免的做法

1. **不要在 Pipeline 中硬编码路径**
   - 使用配置或参数传入
   
2. **不要忽略异常**
   - 至少记录到日志（self.logger.error）
   
3. **不要在 _execute() 中做重量级初始化**
   - 应该放在 _initialize() 中
   
4. **不要忘记调用 _increment_processed()**
   - 否则 processed_count 始终为 0

---

## 🆘 常见问题

### Q1: 如何添加新的错误码？

```python
# 在 exceptions.py 的 ErrorCode 枚举中添加
class ErrorCode(IntEnum):
    # ... 已有错误码 ...
    
    # 新增自定义错误码（建议从9000开始）
    MY_CUSTOM_ERROR = 9001
    
# 同时在 _error_descriptions 字典中添加描述
_error_descriptions = {
    # ... 已有描述 ...
    ErrorCode.MY_CUSTOM_ERROR: {
        "en": "Custom error description",
        "zh_cn": "自定义错误描述"
    }
}
```

### Q2: 如何实现异步 Pipeline？

```python
class AsyncPipeline(BasePipeline):
    async def _execute(self, input_data=None, **kwargs):
        # 异步操作
        result = await some_async_operation()
        return PipelineResult(success=True, output=result)

# 使用
pipeline = AsyncPipeline()
result = await pipeline.run_async(data)
```

### Q3: 如何在多个 Pipeline 间共享状态？

```python
# 方式1：通过配置传递
config.set('shared_state.key', value)

# 方式2：使用回调
def on_complete(result):
    shared_store[result.module_name] = result.output

pipeline.on_complete(on_complete)
```

---

## 📚 更多文档

- [完整重构报告](../docs/REFACTORING_REPORT_V2.md) - 详细的技术决策和量化指标
- [AgentOS 架构文档](../../AgentOS/docs/architecture/) - 参考架构设计
- [API 文档（待生成）] - Sphinx 自动生成的 API 文档

---

## 🤝 贡献指南

欢迎提交 Issue 和 PR！请遵循：

1. 新模块必须继承 `BasePipeline`
2. 所有公开接口必须有 docstring 和类型注解
3. 必须为新功能编写单元测试
4. 遵循现有的代码风格

---

**开始享受全新的 Workshop V2.0 吧！🎉**

如有问题，请查阅完整重构报告或联系维护团队。
