# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

"""标准化数据IO工具 - 与 deepness 项目保持一致的接口规范"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def load_scene_data(scene_dir: str) -> Dict[str, Any]:
    """
    加载场景数据
    
    Args:
        scene_dir: 场景数据目录路径
        
    Returns:
        包含场景元数据和数据文件路径的字典
        
    Raises:
        FileNotFoundError: 当场景目录不存在时
        ValueError: 当场景数据不完整时
    """
    scene_path = Path(scene_dir)
    if not scene_path.exists():
        raise FileNotFoundError(f"场景目录不存在: {scene_dir}")
    
    # 加载元数据
    manifest_path = scene_path / "manifest.json"
    if not manifest_path.exists():
        logger.warning(f"场景元数据文件不存在: {manifest_path}")
        manifest = {}
    else:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    
    # 收集数据文件
    data_files = {
        'rgb_images': list(scene_path.glob("rgb/*.png")) + list(scene_path.glob("rgb/*.jpg")),
        'depth_images': list(scene_path.glob("depth/*.png")),
        'annotations': list(scene_path.glob("annotations.json")),
        'calibration': list(scene_path.glob("intrinsics.json")) + list(scene_path.glob("extrinsics.json")),
        'timestamps': list(scene_path.glob("timestamps.csv"))
    }
    
    # 过滤存在的文件
    data_files = {k: [str(f) for f in v if f.exists()] for k, v in data_files.items()}
    
    result = {
        'scene_id': scene_path.name,
        'scene_path': str(scene_path),
        'manifest': manifest,
        'data_files': data_files,
        'file_count': sum(len(files) for files in data_files.values())
    }
    
    logger.info(f"成功加载场景数据: {scene_path.name}, 文件数: {result['file_count']}")
    return result

def save_processed_data(data: Dict[str, Any], output_dir: str, format_type: str = "json") -> None:
    """
    保存处理结果数据
    
    Args:
        data: 要保存的数据字典
        output_dir: 输出目录路径
        format_type: 保存格式 ("json", "yaml")
        
    Raises:
        ValueError: 当格式类型不支持时
        IOError: 当保存失败时
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if format_type == "json":
        output_file = output_path / "processed_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif format_type == "yaml":
        output_file = output_path / "processed_data.yaml"
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"不支持的格式类型: {format_type}")
    
    logger.info(f"数据已保存到: {output_file}")

def validate_data_integrity(data_dir: str) -> Dict[str, Any]:
    """
    验证数据完整性
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        包含验证结果的字典
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        return {
            'valid': False,
            'errors': [f"数据目录不存在: {data_dir}"]
        }
    
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    # 检查必需文件
    required_files = ['manifest.json']
    for req_file in required_files:
        if not (data_path / req_file).exists():
            validation_results['errors'].append(f"缺少必需文件: {req_file}")
    
    # 统计各类文件数量
    file_stats = {
        'rgb_images': len(list(data_path.glob("rgb/*.[pj][np]g"))),
        'depth_images': len(list(data_path.glob("depth/*.png"))),
        'annotation_files': len(list(data_path.glob("annotations.json"))),
        'calibration_files': len(list(data_path.glob("*trinsics.json")))
    }
    
    validation_results['stats'] = file_stats
    
    # 检查数据一致性
    if file_stats['rgb_images'] != file_stats['depth_images']:
        validation_results['warnings'].append(
            f"RGB图像数量({file_stats['rgb_images']})与深度图像数量({file_stats['depth_images']})不匹配"
        )
    
    validation_results['valid'] = len(validation_results['errors']) == 0
    
    if validation_results['valid']:
        logger.info(f"数据完整性验证通过: {data_dir}")
    else:
        logger.error(f"数据完整性验证失败: {data_dir}")
        for error in validation_results['errors']:
            logger.error(f"  - {error}")
    
    return validation_results

def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件（支持JSON和YAML格式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        FileNotFoundError: 当配置文件不存在时
        ValueError: 当文件格式不支持时
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    suffix = config_file.suffix.lower()
    
    try:
        if suffix in ['.yaml', '.yml']:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        elif suffix == '.json':
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"不支持的配置文件格式: {suffix}")
    except Exception as e:
        logger.error(f"加载配置文件失败 {config_path}: {e}")
        raise

def save_config_file(config_data: Dict[str, Any], config_path: str) -> None:
    """
    保存配置文件
    
    Args:
        config_data: 配置数据字典
        config_path: 配置文件路径
        
    Raises:
        IOError: 当保存失败时
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    suffix = config_file.suffix.lower()
    
    try:
        if suffix in ['.yaml', '.yml']:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        elif suffix == '.json':
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的配置文件格式: {suffix}")
            
        logger.info(f"配置文件已保存: {config_path}")
    except Exception as e:
        logger.error(f"保存配置文件失败 {config_path}: {e}")
        raise