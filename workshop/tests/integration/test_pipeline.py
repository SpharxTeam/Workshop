# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 测试完整流水线

import pytest
import subprocess
import os

def test_full_pipeline_with_small_bag():
    """使用一个小型bag测试完整流水线"""
    # 检查是否存在测试bag（需提前准备）
    bag_path = "tests/fixtures/sample.bag"
    if not os.path.exists(bag_path):
        pytest.skip("测试bag文件不存在")
    
    # 运行流水线脚本
    result = subprocess.run(
        ["./scripts/pipeline/run_full.sh", bag_path],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "全部完成" in result.stdout