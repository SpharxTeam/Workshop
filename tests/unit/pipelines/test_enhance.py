# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 测试增强模块

import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_yolo(monkeypatch):
    """模拟 YOLO 模型"""
    mock_model = MagicMock()
    # 模拟检测结果
    mock_result = MagicMock()
    mock_result.boxes = MagicMock()
    mock_result.boxes.xyxy = MagicMock()
    mock_result.boxes.xyxy.cpu.return_value.numpy.return_value = np.array([[10, 20, 110, 220]])
    mock_result.boxes.conf = MagicMock()
    mock_result.boxes.conf.cpu.return_value.numpy.return_value = np.array([0.95])
    mock_result.boxes.cls = MagicMock()
    mock_result.boxes.cls.cpu.return_value.numpy.return_value = np.array([0])
    mock_model.return_value = [mock_result]
    mock_model.names = {0: 'person'}
    
    # 替换 ultralytics.YOLO
    import ultralytics
    monkeypatch.setattr(ultralytics, 'YOLO', lambda *args, **kwargs: mock_model)
    return mock_model

def test_process_video_success(mock_yolo, sample_rgb_dir, temp_output_dir):
    """测试 process_video 正常处理图像目录"""
    from pipelines.enhance.algorithm.yolo_detector import process_video
    
    # 准备场景目录
    scene_dir = temp_output_dir / "scene_test"
    scene_dir.mkdir()
    # 复制图像到场景目录的 rgb 子目录
    rgb_dir = scene_dir / "rgb"
    import shutil
    shutil.copytree(sample_rgb_dir, rgb_dir)
    
    output_dir = temp_output_dir / "enhanced"
    result = process_video(str(scene_dir), str(output_dir), config={'conf_threshold': 0.25})
    
    assert result is True
    # 检查标注文件
    annot_path = output_dir / "annotations.json"
    assert annot_path.exists()
    with open(annot_path) as f:
        coco = json.load(f)
    assert len(coco["images"]) == 3  # sample_rgb_dir 中有3帧
    assert len(coco["annotations"]) == 3  # 每帧一个目标
    assert coco["categories"][0]["name"] == "person"

def test_process_video_no_images(temp_output_dir):
    """测试目录中没有图像的情况"""
    from pipelines.enhance.algorithm.yolo_detector import process_video
    
    scene_dir = temp_output_dir / "scene_empty"
    scene_dir.mkdir()
    rgb_dir = scene_dir / "rgb"
    rgb_dir.mkdir()  # 空目录
    
    with pytest.raises(IOError, match="RGB 目录中没有图像文件"):
        process_video(str(scene_dir), temp_output_dir)