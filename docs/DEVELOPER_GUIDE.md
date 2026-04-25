# Workshop V2.0 开发者指南

## 目录

- [1. 环境搭建](#1-环境搭建)
- [2. 项目结构详解](#2-项目结构详解)
- [3. 开发流程](#3-开发流程)
- [4. 代码规范](#4-代码规范)
- [5. 创建新 Pipeline](#5-创建新-pipeline)
- [6. 测试指南](#6-测试指南)
- [7. 调试技巧](#7-调试技巧)
- [8. 性能优化](#8-性能优化)
- [9. 常见问题](#9-常见问题)

---

## 1. 环境搭建

### 1.1 前置要求

- **操作系统**: Ubuntu 20.04+ / macOS 11+ / Windows 11 (WSL2)
- **Python**: 3.8+ (推荐 3.10 或 3.11)
- **Git**: 2.30+
- **Docker**: 20.10+ (可选，用于容器化部署)

### 1.2 克隆项目

```bash
git clone https://atomgit.com/spharx/workshop.git
cd workshop
```

### 1.3 创建虚拟环境

```bash
# 使用 venv (推荐)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 使用 conda
conda create -n workshop python=3.10 -y
conda activate workshop
```

### 1.4 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 开发模式安装 (可编辑安装)
pip install -e ".[dev]"

# 如果需要硬件支持
pip install -e ".[hardware]"

# 如果需要机器学习支持
pip install -e ".[ml]"
```

### 1.5 验证安装

```python
# 在 Python 中测试导入
from core_workshop import BasePipeline, ConfigManager, get_info

print(get_info())
# 输出: {'name': 'Workshop', 'version': '2.0.0', ...}
```

### 1.6 配置环境变量

```bash
# 复制环境变量模板
cp .env.template .env

# 编辑配置
vim .env  # 或使用其他编辑器
```

---

## 2. 项目结构详解

### 2.1 顶层目录

```
workshop/                          # 项目根目录
├── workshop/                      # 核心代码包 (V2.0)
│   ├── __init__.py               # 包入口，导出公共 API
│   ├── common/                   # 通用模块
│   │   ├── core/                # ★ 核心基础设施 (10个模块)
│   │   ├── configs/             # YAML 配置文件
│   │   ├── schemas/             # 数据模式定义
│   │   └── dashboard/           # Web 监控仪表板
│   ├── pipelines/               # 数据处理管道 (6个)
│   ├── hardware/                # 硬件抽象层
│   ├── tests/                   # 测试套件
│   ├── scripts/                 # 运维工具脚本
│   ├── config/                  # Prometheus/Grafana 配置
│   └── docs/                    # 技术文档
├── common/                       # 向后兼容层
├── pipelines/                    # 向后兼容层
├── hardware/                     # 向后兼容层
├── tests/                        # 向后兼容层
├── scripts/                      # Shell 脚本
├── config/                       # 根级配置
├── docs/                         # 根级文档
├── pyproject.toml                # 项目配置 (★ 新增)
├── requirements.txt              # 依赖列表 (★ 新增)
├── Dockerfile                    # Docker 构建
├── docker-compose.yml            # 容器编排
└── README.md                     # 项目说明
```

### 2.2 核心模块说明

#### common/core/ - 核心基础设施

| 模块 | 功能 | 关键类/函数 |
|------|------|------------|
| `base_pipeline.py` | Pipeline 抽象基类 | `BasePipeline`, `PipelineResult`, `PipelineStatus` |
| `config_manager.py` | 配置管理 | `ConfigManager` |
| `exceptions.py` | 异常体系 | `WorkshopError`, `ErrorCode`, `error_code_manager` |
| `logging_setup.py` | 日志系统 | `setup_logging()`, `get_logger()` |
| `input_validator.py` | 输入验证 | `InputValidator`, `Pattern` |
| `io_abstraction.py` | IO 抽象层 | `IOManager`, `IStorageBackend`, `LocalStorageBackend` |
| `metrics.py` | Prometheus 监控 | `WorkshopMetrics`, `get_metrics()` |
| `performance.py` | 性能工具 | `BenchmarkSuite`, `MemoryProfiler`, `quick_benchmark()` |
| `security_audit.py` | 安全审计 | `CodeSecurityScanner`, `run_full_security_audit()` |

#### pipelines/ - 数据处理管道

每个管道遵循统一的目录结构：

```
run_XX_name/
├── algorithm/          # 算法实现
│   ├── __init__.py
│   ├── module_a.py    # 具体算法
│   └── module_b.py
├── model/              # 模型相关（如需要）
│   ├── __init__.py
│   └── manager.py      # 模型管理器
├── runner.py           # V1 运行器 (向后兼容)
├── runner_v2.py        # V2 运行器 (基于 BasePipeline) ★
├── requirements.txt    # 特定依赖
└── Dockerfile          # 容器化配置
```

---

## 3. 开发流程

### 3.1 Git 工作流

```bash
# 1. 更新主分支
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/my-new-feature

# 3. 开发和提交
git add .
git commit -m "feat: 添加新的数据处理算法"

# 4. 推送分支
git push origin feature/my-new-feature

# 5. 创建 Pull Request
# 访问 AtomGit/GitHub 创建 PR
```

### 3.2 Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```bash
feat(pipelines): 添加新的数据增强算法 HDVS-SegV2

- 实现 HDVS 分割算法 V2 版本
- 支持多尺度特征融合
- 提升 mIoU 5%

Closes #123
```

### 3.3 分支策略

- `main`: 生产稳定版本
- `develop`: 开发主分支
- `feature/*`: 新功能开发
- `fix/*`: Bug 修复
- `release/*`: 发布准备

---

## 4. 代码规范

### 4.1 Python 编码风格

项目使用以下工具保证代码质量：

#### Black - 代码格式化

```bash
# 格式化单个文件
black workshop/common/core/base_pipeline.py

# 格式化整个项目
black .

# 检查哪些文件需要格式化 (不修改)
black --check .

# 显示差异
black --diff .
```

**配置**: 见 `pyproject.toml` 的 `[tool.black]` 部分

#### isort - 导入排序

```bash
# 排序导入
isort workshop/common/core/

# 与 Black 配合使用
isort --profile black .
```

**配置**: 见 `pyproject.toml` 的 `[tool.isort]` 部分

#### flake8 / ruff - Linting

```bash
# 使用 ruff (更快)
ruff check workshop/common/core/

# 自动修复简单问题
ruff check --fix workshop/common/core/
```

**配置**: 见 `pyproject.toml` 的 `[tool.ruff]` 部分

#### mypy - 类型检查

```bash
# 类型检查
mypy workshop/common/core/

# 严格模式
mypy --strict workshop/common/core/
```

### 4.2 代码风格要点

```python
# ✅ 正确: 使用类型注解
def process_data(
    input_path: str,
    output_dir: Optional[str] = None,
    max_workers: int = 4
) -> PipelineResult:
    """处理数据的简短描述。

    Args:
        input_path: 输入文件路径
        output_dir: 输出目录 (可选)
        max_workers: 最大工作线程数

    Returns:
        PipelineResult: 处理结果

    Raises:
        ValidationError: 当输入路径无效时
        DataIOError: 当文件读取失败时
    """
    ...

# ❌ 错误: 缺少类型注解和文档字符串
def process_data(input_path, output_dir=None, max_workers=4):
    ...
```

### 4.3 文档字符串规范

使用 Google 风格的 docstring：

```python
class MyClass:
    """类的简短描述。

    更详细的描述（如果需要）。

    Attributes:
        attr1: 属性1的描述
        attr2: 属性2的描述
    """

    def my_method(self, param1: str, param2: int = 0) -> bool:
        """方法的简短描述。

        Args:
            param1: 参数1描述
            param2: 参数2描述，默认为0

        Returns:
            返回值描述

        Raises:
            ValueError: 当param1为空时
            TypeError: 当参数类型错误时

        Example:
            >>> obj = MyClass()
            >>> obj.my_method("test", 5)
            True
        """
        ...
```

---

## 5. 创建新 Pipeline

### 5.1 完整示例：创建自定义 Pipeline

假设我们需要创建一个新的数据增强管道 `run_06_augment`：

#### Step 1: 创建目录结构

```bash
mkdir -p workshop/pipelines/run_06_augment/{algorithm,model}
touch workshop/pipelines/run_06_augment/__init__.py
touch workshop/pipelines/run_06_augment/algorithm/__init__.py
touch workshop/pipelines/run_06_augment/model/__init__.py
```

#### Step 2: 实现算法模块

```python
# workshop/pipelines/run_06_augment/algorithm/augmentor.py
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np
from core_workshop import BasePipeline, PipelineResult


class ImageAugmentor:
    """图像增强器"""

    def __init__(self, config: 'ConfigManager'):
        self.config = config
        self.rotation_range = config.get('rotation_range', default=15)
        self.brightness_range = config.get('brightness_range', default=0.2)

    def rotate(self, image: np.ndarray, angle: float) -> np.ndarray:
        """随机旋转图像"""
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h))

    def adjust_brightness(self, image: np.ndarray, factor: float) -> np.ndarray:
        """调整亮度"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def augment(self, image: np.ndarray) -> List[np.ndarray]:
        """执行所有增强操作"""
        augmented = [image]

        # 随机旋转
        angle = np.random.uniform(-self.rotation_range, self.rotation_range)
        augmented.append(self.rotate(image, angle))

        # 随机亮度调整
        brightness = np.random.uniform(
            1 - self.brightness_range,
            1 + self.brightness_range
        )
        augmented.append(self.adjust_brightness(image, brightness))

        return augmented
```

#### Step 3: 实现 Pipeline Runner

```python
# workshop/pipelines/run_06_augment/runner_v2.py
from typing import Any, Dict, List, Optional
import logging
import time
from pathlib import Path

from core_workshop import (
    BasePipeline,
    PipelineResult,
    PipelineStatus,
    ConfigManager,
    InputValidator,
    get_logger
)

from .algorithm.augmentor import ImageAugmentor


class AugmentPipeline(BasePipeline):
    """
    数据增强管道 (Step 06)

    功能：
    - 图像旋转增强
    - 亮度对比度调整
    - 颜色抖动
    - 高斯噪声添加

    输入:
        {
            'images': [np.ndarray, ...],
            'metadata': {...}
        }

    输出:
        {
            'augmented_images': [[np.ndarray, ...], ...],
            'augmentation_params': [...],
            'count': int
        }
    """

    PIPELINE_NAME = "run_06_augment"
    VERSION = "2.0.0"

    def _initialize(self) -> None:
        """初始化增强管道"""
        self.config = ConfigManager(
            module_name=self.PIPELINE_NAME,
            auto_load=True
        )

        self.validator = InputValidator()
        self.logger = get_logger(f"Pipeline.{self.PIPELINE_NAME}")

        # 初始化增强器
        self.augmentor = ImageAugmentor(self.config)

        # 配置参数
        self.num_augments_per_image = self.config.get(
            'num_augments',
            default=3
        )
        self.output_format = self.config.get(
            'output_format',
            default='numpy'
        )

        self.logger.info(f"{self.PIPELINE_NAME} 初始化完成")
        self.logger.debug(f"配置: num_augments={self.num_augments_per_image}")

    def _execute(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> PipelineResult:
        """执行数据增强"""

        start_time = time.time()
        augmented_all = []
        augmentation_params = []

        try:
            images = input_data.get('images', [])
            metadata = input_data.get('metadata', {})

            if not images:
                raise ValueError("输入图像列表为空")

            self.logger.info(f"开始处理 {len(images)} 张图像")

            for idx, image in enumerate(images):
                if not isinstance(image, (list, tuple)):
                    images_list = [image]
                else:
                    images_list = image

                augmented_batch = []
                for img in images_list:
                    augmented = self.augmentor.augment(img)
                    augmented_batch.extend(augmented)
                    augmentation_params.append({
                        'original_index': idx,
                        'num_generated': len(augmented) - 1
                    })

                augmented_all.append(augmented_batch)

                if (idx + 1) % 100 == 0:
                    self.logger.debug(f"已处理 {idx + 1}/{len(images)} 张图像")

            execution_time = time.time() - start_time
            total_augmented = sum(len(batch) for batch in augmented_all)

            self.logger.info(f"增强完成: {total_augmented} 张图像 ({execution_time:.2f}s)")

            return PipelineResult(
                success=True,
                output={
                    'augmented_images': augmented_all,
                    'augmentation_params': augmentation_params,
                    'count': total_augmented,
                    'format': self.output_format
                },
                processed_count=len(images),
                metrics={
                    'execution_time': execution_time,
                    'avg_per_image': execution_time / len(images) if images else 0,
                    'augmentation_ratio': total_augmented / len(images) if images else 0
                }
            )

        except Exception as e:
            self.logger.error(f"增强失败: {str(e)}")
            return PipelineResult(
                success=False,
                error=str(e),
                metrics={'execution_time': time.time() - start_time}
            )

    def _cleanup(self) -> None:
        """清理资源"""
        self.logger.info(f"{self.PIPELINE_NAME} 清理完成")
```

#### Step 4: 创建单元测试

```python
# tests/unit/pipelines/test_augment.py
import pytest
import numpy as np
from unittest.mock import Mock, patch

from core_workshop.pipelines.run_06_augment.runner_v2 import AugmentPipeline


class TestAugmentPipeline:

    @pytest.fixture
    def pipeline(self):
        """创建 Pipeline 实例"""
        with AugmentPipeline() as p:
            yield p

    @pytest.fixture
    def sample_input(self):
        """创建测试输入"""
        return {
            'images': [
                np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                for _ in range(5)
            ],
            'metadata': {
                'capture_date': '2024-01-01',
                'camera_id': 'test_camera'
            }
        }

    def test_initialization(self, pipeline):
        """测试初始化"""
        assert pipeline.status.name == 'READY'
        assert pipeline.config is not None

    def test_execute_success(self, pipeline, sample_input):
        """测试正常执行"""
        result = pipeline.run(sample_input)

        assert result.success is True
        assert result.processed_count == 5
        assert 'augmented_images' in result.output
        assert result.output['count'] > 5  # 应该有更多增强图像

    def test_execute_empty_input(self, pipeline):
        """测试空输入"""
        result = pipeline.run({'images': []})

        assert result.success is False
        assert '空' in result.error

    def test_metrics_recorded(self, pipeline, sample_input):
        """测试指标记录"""
        result = pipeline.run(sample_input)

        assert 'execution_time' in result.metrics
        assert result.metrics['execution_time'] > 0
        assert 'avg_per_image' in result.metrics

    def test_lifecycle_states(self, pipeline):
        """测试生命周期状态转换"""
        assert pipeline.status.name in ['CREATED', 'READY']
```

#### Step 5: 注册到 __init__.py

```python
# workshop/pipelines/__init__.py (追加)
__all__ = [
    # ... 已有的
    'run_00_ingest',
    'run_01_quality',
    'run_02_enhance',
    'run_03_calibrate',
    'run_04_pack',
    'run_05_delivery',
    'run_06_augment',  # ★ 新增
    'streaming',
]
```

---

## 6. 测试指南

### 6.1 测试结构

```
tests/
├── conftest.py              # 全局 fixtures
├── pytest.ini              # pytest 配置
├── unit/                   # 单元测试
│   ├── core/              # 核心模块测试
│   │   ├── test_base_pipeline.py
│   │   ├── test_config_manager.py
│   │   ├── test_exceptions.py
│   │   └── test_input_validator.py
│   └── pipelines/         # 管道测试
│       ├── test_ingest.py
│       ├── test_quality.py
│       └── test_augment.py  # ★ 新增
├── integration/            # 集成测试
│   ├── test_pipeline.py
│   └── test_hardware.py
└── framework/             # 测试框架
    └── test_framework.py
```

### 6.2 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/core/test_base_pipeline.py -v

# 运行特定测试类
pytest tests/unit/core/test_config_manager.py::TestConfigManager -v

# 运行单个测试用例
pytest tests/unit/core/test_base_pipeline.py::TestBasePipeline::test_lifecycle -v

# 只运行标记的测试
pytest -m "not slow"

# 并行执行 (需要 pytest-xdist)
pytest -n auto

# 生成覆盖率报告
pytest --cov=workshop --cov-report=html --cov-report=term-missing

# 详细输出
pytest -v -s
```

### 6.3 编写测试的最佳实践

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestMyComponent:

    @pytest.fixture
    def setup_component(self):
        """设置测试环境"""
        component = MyComponent()
        yield component
        component.cleanup()

    def test_normal_case(self, setup_component):
        """测试正常情况"""
        result = setup_component.process(valid_input)
        assert result.success is True
        assert result.data is not None

    def test_edge_cases(self, setup_component):
        """测试边界条件"""
        # 空输入
        result = setup_component.process([])
        assert result.success is False

        # 超大输入
        large_input = [0] * 1000000
        result = setup_component.process(large_input)
        assert result.success is True

    def test_error_handling(self, setup_component):
        """测试错误处理"""
        with pytest.raises(ValueError, match="无效输入"):
            setup_component.process(invalid_input)

    @patch('workshop.common.core.some_module.external_service')
    def test_with_mock(self, mock_service, setup_component):
        """使用 Mock 测试"""
        mock_service.call.return_value = {"status": "ok"}

        result = setup_component.use_external_service()

        mock_service.assert_called_once()
        assert result["status"] == "ok"

    @pytest.mark.slow
    def test_slow_operation(self, setup_component):
        """标记为慢速测试"""
        # 这个测试可能需要较长时间
        result = setup_component.heavy_computation()
        assert result is not None

    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (3, 6),
        (5, 10),
    ])
    def test_parameterized(self, setup_component, input_val, expected):
        """参数化测试"""
        result = setup_component.double(input_val)
        assert result == expected
```

---

## 7. 调试技巧

### 7.1 日志调试

```python
from workshop.common.core.logging_setup import get_logger

logger = get_logger(__name__)

def debug_function(data):
    logger.debug(f"输入数据: {data}")  # DEBUG 级别
    logger.info(f"开始处理")            # INFO 级别
    logger.warning(f"发现异常值")        # WARNING 级别
    logger.error(f"处理失败")           # ERROR 级别
```

**日志级别控制**:

```bash
# 设置日志级别为 DEBUG
LOG_LEVEL=DEBUG python my_script.py

# 在代码中设置
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### 7.2 断点调试

使用 VS Code 或 PyCharm 设置断点：

```python
# 方式 1: IDE 断点 (推荐)

# 方式 2: Python breakpoint() 函数 (Python 3.7+)
def complex_function(x):
    result = some_calculation(x)
    breakpoint()  # 在此处暂停，进入调试器
    return process(result)
```

### 7.3 性能分析

```python
from workshop.common.core.performance import (
    quick_benchmark,
    MemoryProfiler,
    measure_performance
)

@measure_performance('slow_function')
def slow_function(data):
    # 复杂计算...
    pass

# 分析内存使用
profiler = MemoryProfiler()
stats = profiler.profile_function(slow_function, large_data)
print(f"峰值内存: {stats['peak_memory_mb']:.2f} MB")

# 快速基准测试
result = quick_benchmark(slow_function, data, iterations=100)
print(f"平均耗时: {result.mean_time:.3f} ms")
print(f"P99 延迟: {result.p99_time:.3f} ms")
```

---

## 8. 性能优化

### 8.1 常见优化技巧

#### 1. 使用 NumPy 向量化操作

```python
# ❌ 慢: Python 循环
result = []
for pixel in image.flatten():
    result.append(pixel * 2 + 10)

# ✅ 快: NumPy 向量化
result = image * 2 + 10
```

#### 2. 批量处理

```python
# ❌ 慢: 逐个处理
for item in items:
    process(item)

# ✅ 快: 批量处理
batch_size = 32
for i in range(0, len(items), batch_size):
    batch = items[i:i+batch_size]
    process_batch(batch)
```

#### 3. 多进程并行

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

def process_item(item):
    return heavy_computation(item)

items = range(1000)

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_item, item) for item in items]

    for future in as_completed(futures):
        result = future.result()
        # 处理结果
```

#### 4. 内存映射大文件

```python
import numpy as np

# 对于大型数组，使用内存映射
large_array = np.memmap('data.dat', dtype=np.float32, mode='w+', shape=(1000000, 1024))
# 操作会自动写入磁盘
large_array[0, :] = some_data
```

### 8.2 性能监控

```python
from workshop.common.core.metrics import get_metrics

metrics = get_metrics()

with metrics.pipeline_timer('my_optimized_function') as timer:
    result = optimized_process(data)
    
    # 添加自定义元数据
    timer.set_metadata({
        'input_size': len(data),
        'output_size': len(result),
        'optimization_applied': True
    })
```

---

## 9. 常见问题

### Q1: 导入错误 ModuleNotFoundError

**问题**: `ModuleNotFoundError: No module named 'workshop'`

**解决方案**:
```bash
# 确保在项目根目录
cd /path/to/workshop

# 以开发模式安装
pip install -e .

# 或者将项目根目录添加到 PYTHONPATH
export PYTHONPATH=/path/to/workshop:$PYTHONPATH
```

### Q2: 配置文件找不到

**问题**: `ConfigurationError: CONFIG_NOT_FOUND`

**解决方案**:
```python
# 明确指定配置目录
config = ConfigManager(
    config_dir='/absolute/path/to/config',
    module_name='my_module'
)

# 或检查配置文件是否存在
import os
assert os.path.exists('/path/to/config/global.yaml')
```

### Q3: 测试失败 - 缺少依赖

**问题**: 测试因缺少可选依赖而失败

**解决方案**:
```bash
# 安装完整开发依赖
pip install -e ".[dev]"

# 或跳过需要特定依赖的测试
pytest -m "not hardware"
```

### Q4: Docker 构建失败

**问题**: `docker build` 报错

**解决方案**:
```bash
# 检查 Dockerfile 语法
docker build --no-cache -t workshop:test .

# 查看详细构建日志
DOCKER_BUILDKIT=0 docker build -t workshop:test .

# 进入容器调试
docker run -it workshop:test bash
```

### Q5: 性能问题

**现象**: Pipeline 执行缓慢

**诊断步骤**:
```python
# 1. 启用性能分析
import cProfile
cProfile.run('pipeline.run(data)', 'profile.stats')

# 2. 查看分析结果
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)

# 3. 使用 Workshop 内置工具
from workshop.common.core.performance import BenchmarkSuite
suite = BenchmarkSuite()
suite.add_test('slow_pipeline', pipeline.run, data, iterations=10)
results = suite.run()
print(suite.export_report())
```

---

## 相关资源

- [API 参考文档](API_REFERENCE.md) - 完整 API 文档
- [架构决策记录](docs/ARCHITECTURE_DECISION_RECORDS.md) - ADR
- [README.md](../README.md) - 项目总览
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码

---

## 获取帮助

- **文档**: 查看 [API Reference](API_REFERENCE.md)
- **Issues**: [AtomGit Issues](https://atomgit.com/spharx/workshop/issues)
- **讨论**: 提交 Issue 或 Pull Request
- **邮件**: lidecheng@spharx.cn / wangliren@spharx.cn

---

**最后更新**: 2026-04-07  
**维护者**: SPHARX DevTeam
