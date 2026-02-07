"""
测试配置和固件
"""
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def sample_image_dir():
    """创建测试用图像目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试图像文件
        img_dir = Path(tmpdir) / "images"
        img_dir.mkdir()
        
        # 创建几个测试文件
        for i in range(5):
            (img_dir / f"test_{i}.jpg").touch()
            
        yield str(img_dir)

@pytest.fixture
def sample_config():
    """测试配置"""
    return {
        'input_path': '/test/input',
        'output_path': '/test/output',
        'stages': ['00', '01', '02']
    }