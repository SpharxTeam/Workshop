#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workshop V2.0 负载测试与压力测试工具
=====================================
功能：
1. 模拟高并发Pipeline执行
2. 内存泄漏检测
3. 系统资源压力测试
4. 吞吐量基准测试
5. 长时间稳定性测试（Soak Test）
6. 自动生成性能报告

使用示例:
    # 基础负载测试
    python load_tester.py --test-type load --concurrent-users 10
    
    # 压力测试
    python load_tester.py --test-type stress --max-load 100
    
    # 内存泄漏检测
    python load_tester.py --test-type memory-leak --iterations 1000
    
    # 完整测试套件
    python load_tester.py --full-suite --duration 3600
"""

import argparse
import gc
import json
import os
import random
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class LoadTestResult:
    """单次负载测试结果"""
    test_name: str
    start_time: float
    end_time: float = 0.0
    duration_seconds: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    response_time_ms: float = 0.0
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0
    cpu_percent: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.end_time > 0 and self.start_time > 0:
            self.duration_seconds = self.end_time - self.start_time


@dataclass
class LoadTestSummary:
    """负载测试汇总"""
    test_type: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p90_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    throughput_per_second: float = 0.0
    total_duration_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_type': self.test_type,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': f"{self.success_rate:.2f}%",
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'min_response_time_ms': round(self.min_response_time_ms, 2),
            'max_response_time_ms': round(self.max_response_time_ms, 2),
            'p50_response_time_ms': round(self.p50_response_time_ms, 2),
            'p90_response_time_ms': round(self.p90_response_time_ms, 2),
            'p99_response_time_ms': round(self.p99_response_time_ms, 2),
            'throughput_per_second': round(self.throughput_per_second, 2),
            'total_duration_seconds': round(self.total_duration_seconds, 2),
            'peak_memory_mb': round(self.peak_memory_mb, 2),
            'avg_cpu_percent': round(self.avg_cpu_percent, 2),
            'error_count': len(self.errors)
        }


class SystemMonitor:
    """系统资源监控器"""
    
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.samples: List[Dict[str, float]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        if not PSUTIL_AVAILABLE:
            print("⚠️  psutil未安装，系统监控功能受限")
    
    def start(self):
        """开始监控"""
        if not PSUTIL_AVAILABLE:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                sample = self._collect_sample()
                if sample:
                    self.samples.append(sample)
                time.sleep(self.sample_interval)
            except Exception:
                pass
    
    def _collect_sample(self) -> Optional[Dict[str, float]]:
        """收集一次采样"""
        try:
            process = psutil.Process(os.getpid())
            
            return {
                'timestamp': time.time(),
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'system_cpu': psutil.cpu_percent(),
                'system_memory': psutil.virtual_memory().percent
            }
        except Exception:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        if not self.samples:
            return {}
        
        cpu_samples = [s['cpu_percent'] for s in self.samples]
        mem_samples = [s['memory_mb'] for s in self.samples]
        
        return {
            'sample_count': len(self.samples),
            'avg_cpu': sum(cpu_samples) / len(cpu_samples),
            'peak_cpu': max(cpu_samples),
            'avg_memory': sum(mem_samples) / len(mem_samples),
            'peak_memory': max(mem_samples),
            'min_memory': min(mem_samples),
            'memory_growth': mem_samples[-1] - mem_samples[0] if len(mem_samples) > 1 else 0,
            'duration_seconds': self.samples[-1]['timestamp'] - self.samples[0]['timestamp'] if len(self.samples) > 1 else 0
        }


class WorkshopLoadTester:
    """
    Workshop V2.0 负载测试器
    ========================
    
    测试类型:
    1. **Load Test** (负载测试): 模拟正常使用场景下的并发用户
    2. **Stress Test** (压力测试): 找到系统的性能瓶颈和崩溃点
    3. **Soak Test** (浸泡/稳定性测试): 长时间运行检测内存泄漏
    4. **Spike Test** (尖峰测试): 突然增加流量测试恢复能力
    5. **Memory Leak Test**: 专门检测内存泄漏
    
    使用示例:
        tester = WorkshopLoadTester()
        
        # 负载测试
        result = tester.run_load_test(
            concurrent_users=10,
            requests_per_user=100,
            test_func=my_pipeline_function
        )
        
        # 压力测试
        result = tester.run_stress_test(
            max_concurrent=100,
            step_size=10
        )
    """
    
    def __init__(self, output_dir: str = 'load_test_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[LoadTestResult] = []
        self.monitor = SystemMonitor()
        self._lock = threading.Lock()
        
        # 统计数据
        self.total_tests_run = 0
        self.total_successes = 0
        self.total_failures = 0
    
    def _get_current_memory_mb(self) -> float:
        """获取当前进程内存使用(MB)"""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024)
            else:
                import resource
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            return 0.0
    
    def _simulate_pipeline_execution(self, pipeline_name: str = 'test',
                                    complexity: str = 'medium',
                                    data_size: int = 1000) -> Tuple[bool, float, str]:
        """
        模拟Pipeline执行（用于测试）
        
        Args:
            pipeline_name: Pipeline名称
            complexity: 复杂度 (light/medium/heavy)
            data_size: 数据大小(条目数)
        
        Returns:
            (是否成功, 耗时ms, 错误消息)
        """
        start = time.perf_counter()
        
        try:
            # 模拟不同复杂度的处理
            if complexity == 'light':
                # 简单计算
                result = sum(range(data_size))
                time.sleep(random.uniform(0.01, 0.05))
                
            elif complexity == 'medium':
                # 中等复杂度：模拟数据处理
                data = [random.random() for _ in range(min(data_size, 10000))]
                processed = [x * 2 + 1 for x in data]
                sorted_data = sorted(processed)
                _ = sum(sorted_data) / len(sorted_data)
                time.sleep(random.uniform(0.05, 0.2))
                
            elif complexity == 'heavy':
                # 高复杂度：模拟大量数据处理
                data = [[random.random() for _ in range(100)] 
                       for _ in range(min(data_size // 10, 1000))]
                
                # 模拟矩阵运算
                for row in data:
                    _ = [x ** 2 for x in row]
                    _ = sum(row) / len(row)
                
                time.sleep(random.uniform(0.1, 0.5))
            
            # 随机失败率（默认1%）
            if random.random() < 0.01:
                raise Exception(f"模拟随机失败 (概率1%)")
            
            elapsed = (time.perf_counter() - start) * 1000
            return True, elapsed, ''
            
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return False, elapsed, str(e)
    
    def run_load_test(self, concurrent_users: int = 10,
                     requests_per_user: int = 50,
                     ramp_up_time: float = 5.0,
                     custom_func: Optional[Callable] = None,
                     **kwargs) -> LoadTestSummary:
        """
        运行负载测试
        
        Args:
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数
            ramp_up_time: 启动时间(秒)，逐渐增加并发
            custom_func: 自定义测试函数 (可选)
        
        Returns:
            测试汇总结果
        """
        print("\n" + "="*70)
        print("📊 Workshop V2.0 负载测试")
        print("="*70)
        print(f"   并发用户: {concurrent_users}")
        print(f"   每用户请求: {requests_per_user}")
        print(f"   总请求数: {concurrent_users * requests_per_user}")
        print(f"   启动时间: {rampup_time}秒")
        print("="*70)
        
        start_time = time.time()
        self.monitor.start()
        self.results.clear()
        
        # 用户启动间隔
        user_interval = ramp_up_time / concurrent_users if concurrent_users > 0 else 0
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for user_id in range(concurrent_users):
                # 渐进式启动用户
                if user_id > 0:
                    time.sleep(user_interval)
                
                # 为每个用户提交任务
                for req_id in range(requests_per_user):
                    future = executor.submit(
                        self._execute_single_request,
                        user_id=user_id,
                        request_id=req_id,
                        custom_func=custom_func,
                        **kwargs
                    )
                    futures.append(future)
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    pass
        
        total_duration = time.time() - start_time
        self.monitor.stop()
        
        # 计算统计信息
        summary = self._calculate_summary('Load Test', total_duration)
        summary.throughput_per_second = summary.successful_requests / total_duration if total_duration > 0 else 0
        
        self._print_summary(summary)
        self._save_results(summary, 'load_test')
        
        return summary
    
    def run_stress_test(self, initial_concurrent: int = 5,
                       max_concurrent: int = 100,
                       step_size: int = 5,
                       requests_per_step: int = 20,
                       step_duration: float = 30.0,
                       **kwargs) -> List[LoadTestSummary]:
        """
        运行压力测试（逐步增加负载）
        
        Args:
            initial_concurrent: 初始并发数
            max_concurrent: 最大并发数
            step_size: 每步增加的并发数
            requests_per_step: 每步的请求数
            step_duration: 每步持续时间(秒)
        
        Returns:
            每步的测试结果列表
        """
        print("\n" + "="*70)
        print("💪 Workshop V2.0 压力测试")
        print("="*70)
        print(f"   初始并发: {initial_concurrent}")
        print(f"   最大并发: {max_concurrent}")
        print(f"   步进大小: {step_size}")
        print(f"   每步持续: {step_duration}秒")
        print("="*70)
        
        summaries = []
        current_concurrent = initial_concurrent
        
        while current_concurrent <= max_concurrent:
            print(f"\n{'─'*60}")
            print(f"📈 测试阶段: 并发={current_concurrent}")
            print(f"{'─'*60}")
            
            try:
                summary = self.run_load_test(
                    concurrent_users=current_concurrent,
                    requests_per_user=requests_per_step,
                    **kwargs
                )
                summaries.append(summary)
                
                # 检查成功率，如果过低则停止
                if summary.success_rate < 80.0:
                    print(f"\n⚠️  成功率降至{summary.success_rate:.1f}%，达到性能瓶颈")
                    break
                
                # 如果错误率突然上升，也停止
                if len(summary.errors) > summary.total_requests * 0.1:
                    print(f"\n⚠️  错误率过高({len(summary.errors)}个错误)，停止测试")
                    break
                
            except Exception as e:
                print(f"\n❌ 在并发={current_concurrent}时发生严重错误: {e}")
                break
            
            current_concurrent += step_size
        
        # 保存完整压力测试报告
        stress_report = {
            'timestamp': datetime.now().isoformat(),
            'test_parameters': {
                'initial_concurrent': initial_concurrent,
                'max_concurrent_reached': current_concurrent - step_size if summaries else 0,
                'step_size': step_size
            },
            'results': [s.to_dict() for s in summaries],
            'conclusion': self._generate_stress_test_conclusion(summaries)
        }
        
        report_path = self.output_dir / f'stress_test_{datetime.now():%Y%m%d_%H%M%S}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(stress_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 压力测试完成！报告已保存至: {report_path}")
        
        return summaries
    
    def run_soak_test(self, duration_minutes: int = 60,
                     concurrent_users: int = 5,
                     request_interval: float = 1.0,
                     **kwargs) -> LoadTestSummary:
        """
        运行浸泡测试（长时间稳定性测试）
        
        用于检测：
        - 内存泄漏
        - 性能退化
        - 资源耗尽
        - 连接池问题
        
        Args:
            duration_minutes: 测试时长(分钟)
            concurrent_users: 持续并发用户数
            request_interval: 请求间隔(秒)
        
        Returns:
            测试汇总
        """
        print("\n" + "="*70)
        print("⏱️  Workshop V2.0 浸泡测试 (Soak Test)")
        print("="*70)
        print(f"   测试时长: {duration_minutes}分钟")
        print(f"   持续并发: {concurrent_users}用户")
        print(f"   请求间隔: {request_interval}秒")
        print("="*70)
        
        duration_seconds = duration_minutes * 60
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        self.monitor.start()
        self.results.clear()
        
        request_count = 0
        
        print(f"\n⏱️  开始长时间运行... (预计结束: {(datetime.now()).strftime('%H:%M:%S')})")
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = set()
            
            while time.time() < end_time:
                # 提交新请求
                future = executor.submit(
                    self._execute_single_request,
                    user_id=request_count % concurrent_users,
                    request_id=request_count,
                    **kwargs
                )
                futures.add(future)
                request_count += 1
                
                # 清理已完成的future
                done = {f for f in futures if f.done()}
                futures -= done
                
                # 控制请求速率
                time.sleep(request_interval)
            
            # 等待剩余的请求完成
            for future in as_completed(futures):
                try:
                    future.result(timeout=30)
                except Exception:
                    pass
        
        total_duration = time.time() - start_time
        self.monitor.stop()
        
        summary = self._calculate_summary('Soak Test', total_duration)
        summary.throughput_per_second = request_count / total_duration if total_duration > 0 else 0
        
        # 分析内存趋势
        monitor_stats = self.monitor.get_statistics()
        if monitor_stats.get('memory_growth', 0) > 100:  # 内存增长超过100MB
            summary.errors.append(
                f"⚠️ 可能存在内存泄漏! 内存增长: {monitor_stats['memory_growth']:.1f}MB"
            )
        
        self._print_summary(summary)
        self._save_results(summary, 'soak_test')
        
        # 输出内存分析
        if monitor_stats:
            print(f"\n📈 资源使用趋势:")
            print(f"   平均CPU: {monitor_stats['avg_cpu']:.1f}%")
            print(f"   平均内存: {monitor_stats['avg_memory']:.1f}MB")
            print(f"   峰值内存: {monitor_stats['peak_memory']:.1f}MB")
            print(f"   内存增长: {monitor_stats['memory_growth']:+.1f}MB")
            
            if monitor_stats['memory_growth'] > 50:
                print(f"   ⚠️  警告: 检测到明显的内存增长，可能存在泄漏!")
        
        return summary
    
    def run_spike_test(self, baseline_users: int = 5,
                      spike_users: int = 50,
                      spike_duration: float = 30.0,
                      recovery_time: float = 60.0,
                      **kwargs) -> Dict[str, LoadTestSummary]:
        """
        运行尖峰测试
        
        模拟突发流量场景，测试系统的弹性恢复能力
        
        Args:
            baseline_users: 基线用户数
            spike_users: 尖峰时增加的用户数
            spike_duration: 尖峰持续时间(秒)
            recovery_time: 恢复观察时间(秒)
        
        Returns:
            各阶段的测试结果
        """
        print("\n" + "="*70)
        print("⚡ Workshop V2.0 尖峰测试 (Spike Test)")
        print("="*70)
        print(f"   基线用户: {baseline_users}")
        print(f"   尖峰用户: +{spike_users} (总计{baseline_users + spike_users})")
        print(f"   尖峰持续: {spike_duration}秒")
        print(f"   恢复观察: {recovery_time}秒")
        print("="*70)
        
        results = {}
        
        # Phase 1: 基线阶段
        print(f"\n📊 Phase 1: 基线运行 ({baseline_users}用户)")
        results['baseline'] = self.run_load_test(
            concurrent_users=baseline_users,
            requests_per_user=20,
            **kwargs
        )
        baseline_avg = results['baseline'].avg_response_time_ms
        
        time.sleep(5)
        
        # Phase 2: 尖峰阶段
        print(f"\n⚡ Phase 2: 尖峰冲击 ({baseline_users + spike_users}用户)")
        results['spike'] = self.run_load_test(
            concurrent_users=baseline_users + spike_users,
            requests_per_user=15,
            **kwargs
        )
        spike_avg = results['spike'].avg_response_time_ms
        
        time.sleep(recovery_time)
        
        # Phase 3: 恢复阶段
        print(f"\n🔄 Phase 3: 恢复检查 ({baseline_users}用户)")
        results['recovery'] = self.run_load_test(
            concurrent_users=baseline_users,
            requests_per_user=20,
            **kwargs
        )
        recovery_avg = results['recovery'].avg_response_time_ms
        
        # 分析结果
        degradation_pct = ((spike_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
        recovery_pct = ((recovery_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
        
        print(f"\n{'='*70}")
        print("📊 尖峰测试分析")
        print(f"{'='*70}")
        print(f"   基线响应时间: {baseline_avg:.2f}ms")
        print(f"   尖峰响应时间: {spike_avg:.2f}ms (+{degradation_pct:.1f}%)")
        print(f"   恢复响应时间: {recovery_avg:.2f}ms ({'完全恢复' if recovery_pct < 10 else '部分恢复'})")
        
        if degradation_pct > 200:
            verdict = "❌ 系统在尖峰下性能严重下降"
        elif degradation_pct > 100:
            verdict = "⚠️  系统在尖峰下有明显性能降级"
        elif recovery_pct < 20:
            verdict = "✅ 系统具有良好的弹性恢复能力"
        else:
            verdict = "🔄 系统可从尖峰中恢复但较慢"
        
        print(f"\n   结论: {verdict}")
        
        return results
    
    def run_memory_leak_test(self, iterations: int = 1000,
                            iteration_func: Optional[Callable] = None,
                            **kwargs) -> Dict[str, Any]:
        """
        专门检测内存泄漏
        
        通过多次迭代执行相同操作，观察内存是否持续增长
        
        Args:
            iterations: 迭代次数
            iteration_func: 自定义迭代函数
        
        Returns:
            内存泄漏检测结果
        """
        print("\n" + "="*70)
        print("💧 Workshop V2.0 内存泄漏检测")
        print("="*70)
        print(f"   迭代次数: {iterations}")
        print("="*70)
        
        self.monitor.start()
        
        # 强制垃圾回收，获取基线内存
        gc.collect()
        baseline_memory = self._get_current_memory_mb()
        
        memory_snapshots = []
        iteration_times = []
        
        print(f"\n🔍 基线内存: {baseline_memory:.2f}MB")
        print(f"开始迭代测试...\n")
        
        progress_interval = max(1, iterations // 20)  # 显示20次进度
        
        for i in range(iterations):
            iter_start = time.perf_counter()
            
            # 执行操作
            if iteration_func:
                try:
                    iteration_func(i)
                except Exception as e:
                    pass
            else:
                # 默认：模拟Pipeline执行
                self._simulate_pipeline_execution(
                    complexity='medium',
                    data_size=random.randint(500, 2000)
                )
            
            iter_time = (time.perf_counter() - iter_start) * 1000
            iteration_times.append(iter_time)
            
            # 定期采集内存快照
            if i % progress_interval == 0 or i == iterations - 1:
                gc.collect()
                current_mem = self._get_current_memory_mb()
                memory_snapshots.append({
                    'iteration': i,
                    'memory_mb': current_mem,
                    'delta_from_baseline': current_mem - baseline_memory,
                    'avg_iteration_time_ms': sum(iteration_times[-progress_interval:]) / min(progress_interval, len(iteration_times))
                })
                
                progress = (i + 1) / iterations * 100
                bar_len = int(progress / 5)
                bar = '█' * bar_len + '░' * (20 - bar_len)
                print(f"\r[{bar}] {progress:5.1f}% | "
                      f"内存: {current_mem:8.2f}MB | "
                      f"增长: {current_mem - baseline_memory:+8.2f}MB | "
                      f"耗时: {iter_time:7.2f}",
                      end='', flush=True)
        
        print(f"\n")  # 换行
        
        self.monitor.stop()
        
        # 最终清理
        gc.collect()
        final_memory = self._get_current_memory_mb()
        
        # 分析结果
        total_growth = final_memory - baseline_memory
        growth_per_iteration = total_growth / iterations if iterations > 0 else 0
        
        # 判断是否存在泄漏
        if total_growth > 50:  # 总增长超过50MB
            if growth_per_iteration > 0.1:  # 每次迭代增长>0.1MB
                leak_severity = "HIGH"
                verdict = "❌ 检测到明显内存泄漏!"
            else:
                leak_severity = "MEDIUM"
                verdict = "⚠️  存在轻微内存增长，建议关注"
        elif total_growth > 10:
            leak_severity = "LOW"
            verdict = "✅ 内存使用在合理范围内"
        else:
            leak_severity = "NONE"
            verdict = "✅ 未检测到内存泄漏"
        
        # 计算统计信息
        avg_time = sum(iteration_times) / len(iteration_times) if iteration_times else 0
        p99_time = sorted(iteration_times)[int(len(iteration_times) * 0.99)] if iteration_times else 0
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_parameters': {
                'iterations': iterations,
                'baseline_memory_mb': round(baseline_memory, 2),
                'final_memory_mb': round(final_memory, 2)
            },
            'results': {
                'total_memory_growth_mb': round(total_growth, 2),
                'growth_per_iteration_mb': round(growth_per_iteration, 4),
                'avg_iteration_time_ms': round(avg_time, 2),
                'p99_iteration_time_ms': round(p99_time, 2),
                'leak_severity': leak_severity,
                'verdict': verdict
            },
            'snapshots': memory_snapshots[::5],  # 每5个保存一个
            'recommendations': self._generate_memory_recommendations(
                leak_severity, growth_per_iteration
            )
        }
        
        # 打印详细结果
        print(f"\n{'='*70}")
        print("💧 内存泄漏检测结果")
        print(f"{'='*70}")
        print(f"   基线内存:     {baseline_memory:>10.2f} MB")
        print(f"   最终内存:     {final_memory:>10.2f} MB")
        print(f"   总增长:       {total_growth:>+10.2f} MB")
        print(f"   每次迭代增长: {growth_per_iteration:>+10.4f} MB")
        print(f"   平均迭代耗时: {avg_time:>10.2f} ms")
        print(f"   P99迭代耗时:  {p99_time:>10.2f} ms")
        print(f"\n   泄漏等级: [{leak_severity}]")
        print(f"   结论: {verdict}")
        
        if result['recommendations']:
            print(f"\n   💡 建议:")
            for rec in result['recommendations']:
                print(f"      • {rec}")
        
        # 保存结果
        report_path = self.output_dir / f'memory_leak_{datetime.now():%Y%m%d_%H%M%S}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告: {report_path}")
        
        return result
    
    def _execute_single_request(self, user_id: int, request_id: int,
                               custom_func: Optional[Callable] = None,
                               **kwargs) -> LoadTestResult:
        """执行单个测试请求"""
        result = LoadTestResult(
            test_name=f"user_{user_id}_req_{request_id}",
            start_time=time.perf_counter(),
            memory_before=self._get_current_memory_mb()
        )
        
        try:
            if custom_func:
                success, elapsed, error = custom_func(user_id, request_id, **kwargs)
            else:
                success, elapsed, error = self._simulate_pipeline_execution(**kwargs)
            
            result.end_time = time.perf_counter()
            result.success = success
            result.response_time_ms = elapsed
            result.error_message = error
            result.memory_after = self._get_current_memory_mb()
            
        except Exception as e:
            result.end_time = time.perf_counter()
            result.success = False
            result.error_message = str(e)
            result.memory_after = self._get_current_memory_mb()
        
        with self._lock:
            self.results.append(result)
            self.total_tests_run += 1
            if result.success:
                self.total_successes += 1
            else:
                self.total_failures += 1
        
        return result
    
    def _calculate_summary(self, test_type: str, 
                          total_duration: float) -> LoadTestSummary:
        """计算测试汇总"""
        if not self.results:
            return LoadTestSummary(test_type=test_type)
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        response_times = [r.response_time_ms for r in successful]
        response_times.sort()
        
        summary = LoadTestSummary(test_type=test_type)
        summary.total_requests = len(self.results)
        summary.successful_requests = len(successful)
        summary.failed_requests = len(failed)
        summary.success_rate = (len(successful) / len(self.results) * 100) if self.results else 0
        summary.total_duration_seconds = total_duration
        
        if response_times:
            summary.avg_response_time_ms = sum(response_times) / len(response_times)
            summary.min_response_time_ms = response_times[0]
            summary.max_response_time_ms = response_times[-1]
            summary.p50_response_time_ms = response_times[int(len(response_times) * 0.5)]
            summary.p90_response_time_ms = response_times[int(len(response_times) * 0.9)]
            summary.p99_response_time_ms = response_times[int(len(response_times) * 0.99)]
        
        # 内存和CPU统计
        memories = [r.memory_after for r in self.results if r.memory_after > 0]
        if memories:
            summary.peak_memory_mb = max(memories)
        
        monitor_stats = self.monitor.get_statistics()
        if monitor_stats:
            summary.avg_cpu_percent = monitor_stats.get('avg_cpu', 0)
        
        # 收集错误信息
        for f in failed[:10]:  # 只记录前10个错误
            if f.error_message:
                summary.errors.append(f"[{f.test_name}] {f.error_message}")
        
        return summary
    
    def _print_summary(self, summary: LoadTestSummary):
        """打印测试摘要"""
        print(f"\n{'='*70}")
        print(f"📊 {summary.test_type} 结果汇总")
        print(f"{'='*70}")
        print(f"   总请求数:      {summary.total_requests:,}")
        print(f"   成功请求:      {summary.successful_requests:,} "
              f"({summary.success_rate:.1f}%)")
        print(f"   失败请求:      {summary.failed_requests:,}")
        print(f"   总耗时:        {summary.total_duration_seconds:.2f}s")
        print(f"   吞吐量:        {summary.throughput_per_second:.2f} req/s")
        print(f"\n   ⏱️  响应时间分布:")
        print(f"      平均:       {summary.avg_response_time_ms:.2f}ms")
        print(f"      最小:       {summary.min_response_time_ms:.2f}ms")
        print(f"      P50:        {summary.p50_response_time_ms:.2f}ms")
        print(f"      P90:        {summary.p90_response_time_ms:.2f}ms")
        print(f"      P99:        {summary.p99_response_time_ms:.2f}ms")
        print(f"      最大:       {summary.max_response_time_ms:.2f}ms")
        print(f"\n   💻 资源使用:")
        print(f"      峰值内存:   {summary.peak_memory_mb:.2f}MB")
        print(f"      平均CPU:    {summary.avg_cpu_percent:.1f}%")
        
        if summary.errors:
            print(f"\n   ❌ 错误示例 (前5个):")
            for err in summary.errors[:5]:
                print(f"      • {err[:80]}...")
    
    def _save_results(self, summary: LoadTestSummary, test_name: str):
        """保存测试结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON格式
        json_path = self.output_dir / f'{test_name}_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _generate_stress_test_conclusion(self, summaries: List[LoadTestSummary]) -> str:
        """生成压力测试结论"""
        if not summaries:
            return "无法生成结论（无有效测试数据）"
        
        last = summaries[-1]
        
        if last.success_rate >= 95.0:
            return "✅ 系统在高并发下表现优秀，未发现明显瓶颈"
        elif last.success_rate >= 80.0:
            return "⚠️  系统在高并发下有性能降级，建议优化或扩容"
        else:
            return "❌ 系统已达性能极限，需要紧急优化或水平扩展"
    
    def _generate_memory_recommendations(self, severity: str,
                                        growth_rate: float) -> List[str]:
        """生成内存优化建议"""
        recommendations = []
        
        if severity in ['HIGH', 'MEDIUM']:
            recommendations.extend([
                "检查是否有大对象未被释放",
                "审查循环中的临时对象创建",
                "确认第三方库是否存在已知内存泄漏",
                "考虑使用内存分析工具 (memory_profiler, objgraph)",
                "检查缓存实现是否有限制机制"
            ])
        
        if growth_rate > 1.0:
            recommendations.append("每次迭代内存增长过高 (>1MB)，需重点排查")
        
        return recommendations


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='Workshop V2.0 负载测试与压力测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --test-type load --concurrent-users 10
  %(prog)s --test-type stress --max-concurrent 100
  %(prog)s --test-type soak --duration-minutes 60
  %(prog)s --test-type spike --spike-users 50
  %(prog)s --test-type memory-leak --iterations 1000
  %(prog)s --full-suite
        """
    )
    
    parser.add_argument('--test-type', '-t',
                       choices=['load', 'stress', 'soak', 'spike', 'memory-leak'],
                       help='测试类型')
    parser.add_argument('--concurrent-users', '-c', type=int, default=10,
                       help='并发用户数 (默认10)')
    parser.add_argument('--requests-per-user', '-r', type=int, default=50,
                       help='每用户请求数 (默认50)')
    parser.add_argument('--max-concurrent', type=int, default=100,
                       help='压力测试最大并发数 (默认100)')
    parser.add_argument('--duration-minutes', type=int, default=60,
                       help='浸泡测试时长(分钟) (默认60)')
    parser.add_argument('--spike-users', type=int, default=50,
                       help='尖峰测试额外用户数 (默认50)')
    parser.add_argument('--iterations', type=int, default=1000,
                       help='内存泄漏检测迭代次数 (默认1000)')
    parser.add_argument('--full-suite', action='store_true',
                       help='运行完整测试套件')
    parser.add_argument('--output-dir', default='load_test_results',
                       help='输出目录 (默认load_test_results)')
    
    args = parser.parse_args()
    
    tester = WorkshopLoadTester(output_dir=args.output_dir)
    
    try:
        if args.full_suite:
            print("\n🎯 运行完整测试套件...\n")
            
            # 1. 快速负载测试
            print("="*70)
            print("1/5 📊 负载测试")
            print("="*70)
            tester.run_load_test(concurrent_users=args.concurrent_users,
                                requests_per_user=args.requests_per_user)
            
            # 2. 内存泄漏检测
            print("\n" + "="*70)
            print("2/5 💧 内存泄漏检测")
            print("="*70)
            tester.run_memory_leak_test(iterations=min(args.iterations, 500))
            
            # 3. 尖峰测试
            print("\n" + "="*70)
            print("3/5 ⚡ 尖峰测试")
            print("="*70)
            tester.run_spike_test(spike_users=args.spike_users)
            
            # 4. 短时间浸泡测试
            print("\n" + "="*70)
            print("4/5 ⏱️  短时间浸泡测试 (5分钟)")
            print("="*70)
            tester.run_soak_test(duration_minutes=5,
                               concurrent_users=max(1, args.concurrent_users // 2))
            
            # 5. 压力测试（如果时间允许）
            print("\n" + "="*70)
            print("5/5 💪 压力测试 (快速)")
            print("="*70)
            tester.run_stress_test(initial_concurrent=5,
                                  max_concurrent=min(args.max_concurrent, 50),
                                  step_size=5,
                                  requests_per_step=10)
            
            print("\n" + "="*70)
            print("🎉 完整测试套件执行完毕!")
            print(f"📂 所有结果保存在: {args.output_dir}/")
            print("="*70)
            
        elif args.test_type == 'load':
            tester.run_load_test(
                concurrent_users=args.concurrent_users,
                requests_per_user=args.requests_per_user
            )
        
        elif args.test_type == 'stress':
            tester.run_stress_test(
                max_concurrent=args.max_concurrent
            )
        
        elif args.test_type == 'soak':
            tester.run_soak_test(
                duration_minutes=args.duration_minutes,
                concurrent_users=args.concurrent_users
            )
        
        elif args.test_type == 'spike':
            tester.run_spike_test(
                spike_users=args.spike_users
            )
        
        elif args.test_type == 'memory-leak':
            tester.run_memory_leak_test(
                iterations=args.iterations
            )
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
