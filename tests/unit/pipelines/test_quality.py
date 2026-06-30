# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# test_quality模块测试

import pytest
import json
from pathlib import Path

def test_generate_quality_report(sample_rgb_dir, sample_timestamps, temp_output_dir):
    """测试质检报告生成"""
    from core_workshop.pipelines.run_01_quality.algorithm.quality_analyzer import generate_quality_report
    
    # 模拟场景目录
    scene_dir = temp_output_dir / "scene_test"
    scene_dir.mkdir()
    # 将rgb目录和timestamps复制到场景目录
    import shutil
    shutil.copytree(sample_rgb_dir, scene_dir / "rgb")
    shutil.copy(sample_timestamps, scene_dir / "timestamps.csv")
    
    output_dir = temp_output_dir / "output"
    generate_quality_report(str(scene_dir), str(output_dir))
    
    # 验证报告生成
    report_path = output_dir / "quality_report.json"
    assert report_path.exists()
    with open(report_path) as f:
        report = json.load(f)
    assert report["scene_id"] == "scene_test"
    assert report["camera_reports"][0]["total_frames"] == 3
    assert "blurry_frames" in report["camera_reports"][0]