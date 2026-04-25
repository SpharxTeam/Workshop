"""
任务队列

提供异步任务队列、工作线程池等功能。
"""

from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    RETRYING = auto()


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.name,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }


@dataclass
class Task:
    """任务定义"""
    id: str
    func: Callable[..., Any]
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None

    def __lt__(self, other: "Task") -> bool:
        return self.priority > other.priority


class Worker:
    """工作线程"""

    def __init__(
        self,
        worker_id: int,
        task_queue: TaskQueue,
    ):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._current_task: Optional[Task] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        while self._running:
            try:
                task = self.task_queue._queue.get(timeout=1.0)
                self._current_task = task
                self._execute_task(task)
                self.task_queue._queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                continue

    def _execute_task(self, task: Task) -> None:
        task.status = TaskStatus.RUNNING
        start_time = datetime.now()
        retries = 0
        last_error = None

        while retries <= task.max_retries:
            try:
                if task.timeout:
                    import signal

                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"任务超时 ({task.timeout}秒)")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(task.timeout))

                result = task.func(*task.args, **task.kwargs)

                if task.timeout:
                    signal.alarm(0)

                task.status = TaskStatus.COMPLETED
                task.result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    start_time=start_time,
                    end_time=datetime.now(),
                    retries=retries,
                )
                task.result.duration_ms = (task.result.end_time - start_time).total_seconds() * 1000

                with self.task_queue._results_lock:
                    self.task_queue._results[task.id] = task.result

                return

            except Exception as e:
                last_error = str(e)
                retries += 1
                task.status = TaskStatus.RETRYING

                if retries <= task.max_retries:
                    time.sleep(task.retry_delay * retries)

        task.status = TaskStatus.FAILED
        task.result = TaskResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            error=last_error,
            start_time=start_time,
            end_time=datetime.now(),
            retries=retries - 1,
        )

        with self.task_queue._results_lock:
            self.task_queue._results[task.id] = task.result


class TaskQueue:
    """任务队列"""

    _instance: Optional[TaskQueue] = None
    _lock = threading.Lock()

    def __new__(cls) -> TaskQueue:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._workers: List[Worker] = []
        self._results: Dict[str, TaskResult] = {}
        self._results_lock = threading.Lock()
        self._max_workers = 4
        self._running = False
        self._initialized = True

    def submit(
        self,
        func: Callable[..., Any],
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
    ) -> str:
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            func=func,
            args=args or (),
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )

        self._queue.put(task)
        return task_id

    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        start_time = time.time()

        while True:
            with self._results_lock:
                if task_id in self._results:
                    return self._results[task_id]

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None

            time.sleep(0.1)

    def wait(self, task_id: str, timeout: Optional[float] = None) -> Any:
        result = self.get_result(task_id, timeout)

        if result is None:
            raise TimeoutError(f"等待任务 {task_id} 超时")

        if result.status == TaskStatus.FAILED:
            raise RuntimeError(f"任务失败: {result.error}")

        return result.result

    def start(self, num_workers: Optional[int] = None) -> None:
        if self._running:
            return

        self._max_workers = num_workers or self._max_workers
        self._running = True

        for i in range(self._max_workers):
            worker = Worker(i, self)
            worker.start()
            self._workers.append(worker)

    def stop(self, wait: bool = True) -> None:
        if not self._running:
            return

        for worker in self._workers:
            worker.stop()

        if wait:
            for worker in self._workers:
                if worker._thread:
                    worker._thread.join(timeout=5.0)

        self._workers.clear()
        self._running = False

    def get_queue_size(self) -> int:
        return self._queue.qsize()

    def get_pending_count(self) -> int:
        return self._queue.unfinished_tasks

    def clear_results(self) -> int:
        with self._results_lock:
            count = len(self._results)
            self._results.clear()
        return count

    def get_statistics(self) -> Dict[str, Any]:
        with self._results_lock:
            results = list(self._results.values())

        return {
            "queue_size": self.get_queue_size(),
            "workers": len(self._workers),
            "running": self._running,
            "total_tasks": len(results),
            "completed": sum(1 for r in results if r.status == TaskStatus.COMPLETED),
            "failed": sum(1 for r in results if r.status == TaskStatus.FAILED),
        }


def get_task_queue() -> TaskQueue:
    return TaskQueue()
