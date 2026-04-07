"""
性能监控服务

提供性能指标收集、阈值监控、告警等功能。
"""

from __future__ import annotations

import json
import statistics
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar

T = TypeVar("T")


class MetricType(Enum):
    """指标类型"""
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()


class AlertSeverity(Enum):
    """告警严重级别"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.metric_type.name,
            "value": self.value,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "labels": self.labels,
            "unit": self.unit,
            "description": self.description,
        }


@dataclass
class PerformanceThreshold:
    """性能阈值"""
    metric_name: str
    warning_threshold: Optional[float] = None
    error_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison: str = "greater"
    enabled: bool = True

    def check(self, value: float) -> Optional[AlertSeverity]:
        if not self.enabled:
            return None

        if self.comparison == "greater":
            if self.critical_threshold is not None and value >= self.critical_threshold:
                return AlertSeverity.CRITICAL
            if self.error_threshold is not None and value >= self.error_threshold:
                return AlertSeverity.ERROR
            if self.warning_threshold is not None and value >= self.warning_threshold:
                return AlertSeverity.WARNING
        elif self.comparison == "less":
            if self.critical_threshold is not None and value <= self.critical_threshold:
                return AlertSeverity.CRITICAL
            if self.error_threshold is not None and value <= self.error_threshold:
                return AlertSeverity.ERROR
            if self.warning_threshold is not None and value <= self.warning_threshold:
                return AlertSeverity.WARNING

        return None


@dataclass
class PerformanceAlert:
    """性能告警"""
    id: str
    metric_name: str
    severity: AlertSeverity
    value: float
    threshold: float
    message: str
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "severity": self.severity.name,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "labels": self.labels,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
        }


class PerformanceMonitor:
    """性能监控器"""

    _instance: Optional[PerformanceMonitor] = None
    _lock = threading.Lock()

    DEFAULT_THRESHOLDS = {
        "cpu_usage": PerformanceThreshold(
            metric_name="cpu_usage",
            warning_threshold=70.0,
            error_threshold=85.0,
            critical_threshold=95.0,
            comparison="greater",
        ),
        "memory_usage": PerformanceThreshold(
            metric_name="memory_usage",
            warning_threshold=70.0,
            error_threshold=85.0,
            critical_threshold=95.0,
            comparison="greater",
        ),
        "disk_usage": PerformanceThreshold(
            metric_name="disk_usage",
            warning_threshold=80.0,
            error_threshold=90.0,
            critical_threshold=95.0,
            comparison="greater",
        ),
        "response_time": PerformanceThreshold(
            metric_name="response_time",
            warning_threshold=1000.0,
            error_threshold=3000.0,
            critical_threshold=5000.0,
            comparison="greater",
            unit="ms",
        ),
        "error_rate": PerformanceThreshold(
            metric_name="error_rate",
            warning_threshold=1.0,
            error_threshold=5.0,
            critical_threshold=10.0,
            comparison="greater",
            unit="%",
        ),
    }

    def __new__(cls) -> PerformanceMonitor:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._metrics: Dict[str, List[PerformanceMetric]] = {}
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._thresholds: Dict[str, PerformanceThreshold] = dict(self.DEFAULT_THRESHOLDS)
        self._alerts: List[PerformanceAlert] = []
        self._alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        self._max_metrics_per_name = 1000
        self._max_alerts = 500
        self._metrics_lock = threading.Lock()
        self._alerts_lock = threading.Lock()
        self._initialized = True

    def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
        description: str = "",
    ) -> None:
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
            unit=unit,
            description=description,
        )

        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(metric)

            if len(self._metrics[name]) > self._max_metrics_per_name:
                self._metrics[name] = self._metrics[name][-self._max_metrics_per_name:]

            if metric_type == MetricType.COUNTER:
                self._counters[name] = self._counters.get(name, 0.0) + value
            elif metric_type == MetricType.GAUGE:
                self._gauges[name] = value
            elif metric_type == MetricType.HISTOGRAM:
                if name not in self._histograms:
                    self._histograms[name] = []
                self._histograms[name].append(value)

        threshold = self._thresholds.get(name)
        if threshold:
            severity = threshold.check(value)
            if severity:
                self._create_alert(metric, severity, threshold)

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        self.record(name, value, MetricType.COUNTER, labels)

    def decrement(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        self.record(name, -value, MetricType.COUNTER, labels)

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        self.record(name, value, MetricType.GAUGE, labels)

    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        self.record(name, value, MetricType.HISTOGRAM, labels)

    def timing(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None) -> None:
        self.record(name, duration_ms, MetricType.HISTOGRAM, labels, unit="ms")

    @contextmanager
    def measure(self, name: str, labels: Optional[Dict[str, str]] = None) -> Iterator[None]:
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.timing(name, duration_ms, labels)

    def timed(self, name: Optional[str] = None) -> Callable[[Callable[T]], Callable[T]]:
        def decorator(func: Callable[T]) -> Callable[T]:
            metric_name = name or f"{func.__module__}.{func.__name__}.duration"

            def wrapper(*args, **kwargs) -> T:
                with self.measure(metric_name):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_counter(self, name: str) -> float:
        with self._metrics_lock:
            return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        with self._metrics_lock:
            return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        with self._metrics_lock:
            values = self._histograms.get(name)
            if not values:
                return None

            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "p50": statistics.quantiles(values, n=100)[49] if len(values) >= 100 else statistics.median(values),
                "p90": statistics.quantiles(values, n=100)[89] if len(values) >= 100 else None,
                "p99": statistics.quantiles(values, n=100)[98] if len(values) >= 100 else None,
            }

    def get_metrics(
        self,
        name: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[PerformanceMetric]:
        with self._metrics_lock:
            if name:
                metrics = list(self._metrics.get(name, []))
            else:
                metrics = []
                for m_list in self._metrics.values():
                    metrics.extend(m_list)

        if since:
            metrics = [m for m in metrics if m.timestamp >= since]

        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        return metrics[:limit]

    def set_threshold(self, threshold: PerformanceThreshold) -> None:
        self._thresholds[threshold.metric_name] = threshold

    def get_threshold(self, metric_name: str) -> Optional[PerformanceThreshold]:
        return self._thresholds.get(metric_name)

    def remove_threshold(self, metric_name: str) -> bool:
        if metric_name in self._thresholds:
            del self._thresholds[metric_name]
            return True
        return False

    def _create_alert(
        self,
        metric: PerformanceMetric,
        severity: AlertSeverity,
        threshold: PerformanceThreshold,
    ) -> PerformanceAlert:
        import uuid

        if severity == AlertSeverity.WARNING:
            threshold_value = threshold.warning_threshold
        elif severity == AlertSeverity.ERROR:
            threshold_value = threshold.error_threshold
        else:
            threshold_value = threshold.critical_threshold

        alert = PerformanceAlert(
            id=str(uuid.uuid4()),
            metric_name=metric.name,
            severity=severity,
            value=metric.value,
            threshold=threshold_value or 0.0,
            message=f"指标 '{metric.name}' 值 {metric.value} 超过阈值 {threshold_value}",
            labels=metric.labels,
        )

        with self._alerts_lock:
            self._alerts.append(alert)
            if len(self._alerts) > self._max_alerts:
                self._alerts = self._alerts[-self._max_alerts:]

        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass

        return alert

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        metric_name: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[PerformanceAlert]:
        with self._alerts_lock:
            alerts = list(self._alerts)

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if metric_name:
            alerts = [a for a in alerts if a.metric_name == metric_name]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]

    def acknowledge_alert(self, alert_id: str) -> bool:
        with self._alerts_lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        with self._alerts_lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    return True
        return False

    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        self._alert_callbacks.append(callback)

    def export_metrics(self, format: str = "json") -> str:
        with self._metrics_lock:
            metrics = {}
            for name, m_list in self._metrics.items():
                metrics[name] = {
                    "type": m_list[0].metric_type.name if m_list else "UNKNOWN",
                    "count": len(m_list),
                    "latest": m_list[-1].to_dict() if m_list else None,
                }
                if name in self._histograms:
                    metrics[name]["stats"] = self.get_histogram_stats(name)

        if format == "json":
            return json.dumps(metrics, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def export_alerts(self, format: str = "json") -> str:
        with self._alerts_lock:
            alerts = [alert.to_dict() for alert in self._alerts]

        if format == "json":
            return json.dumps(alerts, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def clear_metrics(self) -> int:
        with self._metrics_lock:
            count = sum(len(m) for m in self._metrics.values())
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
        return count

    def clear_alerts(self) -> int:
        with self._alerts_lock:
            count = len(self._alerts)
            self._alerts.clear()
        return count

    def get_statistics(self) -> Dict[str, Any]:
        with self._metrics_lock:
            total_metrics = sum(len(m) for m in self._metrics.values())
            unique_metrics = len(self._metrics)

        with self._alerts_lock:
            total_alerts = len(self._alerts)
            unacknowledged_alerts = sum(1 for a in self._alerts if not a.acknowledged)
            unresolved_alerts = sum(1 for a in self._alerts if not a.resolved)
            critical_alerts = sum(1 for a in self._alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved)

        return {
            "total_metrics": total_metrics,
            "unique_metrics": unique_metrics,
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "unresolved_alerts": unresolved_alerts,
            "critical_alerts": critical_alerts,
            "thresholds_configured": len(self._thresholds),
        }


def get_performance_monitor() -> PerformanceMonitor:
    return PerformanceMonitor()


def measure_time(name: Optional[str] = None) -> Callable[[Callable[T]], Callable[T]]:
    return get_performance_monitor().timed(name)
