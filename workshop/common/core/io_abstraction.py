# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# IO 抽象层 - 统一文件/云存储接口
# 参考 AgentOS 资源管理设计，提供高性能、安全的数据IO抽象

import os
import sys
import json
import hashlib
import time
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, BinaryIO, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum, auto
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    ConfigManager,
    setup_logging,
    InputValidator,
    ErrorCode,
    DataIOError,
    WorkshopError,
    error_code_manager
)

T = TypeVar('T')


class StorageBackend(Enum):
    """存储后端类型"""
    LOCAL = "local"
    OSS = "oss"  # 阿里云对象存储
    S3 = "s3"   # AWS S3
    GCS = "gcs" # Google Cloud Storage
    AZURE = "azure"  # Azure Blob Storage


class CompressionFormat(Enum):
    """压缩格式"""
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    LZ4 = "lz4"  # 高性能压缩
    ZSTD = "zstd"  # Zstandard 压缩


@dataclass
class FileMetadata:
    """文件元数据"""
    path: str
    size_bytes: int = 0
    content_type: str = ""
    created_at: float = 0.0
    modified_at: float = 0.0
    checksum_md5: str = ""
    checksum_sha256: str = ""
    compression: CompressionFormat = CompressionFormat.NONE
    custom_metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'size_bytes': self.size_bytes,
            'content_type': self.content_type,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'checksum_md5': self.checksum_md5,
            'checksum_sha256': self.checksum_sha256,
            'compression': self.compression.value,
            'custom_metadata': self.custom_metadata
        }


@dataclass
class IOResult:
    """IO操作结果"""
    success: bool
    operation: str  # read/write/delete/list
    path: str = ""
    bytes_transferred: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Optional[FileMetadata] = None
    
    @property
    def throughput_mbps(self) -> float:
        if self.duration_ms == 0:
            return 0.0
        return (self.bytes_transferred * 8) / (self.duration_ms / 1000) / 1e6


class IStorageBackend(ABC):
    """
    存储后端接口 - 参考 AgentOS 资源抽象设计
    
    所有存储实现必须继承此类，提供统一的读写接口。
    
    设计原则：
    - K-3 服务隔离：存储细节与业务逻辑解耦
    - E-6 错误可追溯：完整的错误链和上下文
    - 性能可观测：自动收集IO指标
    """
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        pass
    
    @abstractmethod
    def read(self, path: str, mode: str = "rb") -> bytes:
        """读取文件内容"""
        pass
    
    @abstractmethod
    def write(self, path: str, data: Union[bytes, str], mode: str = "wb") -> int:
        """写入数据，返回写入字节数"""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """删除文件或目录"""
        pass
    
    @abstractmethod
    def list_files(self, directory: str, pattern: str = "*") -> List[FileMetadata]:
        """列出目录中的文件"""
        pass
    
    @abstractmethod
    def get_metadata(self, path: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        pass
    
    @abstractmethod
    def get_size(self, path: str) -> int:
        """获取文件大小（字节）"""
        pass
    
    # 可选方法（子类可按需覆盖）
    
    def copy(self, src: str, dst: str) -> bool:
        """复制文件"""
        raise NotImplementedError(f"{self.__class__.__name__} 不支持 copy 操作")
    
    def move(self, src: str, dst: str) -> bool:
        """移动/重命名文件"""
        raise NotImplementedError(f"{self.__class__.__name__} 不支持 move 操作")
    
    def create_directory(self, path: str) -> bool:
        """创建目录"""
        raise NotImplementedError(f"{self.__class__.__name__} 不支持 create_directory")


class LocalStorageBackend(IStorageBackend):
    """
    本地文件系统存储后端
    
    特性：
    - 完整的路径安全性验证
    - 自动元数据收集
    - 性能指标记录
    - 支持压缩透明处理
    """
    
    def __init__(self, base_path: str = "/app"):
        self._base_path = Path(base_path)
        self._connected = False
        self._logger = setup_logging("io.local")
        self._validator = InputValidator()
        
        # 性能统计
        self._stats = {
            'reads': 0,
            'writes': 0,
            'bytes_read': 0,
            'bytes_written': 0,
            'total_time_ms': 0
        }
    
    def connect(self, config: Dict[str, Any] = None) -> bool:
        try:
            self._base_path.mkdir(parents=True, exist_ok=True)
            self._connected = True
            self._logger.info(f"本地存储已连接: {self._base_path}")
            return True
        except Exception as e:
            self._logger.error(f"本地存储连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        self._connected = False
        self._logger.info("本地存储已断开")
    
    def _validate_path(self, path: str, must_exist: bool = False) -> Path:
        """验证并解析路径（防路径遍历攻击）"""
        full_path = self._base_path / path
        
        # 安全性检查：确保路径在 base_path 内
        try:
            full_path.resolve().relative_to(self._base_path.resolve())
        except ValueError:
            raise DataIOError(
                ErrorCode.IO_ERROR,
                f"路径遍历攻击检测: {path}",
                attempted_path=str(full_path.resolve()),
                allowed_base=str(self._base_path.resolve())
            )
        
        if must_exist and not full_path.exists():
            raise DataIOError(
                ErrorCode.FILE_NOT_FOUND,
                f"路径不存在: {path}"
            )
        
        return full_path
    
    def exists(self, path: str) -> bool:
        try:
            resolved = self._validate_path(path)
            return resolved.exists()
        except Exception:
            return False
    
    def read(self, path: str, mode: str = "rb") -> bytes:
        start_time = time.time()
        
        try:
            file_path = self._validate_path(path, must_exist=True)
            
            with open(file_path, mode) as f:
                data = f.read()
            
            duration = (time.time() - start_time) * 1000
            
            self._update_stats('read', len(data), duration)
            
            self._logger.debug(
                f"读取完成: {path} "
                f"(大小: {len(data)} 字节, 耗时: {duration:.2f}ms)"
            )
            
            return data
            
        except DataIOError:
            raise
        except Exception as e:
            error_code_manager.record_error(DataIOError(ErrorCode.READ_ERROR, str(e), cause=e))
            raise DataIOError(ErrorCode.READ_ERROR, f"读取失败: {path} ({e})", cause=e)
    
    def write(self, path: str, data: Union[bytes, str], mode: str = "wb") -> int:
        start_time = time.time()
        
        try:
            file_path = self._validate_path(path)
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            with open(file_path, mode) as f:
                written = f.write(data)
            
            duration = (time.time() - start_time) * 1000
            
            self._update_stats('write', written, duration)
            
            self._logger.debug(
                f"写入完成: {path} "
                f"(大小: {written} 字节, 耗时: {duration:.2f}ms)"
            )
            
            return written
            
        except DataIOError:
            raise
        except Exception as e:
            error_code_manager.record_error(DataIOError(ErrorCode.WRITE_ERROR, str(e), cause=e))
            raise DataIOError(ErrorCode.WRITE_ERROR, f"写入失败: {path} ({e})", cause=e)
    
    def delete(self, path: str) -> bool:
        try:
            file_path = self._validate_path(path, must_exist=True)
            
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
            else:
                return False
            
            self._logger.debug(f"删除成功: {path}")
            return True
            
        except DataIOError:
            raise
        except Exception as e:
            error_code_manager.record_error(DataIOError(ErrorCode.IO_ERROR, str(e), cause=e))
            raise DataIOError(ErrorCode.IO_ERROR, f"删除失败: {path} ({e})", cause=e)
    
    def list_files(self, directory: str, pattern: str = "*") -> List[FileMetadata]:
        try:
            dir_path = self._validate_path(directory, must_exist=True)
            
            files = []
            for file_path in sorted(dir_path.glob(pattern)):
                if file_path.is_file():
                    metadata = self.get_metadata(str(file_path.relative_to(self._base_path)))
                    if metadata:
                        files.append(metadata)
            
            return files
            
        except DataIOError:
            raise
        except Exception as e:
            error_code_manager.record_error(DataIOError(ErrorCode.IO_ERROR, str(e), cause=e))
            raise DataIOError(ErrorCode.IO_ERROR, f"列出文件失败: {directory}", cause=e)
    
    def get_metadata(self, path: str) -> Optional[FileMetadata]:
        try:
            file_path = self._validate_path(path, must_exist=True)
            
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # 计算校验和（可选，对于大文件可能耗时）
            checksum_md5 = ""
            if stat.st_size < 10 * 1024 * 1024:  # 小于10MB才计算
                with open(file_path, 'rb') as f:
                    checksum_md5 = hashlib.md5(f.read()).hexdigest()
            
            return FileMetadata(
                path=path,
                size_bytes=stat.st_size,
                content_type=mime_type or "application/octet-stream",
                created_at=stat.st_ctime,
                modified_at=stat.st_mtime,
                checksum_md5=checksum_md5
            )
            
        except DataIOError:
            raise
        except Exception as e:
            self._logger.warning(f"获取元数据失败: {path} - {e}")
            return None
    
    def get_size(self, path: str) -> int:
        try:
            file_path = self._validate_path(path, must_exist=True)
            return file_path.stat().st_size
        except DataIOError:
            raise
        except Exception as e:
            raise DataIOError(ErrorCode.IO_ERROR, f"获取大小失败: {path}", cause=e)
    
    def copy(self, src: str, dst: str) -> bool:
        try:
            src_path = self._validate_path(src, must_exist=True)
            dst_path = self._validate_path(dst)
            
            import shutil
            shutil.copy2(src_path, dst_path)
            
            self._logger.debug(f"复制成功: {src} → {dst}")
            return True
            
        except DataIOError:
            raise
        except Exception as e:
            raise DataIOError(ErrorCode.IO_ERROR, f"复制失败: {src} → {dst}", cause=e)
    
    def move(self, src: str, dst: str) -> bool:
        try:
            src_path = self._validate_path(src, must_exist=True)
            dst_path = self._validate_path(dst)
            
            src_path.rename(dst_path)
            
            self._logger.debug(f"移动成功: {src} → {dst}")
            return True
            
        except DataIOError:
            raise
        except Exception as e:
            raise DataIOError(ErrorCode.IO_ERROR, f"移动失败: {src} → {dst}", cause=e)
    
    def create_directory(self, path: str) -> bool:
        try:
            dir_path = self._validate_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"目录创建成功: {path}")
            return True
        except DataIOError:
            raise
        except Exception as e:
            raise DataIOError(ErrorCode.IO_ERROR, f"创建目录失败: {path}", cause=e)
    
    def _update_stats(self, operation: str, bytes_count: int, duration_ms: float):
        """更新性能统计"""
        if operation == 'read':
            self._stats['reads'] += 1
            self._stats['bytes_read'] += bytes_count
        elif operation == 'write':
            self._stats['writes'] += 1
            self._stats['bytes_written'] += bytes_count
        
        self._stats['total_time_ms'] += duration_ms
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取IO统计信息"""
        total_ops = self._stats['reads'] + self._stats['writes']
        avg_speed = (
            (self._stats['bytes_read'] + self._stats['bytes_written']) /
            max(self._stats['total_time_ms'], 1) *
            1000  # bytes/ms to bytes/s
        ) if total_ops > 0 else 0
        
        return {
            **self._stats,
            'total_operations': total_ops,
            'average_speed_bytes_per_s': avg_speed,
            'average_speed_mb_per_s': avg_speed / (1024 * 1024),
            'backend_type': 'local',
            'base_path': str(self._base_path)
        }


class IOManager:
    """
    IO 管理器 - 统一的数据访问入口
    
    功能：
    - 多后端支持（本地/OSS/S3）
    - 透明的压缩/解压
    - 完整性校验
    - 并发IO操作
    - 性能监控
    
    Example:
        >>> io = IOManager(storage_backend="local", base_path="/app/data")
        >>> io.write("scene_001/image.jpg", image_data)
        >>> data = io.read("scene_001/image.jpg")
        >>> meta = io.get_metadata("scene_001/image.jpg")
    """
    
    def __init__(
        self,
        storage_backend: str = "local",
        base_path: str = "/app",
        config: Optional[Dict] = None,
        auto_connect: bool = True
    ):
        self._backend_type = storage_backend.lower()
        self._config = config or {}
        self._logger = setup_logging("io.manager")
        self._backend: Optional[IStorageBackend] = None
        self._compression_format = CompressionFormat.NONE
        
        # 初始化后端
        self._initialize_backend(base_path)
        
        if auto_connect:
            self.connect()
    
    def _initialize_backend(self, base_path: str):
        """初始化存储后端"""
        backend_map = {
            'local': LocalStorageBackend,
            # 可扩展：'oss': OSSStorageBackend, 's3': S3StorageBackend
        }
        
        backend_class = backend_map.get(self._backend_type)
        if not backend_class:
            raise WorkshopError(
                ErrorCode.NOT_SUPPORTED,
                f"不支持的存储后端: {self._backend_type}, "
                f"支持的后端: {list(backend_map.keys())}"
            )
        
        if self._backend_type == 'local':
            self._backend = backend_class(base_path=base_path)
        else:
            self._backend = backend_class(**self._config)
    
    def connect(self) -> bool:
        """建立连接"""
        if self._backend:
            return self._backend.connect(self._config)
        return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self._backend:
            self._backend.disconnect()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    # 核心IO操作代理
    
    def read(self, path: str, decompress: bool = True) -> bytes:
        """读取文件内容（可选自动解压）"""
        data = self._backend.read(path)
        
        if decompress and self._compression_format != CompressionFormat.NONE:
            data = self._decompress(data)
        
        return data
    
    def write(self, path: str, data: Union[bytes, str], compress: bool = False) -> int:
        """写入数据（可选自动压缩）"""
        if compress and self._compression_format != CompressionFormat.NONE:
            data = self._compress(data)
        
        return self._backend.write(path, data)
    
    def exists(self, path: str) -> bool:
        return self._backend.exists(path)
    
    def delete(self, path: str) -> bool:
        return self._backend.delete(path)
    
    def list_files(self, directory: str, pattern: str = "*") -> List[FileMetadata]:
        return self._backend.list_files(directory, pattern)
    
    def get_metadata(self, path: str) -> Optional[FileMetadata]:
        return self._backend.get_metadata(path)
    
    def get_size(self, path: str) -> int:
        return self._backend.get_size(path)
    
    def copy(self, src: str, dst: str) -> bool:
        return self._backend.copy(src, dst)
    
    def move(self, src: str, dst: str) -> bool:
        return self._backend.move(src, dst)
    
    def create_directory(self, path: str) -> bool:
        return self._backend.create_directory(path)
    
    # 批量操作
    
    def batch_read(self, paths: List[str], max_workers: int = 4) -> Dict[str, bytes]:
        """批量并行读取"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.read, path): path 
                for path in paths
            }
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    self._logger.error(f"批量读取失败: {path} - {e}")
                    results[path] = b''
        
        return results
    
    def batch_write(self, data_dict: Dict[str, Union[bytes, str]], max_workers: int = 4) -> Dict[str, int]:
        """批量并行写入"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.write, path, data): path 
                for path, data in data_dict.items()
            }
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    self._logger.error(f"批量写入失败: {path} - {e}")
                    results[path] = -1
        
        return results
    
    # 数据完整性校验
    
    def compute_checksum(self, path: str, algorithm: str = "md5") -> str:
        """计算文件校验和"""
        data = self._backend.read(path)
        
        if algorithm.lower() == "md5":
            return hashlib.md5(data).hexdigest()
        elif algorithm.lower() == "sha256":
            return hashlib.sha256(data).hexdigest()
        else:
            raise ValueError(f"不支持的哈希算法: {algorithm}")
    
    def verify_integrity(self, path: str, expected_checksum: str, algorithm: str = "md5") -> bool:
        """验证文件完整性"""
        actual = self.compute_checksum(path, algorithm)
        match = actual.lower() == expected_checksum.lower()
        
        if not match:
            self._logger.warning(
                f"完整性校验失败: {path}\n"
                f"  期望: {expected_checksum}\n"
                f"  实际: {actual}"
            )
        
        return match
    
    # 压缩相关方法
    
    def set_compression(self, format: CompressionFormat):
        """设置默认压缩格式"""
        self._compression_format = format
    
    def _compress(self, data: Union[bytes, str]) -> bytes:
        """压缩数据"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if self._compression_format == CompressionFormat.GZIP:
            import gzip
            return gzip.compress(data)
        elif self._compression_format == CompressionFormat.ZIP:
            import zipfile
            from io import BytesIO
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("data", data)
            return buffer.getvalue()
        else:
            return data
    
    def _decompress(self, data: bytes) -> bytes:
        """解压数据"""
        if self._compression_format == CompressionFormat.GZIP:
            import gzip
            return gzip.decompress(data)
        elif self._compression_format == CompressionFormat.ZIP:
            import zipfile
            from io import BytesIO
            with zipfile.ZipFile(BytesIO(data), 'r') as zf:
                return zf.read("data")
        else:
            return data
    
    # 统计信息
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取IO统计"""
        stats = {
            'manager_type': self._backend_type,
            'compression': self._compression_format.value
        }
        
        if hasattr(self._backend, 'get_statistics'):
            stats.update(self._backend.get_statistics())
        
        return stats


# 全局单例实例
_global_io_manager: Optional[IOManager] = None


def get_io_manager() -> IOManager:
    """获取全局 IO 管理器实例"""
    global _global_io_manager
    
    if _global_io_manager is None:
        _global_io_manager = IOManager(auto_connect=True)
    
    return _global_io_manager


def init_io_manager(config: Optional[Dict] = None) -> IOManager:
    """初始化全局 IO 管理器"""
    global _global_io_manager
    _global_io_manager = IOManager(config=config, auto_connect=True)
    return _global_io_manager


__all__ = [
    'IStorageBackend',
    'LocalStorageBackend',
    'IOManager',
    'FileMetadata',
    'IOResult',
    'StorageBackend',
    'CompressionFormat',
    'get_io_manager',
    'init_io_manager'
]
