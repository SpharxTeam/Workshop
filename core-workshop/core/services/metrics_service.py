"""
Metrics Service - V3.0
======================

指标服务 - Prometheus 指标收集和导出

参考:
    - AgentOS Metrics 模块
    - Deepness MetricsService
"""

from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import threading
from contextlib import contextmanager

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary,
        CollectorRegistry, REGISTRY,
        start_http_server,
        PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricConfig:
    """指标配置"""
    namespace: str = "workshop"
    subsystem: str = ""
    enable_default_metrics: bool = True
    port: int = 9090
    enable_http_server: bool = False


class MetricDefinition:
    """指标定义"""

    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ):
        self.name = name
        self.metric_type = metric_type
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]


class MetricsCollector:
    """
    指标收集器
    
    收集和管理指标数据
    """

    def __init__(self, namespace: str = "workshop"):
        self._namespace = namespace
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_metric(self, definition: MetricDefinition) -> Any:
        """
        注册指标
        
        Args:
            definition: 指标定义
            
        Returns:
            Any: 指标实例
        """
        if not PROMETHEUS_AVAILABLE:
            return None

        with self._lock:
            full_name = f"{self._namespace}_{definition.name}"

            if full_name in self._metrics:
                return self._metrics[full_name]

            if definition.metric_type == MetricType.COUNTER:
                metric = Counter(
                    full_name,
                    definition.description,
                    definition.labels,
                )
            elif definition.metric_type == MetricType.GAUGE:
                metric = Gauge(
                    full_name,
                    definition.description,
                    definition.labels,
                )
            elif definition.metric_type == MetricType.HISTOGRAM:
                metric = Histogram(
                    full_name,
                    definition.description,
                    definition.labels,
                    buckets=definition.buckets,
                )
            elif definition.metric_type == MetricType.SUMMARY:
                metric = Summary(
                    full_name,
                    definition.description,
                    definition.labels,
                )
            else:
                raise ValueError(f"不支持的指标类型: {definition.metric_type}")

            self._metrics[full_name] = metric
            return metric

    def get_metric(self, name: str) -> Optional[Any]:
        """获取指标"""
        full_name = f"{self._namespace}_{name}"
        return self._metrics.get(full_name)

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        增加计数器
        
        Args:
            name: 指标名称
            value: 增加值
            labels: 标签
        """
        metric = self.get_metric(name)
        if metric and PROMETHEUS_AVAILABLE:
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        设置仪表值
        
        Args:
            name: 指标名称
            value: 值
            labels: 标签
        """
        metric = self.get_metric(name)
        if metric and PROMETHEUS_AVAILABLE:
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        观察直方图值
        
        Args:
            name: 指标名称
            value: 值
            labels: 标签
        """
        metric = self.get_metric(name)
        if metric and PROMETHEUS_AVAILABLE:
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)


class MetricsRegistry:
    """
    指标注册表
    
    管理所有指标的定义和实例
    """

    def __init__(self, namespace: str = "workshop"):
        self._namespace = namespace
        self._definitions: Dict[str, MetricDefinition] = {}
        self._collector = MetricsCollector(namespace)

    def register(self, definition: MetricDefinition) -> Any:
        """
        注册指标定义
        
        Args:
            definition: 指标定义
            
        Returns:
            Any: 指标实例
        """
        self._definitions[definition.name] = definition
        return self._collector.register_metric(definition)

    def get_collector(self) -> MetricsCollector:
        """获取收集器"""
        return self._collector

    def get_definitions(self) -> Dict[str, MetricDefinition]:
        """获取所有定义"""
        return dict(self._definitions)


class MetricsService:
    """
    指标服务 - V3.0
    
    特性:
    - Prometheus 指标收集
    - 多种指标类型 (Counter, Gauge, Histogram, Summary)
    - HTTP 端点导出
    - 性能追踪
    """

    _instance: Optional['MetricsService'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[MetricConfig] = None):
        """
        初始化指标服务
        
        Args:
            config: 指标配置
        """
        if self._initialized:
            return

        self._config = config or MetricConfig()
        self._registry = MetricsRegistry(self._config.namespace)
        self._collector = self._registry.get_collector()
        self._http_server_started = False
        
        self._setup_default_metrics()
        self._initialized = True

    def _setup_default_metrics(self) -> None:
        """设置默认指标"""
        # Pipeline 指标
        self._registry.register(MetricDefinition(
            name="pipeline_executions_total",
            metric_type=MetricType.COUNTER,
            description="Pipeline 执行总数",
            labels=["pipeline_name", "status"],
        ))

        self._registry.register(MetricDefinition(
            name="pipeline_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            description="Pipeline 执行耗时",
            labels=["pipeline_name"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
        ))

        self._registry.register(MetricDefinition(
            name="active_pipelines",
            metric_type=MetricType.GAUGE,
            description="当前活跃的 Pipeline 数量",
        ))

        # 错误指标
        self._registry.register(MetricDefinition(
            name="errors_total",
            metric_type=MetricType.COUNTER,
            description="错误总数",
            labels=["error_type", "severity"],
        ))

        # 数据处理指标
        self._registry.register(MetricDefinition(
            name="data_processed_bytes",
            metric_type=MetricType.COUNTER,
            description="处理的数据量 (字节)",
            labels=["pipeline_name"],
        ))

        self._registry.register(MetricDefinition(
            name="data_processed_total",
            metric_type=MetricType.COUNTER,
            description="处理的数据项数",
            labels=["pipeline_name"],
        ))

    def start_http_server(self, port: Optional[int] = None) -> None:
        """
        启动 HTTP 服务器
        
        Args:
            port: 端口号
        """
        if not PROMETHEUS_AVAILABLE:
            return

        if self._http_server_started:
            return

        port = port or self._config.port
        start_http_server(port)
        self._http_server_started = True

    @contextmanager
    def track_pipeline(
        self,
        pipeline_name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        追踪 Pipeline 执行
        
        Args:
            pipeline_name: Pipeline 名称
            labels: 额外标签
        """
        start_time = time.time()
        self._collector.increment_gauge("active_pipelines", 1)
        
        try:
            yield
            status = "success"
        except Exception as e:
            status = "error"
            self._collector.increment_counter(
                "errors_total",
                labels={"error_type": type(e).__name__, "severity": "error"},
            )
            raise
        finally:
            duration = time.time() - start_time
            
            self._collector.observe_histogram(
                "pipeline_duration_seconds",
                duration,
                labels={"pipeline_name": pipeline_name},
            )
            
            self._collector.increment_counter(
                "pipeline_executions_total",
                labels={"pipeline_name": pipeline_name, "status": status},
            )
            
            self._collector.set_gauge("active_pipelines", -1)

    def record_data_processed(
        self,
        pipeline_name: str,
        bytes_count: int,
        items_count: int = 1,
    ) -> None:
        """
        记录数据处理量
        
        Args:
            pipeline_name: Pipeline 名称
            bytes_count: 字节数
            items_count: 数据项数
        """
        self._collector.increment_counter(
            "data_processed_bytes",
            bytes_count,
            labels={"pipeline_name": pipeline_name},
        )
        
        self._collector.increment_counter(
            "data_processed_total",
            items_count,
            labels={"pipeline_name": pipeline_name},
        )

    def get_collector(self) -> MetricsCollector:
        """获取收集器"""
        return self._collector

    def get_registry(self) -> MetricsRegistry:
        """获取注册表"""
        return self._registry


def get_metrics() -> MetricsService:
    """
    获取指标服务实例的便捷函数
    
    Returns:
        MetricsService: 指标服务实例
    """
    return MetricsService()


def track_performance(metric_name: str):
    """
    性能追踪装饰器
    
    Args:
        metric_name: 指标名称
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            with metrics.track_pipeline(metric_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
