# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# BasePipeline 单元测试

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.core.base_pipeline import (
    BasePipeline,
    PipelineResult,
    PipelineStatus
)
from common.core.config_manager import ConfigManager
from common.core.exceptions import ErrorCode


class SimpleTestPipeline(BasePipeline):
    """用于测试的简单 Pipeline 实现"""
    
    MODULE_NAME = "test_pipeline"
    VERSION = "1.0.0"
    
    def __init__(self, should_fail=False, **kwargs):
        self._should_fail = should_fail
        self._initialized = False
        self._cleaned_up = False
        super().__init__(**kwargs)
    
    def _initialize(self):
        if self._should_fail:
            raise RuntimeError("Initialization failed")
        self._initialized = True
    
    def _execute(self, input_data=None, **kwargs):
        if self._should_fail:
            raise RuntimeError("Execution failed")
        
        # 模拟处理
        time.sleep(0.01)  # 10ms 模拟处理时间
        
        return PipelineResult(
            success=True,
            output={'processed': input_data},
            metrics={'items_processed': 1}
        )
    
    def _cleanup(self):
        self._cleaned_up = True


def test_pipeline_creation():
    """测试 Pipeline 创建"""
    pipeline = SimpleTestPipeline()
    
    assert pipeline.status == PipelineStatus.CREATED
    assert pipeline.module_name == "test_pipeline"
    assert pipeline.VERSION == "1.0.0"
    assert pipeline.is_running is False
    
    print("  ✓ Pipeline creation works")


def test_pipeline_lifecycle():
    """测试 Pipeline 生命周期"""
    pipeline = SimpleTestPipeline()
    
    # 初始状态
    assert pipeline.status == PipelineStatus.CREATED
    assert pipeline._initialized is False
    
    # 运行后状态变化
    result = pipeline.run(input_data="test")
    
    # 应该经过完整生命周期
    assert result.success is True
    assert pipeline._initialized is True
    assert pipeline._cleaned_up is True
    assert pipeline.status == PipelineStatus.SHUTDOWN
    
    print("  ✓ Pipeline lifecycle works correctly")


def test_pipeline_successful_execution():
    """测试成功执行"""
    pipeline = SimpleTestPipeline()
    
    result = pipeline.run(input_data="hello world")
    
    assert result.success is True
    assert result.output == {'processed': 'hello world'}
    assert result.error is None
    assert result.error_code is None
    assert result.execution_time > 0
    assert 'items_processed' in result.metrics
    
    print("  ✓ Successful execution produces correct results")


def test_pipeline_failed_execution():
    """测试失败执行"""
    pipeline = SimpleTestPipeline(should_fail=True)
    
    result = pipeline.run()
    
    assert result.success is False
    assert result.error is not None
    assert "Execution failed" in result.error or "failed" in str(result.error).lower()
    assert result.execution_time >= 0
    
    print("  ✓ Failed execution handles errors properly")


def test_pipeline_init_failure():
    """测试初始化失败"""
    pipeline = SimpleTestPipeline(should_fail=True)
    
    result = pipeline.run()
    
    assert result.success is False
    assert result.error is not None
    
    print("  ✓ Initialization failure handled gracefully")


def test_pipeline_callbacks():
    """测试回调函数"""
    start_called = []
    complete_called = []
    error_called = []
    
    def on_start():
        start_called.append(True)
    
    def on_complete(result):
        complete_called.append(result)
    
    def on_error(error):
        error_called.append(error)
    
    # 成功场景的回调
    pipeline = SimpleTestPipeline()
    pipeline.on_start(on_start)
    pipeline.on_complete(on_complete)
    pipeline.on_error(on_error)
    
    result = pipeline.run(input_data="callback_test")
    
    assert len(start_called) == 1
    assert len(complete_called) == 1
    assert len(error_called) == 0
    assert complete_called[0].success is True
    
    print("  ✓ Callbacks work in success scenario")


def test_pipeline_metrics():
    """测试性能指标收集"""
    pipeline = SimpleTestPipeline()
    
    result = pipeline.run(input_data="metrics_test")
    
    assert 'execution_time' in result.metrics
    assert result.execution_time > 0
    assert result.processed_count >= 1
    
    # 从 pipeline 获取指标
    pipeline_metrics = pipeline.metrics
    assert isinstance(pipeline_metrics, dict)
    
    print("  ✓ Metrics collection works")


def test_pipeline_context_manager():
    """测试上下文管理器支持"""
    with SimpleTestPipeline() as pipeline:
        assert pipeline._initialized is True
        assert pipeline.status == PipelineStatus.READY
    
    # 退出后应该已清理
    assert pipeline._cleaned_up is True
    
    print("  ✓ Context manager support works")


def test_pipeline_health_check():
    """测试健康检查"""
    pipeline = SimpleTestPipeline()
    
    health = pipeline.health_check()
    
    assert 'status' in health
    assert 'module' in health
    assert 'version' in health
    assert health['module'] == "test_pipeline"
    assert health['version'] == "1.0.0"
    
    print("  ✓ Health check works")


def test_pipeline_warnings():
    """测试警告收集"""
    class WarningTestPipeline(BasePipeline):
        MODULE_NAME = "warning_test"
        
        def _initialize(self): pass
        def _cleanup(self): pass
        
        def _execute(self, input_data=None, **kwargs):
            self._add_warning("Warning 1")
            self._add_warning("Warning 2")
            
            return PipelineResult(success=True)
    
    pipeline = WarningTestPipeline()
    result = pipeline.run()
    
    assert len(result.warnings) == 2
    assert "Warning 1" in result.warnings
    assert "Warning 2" in result.warnings
    
    print("  ✓ Warning collection works")


def test_pipeline_repr():
    """测试字符串表示"""
    pipeline = SimpleTestPipeline()
    
    repr_str = repr(pipeline)
    
    assert "SimpleTestPipeline" in repr_str
    assert "test_pipeline" in repr_str
    assert "CREATED" in repr_str or "created" in repr_str.lower()
    
    print("  ✓ String representation works")


def test_base_pipeline():
    """主测试入口：运行所有 BasePipeline 测试"""
    print("\n▶ Testing BasePipeline...")
    
    test_pipeline_creation()
    test_pipeline_lifecycle()
    test_pipeline_successful_execution()
    test_pipeline_failed_execution()
    test_pipeline_init_failure()
    test_pipeline_callbacks()
    test_pipeline_metrics()
    test_pipeline_context_manager()
    test_pipeline_health_check()
    test_pipeline_warnings()
    test_pipeline_repr()
    
    print("✓ All BasePipeline tests passed!\n")


if __name__ == "__main__":
    test_base_pipeline()
