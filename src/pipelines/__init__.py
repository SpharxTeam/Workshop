"""
SpharxWorkshop ?????
???????????
"""

import importlib
from typing import Dict, Any

# ???????
PIPELINE_MODULES = {
    'preprocess': '_01_preprocess',
    'annotation_2d': '_02_2d_annotation',
    'reconstruction_3d': '_03_3d_reconstruction',
    'lifting_2d_to_3d': '_04_2d_to_3d_lifting',
    'physics_generation': '_05_physics_generation',
    'dataset_assembly': '_06_dataset_assembly'
}

def get_pipeline_module(module_name: str):
    """"""
    if module_name not in PIPELINE_MODULES:
        raise ValueError(f"????????: {module_name}")
    
    module_path = f"src.pipelines.{PIPELINE_MODULES[module_name]}"
    return importlib.import_module(module_path)

def list_pipelines() -> Dict[str, str]:
    """"""
    return {
        'preprocess': '?????',
        'annotation_2d': '2D????',
        'reconstruction_3d': '3D???????',
        'lifting_2d_to_3d': '2D?3D???????',
        'physics_generation': '???????????',
        'dataset_assembly': '??????????'
    }

# ?????
try:
    from .pipeline_manager import PipelineManager
    from .pipeline_controller import PipelineController
except ImportError as e:
    print(f"??: ?????????: {e}")

# ???????
try:
    from ._01_preprocess import DataPreprocessor as Preprocessor
    from ._02_2d_annotation import AnnotationPipeline, SAMAnnotator
except ImportError as e:
    print(f"??: ???????????: {e}")

__all__ = [
    'get_pipeline_module',
    'list_pipelines',
    'PipelineManager',
    'PipelineController',
    'Preprocessor',
    'AnnotationPipeline', 
    'SAMAnnotator'
]
