# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 测试打包模块

import pytest
import json
from pathlib import Path

def create_scene_structure(base_dir, scene_id):
    """创建模拟场景目录结构用于测试"""
    scene_dir = base_dir / scene_id
    scene_dir.mkdir()
    # 创建必需文件
    (scene_dir / "rgb").mkdir()
    (scene_dir / "depth").mkdir()
    (scene_dir / "rgb").joinpath("frame_000000.jpg").touch()
    (scene_dir / "depth").joinpath("frame_000000.png").touch()
    (scene_dir / "timestamps.csv").write_text("timestamp\n1000\n2000")
    # 可选文件
    quality_dir = scene_dir / "quality"
    quality_dir.mkdir()
    (quality_dir / "quality_report.json").write_text('{"test": true}')
    enhanced_dir = scene_dir / "enhanced"
    enhanced_dir.mkdir()
    (enhanced_dir / "annotations.json").write_text('{"annotations": []}')
    calib_dir = scene_dir / "calib"
    calib_dir.mkdir()
    (calib_dir / "intrinsics.json").write_text('{"camera_matrix": []}')
    return scene_dir

def test_pack_scene_success(temp_output_dir):
    """测试打包成功"""
    from pipelines.pack.algorithm.packer import pack_scene
    
    scene_dir = create_scene_structure(temp_output_dir, "scene_001")
    output_dir = temp_output_dir / "dataset"
    
    result = pack_scene(str(scene_dir), str(output_dir))
    assert result is True
    
    # 检查输出目录
    assert output_dir.exists()
    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["scene_id"] == "scene_001"
    assert len(manifest["files"]) > 0

def test_pack_scene_missing_required(temp_output_dir):
    """测试缺少必需文件的情况"""
    from pipelines.pack.algorithm.packer import pack_scene
    
    scene_dir = temp_output_dir / "scene_bad"
    scene_dir.mkdir()
    # 不创建 rgb.mp4 或 timestamps.csv
    
    with pytest.raises(FileNotFoundError):
        pack_scene(str(scene_dir), str(temp_output_dir / "out"))