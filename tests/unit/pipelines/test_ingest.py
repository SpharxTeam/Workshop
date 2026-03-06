# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# test_ingest模块测试

import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import os

# 模拟 pyrealsense2
@pytest.fixture
def mock_rs(monkeypatch):
    """模拟 RealSense 相关类和函数"""
    mock_pipeline = MagicMock()
    mock_config = MagicMock()
    
    # 模拟帧对象
    mock_frames = MagicMock()
    mock_color_frame = MagicMock()
    mock_color_frame.get_data.return_value = np.ones((480, 640, 3), dtype=np.uint8)
    mock_frames.get_color_frame.return_value = mock_color_frame
    
    # 模拟深度帧
    mock_depth_frame = MagicMock()
    mock_depth_frame.get_data.return_value = np.ones((480, 640), dtype=np.uint16)
    mock_frames.get_depth_frame.return_value = mock_depth_frame
    
    # 模拟 pipeline
    mock_pipeline.wait_for_frames.side_effect = [mock_frames] * 3 + [StopIteration]
    
    # 注入模拟
    import sys
    sys.modules['pyrealsense2'] = MagicMock()
    sys.modules['pyrealsense2'].pipeline.return_value = mock_pipeline
    sys.modules['pyrealsense2'].config.return_value = mock_config
    
    return mock_pipeline, mock_config

def test_parse_bag_success(mock_rs, temp_output_dir):
    """测试 parse_bag 正常解析"""
    from pipelines.ingest.algorithm.bag_parser import parse_bag
    
    # 执行
    result = parse_bag("dummy.bag", str(temp_output_dir))
    
    # 验证
    assert result is True
    rgb_dir = temp_output_dir / "rgb"
    depth_dir = temp_output_dir / "depth"
    assert rgb_dir.exists()
    assert depth_dir.exists()
    # 检查是否生成了3帧
    rgb_files = list(rgb_dir.glob("frame_*.jpg"))
    depth_files = list(depth_dir.glob("frame_*.png"))
    assert len(rgb_files) == 3
    assert len(depth_files) == 3
    # 检查时间戳文件
    ts_path = temp_output_dir / "timestamps.csv"
    assert ts_path.exists()
    df = pd.read_csv(ts_path)
    assert len(df) == 3

def test_parse_bag_file_not_exist(temp_output_dir):
    """测试 bag 文件不存在的情况"""
    from pipelines.ingest.algorithm.bag_parser import parse_bag
    result = parse_bag("/nonexistent.bag", str(temp_output_dir))
    assert result is False