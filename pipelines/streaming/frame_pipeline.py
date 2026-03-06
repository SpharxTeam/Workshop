# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 流式处理框架：基于生产者-消费者模型的异步流水线，支持多种图像格式（jpg, webp, png）

import queue
import threading
import cv2
import numpy as np
import logging
import traceback

logger = logging.getLogger(__name__)

class FrameProducer:
    """帧生产者：从图像目录读取帧，推入多个消费者队列"""
    
    def __init__(self, source_dir: str, max_queue_size: int = 30):
        self.source_dir = source_dir
        self.max_queue_size = max_queue_size
        self.consumer_queues: Dict[str, queue.Queue] = {}
        self.running = False
        self.thread = None
    
    def register_consumer(self, consumer_name: str) -> queue.Queue:
        q = queue.Queue(maxsize=self.max_queue_size)
        self.consumer_queues[consumer_name] = q
        return q
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._produce, name="Producer")
        self.thread.start()
        logger.info(f"帧生产者启动，目录: {self.source_dir}")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        logger.info("帧生产者已停止")
    
    def _produce(self):
        import os
        from pathlib import Path
        
        try:
            frame_files = []
            for ext in ['*.jpg', '*.jpeg', '*.webp', '*.png']:
                frame_files.extend(sorted(Path(self.source_dir).glob(ext)))
            
            total_frames = len(frame_files)
            logger.info(f"发现 {total_frames} 帧图像")
            
            for idx, frame_path in enumerate(frame_files):
                if not self.running:
                    break
                
                frame = cv2.imread(str(frame_path))
                if frame is None:
                    logger.warning(f"无法读取帧: {frame_path.name}，跳过")
                    continue
                
                frame_name = frame_path.name
                for name, q in self.consumer_queues.items():
                    try:
                        q.put((frame, frame_name, idx), block=True, timeout=5)
                    except queue.Full:
                        logger.error(f"队列 {name} 已满，生产者等待超时")
                        q.put((frame, frame_name, idx), block=True)
                
                if (idx + 1) % 100 == 0:
                    logger.info(f"已生产 {idx+1}/{total_frames} 帧")
            
            for q in self.consumer_queues.values():
                q.put(None, block=True)
            
            logger.info(f"生产完成，共 {total_frames} 帧")
        except Exception as e:
            logger.error(f"生产者线程异常: {e}")


class FrameConsumer(threading.Thread):
    """帧消费者基类"""
    
    def __init__(self, name: str, queue: queue.Queue):
        super().__init__(name=name)
        self.name = name
        self.queue = queue
        self.running = False
        self.processed_count = 0
        self.results = []
        self.exception = None
    
    def run(self):
        self.running = True
        logger.info(f"消费者 {self.name} 启动")
        
        try:
            while self.running:
                try:
                    item = self.queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if item is None:
                    break
                
                frame, frame_name, idx = item
                try:
                    self.process_frame(frame, frame_name, idx)
                except Exception as e:
                    logger.error(f"消费者 {self.name} 处理帧 {frame_name} 时出错: {e}")
                self.processed_count += 1
                self.queue.task_done()
                
                if self.processed_count % 100 == 0:
                    logger.info(f"消费者 {self.name} 已处理 {self.processed_count} 帧")
            
            logger.info(f"消费者 {self.name} 结束，处理 {self.processed_count} 帧")
        except Exception as e:
            logger.error(f"消费者 {self.name} 发生异常: {e}")
            self.exception = e
        finally:
            self.running = False
    
    def process_frame(self, frame: np.ndarray, frame_name: str, frame_idx: int):
        raise NotImplementedError


class QualityConsumer(FrameConsumer):
    def __init__(self, queue: queue.Queue, config: dict = None):
        super().__init__("quality", queue)
        self.config = config or {}
        self.blur_threshold = self.config.get('blur_threshold', 100)
    
    def process_frame(self, frame: np.ndarray, frame_name: str, frame_idx: int):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        mean_brightness = np.mean(gray)
        
        self.results.append({
            'frame_idx': frame_idx,
            'frame_name': frame_name,
            'blur_score': float(laplacian_var),
            'brightness': float(mean_brightness),
            'is_blurry': bool(laplacian_var < self.blur_threshold)
        })


class EnhanceConsumer(FrameConsumer):
    def __init__(self, queue: queue.Queue, model, config: dict = None):
        super().__init__("enhance", queue)
        self.model = model
        self.config = config or {}
        self.conf_thres = self.config.get('conf_threshold', 0.25)
        self.image_width = None
        self.image_height = None
    
    def process_frame(self, frame: np.ndarray, frame_name: str, frame_idx: int):
        if self.image_width is None:
            self.image_height, self.image_width = frame.shape[:2]
        
        results = self.model(frame, conf=self.conf_thres, verbose=False)
        
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
        
        self.results.append({
            'frame_idx': frame_idx,
            'frame_name': frame_name,
            'detections': detections,
            'width': self.image_width,
            'height': self.image_height
        })


class PipelineOrchestrator:
    def __init__(self, source_dir: str, max_queue_size: int = 30):
        self.producer = FrameProducer(source_dir, max_queue_size)
        self.consumers: List[FrameConsumer] = []
    
    def add_quality_consumer(self, config: dict = None) -> QualityConsumer:
        q = self.producer.register_consumer("quality")
        consumer = QualityConsumer(q, config or {})
        self.consumers.append(consumer)
        return consumer
    
    def add_enhance_consumer(self, model, config: dict = None) -> EnhanceConsumer:
        q = self.producer.register_consumer("enhance")
        consumer = EnhanceConsumer(q, model, config or {})
        self.consumers.append(consumer)
        return consumer
    
    def run(self):
        self.producer.start()
        for consumer in self.consumers:
            consumer.start()
        
        self.producer.thread.join()
        for consumer in self.consumers:
            consumer.join()
        
        for consumer in self.consumers:
            if consumer.exception:
                logger.error(f"消费者 {consumer.name} 发生异常")
        
        logger.info("流水线处理完成")
        return {c.name: c.results for c in self.consumers}