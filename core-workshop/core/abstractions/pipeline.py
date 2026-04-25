"""
Pipeline Abstractions - V3.0
===========================

Pipeline 抽象基类和生命周期管理

参考:
    - AgentOS BaseManager 模式
    - Deepness Pipeline ABC
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import time
import threading
import logging


class PipelineStatus(Enum):
    """Pipeline 生命周期状态"""
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELED = auto()
    SHUTDOWN = auto()


@dataclass
class PipelineResult:
    """Pipeline 执行结果"""
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional['ErrorCode'] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    processed_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'error_code': self.error_code.name if self.error_code else None,
            'metrics': self.metrics,
            'warnings': self.warnings,
            'execution_time': self.execution_time,
            'processed_count': self.processed_count,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class PipelineContext:
    """Pipeline 执行上下文"""
    pipeline_id: str
    pipeline_name: str
    version: str
    config: Dict[str, Any]
    logger: logging.Logger
    start_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_metadata(self, key: str, value: Any) -> None:
        """更新元数据"""
        self.metadata[key] = value


class BasePipeline(ABC):
    """
    Pipeline 抽象基类 - V3.0
    
    参考 AgentOS Agent 和 BaseManager 模式
    
    Lifecycle:
        CREATED → INITIALIZING → READY → RUNNING → (COMPLETED | FAILED | CANCELED) → SHUTDOWN
    
    使用方式:
        with MyPipeline() as pipeline:
            result = pipeline.run(input_data)
    """

    def __init__(self, config_dir: Optional[str] = None, **kwargs):
        """
        初始化 Pipeline
        
        Args:
            config_dir: 配置目录路径
            **kwargs: 额外参数
        """
        self._status = PipelineStatus.CREATED
        self._config_dir = config_dir
        self._kwargs = kwargs
        self._lock = threading.RLock()
        self._context: Optional[PipelineContext] = None
        self._logger = logging.getLogger(self.__class__.__name__)
        
        self._transition_to(PipelineStatus.INITIALIZING)
        try:
            self._initialize()
            self._transition_to(PipelineStatus.READY)
        except Exception as e:
            self._logger.error(f"Pipeline 初始化失败: {e}")
            self._transition_to(PipelineStatus.FAILED)
            raise

    @property
    def status(self) -> PipelineStatus:
        """获取当前状态"""
        return self._status

    @property
    def is_ready(self) -> bool:
        """是否就绪"""
        return self._status == PipelineStatus.READY

    @property
    def is_running(self) -> bool:
        """是否运行中"""
        return self._status == PipelineStatus.RUNNING

    def _transition_to(self, new_status: PipelineStatus) -> None:
        """状态转换"""
        with self._lock:
            old_status = self._status
            self._status = new_status
            self._logger.debug(f"Pipeline 状态转换: {old_status.name} → {new_status.name}")

    @abstractmethod
    def _initialize(self) -> None:
        """
        初始化 Pipeline - 必须实现
        
        在此方法中:
        - 加载配置
        - 初始化资源
        - 设置日志
        """
        pass

    @abstractmethod
    def _execute(self, input_data: Any, **kwargs) -> PipelineResult:
        """
        执行 Pipeline 核心逻辑 - 必须实现
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            PipelineResult: 执行结果
        """
        pass

    @abstractmethod
    def _cleanup(self) -> None:
        """
        清理资源 - 必须实现
        
        在此方法中:
        - 释放资源
        - 关闭连接
        - 清理临时文件
        """
        pass

    def run(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行 Pipeline (完整生命周期管理)
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            PipelineResult: 执行结果
        """
        if not self.is_ready:
            return PipelineResult(
                success=False,
                error=f"Pipeline 未就绪，当前状态: {self._status.name}",
            )

        with self._lock:
            self._transition_to(PipelineStatus.RUNNING)
            start_time = time.time()

            try:
                result = self._execute(input_data, **kwargs)
                result.execution_time = time.time() - start_time
                
                if result.success:
                    self._transition_to(PipelineStatus.COMPLETED)
                else:
                    self._transition_to(PipelineStatus.FAILED)
                
                return result

            except Exception as e:
                self._logger.error(f"Pipeline 执行失败: {e}", exc_info=True)
                self._transition_to(PipelineStatus.FAILED)
                return PipelineResult(
                    success=False,
                    error=str(e),
                    execution_time=time.time() - start_time,
                )

    def pause(self) -> bool:
        """暂停执行"""
        if self.is_running:
            self._transition_to(PipelineStatus.PAUSED)
            return True
        return False

    def resume(self) -> bool:
        """恢复执行"""
        if self._status == PipelineStatus.PAUSED:
            self._transition_to(PipelineStatus.RUNNING)
            return True
        return False

    def cancel(self) -> bool:
        """取消执行"""
        if self._status in [PipelineStatus.RUNNING, PipelineStatus.PAUSED]:
            self._transition_to(PipelineStatus.CANCELED)
            return True
        return False

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._cleanup()
        self._transition_to(PipelineStatus.SHUTDOWN)
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} status={self._status.name}>"
