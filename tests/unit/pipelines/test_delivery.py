# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 测试交付模块

import pytest
from pathlib import Path
from unittest.mock import patch

def create_dummy_dataset(base_dir):
    """创建模拟数据集目录"""
    dataset_dir = base_dir / "dataset_001"
    dataset_dir.mkdir()
    (dataset_dir / "rgb").mkdir()
    (dataset_dir / "manifest.json").write_text('{"files": []}')
    (dataset_dir / "rgb/frame_000000.jpg").touch()
    return dataset_dir

@patch('pipelines.delivery.algorithm.oss_uploader.upload_to_oss')
def test_upload_dataset_success(mock_upload, temp_output_dir):
    """测试数据集上传成功"""
    from pipelines.delivery.algorithm.oss_uploader import upload_dataset
    
    dataset_dir = create_dummy_dataset(temp_output_dir)
    oss_config = {
        'endpoint': 'oss-cn-hangzhou.aliyuncs.com',
        'bucket': 'test-bucket',
        'access_key_id': 'test_id',
        'access_key_secret': 'test_secret'
    }
    mock_upload.return_value = True
    
    result = upload_dataset(str(dataset_dir), oss_config)
    assert result is True
    # 验证 upload_to_oss 被调用
    assert mock_upload.call_count > 0

@patch('pipelines.delivery.algorithm.oss_uploader.upload_to_oss')
def test_upload_dataset_partial_failure(mock_upload, temp_output_dir):
    """测试部分文件上传失败"""
    from pipelines.delivery.algorithm.oss_uploader import upload_dataset
    
    dataset_dir = create_dummy_dataset(temp_output_dir)
    oss_config = {'endpoint': 'test', 'bucket': 'test'}
    # 模拟 upload_to_oss 第一次成功，第二次失败
    mock_upload.side_effect = [True, False]
    
    result = upload_dataset(str(dataset_dir), oss_config)
    assert result is False

def test_upload_dataset_dir_not_exist(temp_output_dir):
    """测试数据集目录不存在"""
    from pipelines.delivery.algorithm.oss_uploader import upload_dataset
    
    result = upload_dataset("/nonexistent", {})
    assert result is False