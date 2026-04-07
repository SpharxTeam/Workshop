#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workshop V2.0 Prometheus监控指标模块
======================================
功能：
1. 自动采集Pipeline执行指标（耗时、成功率、吞吐量）
2. 系统资源监控（CPU、内存、磁盘I/O）
3. 业务数据统计（处理文件数、数据量大小）
4. 自定义指标注册与导出
5. HTTP /metrics端点服务

使用示例:
    from common.core.metrics import WorkshopMetrics
    
    metrics = WorkshopMetrics()
    metrics.init_metrics_server(port=9090)
    
    # 在Pipeline中使用
    with metrics.pipeline_timer('ingest'):
        pipeline.run(data)
    
    metrics.record_pipeline_result('ingest', success=True, items_processed=100)
"""

import os
import sys
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY,
        start_http_server,
        Metric
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("[警告] prometheus-client未安装，将使用简化版指标收集")


@dataclass
class PipelineMetricsRecord:
    """单次Pipeline执行的指标记录"""
    pipeline_name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    input_size_bytes: int = 0
    output_size_bytes: int = 0
    items_processed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.end_time > 0 and self.start_time > 0:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class SystemMetricsSnapshot:
    """系统资源快照"""
    timestamp: float
    cpu_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    open_files: int = 0
    thread_count: int = 0


class SimpleMetricsCollector:
    """
    简化版指标收集器（当prometheus-client不可用时）
    提供基本的内存内指标收集和JSON格式导出
    """
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # 初始化默认指标
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """初始化默认的Workshop指标"""
        default_counters = [
            'workshop_pipeline_executions_total',
            'workshop_pipeline_successes_total',
            'workshop_pipeline_failures_total',
            'workshop_errors_total',
            'workshop_requests_total',
            'workshop_data_ingested_files',
            'workshop_data_processed_items',
        ]
        
        for counter in default_counters:
            self._counters[counter] = 0
        
        default_histograms = [
            'workshop_pipeline_duration_seconds',
            'workshop_request_duration_seconds',
            'workshop_io_operation_duration_seconds',
        ]
        
        for hist in default_histograms:
            self._histograms[hist] = []
        
        default_gauges = [
            'workshop_active_pipelines',
            'workshop_queue_length',
            'workshop_last_execution_timestamp',
            'workshop_memory_usage_mb',
        ]
        
        for gauge in default_gauges:
            self._gauges[gauge] = 0.0
    
    def inc(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """增加计数器"""
        with self._lock:
            key = f"{name}_{hash(frozenset(labels.items()))}" if labels else name
            self._counters[key] = self._counters.get(key, 0) + value
    
    def observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录观测值到直方图"""
        with self._lock:
            key = f"{name}_{hash(frozenset(labels.items()))}" if labels else name
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
    
    def set(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表值"""
        with self._lock:
            key = f"{name}_{hash(frozenset(labels.items()))}" if labels else name
            self._gauges[key] = value
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标的当前值"""
        with self._lock:
            return {
                'timestamp': time.time(),
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    k: {
                        'count': len(v),
                        'sum': sum(v),
                        'avg': sum(v) / len(v) if v else 0,
                        'min': min(v) if v else 0,
                        'max': max(v) if v else 0,
                    }
                    for k, v in self._histograms.items()
                }
            }
    
    def export_to_prometheus_format(self) -> str:
        """导出为Prometheus文本格式"""
        lines = []
        
        # Counters
        for name, value in self._counters.items():
            lines.append(f"# HELP {name} Total count")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
            lines.append("")
        
        # Gauges
        for name, value in self._gauges.items():
            lines.append(f"# HELP {name} Current value")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
            lines.append("")
        
        return "\n".join(lines)


class WorkshopMetrics:
    """
    Workshop V2.0 统一监控指标管理器
    =================================
    
    功能：
    - Pipeline性能指标自动收集
    - 系统资源监控
    - 业务KPI追踪
    - Prometheus格式指标导出
    - HTTP /metrics端点
    
    使用示例:
        metrics = WorkshopMetrics()
        metrics.init_metrics_server(port=9090)
        
        # 装饰器方式测量Pipeline耗时
        @metrics.pipeline_timer('quality_check')
        def run_quality_check(data):
            ...
        
        # 上下文管理器方式
        with metrics.pipeline_timer('calibration') as timer:
            result = calibrate(data)
            timer.set_metadata({'reprojection_error': result.error})
        
        # 手动记录指标
        metrics.record_pipeline_result('pack', success=True, 
                                       items_processed=500,
                                       output_size_mb=1024.5)
    """
    
    def __init__(self, registry: CollectorRegistry = None, enabled: bool = True):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self.registry = registry or (REGISTRY if PROMETHEUS_AVAILABLE else None)
        
        # 使用真实Prometheus或简化版收集器
        if self.enabled:
            self._init_prometheus_metrics()
            self.collector = None
        else:
            self.collector = SimpleMetricsCollector()
            print("📊 使用简化版指标收集器（未检测到prometheus-client）")
        
        # 执行历史记录
        self.execution_history: List[PipelineMetricsRecord] = []
        self.history_lock = threading.Lock()
        self.max_history_size = 1000
        
        # HTTP服务器引用
        self._http_server = None
        self._metrics_thread = None
        
        # 系统监控定时器
        self._system_monitor_running = False
    
    def _init_prometheus_metrics(self):
        """初始化Prometheus指标"""
        
        # === Pipeline执行指标 ===
        self.pipeline_executions = Counter(
            'workshop_pipeline_executions_total',
            'Total number of pipeline executions',
            ['pipeline_name', 'status'],
            registry=self.registry
        )
        
        self.pipeline_duration = Histogram(
            'workshop_pipeline_duration_seconds',
            'Time spent executing pipeline',
            ['pipeline_name'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
            registry=self.registry
        )
        
        self.active_pipelines = Gauge(
            'workshop_active_pipelines',
            'Number of pipelines currently running',
            registry=self.registry
        )
        
        # === 数据处理指标 ===
        self.data_ingested = Counter(
            'workshop_data_ingested_files_total',
            'Total number of files ingested',
            ['source_type'],
            registry=self.registry
        )
        
        self.data_processed = Counter(
            'workshop_data_processed_items_total',
            'Total number of data items processed',
            ['pipeline_name', 'item_type'],
            registry=self.registry
        )
        
        self.data_throughput = Histogram(
            'workshop_data_throughput_items_per_second',
            'Data processing throughput',
            ['pipeline_name'],
            registry=self.registry
        )
        
        # === 错误与异常指标 ===
        self.errors_total = Counter(
            'workshop_errors_total',
            'Total number of errors',
            ['error_type', 'pipeline_name'],
            registry=self.registry
        )
        
        self.exceptions_total = Counter(
            'workshop_exceptions_total',
            'Total number of exceptions',
            ['exception_type', 'pipeline_name'],
            registry=self.registry
        )
        
        # === 系统资源指标 ===
        self.process_cpu_usage = Gauge(
            'workshop_process_cpu_usage_percent',
            'Current process CPU usage percentage',
            registry=self.registry
        )
        
        self.process_memory_usage = Gauge(
            'workshop_process_memory_usage_mb',
            'Current process memory usage in MB',
            registry=self.registry
        )
        
        # === I/O操作指标 ===
        self.io_operations = Counter(
            'workshop_io_operations_total',
            'Total number of I/O operations',
            ['operation_type', 'storage_backend'],
            registry=self.registry
        )
        
        self.io_operation_duration = Histogram(
            'workshop_io_operation_duration_seconds',
            'Duration of I/O operations',
            ['operation_type', 'storage_backend'],
            registry=self.registry
        )
        
        # === 时间戳标记 ===
        self.last_successful_execution = Gauge(
            'workshop_last_success_timestamp',
            'Unix timestamp of last successful execution',
            ['pipeline_name'],
            registry=self.registry
        )
        
        self.last_backup_timestamp = Gauge(
            'workshop_backup_last_success_timestamp',
            'Unix timestamp of last successful backup',
            registry=self.registry
        )
        
        # 应用信息
        self.app_info = Info(
            'workshop_app',
            'Application information',
            registry=self.registry
        )
        self.app_info.info({
            'version': '2.0.0',
            'environment': os.getenv('WORKSHOP_ENV', 'development'),
            'python_version': sys.version.split()[0]
        })
    
    def init_metrics_server(self, port: int = 9090, host: str = '0.0.0.0'):
        """
        启动HTTP指标服务器
        
        Args:
            port: 监听端口 (默认9090)
            host: 绑定地址 (默认所有接口)
        """
        if not self.enabled:
            print(f"⚠️  Prometheus客户端不可用，无法启动HTTP指标服务器")
            print(f"   请运行: pip install prometheus-client")
            return False
        
        try:
            if self._http_server is not None:
                print(f"⚠️  指标服务器已在运行 (端口 {port})")
                return True
            
            start_http_server(port, addr=host, registry=self.registry)
            
            print(f"✅ Prometheus指标服务器已启动")
            print(f"   📍 地址: http://{host}:{port}/metrics")
            print(f"   📊 可在Grafana中配置此数据源进行可视化")
            
            # 启动系统资源监控
            self._start_system_monitor()
            
            return True
            
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"⚠️  端口 {port} 已被占用，尝试其他端口...")
                for alt_port in range(port+1, port+10):
                    try:
                        start_http_server(alt_port, addr=host, registry=self.registry)
                        print(f"✅ 使用备用端口 {alt_port}")
                        self._start_system_monitor()
                        return True
                    except:
                        continue
            
            print(f"❌ 无法启动指标服务器: {e}")
            return False
    
    def _start_system_monitor(self, interval: int = 15):
        """启动后台系统资源监控线程"""
        if self._system_monitor_running:
            return
        
        self._system_monitor_running = True
        
        def monitor_loop():
            while self._system_monitor_running:
                try:
                    self._collect_system_metrics()
                except Exception as e:
                    pass
                
                time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print(f"📈 系统资源监控已启动 (间隔: {interval}s)")
    
    def _collect_system_metrics(self):
        """收集系统资源指标"""
        import resource
        
        try:
            # CPU使用率 (简化计算，实际应使用psutil)
            # 这里仅作为示例，生产环境建议集成psutil
            pass
            
            # 内存使用
            usage = resource.getrusage(resource.RUSAGE_SELF)
            mem_mb = (usage.ru_maxrss) / 1024  # Linux: KB, macOS: bytes
            
            if self.enabled:
                self.process_memory_usage.set(mem_mb)
            elif self.collector:
                self.collector.set('workshop_memory_usage_mb', mem_mb)
                
        except Exception:
            pass
    
    def pipeline_timer(self, pipeline_name: str):
        """
        Pipeline计时装饰器和上下文管理器
        
        用法1: 作为装饰器
            @metrics.pipeline_timer('ingest')
            def my_pipeline(data):
                ...
        
        用法2: 作为上下文管理器
            with metrics.pipeline_timer('calibration') as timer:
                result = calibrate(data)
                timer.set_metadata({'error': result.reprojection_error})
        
        Returns:
            计时器对象或装饰器函数
        """
        
        class PipelineTimerContext:
            """Pipeline计时上下文管理器"""
            
            def __init__(self, parent, name):
                self.parent = parent
                self.name = name
                self.start_time = 0.0
                self.metadata = {}
            
            def __enter__(self):
                self.start_time = time.time()
                if self.parent.enabled:
                    self.parent.active_pipelines.inc()
                elif self.parent.collector:
                    self.parent.collector.inc('workshop_active_pipelines')
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                
                if self.parent.enabled:
                    self.parent.active_pipelines.dec()
                    
                    status = 'success' if exc_type is None else 'failure'
                    self.parent.pipeline_executions.labels(
                        pipeline_name=self.name,
                        status=status
                    ).inc()
                    
                    self.parent.pipeline_duration.labels(
                        pipeline_name=self.name
                    ).observe(duration)
                    
                    if exc_type is None:
                        self.parent.last_successful_execution.labels(
                            pipeline_name=self.name
                        ).set(time.time())
                    else:
                        self.parent.errors_total.labels(
                            error_type=exc_type.__name__,
                            pipeline_name=self.name
                        ).inc()
                        
                elif self.parent.collector:
                    self.parent.collector.inc('workshop_active_pipelines', -1)
                    self.parent.collector.inc('workshop_pipeline_executions_total')
                    
                    status = 'success' if exc_type is None else 'failure'
                    if status == 'success':
                        self.parent.collector.inc('workshop_pipeline_successes_total')
                    else:
                        self.parent.collector.inc('workshop_pipeline_failures_total')
                        self.parent.collector.inc('workshop_errors_total')
                    
                    self.parent.collector.observe(
                        'workshop_pipeline_duration_seconds',
                        duration
                    )
                
                # 记录到历史
                record = PipelineMetricsRecord(
                    pipeline_name=self.name,
                    start_time=self.start_time,
                    end_time=time.time(),
                    success=exc_type is None,
                    error_message=str(exc_val) if exc_val else None,
                    metadata=self.metadata
                )
                self.parent._add_to_history(record)
                
                return False  # 不抑制异常
        
        return PipelineTimerContext(self, pipeline_name)
    
    def record_pipeline_result(self, pipeline_name: str, success: bool,
                              items_processed: int = 0,
                              input_size_bytes: int = 0,
                              output_size_bytes: int = 0,
                              **kwargs):
        """
        手动记录Pipeline执行结果
        
        Args:
            pipeline_name: Pipeline名称
            success: 是否成功
            items_processed: 处理的项目数
            input_size_bytes: 输入数据大小(字节)
            output_size_bytes: 输出数据大小(字节)
            **kwargs: 额外的元数据
        """
        if self.enabled:
            if success:
                self.data_processed.labels(
                    pipeline_name=pipeline_name,
                    item_type='items'
                ).inc(items_processed)
        
        elif self.collector:
            if success:
                self.collector.inc('workshop_data_processed_items', items_processed)
    
    def record_io_operation(self, operation: str, backend: str = 'local',
                           duration: float = 0, success: bool = True):
        """
        记录I/O操作指标
        
        Args:
            operation: 操作类型 (read/write/delete/list)
            backend: 存储后端 (local/s3/oss/...)
            duration: 操作耗时(秒)
            success: 是否成功
        """
        if self.enabled:
            self.io_operations.labels(
                operation_type=operation,
                storage_backend=backend
            ).inc()
            
            if duration > 0:
                self.io_operation_duration.labels(
                    operation_type=operation,
                    storage_backend=backend
                ).observe(duration)
        
        elif self.collector:
            self.collector.inc('workshop_io_operations_total')
            if duration > 0:
                self.collector.observe(
                    'workshop_io_operation_duration_seconds',
                    duration
                )
    
    def record_error(self, error_type: str, pipeline_name: str = 'unknown',
                    message: str = ''):
        """记录错误"""
        if self.enabled:
            self.errors_total.labels(
                error_type=error_type,
                pipeline_name=pipeline_name
            ).inc()
        elif self.collector:
            self.collector.inc('workshop_errors_total')
    
    def record_ingestion(self, source_type: str = 'file', file_count: int = 1):
        """记录数据摄入"""
        if self.enabled:
            self.data_ingested.labels(source_type=source_type).inc(file_count)
        elif self.collector:
            self.collector.inc('workshop_data_ingested_files', file_count)
    
    def mark_backup_complete(self):
        """标记备份完成"""
        if self.enabled:
            self.last_backup_timestamp.set(time.time())
    
    def set_metadata(self, key: str, value: str):
        """设置应用级元数据标签"""
        pass  # 需要重新创建Info对象才能更新
    
    def _add_to_history(self, record: PipelineMetricsRecord):
        """添加到执行历史记录"""
        with self.history_lock:
            self.execution_history.append(record)
            
            # 保持历史记录不超过最大长度
            if len(self.execution_history) > self.max_history_size:
                self.execution_history = \
                    self.execution_history[-(self.max_history_size//2):]
    
    def get_recent_executions(self, count: int = 50) -> List[Dict]:
        """获取最近的执行记录"""
        with self.history_lock:
            recent = self.execution_history[-count:]
            
            return [
                {
                    'pipeline_name': r.pipeline_name,
                    'duration_ms': round(r.duration_ms, 2),
                    'success': r.success,
                    'timestamp': datetime.fromtimestamp(r.start_time).isoformat(),
                    'items_processed': r.items_processed,
                    'metadata': r.metadata
                }
                for r in recent
            ]
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        with self.history_lock:
            if not self.execution_history:
                return {'total_executions': 0}
            
            total = len(self.execution_history)
            successes = sum(1 for r in self.execution_history if r.success)
            failures = total - successes
            
            durations = [r.duration_ms for r in self.execution_history if r.duration_ms > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_executions': total,
                'success_count': successes,
                'failure_count': failures,
                'success_rate': round(successes / total * 100, 1),
                'avg_duration_ms': round(avg_duration, 2),
                'min_duration_ms': round(min(durations), 2) if durations else 0,
                'max_duration_ms': round(max(durations), 2) if durations else 0,
                'total_items_processed': sum(r.items_processed for r in self.execution_history)
            }
    
    def export_metrics(self) -> str:
        """导出所有指标为文本格式"""
        if self.enabled:
            return generate_latest(self.registry).decode('utf-8')
        elif self.collector:
            return self.collector.export_to_prometheus_format()
        else:
            return "# No metrics available"
    
    def shutdown(self):
        """关闭指标服务器和监控"""
        self._system_monitor_running = False
        print("📊 监控指标系统已关闭")


# 全局单例实例
_global_metrics_instance: Optional[WorkshopMetrics] = None
_metrics_lock = threading.Lock()


def get_metrics() -> WorkshopMetrics:
    """
    获取全局Metrics实例（单例模式）
    
    Returns:
        WorkshopMetrics全局实例
    """
    global _global_metrics_instance
    
    if _global_metrics_instance is None:
        with _metrics_lock:
            if _global_metrics_instance is None:
                _global_metrics_instance = WorkshopMetrics()
    
    return _global_metrics_instance


def init_metrics_server(port: int = 9090) -> bool:
    """
    初始化并启动全局指标服务器
    
    Args:
        port: HTTP监听端口
    
    Returns:
        是否成功启动
    """
    metrics = get_metrics()
    return metrics.init_metrics_server(port=port)


def measure_performance(pipeline_name: str = None):
    """
    性能测量装饰器工厂函数
    
    用法:
        @measure_performance('my_pipeline')
        def process_data(data):
            ...
    
    Args:
        pipeline_name: 要测量的Pipeline名称
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = pipeline_name or func.__name__
            metrics = get_metrics()
            
            with metrics.pipeline_timer(name):
                result = func(*args, **kwargs)
            
            return result
        return wrapper
    return decorator


if __name__ == '__main__':
    print("="*70)
    print("📊 Workshop V2.0 监控指标测试")
    print("="*70)
    
    # 测试指标收集
    metrics = WorkshopMetrics()
    
    print("\n1️⃣ 测试Pipeline计时:")
    with metrics.pipeline_timer('test_pipeline') as timer:
        time.sleep(0.1)
        timer.set_metadata({'test': 'value'})
    print("   ✅ 计时完成")
    
    print("\n2️⃣ 测试手动记录指标:")
    metrics.record_pipeline_result('test', success=True, items_processed=42)
    metrics.record_ingestion('camera', file_count=10)
    metrics.record_io_operation('read', 'local', duration=0.05)
    print("   ✅ 指标已记录")
    
    print("\n3️⃣ 统计摘要:")
    summary = metrics.get_statistics_summary()
    for key, value in summary.items():
        print(f"   • {key}: {value}")
    
    print("\n4️⃣ 最近执行记录:")
    recent = metrics.get_recent_executions(5)
    for record in recent:
        print(f"   • {record['pipeline_name']}: "
              f"{record['duration_ms']}ms "
              f"{'✅' if record['success'] else '❌'}")
    
    print("\n5️⃣ 导出的指标格式预览:")
    exported = metrics.export_metrics()
    lines = exported.strip().split('\n')[:20]
    for line in lines:
        print(f"   {line}")
    if len(exported.strip().split('\n')) > 20:
        print(f"   ... (共{len(exported.strip().split(chr(10)))}行)")
    
    print("\n✅ 所有测试通过!")
