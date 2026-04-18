"""
装饰器工具

提供重试、节流、防抖、缓存等装饰器。
"""

from __future__ import annotations

import functools
import threading
import time
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间增长因子
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        if on_retry:
                            on_retry(e, attempt)

                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return wrapper

    return decorator


def throttle(
    interval: float = 1.0,
    leading: bool = True,
    trailing: bool = True,
):
    """
    节流装饰器

    Args:
        interval: 节流间隔（秒）
        leading: 是否在开始时立即执行
        trailing: 是否在结束后执行最后一次
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        last_call_time: float = 0
        last_args: tuple = ()
        last_kwargs: dict = {}
        pending: bool = False
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            nonlocal last_call_time, last_args, last_kwargs, pending

            with lock:
                current_time = time.time()
                time_since_last = current_time - last_call_time

                last_args = args
                last_kwargs = kwargs

                if time_since_last >= interval:
                    if leading:
                        last_call_time = current_time
                        return func(*args, **kwargs)
                    else:
                        pending = True
                        if not hasattr(wrapper, "_timer"):
                            wrapper._timer = threading.Timer(
                                interval,
                                lambda: _execute_trailing(func, wrapper)
                            )
                            wrapper._timer.start()
                else:
                    pending = True

                return None

        def _execute_trailing(f, w):
            nonlocal last_call_time, last_args, last_kwargs, pending

            with lock:
                if pending and trailing:
                    last_call_time = time.time()
                    pending = False
                    f(*last_args, **last_kwargs)

        return wrapper

    return decorator


def debounce(
    wait: float = 1.0,
    immediate: bool = False,
):
    """
    防抖装饰器

    Args:
        wait: 等待时间（秒）
        immediate: 是否立即执行
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        timer: Optional[threading.Timer] = None
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            nonlocal timer

            def execute():
                nonlocal timer
                with lock:
                    timer = None
                func(*args, **kwargs)

            with lock:
                if timer is not None:
                    timer.cancel()

                if immediate and timer is None:
                    func(*args, **kwargs)

                timer = threading.Timer(wait, execute)
                timer.start()

            return None

        return wrapper

    return decorator


def memoize(
    maxsize: int = 128,
    ttl: Optional[float] = None,
):
    """
    记忆化装饰器

    Args:
        maxsize: 缓存最大大小
        ttl: 缓存过期时间（秒）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: dict = {}
        timestamps: dict = {}
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))

            with lock:
                current_time = time.time()

                if key in cache:
                    if ttl is None or current_time - timestamps[key] < ttl:
                        return cache[key]
                    else:
                        del cache[key]
                        del timestamps[key]

                if maxsize > 0 and len(cache) >= maxsize:
                    oldest_key = min(timestamps, key=timestamps.get)
                    del cache[oldest_key]
                    del timestamps[oldest_key]

                result = func(*args, **kwargs)
                cache[key] = result
                timestamps[key] = current_time

                return result

        wrapper.cache_clear = lambda: (cache.clear(), timestamps.clear())
        wrapper.cache_info = lambda: {"size": len(cache), "maxsize": maxsize}

        return wrapper

    return decorator


def timed(
    logger: Optional[Any] = None,
    level: str = "INFO",
    message: Optional[str] = None,
):
    """
    计时装饰器

    Args:
        logger: 日志记录器
        level: 日志级别
        message: 自定义消息
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                msg = message or f"{func.__name__} 执行耗时: {duration:.4f}秒"

                if logger:
                    log_method = getattr(logger, level.lower(), logger.info)
                    log_method(msg)
                else:
                    print(msg)

        return wrapper

    return decorator


def deprecated(
    message: Optional[str] = None,
    version: Optional[str] = None,
):
    """
    废弃警告装饰器

    Args:
        message: 自定义警告消息
        version: 废弃版本
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            import warnings

            msg = message or f"{func.__name__} 已废弃"
            if version:
                msg += f"，将在版本 {version} 中移除"

            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_args(*validators, **kwvalidators):
    """
    参数验证装饰器

    Args:
        validators: 位置参数验证器
        kwvalidators: 关键字参数验证器
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for i, validator in enumerate(validators):
                if i < len(args):
                    if not validator(args[i]):
                        raise ValueError(f"参数 {i} 验证失败")

            for key, validator in kwvalidators.items():
                if key in kwargs:
                    if not validator(kwargs[key]):
                        raise ValueError(f"参数 '{key}' 验证失败")

            return func(*args, **kwargs)

        return wrapper

    return decorator
