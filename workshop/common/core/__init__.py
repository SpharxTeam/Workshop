# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Workshop 核心模块
================

提供数据处理管道的基础设施和核心功能。

子模块:
    - base_pipeline: Pipeline 抽象基类，定义标准接口
    - config_manager: 配置管理器，支持三级合并策略
    - exceptions: 统一异常体系和 100+ 错误码
    - logging_setup: 日志系统配置
    - input_validator: 输入验证和安全检查
    - io_abstraction: IO 抽象层，支持多存储后端
    - metrics: Prometheus 监控指标
    - performance: 性能基准测试工具
    - security_audit: 安全审计 (SAST)

使用示例:
    from workshop.core import BasePipeline, ConfigManager
    
    class MyPipeline(BasePipeline):
        def _initialize(self):
            self.config = ConfigManager(module_name='my_pipeline')
        
        def _execute(self, input_data):
            # 处理逻辑
            return PipelineResult(success=True)
        
        def _cleanup(self):
            # 清理资源
            pass
"""

# 确保核心模块可导入
from .base_pipeline import BasePipeline, PipelineResult, PipelineStatus
from .config_manager import ConfigManager
from .exceptions import (
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
    ErrorCode,
    ErrorSeverity,
    error_code_manager
)
from .logging_setup import setup_logging, get_logger
from .input_validator import InputValidator, Pattern
from .io_abstraction import (
    IStorageBackend,
    LocalStorageBackend,
    IOManager,
    FileMetadata,
    IOResult,
    CompressionFormat,
    get_io_manager,
    init_io_manager
)
from .metrics import (
    WorkshopMetrics,
    get_metrics,
    measure_performance,
    init_metrics_server
)
from .performance import (
    PerformanceMetric,
    BenchmarkResult,
    PerformanceTimer,
    BenchmarkSuite,
    MemoryProfiler,
    quick_benchmark,
    compare_functions
)
from .security_audit import (
    SecuritySeverity,
    SecurityFinding,
    SecurityAuditReport,
    CodeSecurityScanner,
    DependencyAuditor,
    ConfigurationAuditor,
    run_full_security_audit
)

__all__ = [
    # Base classes
    'BasePipeline',
    'PipelineResult',
    'PipelineStatus',
    
    # Config
    'ConfigManager',
    
    # Exceptions
    'WorkshopError',
    'ConfigurationError',
    'PipelineError',
    'ValidationError',
    'HardwareError',
    'DataIOError',
    'ErrorCode',
    'ErrorSeverity',
    'error_code_manager',
    
    # Logging
    'setup_logging',
    'get_logger',
    
    # Validation
    'InputValidator',
    'Pattern',
    
    # I/O
    'IStorageBackend',
    'LocalStorageBackend',
    'IOManager',
    'FileMetadata',
    'IOResult',
    'CompressionFormat',
    'get_io_manager',
    'init_io_manager',
    
    # Metrics
    'WorkshopMetrics',
    'get_metrics',
    'measure_performance',
    'init_metrics_server',
    
    # Performance
    'PerformanceMetric',
    'BenchmarkResult',
    'PerformanceTimer',
    'BenchmarkSuite',
    'MemoryProfiler',
    'quick_benchmark',
    'compare_functions',
    
    # Security
    'SecuritySeverity',
    'SecurityFinding',
    'SecurityAuditReport',
    'CodeSecurityScanner',
    'DependencyAuditor',
    'ConfigurationAuditor',
    'run_full_security_audit',
]
