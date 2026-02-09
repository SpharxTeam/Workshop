"""
高级流水线管理器
负责任务队列、调度、监控和作业管理
与 pipeline_controller.py 分工：
- manager: 高级任务管理、队列、调度、监控
- controller: 具体流水线协调、模块调用
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

from src.schemas.task import PipelineTask, ProcessingStatus, PipelineResult
from src.schemas.scene import SceneMetadata
from src.utils.logging import PipelineLogger

logger = logging.getLogger(__name__)


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("/home/SpharxWorkshop/workspace/tasks")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.pending_tasks: List[PipelineTask] = []
        self.running_tasks: Dict[str, PipelineTask] = {}
        self.completed_tasks: Dict[str, PipelineTask] = {}
        self.logger = PipelineLogger("task_queue")
        
    def add_task(self, task: PipelineTask) -> str:
        """添加任务到队列"""
        task.id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task.scene_id}"
        task.submitted_at = datetime.now()
        task.status = ProcessingStatus.PENDING
        
        # 保存任务到文件
        task_file = self.storage_path / f"{task.id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task.dict(), f, indent=2, default=str)
        
        self.pending_tasks.append(task)
        self.logger.info(f"任务已添加: {task.id} - {task.scene_id} - {task.pipeline_type}")
        return task.id
    
    def get_task(self, task_id: str) -> Optional[PipelineTask]:
        """获取任务信息"""
        # 首先在内存中查找
        for task in self.pending_tasks:
            if task.id == task_id:
                return task
        
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        # 从文件加载
        task_file = self.storage_path / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
                return PipelineTask(**task_data)
        
        return None
    
    def update_task_status(self, task_id: str, status: ProcessingStatus, 
                          result: Optional[PipelineResult] = None,
                          error_message: Optional[str] = None):
        """更新任务状态"""
        task = self.get_task(task_id)
        if not task:
            self.logger.warning(f"任务不存在: {task_id}")
            return
        
        task.status = status
        
        if status == ProcessingStatus.PROCESSING and not task.started_at:
            task.started_at = datetime.now()
        elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
            task.completed_at = datetime.now()
        
        if result:
            task.result = result
        if error_message:
            task.error_message = error_message
        
        # 移动任务到相应的列表
        if status == ProcessingStatus.PROCESSING:
            if task in self.pending_tasks:
                self.pending_tasks.remove(task)
            self.running_tasks[task_id] = task
        elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            self.completed_tasks[task_id] = task
        
        # 保存更新
        task_file = self.storage_path / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task.dict(), f, indent=2, default=str)
        
        self.logger.info(f"任务状态更新: {task_id} -> {status}")


class PipelineMonitor:
    """流水线监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_processing_time': 0.0,
            'current_tasks': {}
        }
        self.logger = PipelineLogger("monitor")
        
    def update_task_metrics(self, task: PipelineTask):
        """更新任务指标"""
        self.metrics['current_tasks'][task.id] = {
            'scene_id': task.scene_id,
            'pipeline_type': task.pipeline_type,
            'status': task.status,
            'progress': task.progress,
            'submitted_at': task.submitted_at,
            'started_at': task.started_at,
            'last_update': datetime.now()
        }
        
        # 更新统计
        if task.status == ProcessingStatus.COMPLETED:
            self.metrics['completed_tasks'] += 1
            if task.processing_time:
                total_time = self.metrics['avg_processing_time'] * (self.metrics['completed_tasks'] - 1)
                self.metrics['avg_processing_time'] = (total_time + task.processing_time) / self.metrics['completed_tasks']
        elif task.status == ProcessingStatus.FAILED:
            self.metrics['failed_tasks'] += 1
        
        self.metrics['total_tasks'] = len(self.metrics['current_tasks'])
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取监控仪表板数据"""
        return {
            **self.metrics,
            'timestamp': datetime.now().isoformat(),
            'system_status': 'healthy' if self.metrics['failed_tasks'] < 5 else 'warning'
        }


class PipelineManager:
    """高级流水线管理器（主入口）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.task_queue = TaskQueue()
        self.monitor = PipelineMonitor()
        self.logger = PipelineLogger("manager")
        self._stop_event = asyncio.Event()
        
    async def initialize(self):
        """初始化管理器"""
        self.logger.info("流水线管理器初始化...")
        # 加载已存在的任务
        self._load_existing_tasks()
        
    def _load_existing_tasks(self):
        """加载已存在的任务文件"""
        task_files = list(self.task_queue.storage_path.glob("task_*.json"))
        for task_file in task_files:
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                    task = PipelineTask(**task_data)
                    
                    # 根据状态添加到相应列表
                    if task.status == ProcessingStatus.PENDING:
                        self.task_queue.pending_tasks.append(task)
                    elif task.status == ProcessingStatus.PROCESSING:
                        self.task_queue.running_tasks[task.id] = task
                    elif task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
                        self.task_queue.completed_tasks[task.id] = task
                    
                    self.monitor.update_task_metrics(task)
                    
            except Exception as e:
                self.logger.warning(f"加载任务文件失败 {task_file}: {e}")
    
    async def submit_pipeline_task(
        self,
        scene_id: str,
        pipeline_type: str = "2d",
        priority: int = 1,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        提交流水线任务
        
        Args:
            scene_id: 场景ID
            pipeline_type: 流水线类型 (2d, 3d, full)
            priority: 任务优先级 (1-10)
            config_overrides: 配置覆盖
            
        Returns:
            任务ID
        """
        from src.schemas.task import PipelineTask
        
        task = PipelineTask(
            scene_id=scene_id,
            pipeline_type=pipeline_type,
            priority=priority,
            config_overrides=config_overrides or {}
        )
        
        task_id = self.task_queue.add_task(task)
        self.monitor.update_task_metrics(task)
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task_id))
        
        return task_id
    
    async def _execute_task(self, task_id: str):
        """执行任务"""
        task = self.task_queue.get_task(task_id)
        if not task:
            self.logger.error(f"任务不存在: {task_id}")
            return
        
        # 更新状态为处理中
        self.task_queue.update_task_status(task_id, ProcessingStatus.PROCESSING)
        
        try:
            # 导入控制器（避免循环导入）
            from src.pipelines.pipeline_controller import PipelineController
            from src.schemas.config import PipelineConfig
            
            # 加载配置
            config = PipelineConfig()
            
            # 应用任务特定的配置覆盖
            for key, value in task.config_overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # 创建控制器并执行
            controller = PipelineController(config)
            
            if task.pipeline_type == "2d":
                result_data = await controller.run_2d_pipeline(task.scene_id)
            elif task.pipeline_type == "3d":
                result_data = await controller.run_3d_pipeline(task.scene_id)
            elif task.pipeline_type == "full":
                result_data = await controller.run_full_pipeline(task.scene_id)
            else:
                raise ValueError(f"未知的流水线类型: {task.pipeline_type}")
            
            # 创建成功结果
            result = PipelineResult(
                success=True,
                scene_id=task.scene_id,
                pipeline_type=task.pipeline_type,
                output_path=result_data.get('output_path'),
                metadata=result_data
            )
            
            # 更新任务状态
            self.task_queue.update_task_status(
                task_id, 
                ProcessingStatus.COMPLETED,
                result=result
            )
            
            self.logger.info(f"任务完成: {task_id}")
            
        except Exception as e:
            self.logger.error(f"任务执行失败 {task_id}: {e}", exc_info=True)
            
            # 创建失败结果
            result = PipelineResult(
                success=False,
                scene_id=task.scene_id,
                pipeline_type=task.pipeline_type,
                error_message=str(e)
            )
            
            # 更新任务状态
            self.task_queue.update_task_status(
                task_id,
                ProcessingStatus.FAILED,
                result=result,
                error_message=str(e)
            )
        
        finally:
            # 更新监控指标
            task = self.task_queue.get_task(task_id)
            if task:
                self.monitor.update_task_metrics(task)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.task_queue.get_task(task_id)
        if not task:
            return None
        
        return {
            'id': task.id,
            'scene_id': task.scene_id,
            'pipeline_type': task.pipeline_type,
            'status': task.status,
            'progress': task.progress,
            'submitted_at': task.submitted_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'processing_time': task.processing_time,
            'error_message': task.error_message,
            'result': task.result.dict() if task.result else None
        }
    
    async def get_task_list(self, status_filter: Optional[str] = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务列表"""
        tasks = []
        
        if not status_filter or status_filter == "pending":
            tasks.extend(self.task_queue.pending_tasks)
        
        if not status_filter or status_filter == "processing":
            tasks.extend(list(self.task_queue.running_tasks.values()))
        
        if not status_filter or status_filter in ["completed", "failed", "cancelled"]:
            tasks.extend(list(self.task_queue.completed_tasks.values()))
        
        # 按优先级和提交时间排序
        tasks.sort(key=lambda x: (-x.priority, x.submitted_at or datetime.min))
        
        # 转换为字典格式
        return [
            {
                'id': task.id,
                'scene_id': task.scene_id,
                'pipeline_type': task.pipeline_type,
                'status': task.status,
                'priority': task.priority,
                'submitted_at': task.submitted_at,
                'progress': task.progress
            }
            for task in tasks[:limit]
        ]
    
    async def get_monitor_dashboard(self) -> Dict[str, Any]:
        """获取监控仪表板数据"""
        return self.monitor.get_dashboard_data()
    
    async def stop(self):
        """停止管理器"""
        self._stop_event.set()
        self.logger.info("流水线管理器已停止")


# 单例实例
_manager_instance: Optional[PipelineManager] = None

def get_pipeline_manager() -> PipelineManager:
    """获取流水线管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PipelineManager()
    return _manager_instance
    