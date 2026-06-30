"""
函数式工具

提供单例模式、计时器、限流器等函数式工具。
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Generator, Optional, TypeVar

T = TypeVar("T")


class SingletonMeta(type):
    """单例元类"""

    _instances: dict = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class Singleton(metaclass=SingletonMeta):
    """单例基类"""

    @classmethod
    def get_instance(cls) -> "Singleton":
        return cls()

    @classmethod
    def reset_instance(cls) -> None:
        with cls._lock:
            if cls in cls._instances:
                del cls._instances[cls]


class TimerState(Enum):
    """计时器状态"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()


@dataclass
class Timer:
    """计时器"""

    name: str = ""
    _start_time: Optional[float] = field(default=None, repr=False)
    _elapsed: float = field(default=0.0, repr=False)
    _state: TimerState = field(default=TimerState.IDLE, repr=False)

    def start(self) -> "Timer":
        if self._state == TimerState.RUNNING:
            return self

        self._start_time = time.time()
        self._state = TimerState.RUNNING
        return self

    def pause(self) -> "Timer":
        if self._state != TimerState.RUNNING:
            return self

        self._elapsed += time.time() - (self._start_time or 0)
        self._state = TimerState.PAUSED
        return self

    def resume(self) -> "Timer":
        if self._state != TimerState.PAUSED:
            return self

        self._start_time = time.time()
        self._state = TimerState.RUNNING
        return self

    def stop(self) -> float:
        if self._state == TimerState.STOPPED:
            return self._elapsed

        if self._state == TimerState.RUNNING:
            self._elapsed += time.time() - (self._start_time or 0)

        self._state = TimerState.STOPPED
        return self._elapsed

    def reset(self) -> "Timer":
        self._start_time = None
        self._elapsed = 0.0
        self._state = TimerState.IDLE
        return self

    @property
    def elapsed(self) -> float:
        if self._state == TimerState.RUNNING:
            return self._elapsed + time.time() - (self._start_time or 0)
        return self._elapsed

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed * 1000

    @property
    def is_running(self) -> bool:
        return self._state == TimerState.RUNNING

    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


class ContextTimer:
    """上下文计时器"""

    _timers: dict = {}
    _lock = threading.Lock()

    @classmethod
    @contextmanager
    def measure(
        cls,
        name: str,
    ) -> Generator[Timer, None, None]:
        timer = Timer(name=name)
        timer.start()

        try:
            yield timer
        finally:
            elapsed = timer.stop()

            with cls._lock:
                if name not in cls._timers:
                    cls._timers[name] = []
                cls._timers[name].append(elapsed)

    @classmethod
    def get_stats(cls, name: str) -> Optional[dict]:
        with cls._lock:
            if name not in cls._timers:
                return None

            times = cls._timers[name]
            if not times:
                return None

            return {
                "count": len(times),
                "total": sum(times),
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
            }

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._timers.clear()


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_closed(self) -> bool:
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._transition_to_half_open()
                return False
            return True
        return False

    def _should_attempt_recovery(self) -> bool:
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout

    def _transition_to_half_open(self) -> None:
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        if self.is_open:
            raise RuntimeError("熔断器处于打开状态")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class RateLimiter:
    """速率限制器"""

    def __init__(
        self,
        rate: float,
        capacity: Optional[int] = None,
    ):
        self.rate = rate
        self.capacity = capacity or int(rate)

        self._tokens = float(self.capacity)
        self._last_update = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self._last_update
        self._tokens = min(
            self.capacity,
            self._tokens + elapsed * self.rate,
        )
        self._last_update = now

    def acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    def wait(self, tokens: int = 1) -> float:
        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0

            needed = tokens - self._tokens
            wait_time = needed / self.rate
            return wait_time

    @contextmanager
    def limit(self, tokens: int = 1):
        wait_time = self.wait(tokens)
        if wait_time > 0:
            time.sleep(wait_time)
        yield
