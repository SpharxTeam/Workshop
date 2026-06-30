"""
监控服务

提供系统监控、告警、指标收集等功能。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class MonitorStatus(Enum):
    """监控状态"""
    HEALTHY = auto()
    WARNING = auto()
    CRITICAL = auto()
    UNKNOWN = auto()


class AlertSeverity(Enum):
    """告警严重级别"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class MonitorTarget:
    """监控目标"""
    id: str
    name: str
    check_func: Callable[[], Dict[str, Any]]
    interval_seconds: float = 30.0
    timeout_seconds: float = 10.0
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    enabled: bool = True
    status: MonitorStatus = MonitorStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_value: Optional[float] = None
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "interval_seconds": self.interval_seconds,
            "enabled": self.enabled,
            "status": self.status.name,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_value": self.last_value,
            "last_error": self.last_error,
        }


@dataclass
class Alert:
    """告警"""
    id: str
    target_id: str
    severity: AlertSeverity
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "target_id": self.target_id,
            "severity": self.severity.name,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class Monitor:
    """监控服务"""

    _instance: Optional[Monitor] = None
    _lock = threading.Lock()

    def __new__(cls) -> Monitor:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._targets: Dict[str, MonitorTarget] = {}
        self._alerts: List[Alert] = []
        self._targets_lock = threading.Lock()
        self._alerts_lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._on_alert: Optional[Callable[[Alert], None]] = None
        self._max_alerts = 1000
        self._initialized = True

    def register_target(
        self,
        target_id: str,
        name: str,
        check_func: Callable[[], Dict[str, Any]],
        interval_seconds: float = 30.0,
        timeout_seconds: float = 10.0,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MonitorTarget:
        target = MonitorTarget(
            id=target_id,
            name=name,
            check_func=check_func,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            enabled=enabled,
            metadata=metadata or {},
        )

        with self._targets_lock:
            self._targets[target_id] = target

        return target

    def unregister_target(self, target_id: str) -> bool:
        with self._targets_lock:
            if target_id in self._targets:
                del self._targets[target_id]
                return True
        return False

    def check_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        with self._targets_lock:
            target = self._targets.get(target_id)

        if target is None or not target.enabled:
            return None

        try:
            result = target.check_func()
            target.last_check = datetime.now()
            target.last_error = None

            if "value" in result:
                target.last_value = result["value"]

                if target.critical_threshold is not None:
                    if result["value"] >= target.critical_threshold:
                        target.status = MonitorStatus.CRITICAL
                        self._create_alert(target, AlertSeverity.CRITICAL, result["value"])
                    elif target.warning_threshold is not None and result["value"] >= target.warning_threshold:
                        target.status = MonitorStatus.WARNING
                        self._create_alert(target, AlertSeverity.WARNING, result["value"])
                    else:
                        target.status = MonitorStatus.HEALTHY
                else:
                    target.status = MonitorStatus.HEALTHY

            return result

        except Exception as e:
            target.last_error = str(e)
            target.status = MonitorStatus.UNKNOWN
            return {"error": str(e)}

    def _create_alert(
        self,
        target: MonitorTarget,
        severity: AlertSeverity,
        value: float,
    ) -> Alert:
        import uuid

        threshold = (
            target.critical_threshold if severity == AlertSeverity.CRITICAL
            else target.warning_threshold
        )

        alert = Alert(
            id=str(uuid.uuid4())[:8],
            target_id=target.id,
            severity=severity,
            message=f"监控目标 '{target.name}' 触发 {severity.name} 告警",
            value=value,
            threshold=threshold,
        )

        with self._alerts_lock:
            self._alerts.append(alert)
            if len(self._alerts) > self._max_alerts:
                self._alerts = self._alerts[-self._max_alerts:]

        if self._on_alert:
            try:
                self._on_alert(alert)
            except Exception:
                pass

        return alert

    def check_all(self) -> Dict[str, Dict[str, Any]]:
        results = {}

        with self._targets_lock:
            target_ids = list(self._targets.keys())

        for target_id in target_ids:
            results[target_id] = self.check_target(target_id) or {}

        return results

    def get_target(self, target_id: str) -> Optional[MonitorTarget]:
        with self._targets_lock:
            return self._targets.get(target_id)

    def get_all_targets(self) -> List[MonitorTarget]:
        with self._targets_lock:
            return list(self._targets.values())

    def get_alerts(
        self,
        target_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Alert]:
        with self._alerts_lock:
            alerts = list(self._alerts)

        if target_id:
            alerts = [a for a in alerts if a.target_id == target_id]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
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
                    alert.resolved_at = datetime.now()
                    return True
        return False

    def _monitor_loop(self) -> None:
        last_checks: Dict[str, float] = {}

        while not self._stop_event.is_set():
            now = time.time()

            with self._targets_lock:
                targets = list(self._targets.values())

            for target in targets:
                if not target.enabled:
                    continue

                last_check = last_checks.get(target.id, 0)
                if now - last_check >= target.interval_seconds:
                    self.check_target(target.id)
                    last_checks[target.id] = now

            self._stop_event.wait(1.0)

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        if not self._running:
            return

        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        self._running = False

    def set_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        self._on_alert = callback

    def get_overall_status(self) -> MonitorStatus:
        with self._targets_lock:
            if not self._targets:
                return MonitorStatus.UNKNOWN

            statuses = [t.status for t in self._targets.values()]

            if any(s == MonitorStatus.CRITICAL for s in statuses):
                return MonitorStatus.CRITICAL
            elif any(s == MonitorStatus.WARNING for s in statuses):
                return MonitorStatus.WARNING
            elif all(s == MonitorStatus.HEALTHY for s in statuses):
                return MonitorStatus.HEALTHY
            else:
                return MonitorStatus.UNKNOWN

    def get_statistics(self) -> Dict[str, Any]:
        with self._targets_lock:
            targets = list(self._targets.values())

        with self._alerts_lock:
            alerts = list(self._alerts)

        return {
            "total_targets": len(targets),
            "enabled_targets": sum(1 for t in targets if t.enabled),
            "healthy": sum(1 for t in targets if t.status == MonitorStatus.HEALTHY),
            "warning": sum(1 for t in targets if t.status == MonitorStatus.WARNING),
            "critical": sum(1 for t in targets if t.status == MonitorStatus.CRITICAL),
            "total_alerts": len(alerts),
            "unacknowledged_alerts": sum(1 for a in alerts if not a.acknowledged),
            "unresolved_alerts": sum(1 for a in alerts if not a.resolved),
            "running": self._running,
        }


def get_monitor() -> Monitor:
    return Monitor()
