"""
追踪服务

提供分布式追踪能力，支持 Span 创建、上下文传播、追踪导出等功能。
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar, Union

T = TypeVar("T")


class SpanKind(Enum):
    """Span 类型"""
    INTERNAL = auto()
    SERVER = auto()
    CLIENT = auto()
    PRODUCER = auto()
    CONSUMER = auto()


class SpanStatus(Enum):
    """Span 状态"""
    UNSET = auto()
    OK = auto()
    ERROR = auto()


@dataclass
class SpanContext:
    """Span 上下文"""
    trace_id: str
    span_id: str
    trace_flags: int = 0
    trace_state: Dict[str, str] = field(default_factory=dict)
    is_remote: bool = False

    @classmethod
    def generate(cls) -> SpanContext:
        return cls(
            trace_id=cls._generate_trace_id(),
            span_id=cls._generate_span_id(),
        )

    @staticmethod
    def _generate_trace_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _generate_span_id() -> str:
        return uuid.uuid4().hex[:16]

    def to_w3c_header(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.trace_flags else '00'}"

    @classmethod
    def from_w3c_header(cls, header: str) -> Optional[SpanContext]:
        try:
            parts = header.split("-")
            if len(parts) != 4 or parts[0] != "00":
                return None
            return cls(
                trace_id=parts[1],
                span_id=parts[2],
                trace_flags=int(parts[3], 16),
            )
        except Exception:
            return None


@dataclass
class Span:
    """Span 定义"""
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    parent: Optional[SpanContext] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    links: List[SpanContext] = field(default_factory=list)

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_attributes(self, attrs: Dict[str, Any]) -> None:
        self.attributes.update(attrs)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None, timestamp: Optional[float] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": timestamp or time.time(),
            "attributes": attributes or {},
        })

    def record_exception(self, exception: Exception, attributes: Optional[Dict[str, Any]] = None) -> None:
        self.set_status(SpanStatus.ERROR)
        self.add_event(
            name="exception",
            attributes={
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
                "exception.stacktrace": self._get_stacktrace(exception),
                **(attributes or {}),
            },
        )

    def set_status(self, status: SpanStatus, description: Optional[str] = None) -> None:
        self.status = status
        if description:
            self.attributes["status.description"] = description

    def end(self, end_time: Optional[float] = None) -> None:
        self.end_time = end_time or time.time()

    def duration_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def is_recording(self) -> bool:
        return self.end_time is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "context": {
                "trace_id": self.context.trace_id,
                "span_id": self.context.span_id,
                "trace_flags": self.context.trace_flags,
            },
            "kind": self.kind.name,
            "parent_span_id": self.parent.span_id if self.parent else None,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms(),
            "status": self.status.name,
            "attributes": self.attributes,
            "events": self.events,
        }

    @staticmethod
    def _get_stacktrace(exception: Exception) -> str:
        import traceback
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))


@dataclass
class TraceContext:
    """追踪上下文（线程本地存储）"""
    current_span: Optional[Span] = None
    span_stack: List[Span] = field(default_factory=list)

    def push_span(self, span: Span) -> None:
        if self.current_span:
            self.span_stack.append(self.current_span)
        self.current_span = span

    def pop_span(self) -> Optional[Span]:
        span = self.current_span
        if self.span_stack:
            self.current_span = self.span_stack.pop()
        else:
            self.current_span = None
        return span


class TracingService:
    """追踪服务"""

    _instance: Optional[TracingService] = None
    _lock = threading.Lock()

    def __new__(cls) -> TracingService:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._local = threading.local()
        self._spans: List[Span] = []
        self._max_spans = 10000
        self._span_lock = threading.Lock()
        self._sampling_rate = 1.0
        self._enabled = True
        self._initialized = True

    def _get_context(self) -> TraceContext:
        if not hasattr(self._local, "trace_context"):
            self._local.trace_context = TraceContext()
        return self._local.trace_context

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        if not self._enabled:
            return Span(name=name, context=SpanContext.generate())

        ctx = self._get_context()

        if parent is None and ctx.current_span:
            parent = ctx.current_span.context

        span_context = SpanContext.generate()
        span = Span(
            name=name,
            context=span_context,
            kind=kind,
            parent=parent,
            attributes=attributes or {},
        )

        ctx.push_span(span)
        return span

    def end_span(self, span: Span) -> None:
        if not self._enabled:
            return

        span.end()

        ctx = self._get_context()
        current = ctx.current_span

        if current is span:
            ctx.pop_span()

        with self._span_lock:
            self._spans.append(span)
            if len(self._spans) > self._max_spans:
                self._spans = self._spans[-self._max_spans:]

    def get_current_span(self) -> Optional[Span]:
        return self._get_context().current_span

    def get_current_trace_id(self) -> Optional[str]:
        span = self.get_current_span()
        return span.context.trace_id if span else None

    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Span]:
        span = self.start_span(name, kind=kind, attributes=attributes)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            self.end_span(span)

    def trace(self, name: Optional[str] = None) -> Callable[[Callable[T]], Callable[T]]:
        def decorator(func: Callable[T]) -> Callable[T]:
            span_name = name or func.__name__

            def wrapper(*args, **kwargs) -> T:
                with self.span(span_name):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def inject_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        span = self.get_current_span()
        if span:
            headers["traceparent"] = span.context.to_w3c_header()
            if span.context.trace_state:
                headers["tracestate"] = ",".join(
                    f"{k}={v}" for k, v in span.context.trace_state.items()
                )
        return headers

    def extract_headers(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        traceparent = headers.get("traceparent")
        if traceparent:
            return SpanContext.from_w3c_header(traceparent)
        return None

    def get_spans(
        self,
        trace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Span]:
        with self._span_lock:
            spans = list(self._spans)

        if trace_id:
            spans = [s for s in spans if s.context.trace_id == trace_id]

        return spans[-limit:]

    def get_trace(self, trace_id: str) -> List[Span]:
        return self.get_spans(trace_id=trace_id, limit=1000)

    def export_spans(self, format: str = "json") -> str:
        with self._span_lock:
            spans = [span.to_dict() for span in self._spans]

        if format == "json":
            return json.dumps(spans, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def clear_spans(self) -> int:
        with self._span_lock:
            count = len(self._spans)
            self._spans.clear()
        return count

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_sampling_rate(self, rate: float) -> None:
        self._sampling_rate = max(0.0, min(1.0, rate))

    def get_statistics(self) -> Dict[str, Any]:
        with self._span_lock:
            total_spans = len(self._spans)
            error_spans = sum(1 for s in self._spans if s.status == SpanStatus.ERROR)
            trace_ids = set(s.context.trace_id for s in self._spans)

        return {
            "total_spans": total_spans,
            "error_spans": error_spans,
            "unique_traces": len(trace_ids),
            "enabled": self._enabled,
            "sampling_rate": self._sampling_rate,
        }


def get_tracing_service() -> TracingService:
    return TracingService()


def traced(name: Optional[str] = None) -> Callable[[Callable[T]], Callable[T]]:
    return get_tracing_service().trace(name)
