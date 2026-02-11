"""
SpharxWorkshop 流水线模块
包含所有数据处理流水线
"""

import importlib
from typing import Dict, Any

# 流水线模块映射
PIPELINE_MODULES = {
    'preprocess': '_01_preprocess',
    'annotation_2d': '_02_2d_annotation',
    'reconstruction_3d': '_03_3d_reconstruction',
    'lifting_2d_to_3d': '_04_2d_to_3d_lifting',
    'physics_generation': '_05_physics_generation',
    'dataset_assembly': '_06_dataset_assembly'
}


def get_pipeline_module(module_name: str):
    """
    动态获取流水线模块
    
    Args:
        module_name: 模块名称（如 'preprocess', 'annotation_2d'）
        
    Returns:
        模块对象
        
    Raises:
        ImportError: 模块不存在或导入失败
    """
    if module_name not in PIPELINE_MODULES:
        raise ValueError(f"未知的流水线模块: {module_name}")
    
    module_path = f"src.pipelines.{PIPELINE_MODULES[module_name]}"
    return importlib.import_module(module_path)


def list_pipelines() -> Dict[str, str]:
    """列出所有可用的流水线模块"""
    return {
        'preprocess': '数据预处理',
        'annotation_2d': '2D自动标注',
        'reconstruction_3d': '3D重建（开发中）',
        'lifting_2d_to_3d': '2D到3D提升（开发中）',
        'physics_generation': '物理事实生成（开发中）',
        'dataset_assembly': '数据集打包（开发中）'
    }


# 导入管理器
try:
    from .pipeline_manager import PipelineManager, get_pipeline_manager
    from .pipeline_controller import PipelineController
except ImportError as e:
    print(f"警告: 流水线管理器导入失败: {e}")
    # 在开发阶段这可能是正常的


# 向后兼容的导入
try:
    from ._01_preprocess import DataPreprocessor
    from ._02_2d_annotation import AnnotationPipeline, SAMAnnotator
except ImportError as e:
    print(f"警告: 部分流水线模块导入失败: {e}")
    # 在开发阶段这可能是正常的


__all__ = [
    'get_pipeline_module',
    'list_pipelines',
    'PipelineManager',
    'get_pipeline_manager',
    'PipelineController',
    'DataPreprocessor',
    'AnnotationPipeline',
    'SAMAnnotator'
]
