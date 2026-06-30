# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Core-Workshop V3.0 - 企业级数据处理管道框架
======================================

基于 AgentOS 微内核架构和 Deepness 模式构建的高性能数据处理系统。

架构层次:
    - core: 核心层 (abstractions, services, security, observability)
    - orchestration: 编排层 (scheduler, task_queue, workflow_engine)
    - services: 服务层 (gateway, monitor, exporter)

主要模块:
    - core_workshop.core.abstractions: 核心抽象基类
    - core_workshop.core.services: 核心服务 (配置、日志、指标)
    - core_workshop.core.security: 安全服务 (验证、审计)
    - core_workshop.core.observability: 可观测性 (追踪、性能、健康)
    - core_workshop.orchestration: 编排层
    - core_workshop.services: API 网关、监控、导出

使用示例:
    >>> from core_workshop.core.abstractions import BasePipeline
    >>> from core_workshop.core.services import ConfigService
    >>> from core_workshop.services import Gateway

版本信息:
    - 当前版本：3.0.0
    - Python 要求：>=3.8
    - 许可证：GPL-3.0

作者: SPHARX DevTeam
网站：https://github.com/spharx-cn/workshop
"""

__version__ = '3.0.0'
__author__ = 'SPHARX DevTeam'
__license__ = 'GPL-3.0'

# V3.0 核心模块导入
from core_workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    PipelineStatus,
    PipelineContext,
    IStorageBackend,
    LocalStorageBackend,
    IHardwareDevice,
    ErrorCode,
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
)

from core_workshop.core.services import (
    ConfigService,
    LoggingService,
    MetricsService,
)

from core_workshop.core.security import (
    ValidationService,
    SecurityService,
)

from core_workshop.core.observability import (
    TracingService,
    PerformanceMonitor,
    HealthService,
)

from core_workshop.orchestration import (
    Scheduler,
    TaskQueue,
    WorkflowEngine,
)

from core_workshop.services import (
    Gateway,
    Monitor,
    Exporter,
)

# 导出所有公共 API
__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__license__',
    
    # 核心抽象
    'BasePipeline',
    'PipelineResult',
    'PipelineStatus',
    'PipelineContext',
    'IStorageBackend',
    'LocalStorageBackend',
    'IHardwareDevice',
    
    # 异常类
    'ErrorCode',
    'WorkshopError',
    'ConfigurationError',
    'PipelineError',
    'ValidationError',
    'HardwareError',
    'DataIOError',
    
    # 核心服务
    'ConfigService',
    'LoggingService',
    'MetricsService',
    
    # 安全服务
    'ValidationService',
    'SecurityService',
    
    # 可观测性
    'TracingService',
    'PerformanceMonitor',
    'HealthService',
    
    # 编排层
    'Scheduler',
    'TaskQueue',
    'WorkflowEngine',
    
    # 服务层
    'Gateway',
    'Monitor',
    'Exporter',
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
        'description': '企业级数据处理管道框架 V3.0',
        'url': 'https://github.com/spharx-cn/workshop',
        'architecture': 'Five-Layer Architecture (Core/Orchestration/Services/Commons)',
        'reference_projects': ['AgentOS', 'Deepness'],
    }
