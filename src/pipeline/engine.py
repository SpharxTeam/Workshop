"""
流水线引擎 - 协调所有处理阶段
"""
import os
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional
from .stage_base import PipelineStage

class PipelineEngine:
    """生产线核心引擎"""
    
    def __init__(self, scene_id: str, enabled_products: List[str],
                 input_dir: str, output_dir: str, workspace_dir: str):
        self.scene_id = scene_id
        self.enabled_products = enabled_products
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.workspace_dir = workspace_dir
        
        # 场景特定路径
        self.scene_input = os.path.join(input_dir, scene_id)
        self.scene_workspace = os.path.join(workspace_dir, scene_id)
        self.scene_output = os.path.join(output_dir, f"{scene_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 创建目录
        os.makedirs(self.scene_workspace, exist_ok=True)
        os.makedirs(self.scene_output, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化日志
        self.logger = logging.getLogger(f"Pipeline.{scene_id}")
        
        # 阶段注册表
        self.stages: Dict[str, PipelineStage] = {}
        self._register_stages()
    
    def _load_config(self) -> Dict:
        """加载流水线配置"""
        config_path = os.path.join(os.path.dirname(__file__), '../../config/pipeline_default.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _register_stages(self):
        """动态注册处理阶段"""
        # 根据启用的产品线决定注册哪些阶段
        stage_classes = {}
        
        # 总是注册输入验证
        from .stages import 00_input_validation
        stage_classes["input_validation"] = 00_input_validation.InputValidationStage
        
        if '2d' in self.enabled_products:
            from .stages import 01_2d_annotation, 02_2d_product_assembly
            stage_classes["2d_annotation"] = 01_2d_annotation.TwoDAnnotationStage
            stage_classes["2d_product"] = 02_2d_product_assembly.TwoDProductAssemblyStage
        
        if '3d_geometry' in self.enabled_products:
            from .stages import 03_3d_reconstruction, 04_2d_to_3d_lift
            stage_classes["3d_reconstruction"] = 03_3d_reconstruction.ThreeDReconstructionStage
            stage_classes["2d_to_3d_lift"] = 04_2d_to_3d_lift.TwoDToThreeDLiftStage
        
        if '3d_physics' in self.enabled_products:
            from .stages import 05_physics_generation, 06_3d_product_assembly
            stage_classes["physics_generation"] = 05_physics_generation.PhysicsGenerationStage
            stage_classes["3d_product"] = 06_3d_product_assembly.ThreeDProductAssemblyStage
        
        # 总是注册输出
        from .stages import 99_output_export
        stage_classes["output_export"] = 99_output_export.OutputExportStage
        
        # 实例化阶段
        for name, stage_class in stage_classes.items():
            self.stages[name] = stage_class(
                config=self.config,
                scene_id=self.scene_id,
                input_dir=self.scene_input,
                workspace_dir=self.scene_workspace,
                output_dir=self.scene_output
            )
    
    def run(self) -> bool:
        """执行完整流水线"""
        self.logger.info(f"开始执行流水线，启用产品: {self.enabled_products}")
        
        # 阶段执行顺序
        stage_order = [
            "input_validation",
            "2d_annotation",
            "2d_product",
            "3d_reconstruction",
            "2d_to_3d_lift",
            "physics_generation",
            "3d_product",
            "output_export"
        ]
        
        # 按顺序执行阶段
        for stage_name in stage_order:
            if stage_name not in self.stages:
                continue
                
            stage = self.stages[stage_name]
            self.logger.info(f"执行阶段: {stage_name}")
            
            try:
                success = stage.execute()
                if not success:
                    self.logger.error(f"阶段 {stage_name} 执行失败")
                    return False
                    
                self.logger.info(f"阶段 {stage_name} 完成")
                
            except Exception as e:
                self.logger.exception(f"阶段 {stage_name} 发生异常: {e}")
                return False
        
        self.logger.info("流水线执行完成")
        return True
    
    def get_status(self) -> Dict:
        """获取流水线状态"""
        return {
            "scene_id": self.scene_id,
            "enabled_products": self.enabled_products,
            "current_stage": None,  # 实际实现中跟踪当前阶段
            "input_dir": self.scene_input,
            "output_dir": self.scene_output,
            "workspace_dir": self.scene_workspace
        }