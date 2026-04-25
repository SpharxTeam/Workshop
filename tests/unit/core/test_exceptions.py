# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 异常系统单元测试

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.core.exceptions import (
    ErrorCode,
    ErrorSeverity,
    ErrorContext,
    ErrorChain,
    WorkshopError,
    ConfigurationError,
    PipelineError,
    ValidationError,
    HardwareError,
    DataIOError,
    ErrorCodeManager,
    error_code_manager
)


def test_error_code_enum():
    """测试错误码枚举定义"""
    assert ErrorCode.SUCCESS == 0
    assert ErrorCode.UNKNOWN_ERROR == 1000
    assert ErrorCode.CONFIG_NOT_FOUND == 2000
    assert ErrorCode.PIPELINE_INIT_FAILED == 3000
    assert ErrorCode.VALIDATION_FAILED == 4000
    assert ErrorCode.HARDWARE_INIT_FAILED == 5000
    assert ErrorCode.READ_ERROR == 6000
    print("  ✓ Error code enum defined correctly")


def test_workshop_error_creation():
    """测试异常类创建"""
    error = WorkshopError(
        ErrorCode.INVALID_PARAMETER,
        "Test error message",
        param1="value1"
    )
    
    assert error.code == ErrorCode.INVALID_PARAMETER
    assert str(error) == "Test error message"
    assert error.context_data['param1'] == "value1"
    assert error.severity == ErrorSeverity.ERROR
    print("  ✓ WorkshopError creation works")


def test_error_descriptions():
    """测试多语言错误描述"""
    error_en = WorkshopError(ErrorCode.FILE_NOT_FOUND)
    error_zh = WorkshopError(ErrorCode.CONFIG_PARSE_ERROR)
    
    assert error_en.description_en != ""
    assert error_zh.description_zh != ""
    assert "not found" in error_en.description_en.lower() or "zh_cn" in error_en.description_en.lower()
    print("  ✓ Error descriptions work (i18n)")


def test_error_severity_levels():
    """测试错误严重程度判断"""
    critical_errors = [
        ErrorCode.OUT_OF_MEMORY,
        ErrorCode.PERMISSION_DENIED,
    ]
    
    warning_errors = [
        ErrorCode.TIMEOUT,
        ErrorCode.CANCELED,
    ]
    
    for code in critical_errors:
        err = WorkshopError(code)
        assert err.severity == ErrorSeverity.CRITICAL
    
    for code in warning_errors:
        err = WorkshopError(code)
        assert err.severity == ErrorSeverity.WARNING
    
    print("  ✓ Error severity levels correct")


def test_subclass_exceptions():
    """测试子类异常"""
    config_err = ConfigurationError(
        ErrorCode.CONFIG_NOT_FOUND,
        "Config file missing"
    )
    assert isinstance(config_err, WorkshopError)
    assert config_err.code == ErrorCode.CONFIG_NOT_FOUND
    
    pipeline_err = PipelineError(
        ErrorCode.PIPELINE_EXECUTION_FAILED,
        "Pipeline failed"
    )
    assert isinstance(pipeline_err, WorkshopError)
    
    validation_err = ValidationError(
        ErrorCode.VALIDATION_FAILED,
        "Invalid input"
    )
    assert isinstance(validation_err, WorkshopError)
    
    hardware_err = HardwareError(
        ErrorCode.DEVICE_NOT_FOUND,
        "Device not found"
    )
    assert isinstance(hardware_err, WorkshopError)
    
    dataio_err = DataIOError(
        ErrorCode.READ_ERROR,
        "Read failed"
    )
    assert isinstance(dataio_err, WorkshopError)
    
    print("  ✓ Subclass exceptions work correctly")


def test_error_chain():
    """测试错误链追踪"""
    chain = ErrorChain()
    
    ctx1 = ErrorContext(
        file="module1.py",
        line=10,
        function="func1",
        message="First error",
        error_code=ErrorCode.VALIDATION_FAILED
    )
    
    ctx2 = ErrorContext(
        file="module2.py",
        line=20,
        function="func2",
        message="Second error",
        error_code=ErrorCode.INVALID_DATA_FORMAT
    )
    
    chain.add_context(ctx1)
    chain.add_context(ctx2)
    
    assert chain.depth == 2
    assert chain.code == ErrorCode.INVALID_DATA_FORMAT
    
    print("  ✓ Error chain tracking works")


def test_error_code_manager():
    """测试错误码管理器统计功能"""
    manager = ErrorCodeManager()
    
    err1 = WorkshopError(ErrorCode.IO_ERROR, "IO Error 1")
    err2 = ConfigurationError(ErrorCode.CONFIG_NOT_FOUND, "Config Missing")
    err3 = PipelineError(ErrorCode.MODULE_LOAD_FAILED, "Module Load Failed")
    
    manager.record_error(err1)
    manager.record_error(err2)
    manager.record_error(err3)
    
    stats = manager.get_stats()
    
    assert stats['total_errors'] == 3
    assert stats['errors_by_category']['WorkshopError'] == 1
    assert stats['errors_by_category']['ConfigurationError'] == 1
    assert stats['errors_by_category']['PipelineError'] == 1
    assert stats['last_error'] is not None
    
    manager.reset_stats()
    reset_stats = manager.get_stats()
    assert reset_stats['total_errors'] == 0
    
    print("  ✓ ErrorCodeManager statistics work")


def test_exception_repr():
    """测试异常的字符串表示"""
    error = WorkshopError(
        ErrorCode.TIMEOUT,
        "Operation timed out",
        timeout=30
    )
    
    repr_str = repr(error)
    assert "WorkshopError" in repr_str
    assert "TIMEOUT" in repr_str
    assert "warning" in repr_str.lower() or "error" in repr_str.lower()
    
    print("  ✓ Exception __repr__ works")


def test_exception_system():
    """主测试入口：运行所有异常系统测试"""
    print("\n▶ Testing Exception System...")
    
    test_error_code_enum()
    test_workshop_error_creation()
    test_error_descriptions()
    test_error_severity_levels()
    test_subclass_exceptions()
    test_error_chain()
    test_error_code_manager()
    test_exception_repr()
    
    print("✓ All exception system tests passed!\n")


if __name__ == "__main__":
    test_exception_system()
