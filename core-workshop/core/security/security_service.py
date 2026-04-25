"""
安全审计服务

提供安全上下文管理、权限控制、审计日志记录等功能。
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4


class AuditLevel(Enum):
    """审计级别"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class Permission(Enum):
    """权限枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    CONFIGURE = "configure"
    EXPORT = "export"
    IMPORT = "import"


@dataclass
class Role:
    """角色定义"""
    name: str
    permissions: Set[Permission]
    description: str = ""
    inherits: Optional[List[str]] = None

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions or Permission.ADMIN in self.permissions


@dataclass
class SecurityAuditLog:
    """安全审计日志"""
    id: str
    timestamp: datetime
    level: AuditLevel
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    resource: Optional[str]
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class SecurityContext:
    """安全上下文"""
    user_id: str
    session_id: str
    roles: List[str] = field(default_factory=list)
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions or Permission.ADMIN in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        return all(self.has_permission(p) for p in permissions)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "roles": self.roles,
            "permissions": [p.value for p in self.permissions],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }


class SecurityService:
    """安全服务"""

    _instance: Optional[SecurityService] = None
    _lock = threading.Lock()

    DEFAULT_ROLES: Dict[str, Role] = {
        "admin": Role(
            name="admin",
            permissions={Permission.ADMIN, Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE, Permission.CONFIGURE},
            description="管理员角色，拥有所有权限"
        ),
        "operator": Role(
            name="operator",
            permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
            description="操作员角色，可以读写和执行"
        ),
        "viewer": Role(
            name="viewer",
            permissions={Permission.READ},
            description="查看者角色，只能读取"
        ),
        "exporter": Role(
            name="exporter",
            permissions={Permission.READ, Permission.EXPORT},
            description="导出者角色，可以读取和导出"
        ),
    }

    def __new__(cls) -> SecurityService:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._roles: Dict[str, Role] = dict(self.DEFAULT_ROLES)
        self._contexts: Dict[str, SecurityContext] = {}
        self._audit_logs: List[SecurityAuditLog] = []
        self._max_audit_logs = 10000
        self._session_timeout = 3600
        self._context_lock = threading.Lock()
        self._audit_lock = threading.Lock()
        self._initialized = True

    def create_context(
        self,
        user_id: str,
        roles: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_timeout: Optional[int] = None,
    ) -> SecurityContext:
        session_id = self._generate_session_id()
        role_names = roles or ["viewer"]
        permissions: Set[Permission] = set()

        for role_name in role_names:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.permissions)

        timeout = session_timeout or self._session_timeout
        expires_at = datetime.fromtimestamp(time.time() + timeout)

        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            roles=role_names,
            permissions=permissions,
            metadata=metadata or {},
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        with self._context_lock:
            self._contexts[session_id] = context

        self._log_audit(
            level=AuditLevel.INFO,
            event_type="session_created",
            user_id=user_id,
            session_id=session_id,
            action="create_session",
            details={"roles": role_names},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return context

    def get_context(self, session_id: str) -> Optional[SecurityContext]:
        with self._context_lock:
            context = self._contexts.get(session_id)
            if context and context.is_expired():
                del self._contexts[session_id]
                self._log_audit(
                    level=AuditLevel.INFO,
                    event_type="session_expired",
                    user_id=context.user_id,
                    session_id=session_id,
                    action="expire_session",
                    details={},
                )
                return None
            return context

    def refresh_context(self, session_id: str, timeout: Optional[int] = None) -> Optional[SecurityContext]:
        with self._context_lock:
            context = self._contexts.get(session_id)
            if context is None:
                return None

            if context.is_expired():
                del self._contexts[session_id]
                return None

            timeout = timeout or self._session_timeout
            context.expires_at = datetime.fromtimestamp(time.time() + timeout)
            return context

    def destroy_context(self, session_id: str) -> bool:
        with self._context_lock:
            context = self._contexts.pop(session_id, None)
            if context:
                self._log_audit(
                    level=AuditLevel.INFO,
                    event_type="session_destroyed",
                    user_id=context.user_id,
                    session_id=session_id,
                    action="destroy_session",
                    details={},
                )
                return True
            return False

    def check_permission(
        self,
        session_id: str,
        permission: Permission,
        resource: Optional[str] = None,
    ) -> bool:
        context = self.get_context(session_id)
        if context is None:
            self._log_audit(
                level=AuditLevel.WARNING,
                event_type="permission_check_failed",
                user_id=None,
                session_id=session_id,
                resource=resource,
                action="check_permission",
                details={"permission": permission.value},
                success=False,
                error_message="会话不存在或已过期",
            )
            return False

        has_permission = context.has_permission(permission)

        self._log_audit(
            level=AuditLevel.DEBUG if has_permission else AuditLevel.WARNING,
            event_type="permission_check",
            user_id=context.user_id,
            session_id=session_id,
            resource=resource,
            action="check_permission",
            details={"permission": permission.value, "granted": has_permission},
            success=has_permission,
        )

        return has_permission

    def require_permission(
        self,
        session_id: str,
        permission: Permission,
        resource: Optional[str] = None,
    ) -> SecurityContext:
        context = self.get_context(session_id)
        if context is None:
            raise PermissionError("会话不存在或已过期")

        if not context.has_permission(permission):
            self._log_audit(
                level=AuditLevel.ERROR,
                event_type="permission_denied",
                user_id=context.user_id,
                session_id=session_id,
                resource=resource,
                action="require_permission",
                details={"permission": permission.value},
                success=False,
                error_message=f"缺少权限: {permission.value}",
            )
            raise PermissionError(f"缺少权限: {permission.value}")

        return context

    def register_role(self, role: Role) -> None:
        self._roles[role.name] = role
        self._log_audit(
            level=AuditLevel.INFO,
            event_type="role_registered",
            user_id=None,
            session_id=None,
            action="register_role",
            details={"role": role.name, "permissions": [p.value for p in role.permissions]},
        )

    def get_role(self, name: str) -> Optional[Role]:
        return self._roles.get(name)

    def list_roles(self) -> List[str]:
        return list(self._roles.keys())

    def _log_audit(
        self,
        level: AuditLevel,
        event_type: str,
        user_id: Optional[str],
        session_id: Optional[str],
        action: str,
        details: Dict[str, Any],
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> SecurityAuditLog:
        log = SecurityAuditLog(
            id=str(uuid4()),
            timestamp=datetime.now(),
            level=level,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            resource=resource,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

        with self._audit_lock:
            self._audit_logs.append(log)
            if len(self._audit_logs) > self._max_audit_logs:
                self._audit_logs = self._audit_logs[-self._max_audit_logs:]

        return log

    def log_event(
        self,
        level: AuditLevel,
        event_type: str,
        action: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
    ) -> SecurityAuditLog:
        context = self.get_context(session_id) if session_id else None

        return self._log_audit(
            level=level,
            event_type=event_type,
            user_id=context.user_id if context else None,
            session_id=session_id,
            resource=resource,
            action=action,
            details=details,
            ip_address=context.ip_address if context else None,
            user_agent=context.user_agent if context else None,
        )

    def get_audit_logs(
        self,
        level: Optional[AuditLevel] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SecurityAuditLog]:
        with self._audit_lock:
            logs = list(self._audit_logs)

        filtered = []
        for log in logs:
            if level and log.level != level:
                continue
            if event_type and log.event_type != event_type:
                continue
            if user_id and log.user_id != user_id:
                continue
            if session_id and log.session_id != session_id:
                continue
            if resource and log.resource != resource:
                continue
            if start_time and log.timestamp < start_time:
                continue
            if end_time and log.timestamp > end_time:
                continue
            filtered.append(log)

        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered[:limit]

    def export_audit_logs(self, format: str = "json") -> str:
        with self._audit_lock:
            logs = [log.to_dict() for log in self._audit_logs]

        if format == "json":
            return json.dumps(logs, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def _generate_session_id(self) -> str:
        return secrets.token_urlsafe(32)

    def generate_token(self, data: Dict[str, Any], secret: Optional[str] = None) -> str:
        secret = secret or os.environ.get("WORKSHOP_SECRET", "default-secret-key")
        payload = json.dumps(data, sort_keys=True)
        signature = hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()
        return f"{payload}|{signature}"

    def verify_token(self, token: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            secret = secret or os.environ.get("WORKSHOP_SECRET", "default-secret-key")
            payload, signature = token.rsplit("|", 1)
            expected_signature = hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()

            if not secrets.compare_digest(signature, expected_signature):
                return None

            return json.loads(payload)
        except Exception:
            return None

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        salt = salt or secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000
        )
        return f"{salt}:{hashed.hex()}"

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            salt, stored_hash = hashed.split(":")
            computed = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                100000
            )
            return secrets.compare_digest(computed.hex(), stored_hash)
        except Exception:
            return False

    def cleanup_expired_sessions(self) -> int:
        count = 0
        with self._context_lock:
            expired = [
                sid for sid, ctx in self._contexts.items()
                if ctx.is_expired()
            ]
            for sid in expired:
                del self._contexts[sid]
                count += 1

        if count > 0:
            self._log_audit(
                level=AuditLevel.INFO,
                event_type="sessions_cleaned",
                user_id=None,
                session_id=None,
                action="cleanup_sessions",
                details={"count": count},
            )

        return count

    def get_statistics(self) -> Dict[str, Any]:
        with self._context_lock:
            active_sessions = len(self._contexts)
            expired_sessions = sum(1 for ctx in self._contexts.values() if ctx.is_expired())

        with self._audit_lock:
            total_logs = len(self._audit_logs)
            error_logs = sum(1 for log in self._audit_logs if log.level in (AuditLevel.ERROR, AuditLevel.CRITICAL))

        return {
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "total_audit_logs": total_logs,
            "error_audit_logs": error_logs,
            "registered_roles": len(self._roles),
        }


def get_security_service() -> SecurityService:
    return SecurityService()


def permission_required(permission: Permission):
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            session_id = kwargs.get("session_id")
            if session_id is None:
                raise PermissionError("缺少会话ID")

            security = get_security_service()
            security.require_permission(session_id, permission)

            return func(*args, **kwargs)
        return wrapper
    return decorator
