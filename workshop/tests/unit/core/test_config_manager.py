# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 配置管理器单元测试

import sys
import tempfile
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.core.config_manager import ConfigManager, load_config
from common.core.exceptions import ConfigurationError, ErrorCode


def test_config_manager_creation():
    """测试配置管理器创建"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建配置目录结构
        config_dir = Path(tmpdir) / "configs"
        modules_dir = config_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建全局配置
        global_config = {
            'global_setting': 'global_value',
            'nested': {'key': 'value'}
        }
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump(global_config, f)
        
        # 创建模块配置
        module_config = {
            'module_setting': 'module_value',
            'nested': {'key': 'module_override'}
        }
        with open(modules_dir / "01_quality.yaml", 'w') as f:
            yaml.dump(module_config, f)
        
        # 测试创建
        mgr = ConfigManager(
            config_dir=str(config_dir),
            module_name="01_quality"
        )
        
        assert mgr.is_loaded
        assert mgr.module_name == "01_quality"
        print("  ✓ ConfigManager creates successfully")


def test_config_merge_priority():
    """测试配置合并优先级"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        modules_dir = config_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        # 全局配置
        global_cfg = {'key1': 'global', 'key2': 'global'}
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump(global_cfg, f)
        
        # 模块配置（应覆盖全局）
        module_cfg = {'key1': 'module', 'key3': 'module'}
        with open(modules_dir / "test_module.yaml", 'w') as f:
            yaml.dump(module_cfg, f)
        
        mgr = ConfigManager(
            config_dir=str(config_dir),
            module_name="test_module"
        )
        
        # 模块配置应该覆盖全局
        assert mgr.get('key1') == 'module'
        # 全局独有的配置保留
        assert mgr.get('key2') == 'global'
        # 模块独有的配置存在
        assert mgr.get('key3') == 'module'
        
        print("  ✓ Config merge priority works correctly")


def test_config_get_with_defaults():
    """测试带默认值的配置获取"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump({'existing_key': 'existing_value'}, f)
        
        mgr = ConfigManager(config_dir=str(config_dir))
        
        # 获取存在的值
        assert mgr.get('existing_key') == 'existing_value'
        
        # 获取不存在的值（返回默认）
        assert mgr.get('nonexistent') is None
        assert mgr.get('nonexistent', default='default_val') == 'default_val'
        
        # 获取嵌套值
        assert mgr.get('nonexistent.nested.key', default='fallback') == 'fallback'
        
        print("  ✓ Config get with defaults works")


def test_config_nested_access():
    """测试嵌套配置访问"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        config_dir.mkdir(exist_ok=True)
        
        nested_config = {
            'level1': {
                'level2': {
                    'level3': 'deep_value'
                }
            },
            'array': [1, 2, 3]
        }
        
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump(nested_config, f)
        
        mgr = ConfigManager(config_dir=str(config_dir))
        
        # 点号分隔访问嵌套值
        assert mgr.get('level1.level2.level3') == 'deep_value'
        assert mgr.get('level1.level2') == {'level3': 'deep_value'}
        
        print("  ✓ Nested config access works")


def test_config_runtime_override():
    """测试运行时配置覆盖"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump({'original_key': 'original_value'}, f)
        
        mgr = ConfigManager(config_dir=str(config_dir))
        
        # 设置运行时覆盖
        mgr.set('original_key', 'overridden_value')
        mgr.set('new_key', 'new_value')
        
        assert mgr.get('original_key') == 'overridden_value'
        assert mgr.get('new_key') == 'new_value'
        
        print("  ✓ Runtime config override works")


def test_config_validation_schema():
    """测试 Schema 验证"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        config_dir.mkdir(exist_ok=True)
        
        test_config = {
            'threshold': 150,
            'mode': 'strict',
            'count': 10
        }
        
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump(test_config, f)
        
        mgr = ConfigManager(config_dir=str(config_dir))
        
        schema = {
            'threshold': {
                'type': int,
                'min': 0,
                'max': 255,
                'required': True
            },
            'mode': {
                'type': str,
                'allowed': ['strict', 'relaxed'],
                'required': True
            },
            'count': {
                'type': int,
                'min': 1,
                'required': True
            },
            'optional_field': {
                'required': False
            }
        }
        
        errors = mgr.validate_schema(schema)
        # 当前配置符合 schema，不应有错误
        assert len(errors) == 0
        
        print("  ✓ Config validation schema works")


def test_load_from_file():
    """测试从文件加载配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建 YAML 配置文件
        config_file = Path(tmpdir) / "custom_config.yaml"
        custom_config = {
            'custom_key': 'custom_value',
            'number': 42,
            'flag': True
        }
        with open(config_file, 'w') as f:
            yaml.dump(custom_config, f)
        
        mgr = ConfigManager(auto_load=False)
        mgr.load_from_file(str(config_file))
        
        assert mgr.is_loaded
        assert mgr.get('custom_key') == 'custom_value'
        assert mgr.get('number') == 42
        assert mgr.get('flag') is True
        
        print("  ✓ Load config from file works")


def test_config_reload():
    """测试配置重新加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        config_dir.mkdir(exist_ok=True)
        
        # 初始配置
        initial_config = {'version': 1}
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump(initial_config, f)
        
        mgr = ConfigManager(config_dir=str(config_dir))
        assert mgr.get('version') == 1
        
        # 修改配置文件
        updated_config = {'version': 2, 'new_feature': True}
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump(updated_config, f)
        
        # 重新加载
        mgr.reload()
        
        assert mgr.get('version') == 2
        assert mgr.get('new_feature') is True
        
        print("  ✓ Config reload works")


def test_config_to_dict():
    """测试配置导出为字典"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "configs"
        modules_dir = config_dir / "modules"
        modules_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "pipeline_config.yaml", 'w') as f:
            yaml.dump({'global': True}, f)
        with open(modules_dir / "test.yaml", 'w') as f:
            yaml.dump({'module': True}, f)
        
        mgr = ConfigManager(config_dir=str(config_dir), module_name="test")
        export = mgr.to_dict()
        
        assert 'config' in export
        assert 'global_config' in export
        assert 'module_config' in export
        assert 'loaded' in export
        assert export['loaded'] is True
        
        print("  ✓ Config to_dict export works")


def test_config_manager():
    """主测试入口：运行所有配置管理器测试"""
    print("\n▶ Testing Config Manager...")
    
    test_config_manager_creation()
    test_config_merge_priority()
    test_config_get_with_defaults()
    test_config_nested_access()
    test_config_runtime_override()
    test_config_validation_schema()
    test_load_from_file()
    test_config_reload()
    test_config_to_dict()
    
    print("✓ All Config Manager tests passed!\n")


if __name__ == "__main__":
    test_config_manager()
