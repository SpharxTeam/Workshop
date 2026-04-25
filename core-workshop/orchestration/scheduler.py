"""
任务调度器

提供定时任务调度、周期性任务管理等功能。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set


class ScheduleType(Enum):
    """调度类型"""
    ONCE = auto()
    INTERVAL = auto()
    DAILY = auto()
    WEEKLY = auto()
    MONTHLY = auto()
    CRON = auto()


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class ScheduledTask:
    """调度任务"""

    id: str
    name: str
    func: Callable[..., Any]
    schedule_type: ScheduleType
    next_run: datetime
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    interval_seconds: Optional[float] = None
    cron_expression: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    last_run: Optional[datetime] = None
    last_result: Optional[Any] = None
    last_error: Optional[str] = None
    run_count: int = 0
    error_count: int = 0

    def should_run(self, now: datetime) -> bool:
        if not self.enabled:
            return False
        return now >= self.next_run

    def update_next_run(self) -> None:
        if self.schedule_type == ScheduleType.ONCE:
            return

        if self.schedule_type == ScheduleType.INTERVAL:
            if self.interval_seconds:
                self.next_run = datetime.now() + timedelta(seconds=self.interval_seconds)

        elif self.schedule_type == ScheduleType.DAILY:
            self.next_run = self.next_run + timedelta(days=1)

        elif self.schedule_type == ScheduleType.WEEKLY:
            self.next_run = self.next_run + timedelta(weeks=1)

        elif self.schedule_type == ScheduleType.MONTHLY:
            next_month = self.next_run.month + 1
            next_year = self.next_run.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            self.next_run = self.next_run.replace(year=next_year, month=next_month)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "schedule_type": self.schedule_type.name,
            "next_run": self.next_run.isoformat(),
            "interval_seconds": self.interval_seconds,
            "priority": self.priority.name,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
        }


class Scheduler:
    """任务调度器"""

    _instance: Optional[Scheduler] = None
    _lock = threading.Lock()

    def __new__(cls) -> Scheduler:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tasks: Dict[str, ScheduledTask] = {}
        self._tasks_lock = threading.Lock()
        self._running: bool = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._check_interval = 1.0
        self._on_task_complete: Optional[Callable[[ScheduledTask, Any], None]] = None
        self._on_task_error: Optional[Callable[[ScheduledTask, Exception], None]] = None
        self._initialized = True

    def schedule(
        self,
        name: str,
        func: Callable[..., Any],
        schedule_type: ScheduleType,
        next_run: Optional[datetime] = None,
        interval_seconds: Optional[float] = None,
        cron_expression: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        enabled: bool = True,
        max_retries: int = 3,
    ) -> ScheduledTask:
        import uuid

        task_id = str(uuid.uuid4())[:8]
        task = ScheduledTask(
            id=task_id,
            name=name,
            func=func,
            schedule_type=schedule_type,
            next_run=next_run or datetime.now(),
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            args=args or (),
            kwargs=kwargs or {},
            priority=priority,
            enabled=enabled,
            max_retries=max_retries,
        )

        with self._tasks_lock:
            self._tasks[task_id] = task

        return task

    def schedule_once(
        self,
        name: str,
        func: Callable[..., Any],
        run_at: datetime,
        **kwargs,
    ) -> ScheduledTask:
        return self.schedule(
            name=name,
            func=func,
            schedule_type=ScheduleType.ONCE,
            next_run=run_at,
            **kwargs,
        )

    def schedule_interval(
        self,
        name: str,
        func: Callable[..., Any],
        interval_seconds: float,
        start_at: Optional[datetime] = None,
        **kwargs,
    ) -> ScheduledTask:
        return self.schedule(
            name=name,
            func=func,
            schedule_type=ScheduleType.INTERVAL,
            next_run=start_at or datetime.now(),
            interval_seconds=interval_seconds,
            **kwargs,
        )

    def schedule_daily(
        self,
        name: str,
        func: Callable[..., Any],
        time: str,
        **kwargs,
    ) -> ScheduledTask:
        hour, minute = map(int, time.split(":"))
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        return self.schedule(
            name=name,
            func=func,
            schedule_type=ScheduleType.DAILY,
            next_run=next_run,
            **kwargs,
        )

    def unschedule(self, task_id: str) -> bool:
        with self._tasks_lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        with self._tasks_lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[ScheduledTask]:
        with self._tasks_lock:
            return list(self._tasks.values())

    def enable_task(self, task_id: str) -> bool:
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if task:
                task.enabled = True
                return True
        return False

    def disable_task(self, task_id: str) -> bool:
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if task:
                task.enabled = False
                return True
        return False

    def _run_task(self, task: ScheduledTask) -> None:
        retries = 0
        last_error = None

        while retries <= task.max_retries:
            try:
                result = task.func(*task.args, **task.kwargs)
                task.last_run = datetime.now()
                task.last_result = result
                task.run_count += 1
                task.last_error = None

                if self._on_task_complete:
                    self._on_task_complete(task, result)

                break

            except Exception as e:
                last_error = str(e)
                task.error_count += 1
                retries += 1

                if retries <= task.max_retries:
                    time.sleep(task.retry_delay * retries)

        if last_error:
            task.last_error = last_error
            if self._on_task_error:
                self._on_task_error(task, Exception(last_error))

        task.update_next_run()

    def _scheduler_loop(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now()
            tasks_to_run: List[ScheduledTask] = []

            with self._tasks_lock:
                for task in self._tasks.values():
                    if task.should_run(now):
                        tasks_to_run.append(task)

            tasks_to_run.sort(key=lambda t: t.priority.value, reverse=True)

            for task in tasks_to_run:
                if task.schedule_type == ScheduleType.ONCE:
                    self.unschedule(task.id)
                self._run_task(task)

            self._stop_event.wait(self._check_interval)

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self) -> None:
        if not self._running:
            return

        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
        self._running = False

    def set_callbacks(
        self,
        on_complete: Optional[Callable[[ScheduledTask, Any], None]] = None,
        on_error: Optional[Callable[[ScheduledTask, Exception], None]] = None,
    ) -> None:
        self._on_task_complete = on_complete
        self._on_task_error = on_error

    def get_statistics(self) -> Dict[str, Any]:
        with self._tasks_lock:
            tasks = list(self._tasks.values())

        return {
            "total_tasks": len(tasks),
            "enabled_tasks": sum(1 for t in tasks if t.enabled),
            "running": self._running,
            "total_runs": sum(t.run_count for t in tasks),
            "total_errors": sum(t.error_count for t in tasks),
        }


def get_scheduler() -> Scheduler:
    return Scheduler()
