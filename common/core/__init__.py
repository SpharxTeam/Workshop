# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop 核心基础设施包初始化 - V2.0 完整版

# Phase 1: 核心基础设施
from .base_pipeline import BasePipeline, PipelineResult, PipelineStatus
from .config_manager import ConfigManager
from .exceptions import (
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
    error_code_manager
)
from .logging_setup import setup_logging, get_logger
from .input_validator import InputValidator

# Phase 4: 数据流处理增强
from .io_abstraction import (
    IStorageBackend,
    LocalStorageBackend,
    IOManager,
    FileMetadata,
    IOResult,
    StorageBackend,
    CompressionFormat,
    get_io_manager,
    init_io_manager
)

# Phase 5: 性能与安全工具
from .performance import (
    PerformanceMetric,
    BenchmarkResult,
    PerformanceTimer,
    measure_performance,
    BenchmarkSuite,
    MemoryProfiler,
    profile_memory,
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
    # Phase 1: 核心基础设施
    'BasePipeline',
    'PipelineResult',
    'PipelineStatus',
    'ConfigManager',
    'WorkshopError',
    'ConfigurationError',
    'PipelineError',
    'ValidationError',
    'HardwareError',
    'DataIOError',
    'error_code_manager',
    'setup_logging',
    'get_logger',
    'InputValidator',
    
    # Phase 4: IO 抽象层
    'IStorageBackend',
    'LocalStorageBackend',
    'IOManager',
    'FileMetadata',
    'IOResult',
    'StorageBackend',
    'CompressionFormat',
    'get_io_manager',
    'init_io_manager',
    
    # Phase 5: 性能测试
    'PerformanceMetric',
    'BenchmarkResult',
    'PerformanceTimer',
    'measure_performance',
    'BenchmarkSuite',
    'MemoryProfiler',
    'profile_memory',
    'quick_benchmark',
    'compare_functions',
    
    # Phase 5: 安全审计
    'SecuritySeverity',
    'SecurityFinding',
    'SecurityAuditReport',
    'CodeSecurityScanner',
    'DependencyAuditor',
    'ConfigurationAuditor',
    'run_full_security_audit'
]
