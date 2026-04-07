"""
健康检查服务

提供系统健康状态检查、组件健康监控等功能。
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


class HealthCheckType(Enum):
    """健康检查类型"""
    LIVENESS = auto()
    READINESS = auto()
    STARTUP = auto()
    CUSTOM = auto()


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: HealthStatus
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.name,
            "message": self.message,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "duration_ms": self.duration_ms,
            "details": self.details,
            "error": self.error,
        }

    def is_healthy(self) -> bool:
        return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    name: str
    check_func: Callable[[], HealthCheckResult]
    check_type: HealthCheckType = HealthCheckType.CUSTOM
    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    failure_threshold: int = 3
    success_threshold: int = 1
    enabled: bool = True


@dataclass
class ComponentHealth:
    """组件健康状态"""
    name: str
    status: HealthStatus
    last_check: Optional[HealthCheckResult] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_checks: int = 0
    total_failures: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.name,
            "last_check": self.last_check.to_dict() if self.last_check else None,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
            "last_success_time": datetime.fromtimestamp(self.last_success_time).isoformat() if self.last_success_time else None,
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
        }


class HealthService:
    """健康检查服务"""

    _instance: Optional[HealthService] = None
    _lock = threading.Lock()

    def __new__(cls) -> HealthService:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._checks: Dict[str, HealthCheckConfig] = {}
        self._components: Dict[str, ComponentHealth] = {}
        self._check_results: Dict[str, List[HealthCheckResult]] = {}
        self._max_results_per_check = 100
        self._checks_lock = threading.Lock()
        self._results_lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = True

    def register_check(
        self,
        name: str,
        check_func: Callable[[], HealthCheckResult],
        check_type: HealthCheckType = HealthCheckType.CUSTOM,
        interval_seconds: float = 30.0,
        timeout_seconds: float = 5.0,
        failure_threshold: int = 3,
        success_threshold: int = 1,
        enabled: bool = True,
    ) -> None:
        config = HealthCheckConfig(
            name=name,
            check_func=check_func,
            check_type=check_type,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            enabled=enabled,
        )

        with self._checks_lock:
            self._checks[name] = config
            if name not in self._components:
                self._components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                )

    def unregister_check(self, name: str) -> bool:
        with self._checks_lock:
            if name in self._checks:
                del self._checks[name]
                if name in self._components:
                    del self._components[name]
                return True
        return False

    def run_check(self, name: str) -> Optional[HealthCheckResult]:
        with self._checks_lock:
            config = self._checks.get(name)

        if config is None or not config.enabled:
            return None

        start_time = time.time()
        error = None
        result = None

        try:
            result = config.check_func()
        except Exception as e:
            error = str(e)
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"健康检查异常: {error}",
                error=error,
            )

        duration_ms = (time.time() - start_time) * 1000
        result.duration_ms = duration_ms

        with self._checks_lock:
            component = self._components.get(name)
            if component:
                component.last_check = result
                component.total_checks += 1

                if result.status == HealthStatus.HEALTHY:
                    component.consecutive_successes += 1
                    component.consecutive_failures = 0
                    component.last_success_time = time.time()

                    if component.consecutive_successes >= config.success_threshold:
                        component.status = HealthStatus.HEALTHY
                else:
                    component.consecutive_failures += 1
                    component.consecutive_successes = 0
                    component.total_failures += 1
                    component.last_failure_time = time.time()

                    if component.consecutive_failures >= config.failure_threshold:
                        component.status = result.status

        with self._results_lock:
            if name not in self._check_results:
                self._check_results[name] = []
            self._check_results[name].append(result)

            if len(self._check_results[name]) > self._max_results_per_check:
                self._check_results[name] = self._check_results[name][-self._max_results_per_check:]

        return result

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        results = {}
        with self._checks_lock:
            check_names = list(self._checks.keys())

        for name in check_names:
            results[name] = self.run_check(name)

        return results

    def get_check_result(self, name: str) -> Optional[HealthCheckResult]:
        with self._results_lock:
            results = self._check_results.get(name)
            if results:
                return results[-1]
        return None

    def get_component_health(self, name: str) -> Optional[ComponentHealth]:
        with self._checks_lock:
            return self._components.get(name)

    def get_all_components(self) -> Dict[str, ComponentHealth]:
        with self._checks_lock:
            return dict(self._components)

    def get_overall_status(self) -> HealthStatus:
        with self._checks_lock:
            if not self._components:
                return HealthStatus.UNKNOWN

            statuses = [c.status for c in self._components.values()]

            if any(s == HealthStatus.UNHEALTHY for s in statuses):
                return HealthStatus.UNHEALTHY
            elif any(s == HealthStatus.DEGRADED for s in statuses):
                return HealthStatus.DEGRADED
            elif all(s == HealthStatus.HEALTHY for s in statuses):
                return HealthStatus.HEALTHY
            else:
                return HealthStatus.UNKNOWN

    def liveness_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name="liveness",
            status=HealthStatus.HEALTHY,
            message="服务存活",
        )

    def readiness_check(self) -> HealthCheckResult:
        overall = self.get_overall_status()
        return HealthCheckResult(
            name="readiness",
            status=overall,
            message="服务就绪检查",
            details={
                "components": {name: c.status.name for name, c in self._components.items()},
            },
        )

    def start_monitoring(self, interval_seconds: float = 30.0) -> None:
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()

        def monitor_loop():
            while not self._stop_event.is_set():
                self.run_all_checks()
                self._stop_event.wait(interval_seconds)

        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

    def get_check_history(self, name: str, limit: int = 50) -> List[HealthCheckResult]:
        with self._results_lock:
            results = list(self._check_results.get(name, []))
        return results[-limit:]

    def export_health(self, format: str = "json") -> str:
        health_data = {
            "overall_status": self.get_overall_status().name,
            "timestamp": datetime.now().isoformat(),
            "components": {name: c.to_dict() for name, c in self._components.items()},
        }

        if format == "json":
            return json.dumps(health_data, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_statistics(self) -> Dict[str, Any]:
        with self._checks_lock:
            total_checks = len(self._checks)
            enabled_checks = sum(1 for c in self._checks.values() if c.enabled)
            components = list(self._components.values())

        status_counts = {}
        for status in HealthStatus:
            status_counts[status.name] = sum(1 for c in components if c.status == status)

        return {
            "total_checks": total_checks,
            "enabled_checks": enabled_checks,
            "overall_status": self.get_overall_status().name,
            "status_distribution": status_counts,
            "monitoring_active": self._monitor_thread is not None and self._monitor_thread.is_alive(),
        }

    def clear_history(self) -> int:
        with self._results_lock:
            count = sum(len(r) for r in self._check_results.values())
            self._check_results.clear()
        return count


def get_health_service() -> HealthService:
    return HealthService()


def create_simple_check(
    name: str,
    check_func: Callable[[], bool],
    healthy_message: str = "健康",
    unhealthy_message: str = "不健康",
) -> Callable[[], HealthCheckResult]:
    def wrapper() -> HealthCheckResult:
        try:
            is_healthy = check_func()
            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                message=healthy_message if is_healthy else unhealthy_message,
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"检查异常: {str(e)}",
                error=str(e),
            )

    return wrapper
