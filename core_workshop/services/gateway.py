"""
API 网关服务

提供路由、中间件、请求处理等功能。
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union


class HttpMethod(Enum):
    """HTTP 方法"""
    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()
    PATCH = auto()
    HEAD = auto()
    OPTIONS = auto()


@dataclass
class RequestContext:
    """请求上下文"""
    request_id: str
    method: HttpMethod
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    path_params: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    remote_addr: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.headers.get(name.lower(), default)

    def get_query(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.query_params.get(name, default)

    def get_path_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.path_params.get(name, default)

    def json_body(self) -> Any:
        if isinstance(self.body, str):
            try:
                return json.loads(self.body)
            except json.JSONDecodeError:
                return None
        return self.body


@dataclass
class Response:
    """响应"""
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    content_type: str = "application/json"

    def json(self, data: Any) -> "Response":
        self.body = json.dumps(data, ensure_ascii=False)
        self.content_type = "application/json"
        return self

    def text(self, text: str) -> "Response":
        self.body = text
        self.content_type = "text/plain"
        return self

    def html(self, html: str) -> "Response":
        self.body = html
        self.content_type = "text/html"
        return self

    def redirect(self, url: str, status_code: int = 302) -> "Response":
        self.status_code = status_code
        self.headers["Location"] = url
        return self

    @classmethod
    def ok(cls, data: Any = None) -> "Response":
        return cls(status_code=200).json({"success": True, "data": data})

    @classmethod
    def created(cls, data: Any = None) -> "Response":
        return cls(status_code=201).json({"success": True, "data": data})

    @classmethod
    def bad_request(cls, message: str = "Bad Request") -> "Response":
        return cls(status_code=400).json({"success": False, "error": message})

    @classmethod
    def not_found(cls, message: str = "Not Found") -> "Response":
        return cls(status_code=404).json({"success": False, "error": message})

    @classmethod
    def internal_error(cls, message: str = "Internal Server Error") -> "Response":
        return cls(status_code=500).json({"success": False, "error": message})


@dataclass
class Route:
    """路由定义"""
    path: str
    method: HttpMethod
    handler: Callable[[RequestContext], Response]
    name: str = ""
    middlewares: List["Middleware"] = field(default_factory=list)
    description: str = ""

    def match(self, method: HttpMethod, path: str) -> Optional[Dict[str, str]]:
        if self.method != method:
            return None

        route_parts = self.path.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        if len(route_parts) != len(path_parts):
            return None

        params = {}
        for route_part, path_part in zip(route_parts, path_parts):
            if route_part.startswith("{") and route_part.endswith("}"):
                param_name = route_part[1:-1]
                params[param_name] = path_part
            elif route_part != path_part:
                return None

        return params


class Middleware:
    """中间件基类"""

    def before_request(self, ctx: RequestContext) -> Optional[Response]:
        return None

    def after_request(self, ctx: RequestContext, response: Response) -> Response:
        return response

    def on_error(self, ctx: RequestContext, error: Exception) -> Response:
        return Response.internal_error(str(error))


class LoggingMiddleware(Middleware):
    """日志中间件"""

    def __init__(self, logger: Optional[Any] = None):
        self.logger = logger

    def before_request(self, ctx: RequestContext) -> Optional[Response]:
        if self.logger:
            self.logger.info(f"[{ctx.request_id}] {ctx.method.name} {ctx.path}")
        return None

    def after_request(self, ctx: RequestContext, response: Response) -> Response:
        if self.logger:
            self.logger.info(f"[{ctx.request_id}] {response.status_code}")
        return response


class CorsMiddleware(Middleware):
    """CORS 中间件"""

    def __init__(
        self,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = True,
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials

    def after_request(self, ctx: RequestContext, response: Response) -> Response:
        origin = ctx.get_header("origin", "*")

        if "*" in self.allow_origins or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()

        return response


class RateLimitMiddleware(Middleware):
    """速率限制中间件"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def before_request(self, ctx: RequestContext) -> Optional[Response]:
        client_id = ctx.remote_addr or ctx.request_id
        now = time.time()

        with self._lock:
            if client_id not in self._requests:
                self._requests[client_id] = []

            self._requests[client_id] = [
                t for t in self._requests[client_id]
                if now - t < 3600
            ]

            minute_ago = now - 60
            requests_last_minute = sum(1 for t in self._requests[client_id] if t > minute_ago)

            if requests_last_minute >= self.requests_per_minute:
                return Response(
                    status_code=429,
                    body=json.dumps({"error": "Rate limit exceeded (per minute)"}),
                    content_type="application/json",
                )

            hour_ago = now - 3600
            requests_last_hour = sum(1 for t in self._requests[client_id] if t > hour_ago)

            if requests_last_hour >= self.requests_per_hour:
                return Response(
                    status_code=429,
                    body=json.dumps({"error": "Rate limit exceeded (per hour)"}),
                    content_type="application/json",
                )

            self._requests[client_id].append(now)

        return None


class Gateway:
    """API 网关"""

    _instance: Optional[Gateway] = None
    _lock = threading.Lock()

    def __new__(cls) -> Gateway:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._routes: List[Route] = []
        self._middlewares: List[Middleware] = []
        self._routes_lock = threading.Lock()
        self._initialized = True

    def route(
        self,
        path: str,
        method: HttpMethod = HttpMethod.GET,
        name: str = "",
        middlewares: Optional[List[Middleware]] = None,
    ) -> Callable:
        def decorator(handler: Callable[[RequestContext], Response]) -> Callable:
            route = Route(
                path=path,
                method=method,
                handler=handler,
                name=name,
                middlewares=middlewares or [],
            )
            with self._routes_lock:
                self._routes.append(route)
            return handler

        return decorator

    def get(self, path: str, **kwargs) -> Callable:
        return self.route(path, HttpMethod.GET, **kwargs)

    def post(self, path: str, **kwargs) -> Callable:
        return self.route(path, HttpMethod.POST, **kwargs)

    def put(self, path: str, **kwargs) -> Callable:
        return self.route(path, HttpMethod.PUT, **kwargs)

    def delete(self, path: str, **kwargs) -> Callable:
        return self.route(path, HttpMethod.DELETE, **kwargs)

    def add_middleware(self, middleware: Middleware) -> None:
        self._middlewares.append(middleware)

    def add_route(self, route: Route) -> None:
        with self._routes_lock:
            self._routes.append(route)

    def _find_route(self, method: HttpMethod, path: str) -> Optional[tuple]:
        for route in self._routes:
            params = route.match(method, path)
            if params is not None:
                return route, params
        return None

    def handle(self, ctx: RequestContext) -> Response:
        for middleware in self._middlewares:
            response = middleware.before_request(ctx)
            if response:
                return response

        result = self._find_route(ctx.method, ctx.path)

        if result is None:
            response = Response.not_found(f"Route not found: {ctx.method.name} {ctx.path}")
        else:
            route, params = result
            ctx.path_params = params

            for middleware in route.middlewares:
                response = middleware.before_request(ctx)
                if response:
                    break
            else:
                try:
                    response = route.handler(ctx)
                except Exception as e:
                    response = Response.internal_error(str(e))

                    for middleware in reversed(route.middlewares):
                        response = middleware.on_error(ctx, e)

        for middleware in reversed(self._middlewares):
            response = middleware.after_request(ctx, response)

        return response

    def get_routes(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": route.path,
                "method": route.method.name,
                "name": route.name,
                "description": route.description,
            }
            for route in self._routes
        ]


def get_gateway() -> Gateway:
    return Gateway()
