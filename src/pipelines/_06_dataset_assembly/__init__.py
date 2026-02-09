"""
数据集打包模块
将各个模块的结果组装成标准数据集
"""

import json
from pathlib import Path
from typing import Dict, Any

class DatasetAssembler:
    """数据集组装器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def assemble_dataset(self, scene_id, pipeline_results):
        """
        组装数据集
        
        Args:
            scene_id: 场景ID
            pipeline_results: 各个流水线的结果
            
        Returns:
            数据集结构
        """
        print(f"[数据集组装] 开始组装数据集: {scene_id}")
        
        dataset = {
            'dataset_info': {
                'name': f'SPHARX_PHYSICS_{scene_id}',
                'version': '1.0.0',
                'scene_id': scene_id,
                'creation_date': '2024-01-01'
            },
            'data_levels': {
                'L1_2d_annotations': pipeline_results.get('2d_annotations', {}),
                'L2_3d_geometry': pipeline_results.get('3d_reconstruction', {}),
                'L3_physics_facts': pipeline_results.get('physics_generation', {})
            },
            'metadata': pipeline_results.get('metadata', {})
        }
        
        return dataset
    
    def export_dataset(self, dataset, output_path, formats=None):
        """
        导出数据集
        
        Args:
            dataset: 数据集字典
            output_path: 输出路径
            formats: 导出格式列表，如 ['json', 'yaml', 'tfrecord']
            
        Returns:
            导出文件列表
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        formats = formats or ['json']
        exported_files = []
        
        for fmt in formats:
            if fmt == 'json':
                file_path = output_path / 'dataset.json'
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(dataset, f, indent=2, ensure_ascii=False)
                exported_files.append(str(file_path))
                print(f"[数据集组装] 导出JSON: {file_path}")
            
            # TODO: 支持更多格式
        
        return exported_files