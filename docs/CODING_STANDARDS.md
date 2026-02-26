# 编码规范

## 📝 Python 编码规范

### 基本原则
遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范，确保代码的一致性和可读性。

### 命名约定

#### 变量和函数
```python
# 使用 snake_case
user_name = "john"
calculate_total_price()

# 常量使用 UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 类名使用 PascalCase
class DataProcessor:
    pass

# 私有成员使用单下划线前缀
class MyClass:
    def _private_method(self):
        pass
```

#### 模块和包
```python
# 模块名使用 lowercase
import data_processor
import config_loader

# 包名使用 lowercase
from common.scripts import config_loader
```

### 代码格式化

#### 导入顺序
```python
# 标准库导入
import os
import sys
from pathlib import Path

# 第三方库导入
import numpy as np
import yaml

# 本地应用导入
from .config_loader import load_config
from ..common.schemas import Scene
```

#### 函数定义
```python
def process_scene_data(
    scene_path: str,
    output_dir: str,
    *,
    quality_threshold: float = 0.8,
    save_intermediate: bool = False
) -> bool:
    """
    处理场景数据并生成标准化输出
    
    Args:
        scene_path: 场景数据路径
        output_dir: 输出目录路径
        quality_threshold: 质量阈值
        save_intermediate: 是否保存中间结果
        
    Returns:
        处理是否成功的布尔值
        
    Raises:
        FileNotFoundError: 当场景路径不存在时
        ValueError: 当参数不合法时
    """
    # 函数实现...
    pass
```

### 类设计规范

#### 基类结构
```python
class BasePipelineModule:
    """流水线模块基类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, input_data: Any) -> Any:
        """处理数据的主要接口"""
        raise NotImplementedError
    
    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        raise NotImplementedError
    
    def generate_report(self) -> dict:
        """生成处理报告"""
        raise NotImplementedError
```

#### 具体实现类
```python
class QualityDetector(BasePipelineModule):
    """质量检测模块"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._load_detection_models()
    
    def process(self, scene_data: SceneData) -> QualityReport:
        """执行质量检测"""
        if not self.validate_input(scene_data):
            raise ValueError("Invalid input data")
        
        # 检测逻辑...
        report = self._analyze_quality(scene_data)
        return report
    
    def _analyze_quality(self, data: SceneData) -> QualityReport:
        """内部质量分析方法"""
        # 具体实现...
        pass
```

## 📊 配置文件规范

### YAML 配置文件
```yaml
# 配置文件头部注释
# workshop 模块配置文件
# 版本: 1.0
# 最后更新: 2026-02-22

# 使用有意义的键名
processing:
  # 添加详细的注释说明
  batch_size: 32           # 批处理大小
  max_workers: 4           # 最大工作进程数
  timeout_seconds: 300     # 超时时间(秒)

# 嵌套结构保持清晰的层次
quality_thresholds:
  image:
    blur_minimum: 100.0    # 模糊度最小阈值
    brightness_range:       # 亮度范围
      min: 30
      max: 220
  depth:
    confidence_min: 0.8    # 最小置信度
```

### JSON 配置文件
```json
{
  "version": "1.0",
  "metadata": {
    "created_at": "2026-02-22T10:30:00Z",
    "author": "Spharx Team"
  },
  "settings": {
    "processing": {
      "parallel_enabled": true,
      "worker_count": 4,
      "buffer_size": 1024
    }
  }
}
```

## 🧪 测试规范

### 单元测试结构
```python
import unittest
from unittest.mock import patch, MagicMock
from workshop.modules.quality.detector import QualityDetector

class TestQualityDetector(unittest.TestCase):
    """质量检测器测试类"""
    
    def setUp(self):
        """测试前置条件"""
        self.config = {"threshold": 0.8}
        self.detector = QualityDetector(self.config)
    
    def test_valid_input_processing(self):
        """测试有效输入处理"""
        # 准备测试数据
        test_data = self._create_test_scene_data()
        
        # 执行测试
        result = self.detector.process(test_data)
        
        # 验证结果
        self.assertIsInstance(result, QualityReport)
        self.assertTrue(result.is_valid)
    
    def test_invalid_input_raises_error(self):
        """测试无效输入抛出异常"""
        with self.assertRaises(ValueError):
            self.detector.process(None)
    
    @patch('workshop.modules.quality.detector.cv2.Laplacian')
    def test_blur_detection(self, mock_laplacian):
        """测试模糊检测功能"""
        # 模拟模糊检测
        mock_laplacian.return_value.var.return_value = 50.0
        
        # 测试逻辑...
        pass
    
    def _create_test_scene_data(self):
        """创建测试用场景数据"""
        return SceneData(
            images=[],
            timestamps=[],
            metadata={}
        )

if __name__ == '__main__':
    unittest.main()
```

### 测试覆盖率要求
- **核心功能**: 100% 覆盖率
- **业务逻辑**: 90% 以上覆盖率
- **边缘情况**: 80% 以上覆盖率
- **错误处理**: 100% 覆盖率

## 📚 文档规范

### 代码注释
```python
def calculate_statistics(data: list) -> dict:
    """
    计算数据统计信息
    
    该函数计算输入数据的基本统计特征，包括均值、
    标准差、最小值和最大值。
    
    Args:
        data: 数值型数据列表
        
    Returns:
        包含统计信息的字典，格式如下:
        {
            'mean': float,      # 均值
            'std': float,       # 标准差
            'min': float,       # 最小值
            'max': float        # 最大值
        }
        
    Raises:
        ValueError: 当输入数据为空时
        TypeError: 当输入包含非数值元素时
        
    Example:
        >>> calculate_statistics([1, 2, 3, 4, 5])
        {'mean': 3.0, 'std': 1.58, 'min': 1, 'max': 5}
    """
    if not data:
        raise ValueError("Input data cannot be empty")
    
    # 验证数据类型
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("All elements must be numeric")
    
    # 计算统计值
    mean = sum(data) / len(data)
    std = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    
    return {
        'mean': mean,
        'std': std,
        'min': min(data),
        'max': max(data)
    }
```

### 模块文档字符串
```python
"""
workshop.modules.quality.detector
==================================

质量检测模块，负责对采集的数据进行多层次质量评估。

主要功能:
- 图像质量检测（模糊度、亮度、对比度）
- 同步质量评估（时间同步、帧同步）
- 深度数据质量分析
- 综合质量评分生成

使用示例:
    >>> from workshop.modules.quality.detector import QualityDetector
    >>> detector = QualityDetector(config)
    >>> report = detector.process(scene_data)
    >>> print(report.overall_score)

作者: Spharx Team
版本: 1.0.0
"""
```

## 🚀 性能优化规范

### 代码优化原则
```python
# ✅ 推荐做法
# 使用列表推导式
squares = [x**2 for x in range(1000)]

# 使用生成器表达式处理大数据
def process_large_dataset(data):
    return sum(x**2 for x in data if x > 0)

# ✗ 不推荐做法
# 避免不必要的循环
squares = []
for x in range(1000):
    squares.append(x**2)
```

### 内存管理
```python
# 及时释放不需要的对象
def process_batch(batch_data):
    result = heavy_computation(batch_data)
    del batch_data  # 显式删除大对象
    return result

# 使用上下文管理器
with open('large_file.dat', 'rb') as f:
    data = f.read()
    # 处理数据...
# 文件自动关闭
```

## 🔧 工具链配置

### 代码格式化工具
```bash
# black 配置
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

# flake8 配置
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist
```

### 预提交钩子
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        args: [--package=workshop]
```

---

**版本**: 1.0  
**最后更新**: 2026年2月22日  
**适用范围**: Workshop 项目所有 Python 代码