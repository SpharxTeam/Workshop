"""
流水线控制器
协调各个流水线模块的执行
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from src.schemas.config import PipelineConfig
from src.utils.logging import PipelineLogger

# 动态导入流水线模块
from src.pipelines import get_pipeline_module

logger = logging.getLogger(__name__)

class PipelineController:
    """流水线控制器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = PipelineLogger("controller")
        self.results_cache = {}
        
    async def run_2d_pipeline(self, scene_id: str) -> Dict[str, Any]:
        """运行2D标注流水线"""
        try:
            scene_path = self.config.get_scene_input_path(scene_id)
            output_path = self.config.get_scene_output_path(scene_id) / "L1_2d_annotations"
            
            self.logger.start_stage("2d_pipeline")
            
            # 1. 数据预处理
            preprocess_module = get_pipeline_module('preprocess')
            preprocessor = preprocess_module.DataPreprocessor()
            preprocess_result = preprocessor.preprocess_scene(scene_path)
            
            # 2. 2D自动标注
            annotation_module = get_pipeline_module('annotation_2d')
            annotator = annotation_module.SAMAnnotator()
            annotator.initialize()
            
            annotation_pipeline = annotation_module.AnnotationPipeline()
            annotation_result = annotation_pipeline.process_scene(scene_path)
            
            # 3. 保存结果
            annotation_pipeline.save_results(output_path)
            
            self.logger.end_stage("2d_pipeline", success=True, metrics={
                'images_processed': len(annotation_result.get('images', [])),
                'total_annotations': annotation_result.get('summary', {}).get('total_annotations', 0),
                'avg_quality': annotation_result.get('summary', {}).get('avg_quality_score', 0)
            })
            
            return {
                'preprocess': preprocess_result,
                'annotation_2d': annotation_result,
                'output_path': str(output_path)
            }
            
        except Exception as e:
            self.logger.error(f"2D流水线执行失败: {e}", exception=e)
            self.logger.end_stage("2d_pipeline", success=False)
            raise
    
    async def run_3d_pipeline(self, scene_id: str) -> Dict[str, Any]:
        """运行3D重建流水线"""
        try:
            self.logger.start_stage("3d_pipeline")
            
            # TODO: 实现3D重建流水线
            reconstruction_module = get_pipeline_module('reconstruction_3d')
            reconstructor = reconstruction_module.Reconstruction3D()
            
            # 这里需要获取2D流水线的结果作为输入
            # 暂时返回占位结果
            result = reconstructor.process_scene(scene_id, [], None)
            
            self.logger.end_stage("3d_pipeline", success=True, metrics={
                'status': 'development'
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"3D流水线执行失败: {e}", exception=e)
            self.logger.end_stage("3d_pipeline", success=False)
            raise
    
    async def run_physics_pipeline(self, scene_id: str) -> Dict[str, Any]:
        """启动物理事实生成流水线"""
        try:
            self.logger.start_stage("physics_pipeline")
            
            # TODO: 实现物理事实生成流水线
            physics_module = get_pipeline_module('physics_generation')
            physics_generator = physics_module.PhysicsGenerator()
            
            # 这里需要获取2D和3D流水线的结果作为输入
            # 暂时返回占位结果
            result = physics_generator.generate_physics({}, {})
            
            self.logger.end_stage("physics_pipeline", success=True, metrics={
                'status': 'development'
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"物理流水线执行失败: {e}", exception=e)
            self.logger.end_stage("physics_pipeline", success=False)
            raise
    
    async def run_full_pipeline(self, scene_id: str) -> Dict[str, Any]:
        """运行完整流水线"""
        try:
            self.logger.start_stage("full_pipeline")
            
            results = {}
            
            # 1. 运行2D流水线
            if self.config.annotation_2d.enabled:
                results['2d'] = await self.run_2d_pipeline(scene_id)
            
            # 2. 运行3D流水线
            if self.config.reconstruction_3d.enabled:
                results['3d'] = await self.run_3d_pipeline(scene_id)
            
            # 3. 运行物理流水线
            if self.config.physics_generation.enabled:
                results['physics'] = await self.run_physics_pipeline(scene_id)
            
            # 4. 组装数据集
            if self.config.get('enable_dataset_assembly', True):
                assembly_module = get_pipeline_module('dataset_assembly')
                assembler = assembly_module.DatasetAssembler()
                
                dataset = assembler.assemble_dataset(scene_id, results)
                output_path = self.config.get_scene_output_path(scene_id)
                exported_files = assembler.export_dataset(dataset, output_path)
                
                results['dataset'] = {
                    'dataset': dataset,
                    'exported_files': exported_files
                }
            
            self.logger.end_stage("full_pipeline", success=True, metrics={
                'total_stages': len(results),
                'completed_stages': [k for k in results.keys()]
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"完整流水线执行失败: {e}", exception=e)
            self.logger.end_stage("full_pipeline", success=False)
            raise