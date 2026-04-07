# Workshop V2.0 API 参考文档

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 核心模块](#2-核心模块)
  - [2.1 BasePipeline](#21-basepipeline)
  - [2.2 ConfigManager](#22-configmanager)
  - [2.3 异常体系](#23-异常体系)
  - [2.4 InputValidator](#24-inputvalidator)
  - [2.5 IO 抽象层](#25-io-抽象层)
  - [2.6 监控指标](#26-监控指标)
  - [2.7 性能工具](#27-性能工具)
  - [2.8 安全审计](#28-安全审计)
- [3. Pipeline 模块](#3-pipeline-模块)
- [4. 硬件抽象层](#4-硬件抽象层)
- [5. 运维工具](#5-运维工具)

---

## 1. 快速开始

### 安装

```bash
# 基础安装
pip install -e .

# 完整安装（含开发工具）
pip install -e ".[dev]"

# 包含硬件支持
pip install -e ".[hardware,ml]"
```

### 基本使用

```python
from workshop import BasePipeline, PipelineResult, ConfigManager
from workshop.common.core.logging_setup import get_logger

logger = get_logger(__name__)

class MyPipeline(BasePipeline):
    """自定义数据处理管道"""

    def _initialize(self):
        """初始化配置和资源"""
        self.config = ConfigManager(module_name='my_pipeline')
        self.logger = get_logger('MyPipeline')
        self.logger.info("Pipeline 初始化完成")

    def _execute(self, input_data: dict) -> PipelineResult:
        """执行业务逻辑"""
        try:
            # 处理数据
            result_data = self._process(input_data)

            return PipelineResult(
                success=True,
                output=result_data,
                processed_count=len(input_data.get('items', [])),
                metrics={'processing_time': 0.123}
            )
        except Exception as e:
            self.logger.error(f"处理失败: {e}")
            return PipelineResult(
                success=False,
                error=str(e),
                metrics={'error': True}
            )

    def _cleanup(self):
        """清理资源"""
        self.logger.info("资源清理完成")

# 使用 Pipeline
if __name__ == '__main__':
    with MyPipeline() as pipeline:
        result = pipeline.run({
            'path': '/data/input.bag',
            'items': ['frame_001.png', 'frame_002.png']
        })

        if result.success:
            print(f"✅ 处理成功: {result.processed_count} 个文件")
            print(f"输出数据: {result.output}")
        else:
            print(f"❌ 处理失败: {result.error}")
```

---

## 2. 核心模块

### 2.1 BasePipeline

Pipeline 抽象基类，定义标准生命周期和接口契约。

#### 类定义

```python
class BasePipeline(ABC):
    """
    Pipeline 抽象基类 - 参考 AgentOS Agent 和 BaseManager 模式
    
    Lifecycle:
        CREATED → INITIALIZING → READY → RUNNING → (COMPLETED | FAILED | CANCELED) → SHUTDOWN
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化 Pipeline
        
        Args:
            config_dir: 配置目录路径 (可选)
        """

    @abstractmethod
    def _initialize(self) -> None:
        """初始化配置和资源 - 必须实现"""
        
    @abstractmethod
    def _execute(self, input_data: Any, **kwargs) -> PipelineResult:
        """执行核心逻辑 - 必须实现"""
        
    @abstractmethod
    def _cleanup(self) -> None:
        """清理资源 - 必须实现"""

    def run(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行 Pipeline (完整生命周期管理)
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            PipelineResult: 执行结果
        """

    def pause(self) -> None:
        """暂停执行"""
        
    def resume(self) -> None:
        """恢复执行"""
        
    def cancel(self) -> None:
        """取消执行"""
```

#### PipelineStatus 状态枚举

```python
class PipelineStatus(Enum):
    CREATED = auto()       # 已创建
    INITIALIZING = auto()  # 初始化中
    READY = auto()         # 就绪
    RUNNING = auto()       # 运行中
    PAUSED = auto()        # 已暂停
    COMPLETED = auto()     # 已完成
    FAILED = auto()        # 失败
    CANCELED = auto()      # 已取消
    SHUTDOWN = auto()      # 已关闭
```

#### PipelineResult 结果类

```python
@dataclass
class PipelineResult:
    success: bool                    # 是否成功
    output: Optional[Any] = None     # 输出数据
    error: Optional[str] = None      # 错误信息
    error_code: Optional[ErrorCode] = None  # 错误码
    metrics: Dict[str, Any] = field(default_factory=dict)  # 性能指标
    warnings: List[str] = field(default_factory=list)       # 警告列表
    execution_time: float = 0.0      # 执行时间（秒）
    processed_count: int = 0         # 处理数量

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
```

#### 使用示例

```python
from workshop import BasePipeline, PipelineResult, PipelineStatus

class DataIngestionPipeline(BasePipeline):
    """数据导入管道示例"""

    def _initialize(self):
        self.config = ConfigManager(
            module_name='ingest',
            config_dir='/app/config'
        )
        self.validator = InputValidator()
        self.logger.info("初始化完成")

    def _execute(self, input_data: dict) -> PipelineResult:
        # 验证输入
        if not self.validator.validate_path(input_data.get('path', '')):
            return PipelineResult(
                success=False,
                error="无效的路径",
                error_code=ErrorCode.VALIDATION_ERROR
            )

        # 处理逻辑
        items = self._parse_bag_file(input_data['path'])

        return PipelineResult(
            success=True,
            output={'items': items},
            processed_count=len(items),
            metrics={
                'file_size': os.path.getsize(input_data['path']),
                'format': 'rosbag'
            }
        )

    def _cleanup(self):
        self.logger.info("清理临时文件")

# 使用
with DataIngestionPipeline() as pipeline:
    print(pipeline.status)  # PipelineStatus.CREATED

    result = pipeline.run({'path': 'data/sample.bag'})
    
    print(result.success)          # True/False
    print(result.processed_count)   # 100
    print(result.execution_time)    # 1.234
    print(result.to_dict())         # 字典格式
```

---

### 2.2 ConfigManager

统一配置管理器，支持多层级合并。

#### 类定义

```python
class ConfigManager:
    """
    统一配置管理器
    
    特性：
    - 支持多层级配置合并（全局 > 模块 > 运行时）
    - 配置验证和类型检查
    - 配置变更监听
    - 热重载支持
    """

    DEFAULT_CONFIG_DIR = "/app/common/configs"

    def __init__(
        self,
        config_dir: Optional[str] = None,
        module_name: Optional[str] = None,
        auto_load: bool = True
    ):
        """
        Args:
            config_dir: 配置目录路径
            module_name: 模块名称
            auto_load: 是否自动加载
        """

    def load(self) -> None:
        """加载所有配置"""

    def reload(self) -> None:
        """热重载配置"""

    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键（支持点号分隔，如 'quality.blur_threshold'）
            default: 默认值
            required: 是否必需
            
        Returns:
            配置值
            
        Raises:
            ConfigurationError: 当 required=True 且键不存在时
        """

    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """
        设置运行时配置
        
        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化
        """

    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置段"""

    def has(self, key: str) -> bool:
        """检查配置是否存在"""

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""

    @property
    def is_loaded(self) -> bool:
        """是否已加载"""

    @property
    def module_name(self) -> Optional[str]:
        """模块名称"""
```

#### 使用示例

```python
from workshop import ConfigManager

# 创建配置管理器
config = ConfigManager(
    config_dir='/app/config',
    module_name='quality',
    auto_load=True
)

# 获取配置值
blur_threshold = config.get('blur_threshold', default=100)
exposure_min = config.get('exposure.min', default=50, required=True)

# 设置运行时覆盖
config.set('blur_threshold', 150)

# 获取完整段
quality_config = config.get_section('quality')

# 检查配置是否存在
if config.has('advanced.enable_gpu'):
    gpu_enabled = config.get('advanced.enable_gpu')
```

#### 配置文件结构

```yaml
# /app/config/global.yaml
global:
  log_level: INFO
  max_workers: 4
  memory_limit_gb: 8

# /app/config/modules/01_quality.yaml
quality:
  blur_threshold: 100
  exposure:
    min: 50
    max: 200
  frame_drop_threshold: 10
```

---

### 2.3 异常体系

统一的异常层次结构和错误码管理。

#### 异常类层次

```python
class WorkshopError(Exception):
    """基础异常类"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            code: 错误码
            message: 错误消息
            cause: 原始异常
            context: 上下文信息
        """

class ConfigurationError(WorkshopError):  # 配置错误
class PipelineError(WorkshopError):       # 管道错误
class ValidationError(WorkshopError):     # 验证错误
class HardwareError(WorkshopError):       # 硬件错误
class DataIOError(WorkshopError):         # 数据IO错误
```

#### ErrorCode 错误码枚举

```python
class ErrorCode(Enum):
    # 通用错误 (1000-1099)
    UNKNOWN_ERROR = (1000, "未知错误")
    INVALID_INPUT = (1001, "无效输入")
    
    # 配置错误 (1100-1199)
    CONFIG_LOAD_ERROR = (1100, "配置加载失败")
    CONFIG_VALIDATION_ERROR = (1101, "配置验证失败")
    CONFIG_NOT_FOUND = (1102, "配置不存在")
    
    # 管道错误 (1200-1299)
    PIPELINE_INIT_FAILED = (1200, "管道初始化失败")
    PIPELINE_EXECUTION_ERROR = (1201, "管道执行错误")
    PIPELINE_TIMEOUT = (1202, "管道超时")
    
    # 验证错误 (1300-1399)
    VALIDATION_ERROR = (1300, "验证失败")
    PATH_TRAVERSAL_DETECTED = (1301, "检测到路径遍历攻击")
    SQL_INJECTION_DETECTED = (1302, "检测到SQL注入")
    
    # 硬件错误 (1400-1499)
    DEVICE_NOT_FOUND = (1400, "设备未找到")
    DEVICE_CONNECTION_FAILED = (1401, "设备连接失败")
    CALIBRATION_FAILED = (1402, "校准失败")
    
    # IO错误 (1500-1599)
    FILE_NOT_FOUND = (1500, "文件未找到")
    FILE_READ_ERROR = (1501, "文件读取错误")
    FILE_WRITE_ERROR = (1502, "文件写入错误")
    UPLOAD_FAILED = (1503, "上传失败")
```

#### ErrorSeverity 严重级别

```python
class ErrorSeverity(Enum):
    CRITICAL = "CRITICAL"    # 严重：系统无法继续运行
    ERROR = "ERROR"          # 错误：当前操作失败
    WARNING = "WARNING"      # 警告：可继续但需关注
    INFO = "INFO"            # 信息：正常提示
```

#### 使用示例

```python
from workshop import (
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ErrorCode,
    ErrorSeverity,
    error_code_manager
)

try:
    config_value = config.get('important_key', required=True)
except ConfigurationError as e:
    logger.error(f"配置错误 [{e.code.name}]: {e.message}")
    logger.error(f"上下文: {e.context}")
    
    # 记录到错误管理系统
    error_code_manager.record_error(e)

# 抛出自定义异常
raise PipelineError(
    code=ErrorCode.PIPELINE_EXECUTION_ERROR,
    message="处理帧时发生错误",
    context={'frame_id': frame_id, 'timestamp': time.time()}
)

# 查询错误统计
stats = error_code_manager.get_stats()
print(f"总错误数: {stats['total']}")
print(f"按类型分布: {stats['by_code']}")
```

---

### 2.4 InputValidator

输入验证和安全检查工具。

#### 类定义

```python
class InputValidator:
    """
    输入验证器 - 防止常见安全漏洞
    
    支持的验证模式：
    - path: 路径安全检查（防止路径遍历）
    - filename: 文件名验证
    - email: 邮箱格式
    - url: URL 格式
    - integer: 整数范围
    - string: 字符串长度/内容
    - json: JSON 格式
    - yaml: YAML 格式
    - custom: 自定义正则表达式
    """

    def validate(
        self,
        value: Any,
        mode: Union[str, Pattern],
        **constraints
    ) -> bool:
        """
        验证输入值
        
        Args:
            value: 待验证的值
            mode: 验证模式或 Pattern 枚举
            **constraints: 约束条件
            
        Returns:
            bool: 是否通过验证
        """

    def validate_path(self, path: str, allow_absolute: bool = False) -> bool:
        """验证路径安全性"""

    def validate_filename(self, filename: str) -> bool:
        """验证文件名安全性"""

    def sanitize(self, value: str, mode: str = 'string') -> str:
        """净化输入值"""

    def validate_and_raise(
        self,
        value: Any,
        mode: str,
        error_message: str = "验证失败"
    ) -> Any:
        """验证并在失败时抛出异常"""
```

#### Pattern 验证模式枚举

```python
class Pattern(Enum):
    PATH = "path"
    FILENAME = "filename"
    EMAIL = "email"
    URL = "url"
    INTEGER = "integer"
    STRING = "string"
    JSON = "json"
    YAML = "yaml"
    CUSTOM = "custom"
```

#### 使用示例

```python
from workshop import InputValidator, Pattern

validator = InputValidator()

# 路径验证（防止路径遍历攻击）
user_input = "../../etc/passwd"
if validator.validate_path(user_input):
    safe_path = validator.sanitize(user_input, 'path')
else:
    raise ValidationError(ErrorCode.PATH_TRAVERSAL_DETECTED, "不安全的路径")

# 文件名验证
filename = "test_image.png"
if validator.validate_filename(filename):
    print("✅ 安全的文件名")

# 多种验证模式
validator.validate("test@example.com", Pattern.EMAIL)
validator.validate("https://example.com", Pattern.URL)
validator.validate(42, Pattern.INTEGER, min_value=0, max_value=100)
validator.validate("short", Pattern.STRING, min_length=3, max_length=50)

# 验证并自动抛出异常
safe_filename = validator.validate_and_raise(
    user_filename,
    Pattern.FILENAME,
    error_message="文件名包含非法字符"
)
```

---

### 2.5 IO 抽象层

统一的 I/O 接口，支持多种存储后端。

#### 核心接口

```python
class IStorageBackend(ABC):
    """存储后端抽象接口"""

    @abstractmethod
    def read(self, path: str) -> bytes:
        """读取文件内容"""

    @abstractmethod
    def write(self, path: str, data: bytes) -> bool:
        """写入文件"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查文件是否存在"""

    @abstractmethod
    def delete(self, path: str) -> bool:
        """删除文件"""

    @abstractmethod
    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """列出目录下的文件"""

    @abstractmethod
    def get_metadata(self, path: str) -> FileMetadata:
        """获取文件元数据"""


class LocalStorageBackend(IStorageBackend):
    """本地文件系统存储后端"""


@dataclass
class FileMetadata:
    """文件元数据"""
    path: str
    size: int
    created_time: float
    modified_time: float
    mime_type: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class IOResult:
    """I/O 操作结果"""
    success: bool
    path: str
    operation: str  # read/write/delete/list
    data: Optional[Any] = None
    metadata: Optional[FileMetadata] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class IOManager:
    """I/O 管理器 - 统一管理多个存储后端"""

    def register_backend(self, name: str, backend: IStorageBackend) -> None:
        """注册存储后端"""

    def get_backend(self, name: str = 'local') -> IStorageBackend:
        """获取存储后端"""

    def read(self, path: str, backend: str = 'local') -> IOResult:
        """读取文件"""

    def write(self, path: str, data: bytes, backend: str = 'local') -> IOResult:
        """写入文件"""

    def copy(self, src: str, dst: str, src_backend: str = 'local', dst_backend: str = 'local') -> IOResult:
        """跨后端复制文件"""
```

#### CompressionFormat 压缩格式

```python
class CompressionFormat(Enum):
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    BZ2 = "bz2"
```

#### 使用示例

```python
from workshop import (
    IOManager,
    LocalStorageBackend,
    FileMetadata,
    get_io_manager,
    init_io_manager
)

# 初始化 IO 管理器
io_mgr = init_io_manager()

# 注册本地存储后端
io_mgr.register_backend('local', LocalStorageBackend(base_path='/data'))

# 读取文件
result = io_mgr.read('/data/images/frame.png')
if result.success:
    image_data = result.data
    meta = result.metadata
    print(f"文件大小: {meta.size} bytes")

# 写入文件
write_result = io_mgr.write('/output/result.json', json.dumps(data).encode())

# 列出目录
files = io_mgr.get_backend('local').list_files('/data/images/', '*.png')

# 使用便捷函数
io = get_io_manager()
result = io.read('/data/input.bag')
```

---

### 2.6 监控指标

Prometheus 监控指标收集和管理。

#### WorkshopMetrics 类

```python
class WorkshopMetrics:
    """
    Prometheus 监控指标管理器
    
    提供的指标：
    - Counter: pipeline_executions_total (Pipeline 执行计数)
    - Histogram: pipeline_duration_seconds (执行耗时分布)
    - Gauge: active_pipelines (活跃 Pipeline 数)
    - Counter: errors_total (错误计数)
    - Summary: data_processed_bytes (数据处理量)
    """

    def __init__(self, namespace: str = 'workshop'):
        """
        Args:
            namespace: Prometheus 指标命名空间
        """

    def init_metrics_server(self, port: int = 9090, host: str = '0.0.0.0') -> None:
        """启动 HTTP 指标服务"""

    def pipeline_timer(self, pipeline_name: str) -> ContextManager:
        """
        Pipeline 计时上下文管理器
        
        Usage:
            with metrics.pipeline_timer('quality_check') as timer:
                result = pipeline.run(data)
                timer.set_metadata({'score': 0.95})
        """

    def record_execution(self, pipeline_name: str, success: bool) -> None:
        """记录 Pipeline 执行事件"""

    def record_error(self, error_type: str, severity: str = 'ERROR') -> None:
        """记录错误"""

    def set_active_pipelines(self, count: int) -> None:
        """设置活跃 Pipeline 数量"""

    def increment_processed_bytes(self, bytes_count: int) -> None:
        """增加已处理字节数"""

    def generate_latest(self) -> str:
        """生成最新的 Prometheus 格式指标数据"""
```

#### 便捷函数

```python
def get_metrics() -> WorkshopMetrics:
    """获取全局 Metrics 实例（单例模式）"""

def measure_performance(func_name: Optional[str] = None):
    """
    性能测量装饰器
    
    Usage:
        @measure_performance('my_function')
        def my_func():
            ...
    """

def init_metrics_server(port: int = 9090) -> None:
    """初始化并启动指标服务器"""
```

#### 使用示例

```python
from workshop.common.core.metrics import (
    WorkshopMetrics,
    get_metrics,
    measure_performance,
    init_metrics_server
)

# 初始化
metrics = get_metrics()
metrics.init_metrics_server(port=9090)

# 方式 1: 上下文管理器计时
with metrics.pipeline_timer('quality_check') as timer:
    result = quality_pipeline.run(frame_data)
    timer.set_metadata({
        'blur_score': 0.95,
        'exposure': 120,
        'frames_processed': 1
    })

# 方式 2: 手动记录
metrics.record_execution('ingest', success=True)
metrics.set_active_pipelines(3)
metrics.increment_processed_bytes(1024 * 1024)

# 方式 3: 装饰器
@measure_performance('process_batch')
def process_batch(batch: list) -> list:
    return [process_item(item) for item in batch]

# 访问指标
print(metrics.generate_latest())
```

---

### 2.7 性能工具

性能基准测试和分析工具。

#### BenchmarkSuite 基准测试套件

```python
class BenchmarkSuite:
    """性能基准测试套件"""

    def __init__(self, name: str = 'benchmark'):
        """
        Args:
            name: 测试套件名称
        """

    def add_test(
        self,
        name: str,
        func: Callable,
        *args,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs
    ) -> None:
        """添加测试用例"""

    def run(self) -> BenchmarkResult:
        """运行所有测试并返回结果"""

    def compare_with_baseline(self, baseline_path: str) -> Dict[str, float]:
        """与基线结果对比"""

    def export_report(self, format: str = 'markdown', output_path: Optional[str] = None) -> str:
        """导出报告"""


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    mean_time: float           # 平均时间 (ms)
    std_dev: float             # 标准差
    min_time: float            # 最小时间
    max_time: float            # 最大时间
    p50_time: float            # P50 百分位
    p95_time: float            # P95 百分位
    p99_time: float            # P99 百分位
    iterations: int            # 迭代次数
    total_time: float          # 总耗时
    throughput: float          # 吞吐量 (ops/sec)


class MemoryProfiler:
    """内存分析工具"""

    def profile_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """分析函数内存使用"""

    def track_allocation(self) -> ContextManager:
        """内存分配追踪上下文管理器"""

    def get_memory_usage() -> float:
        """获取当前进程内存使用量 (MB)"""
```

#### 便捷函数

```python
def quick_benchmark(func: Callable, *args, iterations: int = 1000, **kwargs) -> BenchmarkResult:
    """快速基准测试单个函数"""

def compare_functions(func_a: Callable, func_b: Callable, *args, iterations: int = 1000, **kwargs) -> Dict[str, Any]:
    """对比两个函数性能"""
```

#### 使用示例

```python
from workshop.common.core.performance import (
    BenchmarkSuite,
    MemoryProfiler,
    quick_benchmark,
    compare_functions
)

# 创建基准测试套件
suite = BenchmarkSuite(name='V2 Performance Test')

# 添加测试用例
suite.add_test('ConfigManager Init', ConfigManager, iterations=100)
suite.add_test('Input Validation', validator.validate, 'test.txt', Pattern.FILENAME)
suite.add_test('Image Processing', process_image, sample_image, iterations=50)

# 运行测试
results = suite.run()

# 导出报告
report = suite.export_report(format='markdown')
print(report)

# 保存为文件
suite.export_report(format='markdown', output_path='benchmark_report.md')

# 快速单函数测试
result = quick_benchmark(process_frame, frame_data, iterations=500)
print(f"平均耗时: {result.mean_time:.3f}ms")
print(f"P99 延迟: {result.p99_time:.3f}ms")
print(f"吞吐量: {result.throughput:.2f} ops/sec")

# 对比两个函数
comparison = compare_functions(old_process, new_process, data, iterations=200)
print(f"性能提升: {comparison['improvement_percent']:.1f}%")

# 内存分析
profiler = MemoryProfiler()
mem_stats = profiler.profile_function(load_large_dataset, dataset_path)
print(f"峰值内存: {mem_stats['peak_memory_mb']:.2f} MB")
print(f"分配次数: {mem_stats['allocation_count']}")

# 当前内存使用
current_mem = MemoryProfiler.get_memory_usage()
print(f"当前内存: {current_mem:.2f} MB")
```

---

### 2.8 安全审计

代码安全和依赖审计工具。

#### CodeSecurityScanner 代码扫描器

```python
class CodeSecurityScanner:
    """
    SAST (静态应用安全测试) 扫描器
    
    检测规则类别：
    - injection: 注入攻击 (SQL注入、命令注入、路径遍历等)
    - crypto: 弱加密算法
    - hardcode: 硬编码敏感信息
    - unsafe: 不安全的函数调用
    - info_leak: 信息泄露风险
    """

    def __init__(self, rules_config: Optional[Dict] = None):
        """初始化扫描器"""

    def scan_file(self, file_path: str) -> SecurityAuditReport:
        """扫描单个文件"""

    def scan_directory(self, dir_path: str, pattern: str = '*.py') -> SecurityAuditReport:
        """扫描目录"""

    def scan_code_string(self, code: str, filename: str = '<string>') -> SecurityAuditReport:
        """扫描代码字符串"""

    def add_custom_rule(self, rule: Dict) -> None:
        """添加自定义规则"""


class DependencyAuditor:
    """依赖安全审计器"""

    def audit_requirements(self, file_path: str) -> SecurityAuditReport:
        """审计 requirements.txt"""

    def check_vulnerabilities(self, package_name: str, version: str) -> List[SecurityFinding]:
        """检查已知漏洞"""

    def generate_dependency_report(self) -> str:
        """生成依赖报告"""


class ConfigurationAuditor:
    """配置安全审计器"""

    def audit_config_file(self, file_path: str) -> SecurityAuditReport:
        """审计配置文件"""

    def check_sensitive_values(self, config: Dict) -> List[SecurityFinding]:
        """检查敏感配置值"""


@dataclass
class SecurityFinding:
    """安全发现"""
    rule_id: str
    severity: SecuritySeverity
    category: str
    title: str
    description: str
    file_path: str
    line_number: int
    recommendation: str
    cwe_id: Optional[str] = None


@dataclass
class SecurityAuditReport:
    """安全审计报告"""
    timestamp: str
    scanner_version: str
    findings: List[SecurityFinding]
    summary: Dict[str, int]  # {critical: n, warning: n, ...}
    score: int               # 安全评分 (0-100)

    def to_json(self) -> str:
        """转换为 JSON"""

    def to_markdown(self) -> str:
        """转换为 Markdown 报告"""


class SecuritySeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


def run_full_security_audit(project_root: str) -> SecurityAuditReport:
    """运行完整的安全审计（代码+依赖+配置）"""
```

#### 使用示例

```python
from workshop.common.core.security_audit import (
    CodeSecurityScanner,
    DependencyAuditor,
    ConfigurationAuditor,
    run_full_security_audit,
    SecuritySeverity
)

# 代码扫描
scanner = CodeSecurityScanner()
report = scanner.scan_directory('/app/workshop/common/core/')

print(f"安全评分: {report.score}/100")
print(f"发现: {report.summary}")

for finding in report.findings[:10]:  # 显示前10个问题
    print(f"[{finding.severity.value}] {finding.title}")
    print(f"  文件: {finding.file_path}:{finding.line_number}")
    print(f"  建议: {finding.recommendation}")

# 导出报告
with open('security_report.md', 'w') as f:
    f.write(report.to_markdown())

# 依赖审计
dep_auditor = DependencyAuditor()
dep_report = dep_auditor.audit_requirements('requirements.txt')

# 配置审计
config_auditor = ConfigurationAuditor()
config_report = config_auditor.audit_config_file('.env')

# 一键完整审计
full_report = run_full_security_audit('/app/workshop/')
print(full_report.to_json())
```

---

## 3. Pipeline 模块

Workshop 提供 6 个标准数据处理管道：

| 模块 | 类名 | 功能 |
|------|------|------|
| `run_00_ingest` | `IngestPipeline` | 数据导入（ROS Bag解析、图像压缩、隐私脱敏） |
| `run_01_quality` | `QualityPipeline` | 质量检测（模糊检测、曝光分析、帧丢弃） |
| `run_02_enhance` | `EnhancePipeline` | 数据增强（YOLO目标检测、HDVS分割） |
| `run_03_calibrate` | `CalibratePipeline` | 相机校准（棋盘格标定、重投影误差评估） |
| `run_04_pack` | `PackPipeline` | 数据打包（多格式打包：ROS/COCO/YOLO/VOC/KITTI） |
| `run_05_delivery` | `DeliveryPipeline` | 数据交付（OSS上传、通知发送、完整性校验） |

### 使用示例

```python
from workshop.pipelines.run_00_ingest.runner_v2 import IngestPipeline
from workshop.pipelines.run_01_quality.runner_v2 import QualityPipeline
from workshop.pipelines.run_04_pack.runner_v2 import PackPipeline

# 完整的数据处理流程
input_data = {'path': '/data/raw/capture.bag'}

# Step 1: 数据导入
with IngestPipeline() as ingest:
    ingest_result = ingest.run(input_data)
    if not ingest_result.success:
        raise Exception(f"导入失败: {ingest_result.error}")

# Step 2: 质量检测
with QualityPipeline() as quality:
    quality_result = quality.run(ingest_result.output)
    # 可以根据质量分数决定是否继续

# Step 3-N: 其他管道...

# 最后: 数据打包
with PackPipeline() as pack:
    pack_result = pack.run(final_output, format='COCO')
    print(f"数据集已打包至: {pack_result.output['dataset_path']}")
```

---

## 4. 硬件抽象层

统一硬件设备管理接口。

### DeviceManager 设备管理器

```python
from workshop.hardware import (
    IHardwareDevice,
    DeviceManager,
    DeviceInfo,
    DeviceStatus,
    RealSenseDeviceV2
)

# 创建设备管理器
device_mgr = DeviceManager()

# 注册 RealSense 相机
camera = RealSenseDeviceV2(device_id='camera_001')
device_mgr.register('camera_001', camera)

# 初始化所有设备
device_mgr.initialize_all()

# 健康检查
status = device_mgr.health_check_all()
for device_id, device_status in status.items():
    print(f"{device_id}: {device_status.value}")

# 获取设备信息
info = device_mgr.get_device_info('camera_001')
print(f"序列号: {info.serial_number}")
print(f"固件版本: {info.firmware_version}")
```

### IHardwareDevice 接口

```python
class IHardwareDevice(ABC):
    """硬件设备抽象接口"""

    @property
    @abstractmethod
    def device_id(self) -> str:
        """设备唯一标识符"""

    @property
    @abstractmethod
    def device_type(self) -> str:
        """设备类型"""

    @abstractmethod
    def initialize(self) -> bool:
        """初始化设备"""

    @abstractmethod
    def shutdown(self) -> None:
        """关闭设备"""

    @abstractmethod
    def health_check(self) -> DeviceStatus:
        """健康检查"""

    @abstractmethod
    def get_info(self) -> DeviceInfo:
        """获取设备信息"""

    @abstractmethod
    def reset(self) -> bool:
        """复位设备"""
```

---

## 5. 运维工具

### ops_toolkit.py 运维自动化

```bash
# 日常维护（推荐每日运行）
python workshop/scripts/ops_toolkit.py --daily-maintenance

# 日志清理
python workshop/scripts/ops_toolkit.py --cleanup-logs --days 7 --execute

# 创建备份
python workshop/scripts/ops_toolkit.py --backup --type full

# 系统健康检查
python workshop/scripts/ops_toolkit.py --health-check

# 磁盘空间检查
python workshop/scripts/ops_toolkit.py --disk-usage --threshold 80
```

### load_tester.py 负载测试

```bash
# 负载测试
python workshop/scripts/load_tester.py --test-type load -c 10 -r 50

# 压力测试（找到瓶颈）
python workshop/scripts/load_tester.py --test-type stress --max-concurrent 100

# 内存泄漏检测
python workshop/scripts/load_tester.py --test-type memory-leak -i 1000

# 完整测试套件
python workshop/scripts/load_tester.py --full-suite

# 输出 JSON 报告
python workshop/scripts/load_tester.py --test-type load -c 20 --report-json report.json
```

### code_quality_checker.py 代码质量检查

```bash
# 检查指定目录
python workshop/scripts/code_quality_checker.py workshop/common/core/

# 完整项目检查
python workshop/scripts/code_quality_checker.py ./

# 输出详细报告
python workshop/scripts/code_quality_checker.py ./ --verbose --report-html report.html
```

---

## 版本信息

- **版本**: 2.0.0
- **Python**: >=3.8
- **许可证**: GPL-3.0
- **作者**: SPHARX DevTeam
- **文档更新**: 2026-04-07

---

## 相关文档

- [README.md](../README.md) - 项目总览
- [开发者指南](DEVELOPER_GUIDE.md) - 开发流程和规范
- [贡献指南](CONTRIBUTING.md) - 如何参与贡献
- [架构决策记录](docs/ARCHITECTURE_DECISION_RECORDS.md) - ADR 文档
- [迁移指南](docs/MIGRATION_REPORT.md) - V1 到 V2 迁移说明
