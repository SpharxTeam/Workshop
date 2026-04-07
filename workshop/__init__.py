# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Workshop V2.0 - 企业级数据处理管道框架
======================================

基于 AgentOS 微内核架构模式构建的高性能数据处理系统。

架构原则:
    - K-1 Kernel Minimalism: 核心基础设施层最小化
    - K-2 Interface Contract: 通过 BasePipeline ABC 强制接口契约
    - K-3 Service Isolation: 每个 Pipeline 模块独立容器化
    - K-4 Pluggable Strategy: 支持运行时策略切换

主要模块:
    - core: 核心基础设施 (BasePipeline, ConfigManager, Exceptions等)
    - pipelines: 数据处理管道模块 (Ingest, Quality, Enhance等)
    - hardware: 硬件抽象层 (相机/传感器管理)
    - tests: 测试套件 (单元测试/集成测试/负载测试)
    - scripts: 运维工具集 (部署/监控/备份)
    - config: 配置文件 (YAML/Prometheus/Grafana)
    - docs: 技术文档

使用示例:
    >>> from workshop.core import BasePipeline, ConfigManager
    >>> from workshop.pipelines.run_00_ingest.runner_v2 import IngestPipeline
    
    # 创建并运行 Pipeline
    with IngestPipeline() as pipeline:
        result = pipeline.run(input_data)
        print(f"处理完成：{result.success}")

版本信息:
    - 当前版本：2.0.0
    - Python 要求：>=3.8
    - 许可证：GPL-3.0

作者: SPHARX DevTeam
网站：https://github.com/spharx-cn/workshop
"""

__version__ = '2.0.0'
__author__ = 'SPHARX DevTeam'
__license__ = 'GPL-3.0'

# 核心模块导入
from workshop.core.base_pipeline import BasePipeline, PipelineResult, PipelineStatus
from workshop.core.config_manager import ConfigManager
from workshop.core.exceptions import (
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
    error_code_manager
)
from workshop.core.logging_setup import setup_logging, get_logger
from workshop.core.input_validator import InputValidator
from workshop.core.metrics import WorkshopMetrics, get_metrics, measure_performance
from workshop.core.io_abstraction import (
    IStorageBackend,
    LocalStorageBackend,
    IOManager,
    FileMetadata,
    IOResult,
    get_io_manager,
    init_io_manager
)
from workshop.core.performance import (
    PerformanceMetric,
    BenchmarkResult,
    PerformanceTimer,
    measure_performance,
    BenchmarkSuite,
    MemoryProfiler,
    quick_benchmark,
    compare_functions
)
from workshop.core.security_audit import (
    SecuritySeverity,
    SecurityFinding,
    SecurityAuditReport,
    CodeSecurityScanner,
    DependencyAuditor,
    ConfigurationAuditor,
    run_full_security_audit
)

# 导出所有公共 API
__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__license__',
    
    # BasePipeline
    'BasePipeline',
    'PipelineResult',
    'PipelineStatus',
    
    # ConfigManager
    'ConfigManager',
    
    # Exceptions
    'WorkshopError',
    'ConfigurationError',
    'PipelineError',
    'ValidationError',
    'HardwareError',
    'DataIOError',
    'error_code_manager',
    
    # Logging
    'setup_logging',
    'get_logger',
    
    # Validation
    'InputValidator',
    
    # Metrics & Monitoring
    'WorkshopMetrics',
    'get_metrics',
    'measure_performance',
    
    # I/O
    'IStorageBackend',
    'LocalStorageBackend',
    'IOManager',
    'FileMetadata',
    'IOResult',
    'get_io_manager',
    'init_io_manager',
    
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


def get_version() -> str:
    """获取 Workshop 版本号"""
    return __version__


def get_info() -> dict:
    """获取 Workshop 详细信息"""
    return {
        'name': 'Workshop',
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'python_requires': '>=3.8',
        'description': '企业级数据处理管道框架',
        'url': 'https://github.com/spharx-cn/workshop',
    }


# 初始化日志系统
setup_logging()
