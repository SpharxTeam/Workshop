# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# InputValidator 单元测试

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.core.input_validator import InputValidator, ValidationResult


def test_validate_required():
    """测试必填参数验证"""
    validator = InputValidator()
    
    # 有效值
    result = validator.validate_required("value", name="param1")
    assert result.valid is True
    assert result.value == "value"
    
    # None 值
    result = validator.validate_required(None, name="param2")
    assert result.valid is False
    assert "必填" in result.errors[0] or "required" in result.errors[0].lower()
    
    # 空字符串
    result = validator.validate_required("", name="param3")
    assert result.valid is False
    assert "空" in result.errors[0] or "empty" in result.errors[0].lower()
    
    print("  ✓ Required validation works")


def test_validate_type():
    """测试类型验证"""
    validator = InputValidator()
    
    # 正确类型
    result = validator.validate_type(42, int, name="age")
    assert result.valid is True
    assert result.value == 42
    
    # 错误类型
    result = validator.validate_type("not_int", int, name="count")
    assert result.valid is False
    assert "类型错误" in result.errors[0] or "type" in result.errors[0].lower()
    
    # 允许 None
    result = validator.validate_type(None, str, name="optional", allow_none=True)
    assert result.valid is True
    
    print("  ✓ Type validation works")


def test_validate_range():
    """测试范围验证"""
    validator = InputValidator()
    
    # 在范围内
    result = validator.validate_range(50, min_val=0, max_val=100, name="percent")
    assert result.valid is True
    
    # 低于最小值
    result = validator.validate_range(-5, min_val=0, max_val=100, name="percent")
    assert result.valid is False
    assert "小于" in result.errors[0] or "less than" in result.errors[0].lower()
    
    # 高于最大值
    result = validator.validate_range(150, min_val=0, max_val=100, name="percent")
    assert result.valid is False
    assert "大于" in result.errors[0] or "greater than" in result.errors[0].lower()
    
    print("  ✓ Range validation works")


def test_validate_string_length():
    """测试字符串长度验证"""
    validator = InputValidator()
    
    # 符合长度要求
    result = validator.validate_string_length("hello", min_length=3, max_length=10, name="name")
    assert result.valid is True
    
    # 太短
    result = validator.validate_string_length("hi", min_length=3, max_length=10, name="name")
    assert result.valid is False
    assert "长度" in result.errors[0] or "length" in result.errors[0].lower()
    
    # 太长
    result = validator.validate_string_length("this is a very long string", min_length=3, max_length=10, name="name")
    assert result.valid is False
    
    print("  ✓ String length validation works")


def test_validate_regex():
    """测试正则表达式验证"""
    validator = InputValidator()
    
    # 匹配邮箱
    result = validator.validate_regex(
        "user@example.com",
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        name="email"
    )
    assert result.valid is True
    
    # 不匹配邮箱
    result = validator.validate_regex(
        "invalid-email",
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        name="email"
    )
    assert result.valid is False
    assert "格式" in result.errors[0] or "format" in result.errors[0].lower()
    
    print("  ✓ Regex validation works")


def test_validate_pattern():
    """测试预定义模式验证"""
    validator = InputValidator()
    
    # 邮箱模式
    result = validator.validate_pattern("test@test.com", "email", name="user_email")
    assert result.valid is True
    
    # UUID 模式
    uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    result = validator.validate_pattern(uuid_str, "uuid", name="id")
    assert result.valid is True
    
    # 无效的模式名称
    result = validator.validate_pattern("value", "nonexistent_pattern", name="field")
    assert result.valid is False
    assert "未知" in result.errors[0] or "unknown" in result.errors[0].lower()
    
    print("  ✓ Predefined pattern validation works")


def test_validate_path_security():
    """测试路径安全性验证（防路径遍历）"""
    import tempfile
    validator = InputValidator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 安全路径
        safe_file = tmp_path / "safe_file.txt"
        safe_file.write_text("content")
        
        result = validator.validate_path(
            str(safe_file),
            must_exist=True,
            should_be_file=True,
            name="input_file"
        )
        assert result.valid is True
        
        # 路径遍历攻击
        result = validator.validate_path(
            "../../../etc/passwd",
            must_exist=False,
            name="malicious_path"
        )
        assert result.valid is False
        assert ".." in result.errors[0]
        
        print("  ✓ Path security validation works (prevents traversal)")


def test_validate_directory_writable():
    """测试目录可写性验证"""
    import tempfile
    validator = InputValidator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 已存在的可写目录
        result = validator.validate_directory_writable(tmpdir, name="output_dir")
        assert result.valid is True
        
        # 不存在的目录（应自动创建）
        new_dir = Path(tmpdir) / "new_subdirectory"
        result = validator.validate_directory_writable(str(new_dir), name="new_dir")
        assert result.valid is True
        assert new_dir.exists()
        
        print("  ✓ Directory writable validation works")


def test_batch_validation():
    """测试批量验证"""
    validator = InputValidator()
    
    validations = [
        (validator.validate_required, ("value",), {"name": "param1"}),
        (validator.validate_type, (42, int,), {"name": "param2"}),
        (validator.validate_range, (50,), {"min_val": 0, "max_val": 100, "name": "param3"}),
    ]
    
    result = validator.validate_all(validations)
    assert result.valid is True
    
    # 包含失败的批量验证
    invalid_validations = [
        (validator.validate_required, (None,), {"name": "missing_param"}),
        (validator.validate_type, ("string", int,), {"name": "wrong_type"}),
    ]
    
    result = validator.validate_all(invalid_validations)
    assert result.valid is False
    assert len(result.errors) == 2
    
    print("  ✓ Batch validation works")


def test_custom_validation_rule():
    """测试自定义验证规则"""
    validator = InputValidator()
    
    # 添加自定义规则：偶数检查
    def check_even(value, name="value"):
        if value % 2 != 0:
            return ValidationResult.failure([f"{name} 必须是偶数"])
        return ValidationResult.success(value)
    
    validator.add_custom_rule("even_number", check_even)
    
    # 偶数
    result = validator.validate_custom(4, "even_number", name="count")
    assert result.valid is True
    
    # 奇数
    result = validator.validate_custom(3, "even_number", name="count")
    assert result.valid is False
    assert "偶数" in result.errors[0] or "even" in result.errors[0].lower()
    
    print("  ✓ Custom validation rule works")


def test_input_validator():
    """主测试入口：运行所有 InputValidator 测试"""
    print("\n▶ Testing InputValidator...")
    
    test_validate_required()
    test_validate_type()
    test_validate_range()
    test_validate_string_length()
    test_validate_regex()
    test_validate_pattern()
    test_validate_path_security()
    test_validate_directory_writable()
    test_batch_validation()
    test_custom_validation_rule()
    
    print("✓ All InputValidator tests passed!\n")


if __name__ == "__main__":
    test_input_validator()
