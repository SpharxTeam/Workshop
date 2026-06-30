# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop V3 集成测试 - 多模块协作验证
# 验证各组件之间的正确协作
# 使用 V3 直接 API (from core_workshop.core.abstractions import ...)

import tempfile
import time
from pathlib import Path

from core_workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    ErrorCode,
    PipelineError,
    ValidationError,
)
from core_workshop.pipelines._validation_helpers import (
    validate_range,
    validate_path_exists_dir,
    validate_directory_writable,
    collect_errors,
)


def test_config_to_pipeline_integration():
    """测试1: 配置管理与Pipeline集成"""
    print("\n▶ 测试: ConfigService → Pipeline 集成")

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

        # 在Pipeline中使用ConfigService (V3)
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
        print("  ✓ ConfigService 与 Pipeline 集成正常")


def test_exception_in_pipeline():
    """测试2: 异常体系在Pipeline中的传播"""
    print("\n▶ 测试: Exception System → Pipeline 集成")

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

    print("  ✓ 异常系统在Pipeline中正确传播")


def test_validation_helpers_in_pipeline():
    """测试3: V3 验证助手与Pipeline集成"""
    print("\n▶ 测试: V3 Validation Helpers → Pipeline 集成")

    class ValidatedPipeline(BasePipeline):
        MODULE_NAME = "validated_test"

        def _initialize(self): pass

        def _execute(self, input_data=None, **kwargs):
            value = kwargs.get('value')

            # V3: 使用 validate_range + collect_errors
            errors = collect_errors(
                validate_range(value, 0, 100, 'value'),
            )

            if errors:
                return PipelineResult(
                    success=False,
                    error='\n'.join(errors),
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

    print("  ✓ V3 Validation Helpers 在Pipeline中正确工作")


def test_path_validation_in_pipeline():
    """测试4: 路径验证与Pipeline集成"""
    print("\n▶ 测试: Path Validation → Pipeline 集成")

    with tempfile.TemporaryDirectory() as tmpdir:
        existing_dir = Path(tmpdir) / "input"
        existing_dir.mkdir()

        output_dir = Path(tmpdir) / "output"

        # 验证存在的目录
        errors = collect_errors(
            validate_path_exists_dir(str(existing_dir), 'input'),
            validate_directory_writable(str(output_dir), 'output'),
        )
        assert not errors, "有效路径应该通过"
        assert output_dir.exists(), "输出目录应被自动创建"

        # 验证不存在的目录
        errors = collect_errors(
            validate_path_exists_dir("/nonexistent/path", 'bad_input'),
        )
        assert errors, "不存在的路径应该失败"

    print("  ✓ Path Validation 与 Pipeline 集成正常")


def test_error_code_coverage():
    """测试5: ErrorCode 覆盖率验证"""
    print("\n▶ 测试: ErrorCode 覆盖率")

    # V3: 验证 ErrorCode v4.0 九大域的关键值
    assert ErrorCode.CONFIG_FILE_NOT_FOUND.value == 1005
    assert ErrorCode.PIPELINE_INIT_FAILED.value == 2001
    assert ErrorCode.VALIDATION_FAILED.value == 3001
    assert ErrorCode.HARDWARE_NOT_CONNECTED.value == 4001
    assert ErrorCode.IO_FILE_NOT_FOUND.value == 5001
    assert ErrorCode.MODULE_LOAD_FAILED.value == 6001

    # 验证错误码域隔离
    config_codes = [c for c in ErrorCode if 1000 <= c.value < 2000]
    pipeline_codes = [c for c in ErrorCode if 2000 <= c.value < 3000]
    validation_codes = [c for c in ErrorCode if 3000 <= c.value < 4000]

    assert len(config_codes) > 0, "Config 域应有错误码"
    assert len(pipeline_codes) > 0, "Pipeline 域应有错误码"
    assert len(validation_codes) > 0, "Validation 域应有错误码"

    print("  ✓ ErrorCode v4.0 覆盖率正常")


def test_pipeline_error_context():
    """测试6: PipelineError 上下文传播"""
    print("\n▶ 测试: PipelineError 上下文传播")

    try:
        inner = ValueError("底层错误")
        raise PipelineError(
            ErrorCode.MODULE_LOAD_FAILED,
            "算法模块加载失败",
            pipeline_name="test_pipeline",
            pipeline_stage="initialize",
            cause=inner,
        )
    except PipelineError as e:
        assert e.code == ErrorCode.MODULE_LOAD_FAILED
        assert "算法模块加载失败" in str(e)
        assert e.__cause__ is inner
        print("  ✓ PipelineError 上下文传播正常")


def run_all_integration_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("Workshop V3 集成测试套件")
    print("=" * 60)

    tests = [
        ("Config → Pipeline", test_config_to_pipeline_integration),
        ("Exception → Pipeline", test_exception_in_pipeline),
        ("Validation → Pipeline", test_validation_helpers_in_pipeline),
        ("Path Validation", test_path_validation_in_pipeline),
        ("ErrorCode Coverage", test_error_code_coverage),
        ("PipelineError Context", test_pipeline_error_context),
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

    print("\n" + "=" * 60)
    print(f"集成测试结果: {passed}/{len(tests)} 通过")

    if failed > 0:
        print(f"⚠️ {failed} 个测试失败")
        return 1
    else:
        print("✅ 所有集成测试通过！")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_all_integration_tests())
