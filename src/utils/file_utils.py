"""
文件操作工具函数
提供统一的文件读写、路径处理、格式转换等功能
"""

import os
import json
import yaml
import pickle
import shutil
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(directory: Union[str, Path]) -> Path:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            directory: 目录路径
            
        Returns:
            创建的目录Path对象
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def safe_write(data: Any, filepath: Union[str, Path], 
                   mode: str = 'w', encoding: str = 'utf-8',
                   backup: bool = True) -> bool:
        """
        安全写入文件，支持备份和原子操作
        
        Args:
            data: 要写入的数据
            filepath: 文件路径
            mode: 写入模式 ('w' 或 'wb')
            encoding: 编码方式
            backup: 是否备份原文件
            
        Returns:
            是否成功
        """
        filepath = Path(filepath)
        
        try:
            # 创建目录
            FileUtils.ensure_dir(filepath.parent)
            
            # 备份原文件
            if backup and filepath.exists():
                backup_path = filepath.with_suffix(f"{filepath.suffix}.bak")
                shutil.copy2(filepath, backup_path)
                logger.debug(f"备份文件: {filepath} -> {backup_path}")
            
            # 原子写入：先写入临时文件，再重命名
            temp_path = filepath.with_suffix(f"{filepath.suffix}.tmp")
            
            if 'b' in mode:
                with open(temp_path, mode) as f:
                    if isinstance(data, (bytes, bytearray)):
                        f.write(data)
                    else:
                        # 对于非二进制数据，先序列化
                        pickle.dump(data, f)
            else:
                with open(temp_path, mode, encoding=encoding) as f:
                    if isinstance(data, (dict, list)):
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    elif isinstance(data, str):
                        f.write(data)
                    else:
                        # 尝试转换为字符串
                        f.write(str(data))
            
            # 重命名临时文件为正式文件
            temp_path.rename(filepath)
            
            logger.debug(f"文件写入成功: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"文件写入失败 {filepath}: {e}")
            # 清理临时文件
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            return False
    
    @staticmethod
    def safe_read(filepath: Union[str, Path], 
                  mode: str = 'r', encoding: str = 'utf-8',
                  default: Any = None) -> Any:
        """
        安全读取文件
        
        Args:
            filepath: 文件路径
            mode: 读取模式 ('r' 或 'rb')
            encoding: 编码方式
            default: 读取失败时的默认值
            
        Returns:
            读取的数据或默认值
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"文件不存在: {filepath}")
            return default
        
        try:
            if 'b' in mode:
                with open(filepath, mode) as f:
                    # 尝试反序列化pickle数据
                    if filepath.suffix in ['.pkl', '.pickle']:
                        return pickle.load(f)
                    else:
                        return f.read()
            else:
                with open(filepath, mode, encoding=encoding) as f:
                    # 根据扩展名自动选择解析方式
                    if filepath.suffix in ['.json', '.json5']:
                        return json.load(f)
                    elif filepath.suffix in ['.yaml', '.yml']:
                        return yaml.safe_load(f)
                    else:
                        return f.read()
                        
        except Exception as e:
            logger.error(f"文件读取失败 {filepath}: {e}")
            return default
    
    @staticmethod
    def get_file_hash(filepath: Union[str, Path], 
                      algorithm: str = 'md5',
                      chunk_size: int = 8192) -> Optional[str]:
        """
        计算文件哈希值
        
        Args:
            filepath: 文件路径
            algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
            chunk_size: 读取块大小
            
        Returns:
            哈希值字符串或None
        """
        filepath = Path(filepath)
        
        if not filepath.exists() or not filepath.is_file():
            return None
        
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"计算文件哈希失败 {filepath}: {e}")
            return None
    
    @staticmethod
    def find_files(directory: Union[str, Path],
                   pattern: str = "*",
                   recursive: bool = True,
                   sort_by: str = "name") -> List[Path]:
        """
        查找匹配模式的文件
        
        Args:
            directory: 搜索目录
            pattern: 文件模式（如 "*.jpg", "image_*.png"）
            recursive: 是否递归搜索
            sort_by: 排序方式 ("name", "size", "mtime")
            
        Returns:
            文件路径列表
        """
        directory = Path(directory)
        
        if not directory.exists():
            return []
        
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        # 过滤出文件（排除目录）
        files = [f for f in files if f.is_file()]
        
        # 排序
        if sort_by == "name":
            files.sort(key=lambda x: x.name)
        elif sort_by == "size":
            files.sort(key=lambda x: x.stat().st_size)
        elif sort_by == "mtime":
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return files
    
    @staticmethod
    def get_image_files(directory: Union[str, Path],
                        recursive: bool = True) -> List[Path]:
        """
        获取目录中的所有图像文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归搜索
            
        Returns:
            图像文件路径列表
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', 
                           '.bmp', '.gif', '.webp'}
        
        all_files = FileUtils.find_files(directory, "*", recursive, "name")
        image_files = [f for f in all_files 
                      if f.suffix.lower() in image_extensions]
        
        return image_files
    
    @staticmethod
    def copy_with_structure(source: Union[str, Path], 
                           destination: Union[str, Path],
                           pattern: str = "*") -> int:
        """
        复制文件并保持目录结构
        
        Args:
            source: 源目录
            destination: 目标目录
            pattern: 文件模式
            
        Returns:
            复制的文件数量
        """
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            logger.warning(f"源目录不存在: {source}")
            return 0
        
        copied_count = 0
        
        for filepath in source.rglob(pattern):
            if filepath.is_file():
                # 计算相对路径
                relative_path = filepath.relative_to(source)
                dest_path = destination / relative_path
                
                # 创建目标目录
                FileUtils.ensure_dir(dest_path.parent)
                
                try:
                    shutil.copy2(filepath, dest_path)
                    copied_count += 1
                except Exception as e:
                    logger.error(f"复制文件失败 {filepath} -> {dest_path}: {e}")
        
        logger.info(f"复制完成: {copied_count} 个文件")
        return copied_count
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """
        计算目录总大小（字节）
        
        Args:
            directory: 目录路径
            
        Returns:
            总大小（字节）
        """
        directory = Path(directory)
        
        if not directory.exists():
            return 0
        
        total_size = 0
        
        for filepath in directory.rglob("*"):
            if filepath.is_file():
                try:
                    total_size += filepath.stat().st_size
                except OSError:
                    continue
        
        return total_size
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节大小
            
        Returns:
            格式化后的字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


class PathResolver:
    """路径解析器，处理相对路径和绝对路径转换"""
    
    def __init__(self, base_dir: Union[str, Path] = None):
        """
        初始化路径解析器
        
        Args:
            base_dir: 基础目录，用于解析相对路径
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
    def resolve(self, path: Union[str, Path]) -> Path:
        """
        解析路径
        
        Args:
            path: 可以是相对路径或绝对路径
            
        Returns:
            绝对路径
        """
        path = Path(path)
        
        if path.is_absolute():
            return path
        else:
            return (self.base_dir / path).resolve()
    
    def relative_to_base(self, path: Union[str, Path]) -> Path:
        """
        获取相对于基础目录的路径
        
        Args:
            path: 绝对路径
            
        Returns:
            相对路径
        """
        path = Path(path)
        
        try:
            return path.relative_to(self.base_dir)
        except ValueError:
            # 如果不包含在基础目录中，返回绝对路径
            return path
    
    @staticmethod
    def get_project_root() -> Path:
        """
        获取项目根目录
        
        Returns:
            项目根目录路径
        """
        # 从当前文件向上查找，直到找到项目根目录标志
        current = Path(__file__).resolve()
        
        # 查找包含 .git 或 setup.py 或 requirements.txt 的目录
        while current.parent != current:
            if (current / ".git").exists() or \
               (current / "requirements.txt").exists() or \
               (current / "setup.py").exists():
                return current
            current = current.parent
        
        # 如果没找到，返回当前工作目录
        return Path.cwd()


class FileLock:
    """简单文件锁，用于进程间同步"""
    
    def __init__(self, lock_file: Union[str, Path], timeout: int = 30):
        """
        初始化文件锁
        
        Args:
            lock_file: 锁文件路径
            timeout: 超时时间（秒）
        """
        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self._locked = False
    
    def acquire(self) -> bool:
        """
        获取锁
        
        Returns:
            是否成功获取锁
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                # 尝试创建锁文件（原子操作）
                self.lock_file.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                
                # 写入进程信息
                pid = os.getpid()
                timestamp = datetime.now().isoformat()
                lock_info = f"pid={pid}, timestamp={timestamp}\n"
                os.write(fd, lock_info.encode())
                os.close(fd)
                
                self._locked = True
                logger.debug(f"获取文件锁: {self.lock_file}")
                return True
                
            except FileExistsError:
                # 锁文件已存在，检查是否过期
                try:
                    lock_age = time.time() - self.lock_file.stat().st_mtime
                    if lock_age > self.timeout:
                        # 锁已过期，清理并重试
                        self.release()
                        continue
                except OSError:
                    pass
                
                # 等待一段时间后重试
                time.sleep(0.1)
        
        logger.warning(f"获取文件锁超时: {self.lock_file}")
        return False
    
    def release(self) -> bool:
        """
        释放锁
        
        Returns:
            是否成功释放
        """
        if self._locked and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                self._locked = False
                logger.debug(f"释放文件锁: {self.lock_file}")
                return True
            except OSError as e:
                logger.error(f"释放文件锁失败 {self.lock_file}: {e}")
                return False
        return True
    
    def __enter__(self):
        """上下文管理器入口"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()