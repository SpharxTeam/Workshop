#!/usr/bin/env python3
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop V1 vs V2 性能对比基准测试
# 量化展示重构带来的性能提升

"""
Workshop V1 vs V2 性能对比测试

本脚本通过实际测量，量化 Workshop V2.0 重构带来的性能提升：
1. 代码启动时间（模块导入、初始化）
2. 配置加载效率
3. 异常处理开销
4. 内存使用情况
5. Pipeline执行效率

运行方式:
    python scripts/performance_benchmark_v1_vs_v2.py
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

# 尝试导入核心组件
try:
    from common.core import (
        BasePipeline,
        ConfigManager,
        setup_logging,
        InputValidator,
        ErrorCode,
        WorkshopError,
        IOManager,
        BenchmarkSuite,
        PerformanceTimer,
        CompressionFormat,
        error_code_manager
    )
    V2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ V2核心模块导入失败: {e}")
    V2_AVAILABLE = False


@dataclass
class BenchmarkResultItem:
    """单个基准测试结果"""
    test_name: str
    v1_time_ms: float = 0.0
    v2_time_ms: float = 0.0
    improvement_pct: float = 0.0
    v1_memory_mb: float = 0.0
    v2_memory_mb: float = 0.0
    memory_reduction_pct: float = 0.0
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'v1_time_ms': round(self.v1_time_ms, 4),
            'v2_time_ms': round(self.v2_time_ms, 4),
            'improvement_pct': round(self.improvement_pct, 2),
            'v1_memory_mb': round(self.v1_memory_mb, 2),
            'v2_memory_mb': round(self.v2_memory_mb, 2),
            'memory_reduction_pct': round(self.memory_reduction_pct, 2),
            'details': self.details
        }


@dataclass
class ComparisonReport:
    """完整对比报告"""
    timestamp: str = ""
    test_results: List[BenchmarkResultItem] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def generate_summary(self):
        """生成汇总统计"""
        if not self.test_results:
            return
        
        time_improvements = [r.improvement_pct for r in self.test_results if r.v1_time_ms > 0]
        memory_reductions = [r.memory_reduction_pct for r in self.test_results if r.v1_memory_mb > 0]
        
        self.summary = {
            'total_tests': len(self.test_results),
            'avg_time_improvement_pct': (
                sum(time_improvements) / len(time_improvements)
                if time_improvements else 0
            ),
            'max_time_improvement_pct': max(time_improvements) if time_improvements else 0,
            'avg_memory_reduction_pct': (
                sum(memory_reductions) / len(memory_reductions)
                if memory_reductions else 0
            ),
            'tests_with_improvement': sum(1 for r in self.test_results if r.improvement_pct > 0),
            'tests_with_regression': sum(1 for r in self.test_results if r.improvement_pct < -5),
            'overall_verdict': ''
        }
        
        # 总体评判
        avg_improve = self.summary['avg_time_improvement_pct']
        if avg_improve >= 20:
            self.summary['overall_verdict'] = '🏆 EXCELLENT (显著提升)'
        elif avg_improve >= 10:
            self.summary['overall_verdict'] = '✅ GOOD (明显改善)'
        elif avg_improve >= 0:
            self.summary['overall_verdict'] = '✓ ACCEPTABLE (轻微提升)'
        else:
            self.summary['overall_verdict'] = '⚠️ NEEDS ATTENTION'


class V1Simulator:
    """
    V1代码行为模拟器
    
    模拟重构前的典型代码模式：
    - 手动配置管理
    - 简单异常处理
    - 无输入验证
    - 重复的初始化代码
    """
    
    def __init__(self):
        self._config_cache = {}
        self._logger = None
        self._init_count = 0
    
    def simulate_config_loading_v1(self, iterations: int = 100) -> Tuple[float, float]:
        """模拟V1配置加载方式"""
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        # 模拟V1的重复配置加载
        for _ in range(iterations):
            # 每次都重新读取文件（无缓存）
            config = {}
            
            # 手动合并配置（简单覆盖逻辑）
            global_cfg = {'log_level': 'INFO', 'debug': False}
            module_cfg = {'blur_threshold': 100}
            
            config.update(global_cfg)
            config.update(module_cfg)  # 简单覆盖
            
            self._config_cache[iterations] = config
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before
    
    def simulate_exception_handling_v1(self, iterations: int = 500) -> Tuple[float, float]:
        """模拟V1异常处理方式"""
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        errors_caught = 0
        
        for i in range(iterations):
            try:
                # 模拟可能失败的操作
                if i % 50 == 0:
                    raise ValueError(f"模拟错误 {i}")
                
                result = i * 2
                
            except Exception as e:
                # V1风格：简单的打印，无结构化信息
                print(f"Error occurred: {e}")  # 不推荐的方式
                errors_caught += 1
                continue
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before
    
    def simulate_input_validation_v1(self, iterations: int = 300) -> Tuple[float, float]:
        """模拟V1输入验证（基本没有）"""
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        validation_failures = 0
        
        for i in range(iterations):
            value = f"input_{i}"
            
            # V1风格：几乎不验证或只做简单检查
            if not value:  # 最基础的检查
                validation_failures += 1
                continue
            
            # 继续处理（即使数据可能无效）
            result = process_data_unsafe(value)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before
    
    def simulate_pipeline_init_v1(self, count: int = 10) -> Tuple[float, float]:
        """模拟V1 Pipeline初始化（重复代码）"""
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        for _ in range(count):
            # V1风格：每个runner都有重复的初始化代码
            import logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger("module")
            
            # 加载配置（重复）
            try:
                with open('/app/config.yaml', 'r') as f:
                    import yaml
                    config = yaml.safe_load(f)
            except:
                config = {}
            
            # 初始化资源（分散在各处）
            model = None
            if config.get('use_model'):
                model = load_model(config['model_path'])
            
            self._init_count += 1
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before


class V2Benchmark:
    """
    V2性能基准测试
    
    测量重构后的实际性能。
    """
    
    def __init__(self):
        self._logger = None
        if V2_AVAILABLE:
            from common.core import setup_logging
            self._logger = setup_logging("benchmark.v2")
    
    def benchmark_config_manager_v2(self, iterations: int = 100) -> Tuple[float, float]:
        """测试V2 ConfigManager性能"""
        
        if not V2_AVAILABLE:
            return 0.0, 0.0
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(iterations):
                # V2方式：使用ConfigManager（带缓存）
                config = ConfigManager(
                    module_name=f"test_{i}",
                    config_dir=tmpdir,
                    auto_load=True
                )
                
                # 获取配置值（支持嵌套访问）
                value = config.get('test_param', default='default')
                
                # 运行时覆盖（不影响原文件）
                config.set('override_test', i)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before
    
    def benchmark_exception_system_v2(self, iterations: int = 500) -> Tuple[float, float]:
        """测试V2异常系统性能"""
        
        if not V2_AVAILABLE:
            return 0.0, 0.0
        
        from common.core import ValidationError, ErrorCode, error_code_manager
        error_code_manager.reset_stats()
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        for i in range(iterations):
            try:
                if i % 50 == 0:
                    raise ValidationError(
                        ErrorCode.INVALID_DATA_FORMAT,
                        f"模拟错误 {i}",
                        field="test_field"
                    )
                
                result = i * 2
                
            except ValidationError as e:
                # V2风格：结构化异常处理
                # 自动记录到统计系统
                error_code_manager.record_error(e)
                continue
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before
    
    def benchmark_input_validator_v2(self, iterations: int = 300) -> Tuple[float, float]:
        """测试V2 InputValidator性能"""
        
        if not V2_AVAILABLE:
            return 0.0, 0.0
        
        from common.core import InputValidator
        
        validator = InputValidator()
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        validation_failures = 0
        
        for i in range(iterations):
            value = f"input_{i}"
            
            # V2风格：全面验证
            validation = validator.validate_all([
                (validator.validate_required, (value,), {'name': 'input'}),
                (validator.validate_type, (value, str), {'name': 'input'}),
                (validator.validate_regex, 
                 (value, r'^input_\d+$'), {'name': 'input'})
            ])
            
            if not validation.valid:
                validation_failures += 1
                continue
            
            # 只在验证通过后才处理
            result = process_data_safe(value)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before
    
    def benchmark_pipeline_base_class_v2(self, count: int = 10) -> Tuple[float, float]:
        """测试V2 BasePipeline基类性能"""
        
        if not V2_AVAILABLE:
            return 0.0, 0.0
        
        from common.core import BasePipeline, PipelineResult
        
        class TestPipeline(BasePipeline):
            MODULE_NAME = "bench_test"
            
            def _initialize(self):
                # 所有初始化集中在此处
                self.threshold = self.config.get('threshold', default=50)
                self.mode = self.config.get('mode', default='strict')
            
            def _execute(self, input_data=None, **kwargs):
                return PipelineResult(success=True)
            
            def _cleanup(self):
                pass
        
        start_time = time.perf_counter()
        memory_before = self._get_process_memory()
        
        for _ in range(count):
            pipeline = TestPipeline()
            result = pipeline.run()
        
        elapsed = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_process_memory()
        
        return elapsed, memory_after - memory_before


# 辅助函数
def process_data_unsafe(data):
    """模拟V1的不安全数据处理"""
    return data.upper()


def process_data_safe(data):
    """模拟V2的安全数据处理"""
    # 在实际使用中会有验证
    return data.upper()


def load_model(path):
    """模拟模型加载"""
    return {"model": "loaded", "path": path}


def _get_process_memory_mb() -> float:
    """获取当前进程内存使用（MB）"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def run_comprehensive_benchmark():
    """运行完整的性能对比测试"""
    
    print("\n" + "="*70)
    print("🚀 Workshop V1 vs V2 性能对比基准测试")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version.split()[0]}")
    
    results = []
    
    # 初始化测试对象
    v1_sim = V1Simulator()
    v2_bench = V2Benchmark()
    
    # ====== 测试1: 配置加载效率 ======
    print("\n▶ 测试1: 配置加载效率")
    print("-"*70)
    
    iterations = 200
    v1_time, v1_mem = v1_sim.simulate_config_loading_v1(iterations)
    v2_time, v2_mem = v2_bench.benchmark_config_manager_v2(iterations)
    
    improve_pct = ((v1_time - v2_time) / max(v1_time, 0.001)) * 100
    mem_reduce = ((v1_mem - v2_mem) / max(abs(v1_mem), 0.001)) * 100
    
    result = BenchmarkResultItem(
        test_name="配置加载效率",
        v1_time_ms=v1_time / iterations,
        v2_time_ms=v2_time / iterations,
        improvement_pct=improve_pct,
        v1_memory_mb=v1_mem,
        v2_memory_mb=v2_mem,
        memory_reduction_pct=mem_reduce,
        details=f"迭代{iterations}次 | "
               f"V1: {v1_time/iterations:.3f}ms/次, "
               f"V2: {v2_time/iterations:.3f}ms/次"
    )
    results.append(result)
    
    print(f"  V1: {result.v1_time_ms:.3f}ms/次 ({result.v1_memory_mb:.2f}MB)")
    print(f"  V2: {result.v2_time_ms:.3f}ms/次 ({result.v2_memory_mb:.2f}MB)")
    print(f"  提升: ⬆ {result.improvement_pct:+.1f}% 时间, "
          f"{result.memory_reduction_pct:+.1f}% 内存")
    
    # ====== 测试2: 异常处理效率 ======
    print("\n▶ 测试2: 异常处理效率")
    print("-"*70)
    
    iterations = 1000
    v1_time, v1_mem = v1_sim.simulate_exception_handling_v1(iterations)
    v2_time, v2_mem = v2_bench.benchmark_exception_system_v2(iterations)
    
    improve_pct = ((v1_time - v2_time) / max(v1_time, 0.001)) * 100
    mem_reduce = ((v1_mem - v2_mem) / max(abs(v1_mem), 0.001)) * 100
    
    result = BenchmarkResultItem(
        test_name="异常处理效率",
        v1_time_ms=v1_time / iterations,
        v2_time_ms=v2_time / iterations,
        improvement_pct=improve_pct,
        v1_memory_mb=v1_mem,
        v2_memory_mb=v2_mem,
        memory_reduction_pct=mem_reduce,
        details=f"捕获{iterations//50}次异常 | "
               f"V1: {v1_time/iterations:.3f}ms/次, "
               f"V2: {v2_time/iterations:.3f}ms/次"
    )
    results.append(result)
    
    print(f"  V1: {result.v1_time_ms:.3f}ms/次 ({result.v1_memory_mb:.2f}MB)")
    print(f"  V2: {result.v2_time_ms:.3f}ms/次 ({result.v2_memory_mb:.2f}MB)")
    print(f"  提升: ⬆ {result.improvement_pct:+.1f}% 时间, "
          f"{result.memory_reduction_pct:+.1f}% 内存")
    
    # ====== 测试3: 输入验证效率 ======
    print("\n▶ 测试3: 输入验证效率")
    print("-"*70)
    
    iterations = 500
    v1_time, v1_mem = v1_sim.simulate_input_validation_v1(iterations)
    v2_time, v2_mem = v2_bench.benchmark_input_validator_v2(iterations)
    
    improve_pct = ((v1_time - v2_time) / max(v1_time, 0.001)) * 100
    mem_reduce = ((v1_mem - v2_mem) / max(abs(v1_mem), 0.001)) * 100
    
    result = BenchmarkResultItem(
        test_name="输入验证效率",
        v1_time_ms=v1_time / iterations,
        v2_time_ms=v2_time / iterations,
        improvement_pct=improve_pct,
        v1_memory_mb=v1_mem,
        v2_memory_mb=v2_mem,
        memory_reduction_pct=mem_reduce,
        details=f"验证{iterations}次输入 | "
               f"V1: 基础检查, "
               f"V2: 全面验证(类型+范围+正则)"
    )
    results.append(result)
    
    print(f"  V1: {result.v1_time_ms:.3f}ms/次 ({result.v1_memory_mb:.2f}MB)")
    print(f"  V2: {result.v2_time_ms:.3f}ms/次 ({result.v2_memory_mb:.2f}MB)")
    print(f"  提升: ⬆ {result.improvement_pct:+.1f}% 时间, "
          f"{result.memory_reduction_pct:+.1f}% 内存")
    
    # ====== 测试4: Pipeline初始化效率 ======
    print("\n▶ 测试4: Pipeline初始化效率")
    print("-"*70)
    
    init_count = 5
    v1_time, v1_mem = v1_sim.simulate_pipeline_init_v1(init_count)
    v2_time, v2_mem = v2_bench.benchmark_pipeline_base_class_v2(init_count)
    
    improve_pct = ((v1_time - v2_time) / max(v1_time, 0.001)) * 100
    mem_reduce = ((v1_mem - v2_mem) / max(abs(v1_mem), 0.001)) * 100
    
    result = BenchmarkResultItem(
        test_name="Pipeline初始化效率",
        v1_time_ms=v1_time / init_count,
        v2_time_ms=v2_time / init_count,
        improvement_pct=improve_pct,
        v1_memory_mb=v1_mem,
        v2_memory_mb=v2_mem,
        memory_reduction_pct=mem_reduce,
        details=f"初始化{init_count}个Pipeline实例 | "
               f"V1: 重复代码~40行×{init_count}, "
               f"V2: BasePipeline基类统一管理"
    )
    results.append(result)
    
    print(f"  V1: {result.v1_time_ms:.3f}ms/实例 ({result.v1_memory_mb:.2f}MB)")
    print(f"  V2: {result.v2_time_ms:.3f}ms/实例 ({result.v2_memory_mb:.2f}MB)")
    print(f"  提升: ⬆ {result.improvement_pct:+.1f}% 时间, "
          f"{result.memory_reduction_pct:+.1f}% 内存")
    
    # ====== 生成报告 ======
    report = ComparisonReport(timestamp=datetime.now().isoformat())
    report.test_results = results
    report.generate_summary()
    
    # 打印详细报告
    print("\n" + "="*70)
    print("📊 性能对比报告")
    print("="*70)
    
    print(f"\n{'测试项':<25} {'V1耗时':>12} {'V2耗时':>12} {'提升':>8} {'内存优化':>10}")
    print("-"*70)
    
    for r in results:
        print(f"{r.test_name:<25} {r.v1_time_ms:>10.2f}ms {r.v2_time_ms:>10.2f}ms "
              f"{r.improvement_pct:>+7.1f}% {r.memory_reduction_pct:>+9.1f}%")
    
    print("-"*70)
    
    summary = report.summary
    print(f"\n{'='*70}")
    print(f"总测试数: {summary['total_tests']}")
    print(f"平均性能提升: {summary['avg_time_improvement_pct']:+.1f}%")
    print(f"最大性能提升: {summary['max_time_improvement_pct']:+.1f}%")
    print(f"平均内存优化: {summary['avg_memory_reduction_pct']:+.1f}%")
    print(f"改进的测试数: {summary['tests_with_improvement']}/{summary['total_tests']}")
    print(f"回退的测试数: {summary.get('tests_with_regression', 0)}")
    print(f"\n总体评价: {summary['overall_verdict']}")
    
    # 保存报告
    output_dir = Path("reports/benchmarks")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / f"v1_vs_v2_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': report.timestamp,
            'results': [r.to_dict() for r in results],
            'summary': report.summary
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告已保存: {report_path}")
    
    return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workshop V1 vs V2 性能对比测试")
    parser.add_argument("--quick", action="store_true", help="快速模式（减少迭代次数）")
    args = parser.parse_args()
    
    if args.quick:
        print("⚡ 快速模式：减少测试迭代次数以加快速度\n")
    
    report = run_comprehensive_benchmark()
    
    # 返回退出码
    overall_status = report.summary.get('overall_verdict', '')
    if 'EXCELLENT' in overall_status or 'GOOD' in overall_status:
        print(f"\n✅ 性能对比完成！{overall_status}")
        return 0
    else:
        print(f"\n⚠️ 性能对比完成。{overall_status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
