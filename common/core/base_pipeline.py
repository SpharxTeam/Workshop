# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Pipeline 基类 - 参考 AgentOS Agent 生命周期管理模式设计
# 遵循 ARCHITECTURAL_PRINCIPLES.md K-2 (接口契约化) 和 E-3 (资源确定性)

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
import time
import logging
import traceback

from .config_manager import ConfigManager
from .exceptions import (
    WorkshopError,
    PipelineError,
    ErrorCode,
    error_code_manager,
    ErrorSeverity
)


class PipelineStatus(Enum):
    """Pipeline 状态枚举"""
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
    """
    Pipeline 执行结果 - 参考 AgentOS TaskResult 设计
    
    Attributes:
        success: 是否成功
        output: 输出数据
        error: 错误信息
        error_code: 错误码
        metrics: 性能指标
        warnings: 警告列表
        execution_time: 执行时间（秒）
        processed_count: 处理数量
    """
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    processed_count: int = 0
    
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
            'processed_count': self.processed_count
        }


class BasePipeline(ABC):
    """
    Pipeline 抽象基类 - 参考 AgentOS Agent 和 BaseManager 模式
    
    提供统一的 Pipeline 接口和生命周期管理，遵循 DRY 原则。
    
    Lifecycle:
        CREATED → INITIALIZING → READY → RUNNING → (COMPLETED | FAILED | CANCELED) → SHUTDOWN
    
    所有 Pipeline 子类必须实现：
        - _initialize(): 初始化资源
        - _execute(): 核心执行逻辑
        - _cleanup(): 清理资源
    
    Example:
        >>> class MyPipeline(BasePipeline):
        ...     def _initialize(self):
        ...         self.model = load_model(self.config.get('model_path'))
        ...     
        ...     def _execute(self, input_data, **kwargs):
        ...         results = self.model.process(input_data)
        ...         return PipelineResult(success=True, output=results)
        ...     
        ...     def _cleanup(self):
        ...         if hasattr(self, 'model'):
        ...             del self.model
        ...
        >>> pipeline = MyPipeline(module_name="my_module")
        >>> result = pipeline.run(input_data=my_data)
    """
    
    # 子类可覆盖的配置
    MODULE_NAME: str = "base_pipeline"
    VERSION: str = "1.0.0"
    
    def __init__(
        self,
        module_name: Optional[str] = None,
        config: Optional[ConfigManager] = None,
        config_dir: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Pipeline
        
        Args:
            module_name: 模块名称（用于加载配置）
            config: 配置管理器实例（可选，如不提供则自动创建）
            config_dir: 配置目录路径
            **kwargs: 额外的初始化参数
        """
        self._module_name = module_name or self.MODULE_NAME
        self._status = PipelineStatus.CREATED
        self._config = config or ConfigManager(
            module_name=self._module_name,
            config_dir=config_dir
        )
        self._logger = logging.getLogger(f"Pipeline.{self._module_name}")
        
        # 生命周期时间戳
        self._created_at = time.time()
        self._started_at: Optional[float] = None
        self._completed_at: Optional[float] = None
        
        # 性能指标
        self._metrics: Dict[str, Any] = {}
        self._warnings: List[str] = []
        self._processed_count = 0
        
        # 回调函数
        self._on_start_callbacks: List[Callable] = []
        self._on_complete_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []
        
        # 存储额外的 kwargs
        self._kwargs = kwargs
        
        self._logger.debug(
            f"Pipeline 初始化: {self.__class__.__name__} "
            f"(module={self._module_name}, version={self.VERSION})"
        )
    
    @property
    def status(self) -> PipelineStatus:
        """获取当前状态"""
        return self._status
    
    @property
    def config(self) -> ConfigManager:
        """获取配置管理器"""
        return self._config
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志器"""
        return self._logger
    
    @property
    def module_name(self) -> str:
        """获取模块名称"""
        return self._module_name
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self._metrics.copy()
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._status == PipelineStatus.RUNNING
    
    def on_start(self, callback: Callable) -> None:
        """注册开始回调"""
        self._on_start_callbacks.append(callback)
    
    def on_complete(self, callback: Callable) -> None:
        """注册完成回调"""
        self._on_complete_callbacks.append(callback)
    
    def on_error(self, callback: Callable) -> None:
        """注册错误回调"""
        self._on_error_callbacks.append(callback)
    
    def run(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        运行 Pipeline（同步模式）
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            PipelineResult: 执行结果
        """
        start_time = time.time()
        
        try:
            # 阶段1：初始化
            self._set_status(PipelineStatus.INITIALIZING)
            self._initialize()
            
            # 阶段2：准备就绪
            self._set_status(PipelineStatus.READY)
            
            # 触发开始回调
            self._trigger_callbacks(self._on_start_callbacks)
            
            # 阶段3：执行
            self._set_status(PipelineStatus.RUNNING)
            self._started_at = time.time()
            
            result = self._execute(input_data, **kwargs)
            
            # 阶段4：完成
            self._completed_at = time.time()
            result.execution_time = time.time() - start_time
            result.metrics.update(self._metrics)
            result.warnings.extend(self._warnings)
            result.processed_count = self._processed_count
            
            if result.success:
                self._set_status(PipelineStatus.COMPLETED)
                self._logger.info(
                    f"Pipeline 执行成功: {self._module_name} "
                    f"(耗时: {result.execution_time:.2f}s, "
                    f"处理: {result.processed_count} 项)"
                )
            else:
                self._set_status(PipelineStatus.FAILED)
                self._logger.error(
                    f"Pipeline 执行失败: {self._module_name} "
                    f"(错误: {result.error})"
                )
            
            # 触发完成回调
            self._trigger_callbacks(self._on_complete_callbacks, result)
            
            return result
            
        except Exception as e:
            error_time = time.time() - start_time
            
            # 记录错误
            if isinstance(e, PipelineError):
                error_code_manager.record_error(e)
            else:
                pipeline_error = PipelineError(
                   ErrorCode.PIPELINE_EXECUTION_FAILED,
                    str(e),
                    cause=e
                )
                error_code_manager.record_error(pipeline_error)
            
            self._set_status(PipelineStatus.FAILED)
            self._logger.critical(
                f"Pipeline 异常终止: {self._module_name}\n"
                f"错误: {e}\n"
                f"{traceback.format_exc()}"
            )
            
            # 触发错误回调
            self._trigger_callbacks(self._on_error_callbacks, e)
            
            return PipelineResult(
                success=False,
                error=str(e),
                error_code=getattr(e, 'code', ErrorCode.PIPELINE_EXECUTION_FAILED),
                execution_time=error_time,
                metrics=self._metrics.copy(),
                warnings=self._warnings.copy(),
                processed_count=self._processed_count
            )
        
        finally:
            # 清理资源
            try:
                self._cleanup()
            except Exception as cleanup_error:
                self._logger.warning(f"清理资源时出错: {cleanup_error}")
            
            self._set_status(PipelineStatus.SHUTDOWN)
    
    async def run_async(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        异步运行 Pipeline
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            PipelineResult: 执行结果
        """
        # 默认实现：在线程池中运行同步版本
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, input_data, **kwargs)
    
    @abstractmethod
    def _initialize(self) -> None:
        """
        初始化资源（子类必须实现）
        
        在此方法中：
        - 加载模型
        - 初始化硬件设备
        - 准备必要的资源
        """
        pass
    
    @abstractmethod
    def _execute(self, input_data: Any, **kwargs) -> PipelineResult:
        """
        核心执行逻辑（子类必须实现）
        
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
        清理资源（子类必须实现）
        
        在此方法中：
        - 释放模型内存
        - 关闭硬件连接
        - 清理临时文件
        """
        pass
    
    def _set_status(self, status: PipelineStatus) -> None:
        """设置状态"""
        old_status = self._status
        self._status = status
        self._logger.debug(f"状态变更: {old_status.name} → {status.name}")
    
    def _add_warning(self, message: str) -> None:
        """添加警告"""
        self._warnings.append(message)
        self._logger.warning(message)
    
    def _update_metric(self, key: str, value: Any) -> None:
        """更新性能指标"""
        self._metrics[key] = value
    
    def _increment_processed(self, count: int = 1) -> None:
        """增加处理计数"""
        self._processed_count += count
    
    def _trigger_callbacks(self, callbacks: List[Callable], *args) -> None:
        """触发回调函数"""
        for callback in callbacks:
            try:
                callback(*args)
            except Exception as e:
                self._logger.warning(f"回调执行失败: {callback.__name__}: {e}")
    
    def validate_input(self, input_data: Any) -> bool:
        """
        验证输入数据（子类可覆盖）
        
        Args:
            input_data: 输入数据
            
        Returns:
            bool: 是否有效
        """
        return input_data is not None
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查（子类可覆盖）
        
        Returns:
            健康状态字典
        """
        return {
            'status': 'healthy' if self._status in [PipelineStatus.READY, PipelineStatus.COMPLETED] else self._status.name,
            'module': self._module_name,
            'version': self.VERSION,
            'uptime': time.time() - self._created_at if self._created_at else 0
        }
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"module={self._module_name!r}, "
            f"status={self._status.name}, "
            f"version={self.VERSION})"
        )
    
    def __enter__(self):
        """上下文管理器入口"""
        self._initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._cleanup()


__all__ = ['BasePipeline', 'PipelineResult', 'PipelineStatus']
