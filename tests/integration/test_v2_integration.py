# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop V2.0 集成测试 - 多模块协作验证
# 验证各组件之间的正确协作

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_config_to_pipeline_integration():
    """测试1: 配置管理器与Pipeline集成"""
    print("\n▶ 测试: ConfigManager → Pipeline 集成")
    
    from common.core import ConfigManager, BasePipeline, PipelineResult, ErrorCode
    
    # 创建测试配置目录
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        config_dir.mkdir()
        modules_dir = config_dir / "modules"
        modules_dir.mkdir()
        
        # 创建模块配置
        import yaml
        module_cfg = {
            'test_param': 'test_value',
            'threshold': 100,
            'enabled': True
        }
        with open(modules_dir / "test_module.yaml", 'w') as f:
            yaml.dump(module_cfg, f)
        
        # 在Pipeline中使用ConfigManager
        class TestIntegratedPipeline(BasePipeline):
            MODULE_NAME = "test_integrated"
            
            def _initialize(self):
                self._param = self.config.get('test_param', default='default')
                self._threshold = self.config.get('threshold', default=50)
                assert self._param == 'test_value', "配置加载失败"
                assert self._threshold == 100, "配置值不匹配"
                self._logger.info("✓ 配置在Pipeline中正确加载")
            
            def _execute(self, input_data=None, **kwargs):
                return PipelineResult(success=True, output={'config_test': True})
            
            def _cleanup(self):
                pass
        
        pipeline = TestIntegratedPipeline(config_dir=str(config_dir))
        result = pipeline.run()
        
        assert result.success, "Pipeline执行应该成功"
        print("  ✓ ConfigManager 与 Pipeline 集成正常")


def test_io_with_pipeline_integration():
    """测试2: IO抽象层与Pipeline集成"""
    print("\n▶ 测试: IOManager → Pipeline 集成")
    
    from common.core import (
        BasePipeline,
        PipelineResult,
        IOManager,
        CompressionFormat
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建使用IO的Pipeline
        class IOPipeline(BasePipeline):
            MODULE_NAME = "io_test"
            
            def _initialize(self):
                self.io_manager = IOManager(
                    storage_backend="local",
                    base_path=tmpdir,
                    auto_connect=True
                )
                self.io_manager.set_compression(CompressionFormat.GZIP)
                
                # 写入测试数据
                test_data = b"integration test data"
                written = self.io_manager.write("test/input.txt", test_data)
                assert written > 0, "写入失败"
                self._logger.info(f"✓ 初始化时写入 {written} 字节")
            
            def _execute(self, input_data=None, **kwargs):
                # 在执行中使用IO
                data = self.io_manager.read("test/input.txt")
                assert data is not None, "读取失败"
                assert len(data) > 0, "数据为空"
                
                return PipelineResult(
                    success=True,
                    output={'data_length': len(data)}
                )
            
            def _cleanup(self):
                if hasattr(self, 'io_manager'):
                    self.io_manager.disconnect()
        
        pipeline = IOPipeline()
        result = pipeline.run()
        
        assert result.success, "IO Pipeline 执行失败"
        assert result.output['data_length'] > 0, "输出数据异常"
        
        print("  ✓ IOManager 与 Pipeline 集成正常")


def test_exception_in_pipeline():
    """测试3: 异常体系在Pipeline中的传播"""
    print("\n▶ 测试: Exception System → Pipeline 集成")
    
    from common.core import (
        BasePipeline,
        PipelineResult,
        ErrorCode,
        ValidationError,
        PipelineError,
        error_code_manager
    )
    
    # 重置错误统计
    error_code_manager.reset_stats()
    
    class ErrorTestPipeline(BasePipeline):
        MODULE_NAME = "error_test"
        
        def _initialize(self): pass
        
        def _execute(self, input_data=None, **kwargs):
            if kwargs.get('should_fail', False):
                raise ValidationError(
                    ErrorCode.INVALID_DATA_FORMAT,
                    "模拟验证错误",
                    field="test_field"
                )
            return PipelineResult(success=True)
        
        def _cleanup(self): pass
    
    pipeline = ErrorTestPipeline()
    
    # 正常情况
    result_ok = pipeline.run()
    assert result_ok.success, "正常情况应该成功"
    
    # 错误情况
    result_fail = pipeline.run(should_fail=True)
    assert not result_fail.success, "错误情况应该失败"
    assert result_fail.error_code == ErrorCode.VALIDATION_FAILED, "错误码不匹配"
    
    # 检查错误是否被记录
    stats = error_code_manager.get_stats()
    assert stats['total_errors'] >= 1, "错误未被记录"
    
    print("  ✓ 异常系统在Pipeline中正确传播和记录")


def test_validator_in_pipeline():
    """测试4: 输入验证器与Pipeline集成"""
    print("\n▶ 测试: InputValidator → Pipeline 集成")
    
    from common.core import (
        BasePipeline,
        PipelineResult,
        InputValidator,
        ErrorCode
    )
    
    class ValidatedPipeline(BasePipeline):
        MODULE_NAME = "validated_test"
        
        def _initialize(self):
            self.validator = InputValidator()
        
        def _execute(self, input_data=None, **kwargs):
            value = kwargs.get('value')
            
            # 使用验证器
            validation = self.validator.validate_all([
                (self.validator.validate_required, (value,), {'name': 'value'}),
                (self.validator.validate_type, (value, int), {'name': 'value'}),
                (self.validator.validate_range, (value, 0, 100), {'name': 'value'}),
            ])
            
            if not validation.valid:
                return PipelineResult(
                    success=False,
                    error='\n'.join(validation.errors),
                    error_code=ErrorCode.VALIDATION_FAILED
                )
            
            return PipelineResult(success=True, output={'validated_value': value})
        
        def _cleanup(self): pass
    
    pipeline = ValidatedPipeline()
    
    # 有效输入
    result_valid = pipeline.run(value=42)
    assert result_valid.success, "有效输入应该通过"
    assert result_valid.output['validated_value'] == 42, "输出值不正确"
    
    # 无效输入（缺失）
    result_missing = pipeline.run(value=None)
    assert not result_missing.success, "缺失值应该失败"
    
    # 无效输入（超出范围）
    result_range = pipeline.run(value=150)
    assert not result_range.success, "超出范围的值应该失败"
    
    print("  ✓ InputValidator 在Pipeline中正确工作")


def test_performance_monitoring():
    """测试5: 性能监控工具集成"""
    print("\n▶ 测试: Performance Tools → 实际应用")
    
    from common.core import (
        BenchmarkSuite,
        PerformanceTimer,
        measure_performance
    )
    
    # 模拟实际业务函数
    def simulate_image_processing(size=1000):
        """模拟图像处理"""
        data = list(range(size))
        processed = [x * 2 for x in data]
        return sum(processed)
    
    # 使用BenchmarkSuite进行对比测试
    suite = BenchmarkSuite("integration_perf")
    
    # 测试不同规模
    for size in [100, 500, 1000]:
        result = suite.benchmark(
            name=f"process_{size}",
            func=simulate_image_processing,
            iterations=10,
            args=(size,)
        )
        
        assert result.iterations > 0, "基准测试应完成"
        assert result.avg_time_ms > 0, "应有耗时记录"
        
        print(f"  处理 {size} 项: 平均 {result.avg_time_ms:.2f}ms, "
              f"P95: {result.p95_time_ms:.2f}ms")
    
    # 使用装饰器测量特定代码块
    @measure_performance("critical_section")
    def critical_operation():
        total = sum(i*i for i in range(5000))
        return total
    
    result, perf_data = critical_operation()
    assert perf_data.avg_time_ms > 0, "应有性能数据"
    
    print(f"  关键段性能: {perf_data.avg_time_ms:.4f}ms")
    
    # 使用PerformanceTimer进行分段计时
    timer = PerformanceTimer("multi_phase_timer")
    timer.start()
    
    phase1_time = 0
    phase2_time = 0
    
    with timer:
        time.sleep(0.01)  # 模拟IO
        phase1_time = timer.lap("io_phase")
        
        time.sleep(0.02)  # 模拟计算
        phase2_time = timer.lap("compute_phase")
    
    elapsed = timer.elapsed_ms
    assert elapsed > 0, "应有总耗时"
    
    print(f"  分段计时: IO={phase1_time*1000:.2f}ms, "
          f"计算={phase2_time*1000:.2f}ms, 总计={elapsed:.2f}ms")
    
    print("  ✓ 性能监控工具集成正常")


def test_security_scanner_on_project_files():
    """测试6: 安全扫描器对项目文件的实际扫描"""
    print("\n▶ 测试: Security Scanner → 项目文件扫描")
    
    from common.core import CodeSecurityScanner, SecuritySeverity
    
    scanner = CodeSecurityScanner()
    
    # 扫描核心模块文件
    project_root = Path(__file__).parent.parent.parent
    core_modules_path = project_root / "common" / "core"
    
    if core_modules_path.exists():
        report = scanner.scan_directory(str(core_modules_path))
        
        print(f"  扫描目录: {core_modules_path}")
        print(f"  扫描文件数: {report.total_files_scanned}")
        print(f"  发现问题: {len(report.findings)}")
        print(f"  严重问题: {report.critical_count}")
        print(f"  高危问题: {report.high_count}")
        
        # 验证报告结构
        assert isinstance(report.findings, list), "findings应该是列表"
        assert report.scan_time != "", "应该有扫描时间"
        
        # 如果发现问题，验证其结构
        if report.findings:
            finding = report.findings[0]
            assert hasattr(finding, 'rule_id'), "finding应该有rule_id"
            assert hasattr(finding, 'severity'), "finding应该有severity"
            assert hasattr(finding, 'title'), "finding应该有title"
            
            print(f"  示例问题: [{finding.rule_id}] {finding.title}")
        
        print("  ✓ 安全扫描器对项目文件工作正常")
    else:
        print("  ⚠ 核心模块目录不存在，跳过此测试")


def run_all_integration_tests():
    """运行所有集成测试"""
    print("="*60)
    print("Workshop V2.0 集成测试套件")
    print("="*60)
    
    tests = [
        ("Config → Pipeline", test_config_to_pipeline_integration),
        ("IO → Pipeline", test_io_with_pipeline_integration),
        ("Exception → Pipeline", test_exception_in_pipeline),
        ("Validator → Pipeline", test_validator_in_pipeline),
        ("Performance Monitoring", test_performance_monitoring),
        ("Security Scanner", test_security_scanner_on_project_files),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {name}: 未预期错误 - {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"集成测试结果: {passed}/{len(tests)} 通过")
    
    if failed > 0:
        print(f"⚠️ {failed} 个测试失败")
        return 1
    else:
        print("✅ 所有集成测试通过！")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_integration_tests())
