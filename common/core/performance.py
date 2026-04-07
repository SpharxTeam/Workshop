# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 性能基准测试套件 - 参考 AgentOS 性能监控设计
# 提供全面的性能测量、分析和报告功能

import sys
import time
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple, TypeVar
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
import threading

sys.path.insert(0, '/app/common/scripts')

T = TypeVar('T')


@dataclass
class PerformanceMetric:
    """性能指标数据点"""
    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp,
            'tags': self.tags
        }


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    iterations: int = 0
    total_time_s: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = 0.0
    max_time_ms: float = 0.0
    median_time_ms: float = 0.0
    p95_time_ms: float = 0.0  # 95th percentile
    p99_time_ms: float = 0.0  # 99th percentile
    std_dev_ms: float = 0.0
    throughput: Optional[float] = None  # ops/s
    metrics: List[PerformanceMetric] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'iterations': self.iterations,
            'total_time_s': round(self.total_time_s, 4),
            'avg_time_ms': round(self.avg_time_ms, 4),
            'min_time_ms': round(self.min_time_ms, 4),
            'max_time_ms': round(self.max_time_ms, 4),
            'median_time_ms': round(self.median_time_ms, 4),
            'p95_time_ms': round(self.p95_time_ms, 4),
            'p99_time_ms': round(self.p99_time_ms, 4),
            'std_dev_ms': round(self.std_dev_ms, 4),
            'throughput': f"{self.throughput:.2f} ops/s" if self.throughput else None,
            'metrics': [m.to_dict() for m in self.metrics]
        }


class PerformanceTimer:
    """
    高精度性能计时器
    
    功能：
    - 微秒级计时精度
    - 上下文管理器支持
    - 装饰器支持
    - 自动统计收集
    """
    
    def __init__(self, name: str = ""):
        self.name = name
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._elapsed: float = 0.0
        self._running = False
        self._laps: List[Tuple[str, float]] = []
    
    def start(self):
        """开始计时"""
        self._start_time = time.perf_counter()
        self._running = True
        return self
    
    def stop(self) -> float:
        """停止计时并返回耗时（秒）"""
        if not self._running:
            raise RuntimeError("计时器未启动")
        
        self._end_time = time.perf_counter()
        self._elapsed = self._end_time - self._start_time
        self._running = False
        
        return self._elapsed
    
    @property
    def elapsed(self) -> float:
        """获取当前耗时（秒）"""
        if self._running:
            return time.perf_counter() - self._start_time
        return self._elapsed
    
    @property
    def elapsed_ms(self) -> float:
        """获取当前耗时（毫秒）"""
        return self.elapsed * 1000
    
    def lap(self, label: str = "") -> float:
        """记录一个分段计时点"""
        current_time = time.perf_counter()
        
        if self._start_time is not None:
            lap_time = current_time - self._start_time
            self._laps.append((label or f"lap_{len(self._laps)+1}", lap_time))
            
            # 重置起点
            self._start_time = current_time
            
            return lap_time
        
        return 0.0
    
    @property
    def laps(self) -> List[Tuple[str, float]]:
        """获取所有分段计时记录"""
        return self._laps.copy()
    
    def reset(self):
        """重置计时器"""
        self._start_time = None
        self._end_time = None
        self._elapsed = 0.0
        self._running = False
        self._laps.clear()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def measure_performance(func: Optional[Callable] = None, *, name: str = ""):
    """
    性能测量装饰器/上下文管理器
    
    用法1：作为装饰器
        @measure_performance("my_function")
        def my_func():
            ...
    
    用法2：作为上下文管理器
        with measure_performance("block_name") as timer:
            ...  # code to measure
        print(timer.elapsed_ms)
    """
    class _MeasureContext:
        def __init__(self, name: str = ""):
            self.timer = PerformanceTimer(name)
            self.result: Optional[BenchmarkResult] = None
        
        def __enter__(self):
            self.timer.start()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = self.timer.stop()
            self.result = BenchmarkResult(
                test_name=self.timer.name or "anonymous",
                total_time_s=elapsed,
                avg_time_ms=elapsed * 1000
            )
    
    if func is not None:
        # 作为装饰器使用
        @wraps(func)
        def wrapper(*args, **kwargs):
            with _MeasureContext(name or func.__name__) as ctx:
                result = func(*args, **kwargs)
            return result, ctx.result
        return wrapper
    else:
        # 作为上下文管理器工厂使用
        return _MeasureContext(name)


class BenchmarkSuite:
    """
    基准测试套件 - 参考业界标准测试框架设计
    
    功能：
    - 自动化基准测试执行
    - 统计分析（平均值、百分位数、标准差）
    - 结果对比和可视化
    - 报告生成
    """
    
    def __init__(self, suite_name: str = "benchmark"):
        self.suite_name = suite_name
        self.results: Dict[str, BenchmarkResult] = {}
        self._logger = setup_logging(f"benchmark.{suite_name}")
        
        # 全局配置
        self.warmup_iterations = 3  # 预热迭代次数
        self.default_iterations = 100  # 默认测试迭代次数
        self.timeout_per_test = 60.0  # 单个测试超时（秒）
    
    def benchmark(
        self,
        name: str,
        func: Callable,
        iterations: Optional[int] = None,
        args: tuple = (),
        kwargs: dict = None,
        warmup: Optional[int] = None,
        setup: Optional[Callable] = None,
        teardown: Optional[Callable] = None
    ) -> BenchmarkResult:
        """
        执行单个基准测试
        
        Args:
            name: 测试名称
            func: 要测试的函数
            iterations: 迭代次数
            args: 函数位置参数
            kwargs: 函数关键字参数
            warmup: 预热次数
            setup: 每次迭代前的准备函数
            teardown: 每次迭代后的清理函数
            
        Returns:
            BenchmarkResult: 测试结果
        """
        iterations = iterations or self.default_iterations
        warmup = warmup or self.warmup_iterations
        kwargs = kwargs or {}
        
        self._logger.info(
            f"开始基准测试: {name} "
            f"(迭代: {iterations}, 预热: {warmup})"
        )
        
        times = []
        
        # 预热阶段
        try:
            for i in range(warmup):
                if setup:
                    setup()
                
                func(*args, **kwargs)
                
                if teardown:
                    teardown()
                    
        except Exception as e:
            self._logger.warning(f"预热失败: {name} - {e}")
        
        # 正式测试阶段
        start_total = time.perf_counter()
        
        for i in range(iterations):
            try:
                if setup:
                    setup()
                
                iter_start = time.perf_counter()
                func(*args, **kwargs)
                iter_end = time.perf_counter()
                
                times.append((iter_end - iter_start) * 1000)  # Convert to ms
                
                if teardown:
                    teardown()
                    
            except Exception as e:
                self._logger.error(f"测试异常: {name} (第{i+1}次) - {e}")
                continue
        
        total_time = time.perf_counter() - start_total
        
        # 计算统计数据
        if times:
            sorted_times = sorted(times)
            n = len(sorted_times)
            
            result = BenchmarkResult(
                test_name=name,
                iterations=n,
                total_time_s=total_time,
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=sorted_times[n // 2],
                p95_time_ms=sorted_times[int(n * 0.95)] if n > 20 else sorted_times[-1],
                p99_time_ms=sorted_times[int(n * 0.99)] if n > 100 else sorted_times[-1],
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                throughput=n / max(total_time, 0.001)
            )
        else:
            result = BenchmarkResult(test_name=name, iterations=0)
        
        self.results[name] = result
        
        self._logger.info(
            f"✓ 基准测试完成: {name}\n"
            f"  迭代: {result.iterations}\n"
            f"  平均耗时: {result.avg_time_ms:.2f}ms\n"
            f"  P95: {result.p95_time_ms:.2f}ms\n"
            f"  吞吐量: {result.throughput:.2f} ops/s"
        )
        
        return result
    
    def compare_baselines(
        self,
        baseline_results: Dict[str, BenchmarkResult],
        tolerance_pct: float = 10.0
    ) -> Dict[str, str]:
        """
        与基线结果对比
        
        Args:
            baseline_results: 基线测试结果字典
            tolerance_pct: 允许的性能退化百分比
            
        Returns:
            对比结论字典 {test_name: "improved"/"regressed"/"stable"}
        """
        comparisons = {}
        
        for name, baseline in baseline_results.items():
            if name not in self.results:
                comparisons[name] = "missing_in_current"
                continue
            
            current = self.results[name]
            
            if baseline.avg_time_ms == 0:
                comparisons[name] = "unknown"
                continue
            
            change_pct = (
                (current.avg_time_ms - baseline.avg_time_ms) /
                baseline.avg_time_ms *
                100
            )
            
            if change_pct < -tolerance_pct:
                status = "improved"
            elif change_pct > tolerance_pct:
                status = "regressed"
            else:
                status = "stable"
            
            comparisons[name] = status
            
            icon = {"improved": "↑", "regressed": "↓", "stable": "→"}.get(status, "?")
            
            self._logger.info(
                f"{icon} {name}: "
                f"{baseline.avg_time_ms:.2f}ms → {current.avg_time_ms:.2f}ms "
                f"({change_pct:+.2f}%) [{status}]"
            )
        
        return comparisons
    
    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成测试报告
        
        Args:
            output_path: 可选的报告输出路径
            
        Returns:
            报告字典
        """
        report = {
            'suite_name': self.suite_name,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': len(self.results),
            'results': {name: r.to_dict() for name, r in self.results.items()},
            'summary': self._generate_summary()
        }
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"报告已保存: {output_path}")
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成摘要统计"""
        if not self.results:
            return {'status': 'no_results'}
        
        all_times = [r.avg_time_ms for r in self.results.values() if r.iterations > 0]
        
        summary = {
            'total_tests': len(self.results),
            'successful_tests': len(all_times),
            'avg_across_all_tests': statistics.mean(all_times) if all_times else 0,
            'fastest_test': min(self.results.items(), key=lambda x: x[1].avg_time_ms)[0] if self.results else "",
            'slowest_test': max(self.results.items(), key=lambda x: x[1].avg_time_ms)[0] if self.results else ""
        }
        
        return summary


class MemoryProfiler:
    """
    内存使用分析器
    
    功能：
    - 实时内存监控
    - 峰值内存检测
    - 内存泄漏预警
    """
    
    def __init__(self):
        self._logger = setup_logging("profiler.memory")
        self._snapshots: List[Dict[str, Any]] = []
    
    def get_current_memory_mb(self) -> float:
        """获取当前进程内存使用（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    
    def snapshot(self, label: str = "") -> Dict[str, Any]:
        """创建内存快照"""
        memory_mb = self.get_current_memory_mb()
        
        snapshot = {
            'label': label or f"snapshot_{len(self._snapshots)}",
            'memory_mb': memory_mb,
            'timestamp': time.time()
        }
        
        self._snapshots.append(snapshot)
        
        self._logger.debug(f"内存快照: {snapshot['label']} = {memory_mb:.2f} MB")
        
        return snapshot
    
    def detect_leak(self, threshold_mb: float = 10.0) -> bool:
        """
        检测可能的内存泄漏
        
        Args:
            threshold_mb: 内存增长阈值（MB）
            
        Returns:
            bool: 是否可能存在泄漏
        """
        if len(self._snapshots) < 2:
            return False
        
        first = self._snapshots[0]['memory_mb']
        last = self._snapshots[-1]['memory_mb']
        growth = last - first
        
        if growth > threshold_mb:
            self._logger.warning(
                f"⚠ 可能的内存泄漏检测:\n"
                f"  初始内存: {first:.2f} MB\n"
                f"  当前内存: {last:.2f} MB\n"
                f"  增长: {growth:.2f} MB (阈值: {threshold_mb} MB)"
            )
            return True
        
        return False


@contextmanager
def profile_memory(label: str = "", check_leak: bool = True):
    """
    内存分析上下文管理器
    
    Example:
        with profile_memory("my_operation") as profiler:
            heavy_operation()
        print(profiler.snapshots)
    """
    profiler = MemoryProfiler()
    
    profiler.snapshot(f"{label}_before")
    
    yield profiler
    
    profiler.snapshot(f"{label}_after")
    
    if check_leak:
        profiler.detect_leak()


# 便捷函数

def quick_benchmark(
    func: Callable,
    iterations: int = 100,
    name: str = ""
) -> BenchmarkResult:
    """快速基准测试"""
    suite = BenchmarkSuite()
    return suite.benchmark(
        name=name or func.__name__,
        func=func,
        iterations=iterations
    )


def compare_functions(
    functions: Dict[str, Callable],
    iterations: int = 100,
    shared_args: tuple = ()
) -> Dict[str, BenchmarkResult]:
    """对比多个函数的性能"""
    suite = BenchmarkSuite("comparison")
    results = {}
    
    for name, func in functions.items():
        results[name] = suite.benchmark(
            name=name,
            func=func,
            iterations=iterations,
            args=shared_args
        )
    
    return results


__all__ = [
    'PerformanceMetric',
    'BenchmarkResult',
    'PerformanceTimer',
    'measure_performance',
    'BenchmarkSuite',
    'MemoryProfiler',
    'profile_memory',
    'quick_benchmark',
    'compare_functions'
]
