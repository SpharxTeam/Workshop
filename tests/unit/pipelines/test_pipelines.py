# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Pipeline V3 模块集成测试
# 使用 V3 直接 API (from core_workshop.core.abstractions import ...)

import tempfile
from pathlib import Path

from core_workshop.core.abstractions import BasePipeline, PipelineResult, ErrorCode
from core_workshop.pipelines._validation_helpers import (
    validate_range,
    collect_errors,
)


def test_enhance_pipeline_creation():
    """测试 Enhance Pipeline 创建"""
    from core_workshop.pipelines.run_02_enhance.runner_v2 import EnhancePipeline

    pipeline = EnhancePipeline()

    assert pipeline.MODULE_NAME == "02_enhance"
    assert pipeline.VERSION == "2.0.0"
    assert hasattr(pipeline, '_model_manager')

    print("  ✓ EnhancePipeline creates successfully")


def test_calibrate_pipeline_creation():
    """测试 Calibrate Pipeline 创建"""
    from core_workshop.pipelines.run_03_calibrate.runner_v2 import CalibratePipeline

    pipeline = CalibratePipeline()

    assert pipeline.MODULE_NAME == "03_calibrate"
    assert pipeline.VERSION == "2.0.0"
    assert hasattr(pipeline, '_calibrate_camera')

    print("  ✓ CalibratePipeline creates successfully")


def test_pack_pipeline_creation():
    """测试 Pack Pipeline 创建"""
    from core_workshop.pipelines.run_04_pack.runner_v2 import PackPipeline

    pipeline = PackPipeline()

    assert pipeline.MODULE_NAME == "04_pack"
    assert pipeline.VERSION == "2.0.0"
    assert len(pipeline.SUPPORTED_FORMATS) > 0
    assert 'coco' in pipeline.SUPPORTED_FORMATS
    assert 'yolo' in pipeline.SUPPORTED_FORMATS

    print("  ✓ PackPipeline creates successfully")


def test_delivery_pipeline_creation():
    """测试 Delivery Pipeline 创建"""
    from core_workshop.pipelines.run_05_delivery.runner_v2 import DeliveryPipeline

    pipeline = DeliveryPipeline()

    assert pipeline.MODULE_NAME == "05_delivery"
    assert pipeline.VERSION == "2.0.0"
    assert len(pipeline.REQUIRED_OSS_CONFIG) == 4
    assert 'endpoint' in pipeline.REQUIRED_OSS_CONFIG

    print("  ✓ DeliveryPipeline creates successfully")


def test_streaming_pipeline_creation():
    """测试 Streaming Pipeline 创建"""
    from core_workshop.pipelines.streaming.frame_pipeline_v2 import StreamingPipeline

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一些测试图像文件
        for i in range(5):
            (Path(tmpdir) / f"frame_{i:03d}.jpg").write_bytes(b'\x00' * 100)

        pipeline = StreamingPipeline(source_dir=tmpdir)

        assert pipeline.MODULE_NAME == "streaming"
        assert pipeline.VERSION == "2.0.0"
        assert pipeline._source_dir == tmpdir

        # 测试添加消费者
        quality_consumer = pipeline.add_quality_consumer()
        assert quality_consumer is not None
        assert quality_consumer.name == "quality"
        assert len(pipeline._consumers) == 1

        print("  ✓ StreamingPipeline creates successfully")


def test_streaming_base_consumer():
    """测试 BaseConsumer 基类"""
    from core_workshop.pipelines.streaming.frame_pipeline_v2 import BaseConsumer, FrameData

    class TestConsumer(BaseConsumer):
        def __init__(self):
            super().__init__("test")
            self.processed_items = []

        def process_frame(self, frame_data: FrameData):
            self.processed_items.append(frame_data.frame_idx)
            return {'processed': frame_data.frame_idx}

    consumer = TestConsumer()

    assert consumer.name == "test"
    assert consumer.is_running is False
    assert consumer.processed_count == 0
    assert consumer.avg_processing_time == 0.0

    print("  ✓ BaseConsumer base class works")


def test_frame_data_structure():
    """测试 FrameData 数据结构"""
    from core_workshop.pipelines.streaming.frame_pipeline_v2 import FrameData
    import numpy as np

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame_data = FrameData(
        frame=frame,
        frame_name="test_001.jpg",
        frame_idx=42,
        metadata={'quality': 'good'}
    )

    assert frame_data.frame_idx == 42
    assert frame_data.frame_name == "test_001.jpg"
    assert frame_data.metadata['quality'] == 'good'
    assert "FrameData" in repr(frame_data)

    print("  ✓ FrameData structure works")


def test_pack_supported_formats():
    """测试 Pack Pipeline 支持的格式列表"""
    from core_workshop.pipelines.run_04_pack.runner_v2 import PackPipeline

    expected_formats = ['ros', 'coco', 'yolo', 'custom', 'voc', 'kitti']

    for fmt in expected_formats:
        assert fmt in PackPipeline.SUPPORTED_FORMATS, \
            f"Missing format: {fmt}"

    print("  ✓ PackPipeline supported formats are complete")


def test_delivery_oss_config_loading():
    """测试 Delivery Pipeline OSS 配置加载"""
    from core_workshop.pipelines.run_05_delivery.runner_v2 import DeliveryPipeline
    import os

    pipeline = DeliveryPipeline()

    # 测试配置加载（即使没有环境变量也不应崩溃）
    oss_config = pipeline._load_oss_config()

    assert isinstance(oss_config, dict)
    assert 'prefix' in oss_config  # 应该有默认值

    print("  ✓ Delivery OSS config loading works")


def test_calibrate_chessboard_validation():
    """测试 Calibrate Pipeline 棋盘格参数验证逻辑 (V3)"""
    # V3: 使用 validate_range + collect_errors 替代 InputValidator
    # 有效尺寸
    valid_sizes = [(9, 6), (11, 8), (7, 5)]
    for size in valid_sizes:
        errors = collect_errors(
            validate_range(size[0], 3, 20, 'cols'),
        )
        assert not errors, f"Valid size {size} should pass"

    # 无效尺寸（超出范围）
    invalid_size = (25, 20)
    errors = collect_errors(
        validate_range(invalid_size[0], 3, 20, 'cols'),
    )
    assert errors, f"Invalid size {invalid_size} should fail"

    print("  ✓ Calibrate chessboard validation logic works (V3)")


def test_enhance_confidence_validation():
    """测试 Enhance Pipeline 置信度阈值验证 (V3)"""
    # V3: 使用 validate_range 替代 InputValidator
    # 有效置信度
    valid_values = [0.0, 0.25, 0.5, 1.0]
    for val in valid_values:
        errors = collect_errors(
            validate_range(val, 0.0, 1.0, 'conf'),
        )
        assert not errors, f"Valid confidence {val} should pass"

    # 无效置信度
    invalid_values = [-0.1, 1.5]
    for val in invalid_values:
        errors = collect_errors(
            validate_range(val, 0.0, 1.0, 'conf'),
        )
        assert errors, f"Invalid confidence {val} should fail"

    print("  ✓ Enhance confidence validation works (V3)")


def test_all_pipelines_inherit_base():
    """测试所有 Pipeline 都正确继承 BasePipeline"""
    pipeline_classes = [
        ('EnhancePipeline', 'core_workshop.pipelines.run_02_enhance.runner_v2'),
        ('CalibratePipeline', 'core_workshop.pipelines.run_03_calibrate.runner_v2'),
        ('PackPipeline', 'core_workshop.pipelines.run_04_pack.runner_v2'),
        ('DeliveryPipeline', 'core_workshop.pipelines.run_05_delivery.runner_v2'),
        ('StreamingPipeline', 'core_workshop.pipelines.streaming.frame_pipeline_v2'),
    ]

    for class_name, module_path in pipeline_classes:
        try:
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            assert issubclass(cls, BasePipeline), \
                f"{class_name} does not inherit BasePipeline"

            # 检查是否有必需的方法
            assert hasattr(cls, '_initialize'), f"{class_name} missing _initialize"
            assert hasattr(cls, '_execute'), f"{class_name} missing _execute"
            assert hasattr(cls, '_cleanup'), f"{class_name} missing _cleanup"

            print(f"  ✓ {class_name} correctly inherits BasePipeline")

        except ImportError as e:
            print(f"  ⚠ Could not import {class_name}: {e}")


def test_pipeline_v3_modules():
    """主测试入口：运行所有 Pipeline V3 模块测试"""
    print("\n▶ Testing Pipeline V3 Modules...")

    test_enhance_pipeline_creation()
    test_calibrate_pipeline_creation()
    test_pack_pipeline_creation()
    test_delivery_pipeline_creation()
    test_streaming_pipeline_creation()
    test_streaming_base_consumer()
    test_frame_data_structure()
    test_pack_supported_formats()
    test_delivery_oss_config_loading()
    test_calibrate_chessboard_validation()
    test_enhance_confidence_validation()
    test_all_pipelines_inherit_base()

    print("✓ All Pipeline V3 tests passed!\n")


if __name__ == "__main__":
    test_pipeline_v3_modules()
