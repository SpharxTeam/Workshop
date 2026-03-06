# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 测试用的共享资源，用于创建临时目录和文件

import pytest
import os
import tempfile
from pathlib import Path

@pytest.fixture
def temp_output_dir():
    """创建一个临时输出目录，测试后自动清理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_rgb_dir(temp_output_dir):
    """创建包含少量模拟RGB图像的目录"""
    import cv2
    import numpy as np
    rgb_dir = temp_output_dir / "rgb"
    rgb_dir.mkdir()
    # 生成3张纯色测试图像
    for i in range(3):
        img = np.ones((480, 640, 3), dtype=np.uint8) * (i * 50)
        cv2.imwrite(str(rgb_dir / f"frame_{i:06d}.jpg"), img)
    return rgb_dir

@pytest.fixture
def sample_timestamps(temp_output_dir):
    """创建模拟时间戳文件"""
    import pandas as pd
    timestamps = pd.DataFrame({'timestamp': [1000 * i for i in range(3)]})
    csv_path = temp_output_dir / "timestamps.csv"
    timestamps.to_csv(csv_path, index=False)
    return csv_path