"""
Core-Workshop 核心层
====================

聚合导出 abstractions / services / security / observability 四个子包的公共 API。

子包:
    - abstractions: 核心抽象基类 (BasePipeline, ErrorCode, ...)
    - services: 核心服务 (ConfigService, LoggingService, MetricsService)
    - security: 安全服务 (ValidationService, SecurityService)
    - observability: 可观测性 (TracingService, PerformanceMonitor, HealthService)
"""

# 延迟导入以避免循环依赖；实际使用时从子包直接导入
# 此 __init__.py 仅确保 core_workshop.core 是一个合法的 Python 包

__all__: list = []
