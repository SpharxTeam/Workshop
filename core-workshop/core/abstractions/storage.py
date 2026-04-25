"""
Storage Abstractions - V3.0
==========================

存储后端抽象接口

参考:
    - AgentOS IO 模块
    - Deepness Storage Service
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
from enum import Enum


class StorageBackendType(Enum):
    """存储后端类型"""
    LOCAL = "local"
    S3 = "s3"
    OSS = "oss"
    AZURE = "azure"
    GCS = "gcs"
    MEMORY = "memory"


class CompressionFormat(Enum):
    """压缩格式"""
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    BZ2 = "bz2"
    LZ4 = "lz4"


@dataclass
class FileMetadata:
    """文件元数据"""
    path: str
    size: int
    created_time: float
    modified_time: float
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    encoding: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'size': self.size,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'mime_type': self.mime_type,
            'checksum': self.checksum,
            'encoding': self.encoding,
            'extra': self.extra,
        }


@dataclass
class IOResult:
    """I/O 操作结果"""
    success: bool
    path: str
    operation: str
    data: Optional[bytes] = None
    metadata: Optional[FileMetadata] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    bytes_transferred: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'path': self.path,
            'operation': self.operation,
            'error': self.error,
            'duration_ms': self.duration_ms,
            'bytes_transferred': self.bytes_transferred,
        }


class IStorageBackend(ABC):
    """
    存储后端抽象接口 - V3.0
    
    所有存储后端必须实现此接口
    """

    @property
    @abstractmethod
    def backend_type(self) -> StorageBackendType:
        """后端类型"""
        pass

    @abstractmethod
    def read(self, path: str) -> IOResult:
        """
        读取文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            IOResult: 操作结果
        """
        pass

    @abstractmethod
    def write(self, path: str, data: bytes, metadata: Optional[Dict] = None) -> IOResult:
        """
        写入文件
        
        Args:
            path: 文件路径
            data: 文件内容
            metadata: 元数据
            
        Returns:
            IOResult: 操作结果
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否存在
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> IOResult:
        """
        删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            IOResult: 操作结果
        """
        pass

    @abstractmethod
    def list_files(self, directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
        """
        列出目录下的文件
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            recursive: 是否递归
            
        Returns:
            List[str]: 文件路径列表
        """
        pass

    @abstractmethod
    def get_metadata(self, path: str) -> Optional[FileMetadata]:
        """
        获取文件元数据
        
        Args:
            path: 文件路径
            
        Returns:
            FileMetadata: 文件元数据
        """
        pass

    @abstractmethod
    def copy(self, src: str, dst: str) -> IOResult:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            IOResult: 操作结果
        """
        pass

    @abstractmethod
    def move(self, src: str, dst: str) -> IOResult:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            IOResult: 操作结果
        """
        pass

    @abstractmethod
    def create_directory(self, path: str) -> IOResult:
        """
        创建目录
        
        Args:
            path: 目录路径
            
        Returns:
            IOResult: 操作结果
        """
        pass

    @abstractmethod
    def delete_directory(self, path: str, recursive: bool = False) -> IOResult:
        """
        删除目录
        
        Args:
            path: 目录路径
            recursive: 是否递归删除
            
        Returns:
            IOResult: 操作结果
        """
        pass


class LocalStorageBackend(IStorageBackend):
    """本地文件系统存储后端"""

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化本地存储后端
        
        Args:
            base_path: 基础路径
        """
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._backend_type = StorageBackendType.LOCAL

    @property
    def backend_type(self) -> StorageBackendType:
        return self._backend_type

    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        p = Path(path)
        if not p.is_absolute():
            p = self._base_path / p
        return p.resolve()

    def read(self, path: str) -> IOResult:
        import time
        start = time.time()
        
        try:
            full_path = self._resolve_path(path)
            with open(full_path, 'rb') as f:
                data = f.read()
            
            return IOResult(
                success=True,
                path=str(full_path),
                operation='read',
                data=data,
                metadata=self.get_metadata(path),
                duration_ms=(time.time() - start) * 1000,
                bytes_transferred=len(data),
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=path,
                operation='read',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def write(self, path: str, data: bytes, metadata: Optional[Dict] = None) -> IOResult:
        import time
        start = time.time()
        
        try:
            full_path = self._resolve_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(data)
            
            return IOResult(
                success=True,
                path=str(full_path),
                operation='write',
                metadata=self.get_metadata(path),
                duration_ms=(time.time() - start) * 1000,
                bytes_transferred=len(data),
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=path,
                operation='write',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def exists(self, path: str) -> bool:
        return self._resolve_path(path).exists()

    def delete(self, path: str) -> IOResult:
        import time
        start = time.time()
        
        try:
            full_path = self._resolve_path(path)
            full_path.unlink()
            
            return IOResult(
                success=True,
                path=str(full_path),
                operation='delete',
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=path,
                operation='delete',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def list_files(self, directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
        full_path = self._resolve_path(directory)
        
        if recursive:
            return [str(p) for p in full_path.rglob(pattern) if p.is_file()]
        else:
            return [str(p) for p in full_path.glob(pattern) if p.is_file()]

    def get_metadata(self, path: str) -> Optional[FileMetadata]:
        try:
            import os
            full_path = self._resolve_path(path)
            stat = full_path.stat()
            
            return FileMetadata(
                path=str(full_path),
                size=stat.st_size,
                created_time=stat.st_ctime,
                modified_time=stat.st_mtime,
            )
        except Exception:
            return None

    def copy(self, src: str, dst: str) -> IOResult:
        import time
        import shutil
        start = time.time()
        
        try:
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, dst_path)
            
            return IOResult(
                success=True,
                path=str(dst_path),
                operation='copy',
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=dst,
                operation='copy',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def move(self, src: str, dst: str) -> IOResult:
        import time
        import shutil
        start = time.time()
        
        try:
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return IOResult(
                success=True,
                path=str(dst_path),
                operation='move',
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=dst,
                operation='move',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def create_directory(self, path: str) -> IOResult:
        import time
        start = time.time()
        
        try:
            full_path = self._resolve_path(path)
            full_path.mkdir(parents=True, exist_ok=True)
            
            return IOResult(
                success=True,
                path=str(full_path),
                operation='create_directory',
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=path,
                operation='create_directory',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def delete_directory(self, path: str, recursive: bool = False) -> IOResult:
        import time
        import shutil
        start = time.time()
        
        try:
            full_path = self._resolve_path(path)
            
            if recursive:
                shutil.rmtree(full_path)
            else:
                full_path.rmdir()
            
            return IOResult(
                success=True,
                path=str(full_path),
                operation='delete_directory',
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return IOResult(
                success=False,
                path=path,
                operation='delete_directory',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
