"""
Pipeline Abstractions - V3.0 (V2 Compatibility Extended)
========================================================

Pipeline 抽象基类和生命周期管理

V3.0 扩展（WS-T02）：
    在保持 V3 抽象方法不变的前提下，新增 V2 runner_v2.py 期望的兼容成员：
    - self.config: PipelineConfig 配置访问对象（.get(key, default) / .to_dict()）
    - self._processed_count / self._increment_processed(count=1)
    - self._add_warning(msg)
    - module_name 属性
    - on_start/on_complete/on_error 回调钩子
    - metrics 属性
    - health_check() 方法
    - config_path= 构造参数（V2 兼容，等价于 config_dir=）

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


class PipelineConfig:
    """
    Pipeline 配置访问对象 - V2 兼容

    提供 V2 期望的 .get(key, default=...) 和 .to_dict() 接口，
    内部包装一个 dict。子类在 _initialize() 中可通过 self._config.update(...)
    或 self._config.set(key, value) 填充配置。
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = dict(data) if data else {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值（键不存在时返回）

        Returns:
            配置值或默认值
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._data[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """批量更新配置"""
        self._data.update(data)

    def to_dict(self) -> Dict[str, Any]:
        """返回全部配置的字典副本"""
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __repr__(self) -> str:
        return f"<PipelineConfig keys={list(self._data.keys())}>"


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
    Pipeline 抽象基类 - V3.0 (V2 Compatibility Extended)

    参考 AgentOS Agent 和 BaseManager 模式

    Lifecycle:
        CREATED → INITIALIZING → READY → RUNNING → (COMPLETED | FAILED | CANCELED) → SHUTDOWN

    使用方式:
        with MyPipeline() as pipeline:
            result = pipeline.run(input_data)

    V2 兼容成员（WS-T02 扩展）:
        - self.config: PipelineConfig 配置访问对象
        - self._processed_count / self._increment_processed(count=1)
        - self._add_warning(msg)
        - module_name 属性
        - on_start/on_complete/on_error 回调钩子
        - metrics 属性
        - health_check() 方法
        - config_path= 构造参数（等价于 config_dir=）
    """

    def __init__(
        self,
        config_dir: Optional[str] = None,
        config_path: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Pipeline

        Args:
            config_dir: 配置目录路径（V3 参数名）
            config_path: 配置文件路径（V2 兼容参数名，等价于 config_dir）
            **kwargs: 额外参数

        Note:
            config_path 为 V2 兼容参数，与 config_dir 等价。
            若两者同时提供，config_dir 优先。
        """
        self._status = PipelineStatus.CREATED
        # V2 兼容：config_path 等价于 config_dir
        self._config_dir = config_dir or config_path
        self._kwargs = kwargs
        self._lock = threading.RLock()
        self._context: Optional[PipelineContext] = None
        self._logger = logging.getLogger(self.__class__.__name__)

        # V2 兼容成员
        self._config = PipelineConfig()
        self._processed_count = 0
        self._warnings: List[str] = []
        self._metrics: Dict[str, Any] = {}

        # V2 兼容回调钩子（默认 None，子类或外部可设置）
        self.on_start: Optional[Callable[['BasePipeline'], None]] = None
        self.on_complete: Optional[Callable[['BasePipeline', 'PipelineResult'], None]] = None
        self.on_error: Optional[Callable[['BasePipeline', Exception], None]] = None

        self._transition_to(PipelineStatus.INITIALIZING)
        try:
            self._initialize()
            self._transition_to(PipelineStatus.READY)
        except Exception as e:
            self._logger.error(f"Pipeline 初始化失败: {e}")
            self._transition_to(PipelineStatus.FAILED)
            raise

    # =========================================================================
    # V3 核心属性
    # =========================================================================

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

    # =========================================================================
    # V2 兼容属性（WS-T02 扩展）
    # =========================================================================

    @property
    def config(self) -> PipelineConfig:
        """
        配置访问对象（V2 兼容）

        V2 代码使用 self.config.get(key, default=...) 和 self.config.to_dict()。
        子类在 _initialize() 中通过 self._config.update(...) 或 self._config.set(key, value)
        填充配置。
        """
        return self._config

    @property
    def module_name(self) -> str:
        """
        模块名（V2 兼容）

        优先返回子类定义的 MODULE_NAME 类属性，否则从类名推导。
        """
        return getattr(self.__class__, 'MODULE_NAME', self.__class__.__name__)

    @property
    def metrics(self) -> Dict[str, Any]:
        """
        运行时指标（V2 兼容）

        子类在 _execute() 中通过 self._metrics[key] = value 填充指标。
        """
        return self._metrics

    @property
    def processed_count(self) -> int:
        """已处理数量（V2 兼容，self._processed_count 的只读访问）"""
        return self._processed_count

    @property
    def warnings(self) -> List[str]:
        """警告列表（V2 兼容，self._warnings 的只读访问）"""
        return list(self._warnings)

    # =========================================================================
    # V2 兼容方法（WS-T02 扩展）
    # =========================================================================

    def _increment_processed(self, count: int = 1) -> None:
        """
        增加已处理计数（V2 兼容）

        V2 代码调用 self._increment_processed(1)。

        Args:
            count: 增量（默认 1）
        """
        with self._lock:
            self._processed_count += count

    def _add_warning(self, message: str) -> None:
        """
        添加警告（V2 兼容）

        V2 代码调用 self._add_warning(msg)。
        警告会自动附加到最终的 PipelineResult.warnings。

        Args:
            message: 警告消息
        """
        with self._lock:
            self._warnings.append(message)
            self._logger.warning(message)

    def health_check(self) -> bool:
        """
        健康检查（V2 兼容）

        默认实现返回 True（健康）。子类可覆盖以实现自定义健康检查逻辑，
        例如检查资源可用性、连接状态等。

        Returns:
            bool: True 表示健康，False 表示不健康
        """
        return self._status in (
            PipelineStatus.READY,
            PipelineStatus.RUNNING,
            PipelineStatus.PAUSED,
        )

    # =========================================================================
    # 状态转换（V3 内部）
    # =========================================================================

    def _transition_to(self, new_status: PipelineStatus) -> None:
        """状态转换"""
        with self._lock:
            old_status = self._status
            self._status = new_status
            self._logger.debug(f"Pipeline 状态转换: {old_status.name} → {new_status.name}")

    # =========================================================================
    # V3 抽象方法（子类必须实现）
    # =========================================================================

    @abstractmethod
    def _initialize(self) -> None:
        """
        初始化 Pipeline - 必须实现

        在此方法中:
        - 加载配置（填充 self._config）
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

    # =========================================================================
    # V3 生命周期管理
    # =========================================================================

    def run(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行 Pipeline (完整生命周期管理)

        在执行前后触发 V2 兼容回调钩子（on_start/on_complete/on_error），
        并将执行期间累积的 warnings 和 metrics 附加到结果。

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
                warnings=list(self._warnings),
            )

        with self._lock:
            self._transition_to(PipelineStatus.RUNNING)
            start_time = time.time()

            # V2 兼容：触发 on_start 回调
            if self.on_start is not None:
                try:
                    self.on_start(self)
                except Exception as cb_err:
                    self._logger.warning(f"on_start 回调异常: {cb_err}")

            try:
                result = self._execute(input_data, **kwargs)
                result.execution_time = time.time() - start_time

                # V2 兼容：附加累积的 warnings 和 metrics
                if self._warnings:
                    result.warnings = list(result.warnings) + list(self._warnings)
                if self._metrics and not result.metrics:
                    result.metrics = dict(self._metrics)
                result.processed_count = self._processed_count

                if result.success:
                    self._transition_to(PipelineStatus.COMPLETED)
                    # V2 兼容：触发 on_complete 回调
                    if self.on_complete is not None:
                        try:
                            self.on_complete(self, result)
                        except Exception as cb_err:
                            self._logger.warning(f"on_complete 回调异常: {cb_err}")
                else:
                    self._transition_to(PipelineStatus.FAILED)
                    # V2 兼容：失败也触发 on_complete
                    if self.on_complete is not None:
                        try:
                            self.on_complete(self, result)
                        except Exception as cb_err:
                            self._logger.warning(f"on_complete 回调异常: {cb_err}")

                return result

            except Exception as e:
                self._logger.error(f"Pipeline 执行失败: {e}", exc_info=True)
                self._transition_to(PipelineStatus.FAILED)
                # V2 兼容：触发 on_error 回调
                if self.on_error is not None:
                    try:
                        self.on_error(self, e)
                    except Exception as cb_err:
                        self._logger.warning(f"on_error 回调异常: {cb_err}")
                return PipelineResult(
                    success=False,
                    error=str(e),
                    execution_time=time.time() - start_time,
                    warnings=list(self._warnings),
                    processed_count=self._processed_count,
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
        return f"<{self.__class__.__name__} status={self._status.name} module={self.module_name}>"
