# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 流式处理 (Streaming) Pipeline V2 - 基于生产者-消费者模型的异步处理框架
# 使用 BasePipeline 基类重构，增强线程安全、错误处理和可观测性

import sys
import logging
import queue
import threading
import time
from typing import Any, Dict, Optional, List, Callable, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path

from core_workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    ErrorCode,
)
from core_workshop.core.services.logging_service import setup_logging, get_logger
from core_workshop.pipelines._validation_helpers import (
    validate_path_exists_dir,
    collect_errors,
)


@dataclass
class FrameData:
    """帧数据结构"""
    frame: Any  # numpy array (image)
    frame_name: str
    frame_idx: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"FrameData(idx={self.frame_idx}, name={self.frame_name!r})"


class BaseConsumer(ABC):
    """
    消费者基类 - 参考 AgentOS Agent 设计
    
    所有自定义消费者必须继承此类并实现 process_frame() 方法。
    
    Lifecycle:
        CREATED → RUNNING → COMPLETED/FAILED → SHUTDOWN
    """
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self._running = False
        self._processed_count = 0
        self._results: List[Any] = []
        self._exception: Optional[Exception] = None
        self._logger = get_logger(f"streaming.consumer.{name}")
        
        # 性能统计
        self._start_time: Optional[float] = None
        self._processing_times: List[float] = []
        
        # 回调
        self._on_frame_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def processed_count(self) -> int:
        return self._processed_count
    
    @property
    def results(self) -> List[Any]:
        return self._results.copy()
    
    @property
    def exception(self) -> Optional[Exception]:
        return self._exception
    
    @property
    def avg_processing_time(self) -> float:
        if not self._processing_times:
            return 0.0
        return sum(self._processing_times) / len(self._processing_times)
    
    def on_frame(self, callback: Callable) -> None:
        """注册帧处理回调"""
        self._on_frame_callbacks.append(callback)
    
    def on_error(self, callback: Callable) -> None:
        """注册错误回调"""
        self._on_error_callbacks.append(callback)
    
    @abstractmethod
    def process_frame(self, frame_data: FrameData) -> Any:
        """
        处理单帧数据（子类必须实现）
        
        Args:
            frame_data: 帧数据对象
            
        Returns:
            处理结果
        """
        pass
    
    def run(self, input_queue: queue.Queue) -> None:
        """运行消费者主循环"""
        self._running = True
        self._start_time = time.time()
        self._logger.info(f"消费者 [{self.name}] 启动")
        
        try:
            while self._running:
                try:
                    item = input_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if item is None:  # 终止信号
                    break
                
                frame_data = FrameData(*item[:3]) if isinstance(item, tuple) else item
                
                try:
                    frame_start = time.time()
                    
                    result = self.process_frame(frame_data)
                    
                    processing_time = time.time() - frame_start
                    self._processing_times.append(processing_time)
                    self._processed_count += 1
                    self._results.append(result)
                    
                    # 触发回调
                    for cb in self._on_frame_callbacks:
                        try:
                            cb(frame_data, result)
                        except Exception as cb_err:
                            self._logger.warning(f"回调执行失败: {cb_err}")
                    
                except Exception as e:
                    self._logger.error(
                        f"消费者 [{self.name}] 处理帧 {frame_data.frame_name} 时出错: {e}"
                    )
                    self._exception = e
                    
                    for cb in self._on_error_callbacks:
                        try:
                            cb(e, frame_data)
                        except Exception as cb_err:
                            self._logger.warning(f"错误回调失败: {cb_err}")
                
                finally:
                    input_queue.task_done()
                
                # 定期日志
                if self._processed_count % 100 == 0:
                    elapsed = time.time() - self._start_time
                    fps = self._processed_count / max(elapsed, 0.001)
                    self._logger.info(
                        f"消费者 [{self.name}] 已处理 {self._processed_count} 帧 "
                        f"(FPS: {fps:.1f}, 平均耗时: {self.avg_processing_time*1000:.1f}ms)"
                    )
            
            self._logger.info(
                f"消费者 [{self.name}] 结束，共处理 {self._processed_count} 帧"
            )
            
        except Exception as e:
            self._logger.error(f"消费者 [{self.name}] 发生异常: {e}", exc_info=True)
            self._exception = e
            
        finally:
            self._running = False
    
    def stop(self) -> None:
        """停止消费者"""
        self._running = False
        self._logger.info(f"消费者 [{self.name}] 已停止")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_time = time.time() - self._start_time if self._start_time else 0
        
        return {
            'name': self.name,
            'processed_count': self._processed_count,
            'total_time_s': total_time,
            'avg_processing_time_ms': self.avg_processing_time * 1000,
            'throughput_fps': self._processed_count / max(total_time, 0.001),
            'has_exception': self._exception is not None,
            'result_count': len(self._results)
        }


class StreamingPipeline(BasePipeline):
    """
    流式处理 Pipeline - 基于 BasePipeline 重构的生产者-消费者框架
    
    特性：
    - 多消费者并行处理
    - 线程安全的队列管理
    - 完整的生命周期管理
    - 性能指标收集
    - 错误恢复机制
    - 可观测性增强
    
    配置项：
        - max_queue_size: 队列最大容量 (30)
        - producer_timeout: 生产者超时时间（秒）(5)
        - consumer_count: 消费者线程数
        - batch_size: 批量处理大小
    
    Example:
        >>> pipeline = StreamingPipeline(source_dir="/app/images")
        >>> pipeline.add_quality_consumer(config={'blur_threshold': 100})
        >>> pipeline.add_enhance_consumer(model=yolo_model)
        >>> result = pipeline.run()
    """
    
    MODULE_NAME = "streaming"
    VERSION = "2.0.0"
    
    SUPPORTED_IMAGE_EXTENSIONS = ['*.jpg', '*.jpeg', '*.webp', '*.png']
    
    def __init__(self, source_dir: str = "", **kwargs):
        self._source_dir = source_dir
        self._producer = None
        self._consumers: List[BaseConsumer] = []
        self._consumer_threads: List[threading.Thread] = []
        self._max_queue_size = 30
        super().__init__(**kwargs)
    
    def _initialize(self) -> None:
        """初始化流式处理资源"""
        self._logger.info("初始化 Streaming Pipeline...")
        
        self._max_queue_size = self.config.get('max_queue_size', default=30)
        self._producer = FrameProducerV2(
            source_dir=self._source_dir,
            max_queue_size=self._max_queue_size,
            logger=self._logger
        )
        
        self._logger.debug("Streaming Pipeline 初始化完成")
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行流式处理
        
        Args:
            input_data: 可选的源目录路径（覆盖初始化时的设置）
            
        Returns:
            PipelineResult: 包含所有消费者结果的字典
        """
        # 验证源目录
        source_dir = kwargs.get('source_dir') or input_data or self._source_dir

        errors = collect_errors(
            validate_path_exists_dir(source_dir, 'source_dir'),
        )

        if errors:
            return PipelineResult(
                success=False,
                error='\n'.join(errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 更新源目录（如果提供了新值）
        if source_dir != self._source_dir:
            self._source_dir = source_dir
            self._producer.source_dir = source_dir
        
        # 验证是否注册了消费者
        if not self._consumers:
            return PipelineResult(
                success=False,
                error="未注册任何消费者，请先调用 add_*_consumer() 方法",
                error_code=ErrorCode.PIPELINE_DEPENDENCY_MISSING
            )
        
        self._logger.info(
            f"开始流式处理\n"
            f"  源目录: {source_dir}\n"
            f"  注册消费者: {[c.name for c in self._consumers]}\n"
            f"  队列容量: {self._max_queue_size}"
        )
        
        start_time = time.time()
        
        try:
            # 为每个消费者注册队列
            for consumer in self._consumers:
                q = self._producer.register_consumer(consumer.name)
                consumer.queue = q
            
            # 启动生产者和消费者
            self._producer.start()
            
            for consumer in self._consumers:
                thread = threading.Thread(
                    target=consumer.run,
                    args=(consumer.queue,),
                    name=f"Consumer-{consumer.name}",
                    daemon=True
                )
                self._consumer_threads.append(thread)
                thread.start()
            
            # 等待完成
            self._producer.thread.join(timeout=300)  # 5分钟超时
            
            for thread in self._consumer_threads:
                thread.join(timeout=60)  # 1分钟超时等待消费者完成
            
            execution_time = time.time() - start_time
            
            # 收集结果
            results = {}
            all_success = True
            errors = []
            
            for consumer in self._consumers:
                stats = consumer.get_statistics()
                results[consumer.name] = {
                    'results': consumer.results,
                    'statistics': stats
                }
                
                if consumer.exception:
                    all_success = False
                    errors.append(f"{consumer.name}: {consumer.exception}")
            
            self._increment_processed(self._producer.total_produced if hasattr(self._producer, 'total_produced') else 0)
            
            # 聚合性能指标
            metrics = {
                'execution_time': execution_time,
                'total_frames': self._producer.total_produced if hasattr(self._producer, 'total_produced') else 0,
                'consumer_count': len(self._consumers),
                'consumers': {
                    c.name: c.get_statistics() 
                    for c in self._consumers
                }
            }
            
            result = PipelineResult(
                success=all_success and not errors,
                output=results,
                metrics=metrics,
                warnings=errors if errors else []
            )
            
            status_str = "✓ " if result.success else "✗ "
            self._logger.info(
                f"{status_str}流式处理完成\n"
                f"  总耗时: {execution_time:.2f}s\n"
                f"  处理帧数: {metrics['total_frames']}\n"
                f"  消费者数: {len(self._consumers)}"
            )
            
            return result
            
        except Exception as e:
            self._logger.error(f"流式处理异常: {e}", exc_info=True)
            
            # 尝试优雅停止所有组件
            self._emergency_stop()
            
            return PipelineResult(
                success=False,
                error=f"流式处理失败: {e}",
                error_code=ErrorCode.PIPELINE_EXECUTION_FAILED
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        # 停止所有消费者
        for consumer in self._consumers:
            if consumer.is_running:
                consumer.stop()
        
        # 停止生产者
        if self._producer and self._producer.running:
            self._producer.stop()
        
        self._consumer_threads.clear()
        self._logger.info("Streaming Pipeline 资源已释放")
    
    def _emergency_stop(self) -> None:
        """紧急停止所有组件"""
        self._logger.warning("执行紧急停止...")
        
        for consumer in self._consumers:
            try:
                consumer.stop()
            except Exception:
                pass
        
        if self._producer:
            try:
                self._producer.stop()
            except Exception:
                pass
    
    def add_quality_consumer(self, config: Optional[Dict] = None) -> 'QualityConsumerV2':
        """添加质量检测消费者"""
        consumer = QualityConsumerV2(config=config or {})
        self._consumers.append(consumer)
        return consumer
    
    def add_enhance_consumer(self, model=None, config: Optional[Dict] = None) -> 'EnhanceConsumerV2':
        """添加增强检测消费者"""
        consumer = EnhanceConsumerV2(model=model, config=config or {})
        self._consumers.append(consumer)
        return consumer
    
    def add_custom_consumer(self, consumer_class: Type[BaseConsumer], **kwargs) -> BaseConsumer:
        """
        添加自定义消费者
        
        Args:
            consumer_class: 消费者类（必须继承 BaseConsumer）
            **kwargs: 传递给消费者构造函数的参数
            
        Returns:
            创建的消费者实例
        """
        if not issubclass(consumer_class, BaseConsumer):
            raise ValueError(
                f"consumer_class 必须继承 BaseConsumer，"
                f"但得到: {consumer_class.__name__}"
            )
        
        consumer = consumer_class(**kwargs)
        self._consumers.append(consumer)
        return consumer


class FrameProducerV2:
    """
    帧生产者 V2 - 增强版
    
    改进：
    - 完善的错误处理
    - 性能统计
    - 进度回调
    - 超时控制
    """
    
    def __init__(self, source_dir: str, max_queue_size: int = 30, logger=None):
        self.source_dir = source_dir
        self.max_queue_size = max_queue_size
        self.logger = logger or logging.getLogger(__name__)
        
        self.consumer_queues: Dict[str, queue.Queue] = {}
        self.running = False
        self.thread = None
        self.total_produced = 0
        self.total_skipped = 0
        
        # 回调
        self._progress_callback: Optional[Callable] = None
    
    def register_consumer(self, consumer_name: str) -> queue.Queue:
        q = queue.Queue(maxsize=self.max_queue_size)
        self.consumer_queues[consumer_name] = q
        return q
    
    def on_progress(self, callback: Callable) -> None:
        """注册进度回调"""
        self._progress_callback = callback
    
    def start(self) -> None:
        self.running = True
        self.thread = threading.Thread(target=self._produce, name="FrameProducer")
        self.thread.start()
        self.logger.info(f"帧生产者启动，目录: {self.source_dir}")
    
    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        self.logger.info("帧生产者已停止")
    
    def _produce(self) -> None:
        import cv2
        from pathlib import Path
        
        try:
            frame_files = []
            for ext in StreamingPipeline.SUPPORTED_IMAGE_EXTENSIONS:
                frame_files.extend(sorted(Path(self.source_dir).glob(ext)))
            
            total_frames = len(frame_files)
            self.logger.info(f"发现 {total_frames} 帧图像")
            
            for idx, frame_path in enumerate(frame_files):
                if not self.running:
                    break
                
                frame = cv2.imread(str(frame_path))
                if frame is None:
                    self.logger.warning(f"无法读取帧: {frame_path.name}，跳过")
                    self.total_skipped += 1
                    continue
                
                frame_name = frame_path.name
                frame_data = (frame, frame_name, idx)
                
                for name, q in self.consumer_queues.items():
                    try:
                        q.put(frame_data, block=True, timeout=5)
                    except queue.Full:
                        self.logger.error(f"队列 {name} 已满，生产者等待超时")
                        q.put(frame_data, block=True)
                
                self.total_produced += 1
                
                # 进度回调
                if self._progress_callback and (idx + 1) % 10 == 0:
                    try:
                        self._progress_callback(idx + 1, total_frames)
                    except Exception:
                        pass
                
                if (idx + 1) % 100 == 0:
                    self.logger.info(f"已生产 {idx+1}/{total_frames} 帧")
            
            # 发送终止信号
            for q in self.consumer_queues.values():
                q.put(None, block=True)
            
            self.logger.info(
                f"生产完成，共 {self.total_produced} 帧 "
                f"(跳过 {self.total_skipped})"
            )
            
        except Exception as e:
            self.logger.error(f"生产者线程异常: {e}")


class QualityConsumerV2(BaseConsumer):
    """质量检测消费者 V2"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("quality", config)
        self.blur_threshold = self.config.get('blur_threshold', default=100)
    
    def process_frame(self, frame_data: FrameData) -> Dict[str, Any]:
        import cv2
        import numpy as np
        
        gray = cv2.cvtColor(frame_data.frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        mean_brightness = np.mean(gray)
        
        return {
            'frame_idx': frame_data.frame_idx,
            'frame_name': frame_data.frame_name,
            'blur_score': float(laplacian_var),
            'brightness': float(mean_brightness),
            'is_blurry': bool(laplacian_var < self.blur_threshold)
        }


class EnhanceConsumerV2(BaseConsumer):
    """增强检测消费者 V2"""
    
    def __init__(self, model=None, config: Optional[Dict] = None):
        super().__init__("enhance", config)
        self.model = model
        self.conf_thres = self.config.get('conf_threshold', default=0.25)
        self.image_width = None
        self.image_height = None
    
    def process_frame(self, frame_data: FrameData) -> Dict[str, Any]:
        if self.image_width is None:
            self.image_height, self.image_width = frame_data.frame.shape[:2]
        
        if self.model is None:
            return {
                'frame_idx': frame_data.frame_idx,
                'frame_name': frame_data.frame_name,
                'detections': [],
                'model_available': False
            }
        
        results = self.model(frame_data.frame, conf=self.conf_thres, verbose=False)
        
        detections = []
        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            
            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                detections.append({
                    'bbox': box.tolist(),
                    'confidence': float(conf),
                    'class_id': int(cls_id)
                })
        
        return {
            'frame_idx': frame_data.frame_idx,
            'frame_name': frame_data.frame_name,
            'detections': detections,
            'width': self.image_width,
            'height': self.image_height,
            'model_available': True
        }


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="流式处理模块 (v2.0)")
    parser.add_argument("--input", required=True, help="图像目录")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    setup_logging(level="INFO")
    logger = get_logger("streaming")
    logger.info(f"Streaming Pipeline v{StreamingPipeline.VERSION} 启动")
    
    pipeline = StreamingPipeline(source_dir=args.input, config_path=args.config)
    
    # 默认添加质量检测消费者
    pipeline.add_quality_consumer()
    
    result = pipeline.run()
    
    if result.success:
        logger.info("✓ 流式处理成功")
        print(f"\n结果摘要:")
        for name, data in result.output.items():
            stats = data['statistics']
            print(f"  {name}: 处理 {stats['processed_count']} 帧, "
                  f"FPS: {stats['throughput_fps']:.1f}")
        sys.exit(0)
    else:
        logger.error(f"✗ 流式处理失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
