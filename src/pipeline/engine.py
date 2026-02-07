"""
流水线引擎核心模块
负责阶段调度、状态管理和错误处理
"""
from typing import List, Dict, Any, Optional
import logging
from .stage_base import PipelineStage

logger = logging.getLogger(__name__)

class PipelineEngine:
    """流水线执行引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stages: List[PipelineStage] = []
        self.current_stage_index = 0
        self.results = {}
        
    def register_stage(self, stage: PipelineStage):
        """注册处理阶段"""
        self.stages.append(stage)
        logger.info(f"Registered stage: {stage.name}")
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整的流水线"""
        logger.info("Starting pipeline execution")
        
        current_data = input_data.copy()
        
        for i, stage in enumerate(self.stages):
            if not stage.enabled:
                logger.info(f"Skipping disabled stage: {stage.name}")
                continue
                
            try:
                logger.info(f"Executing stage {i+1}/{len(self.stages)}: {stage.name}")
                result = stage.execute(current_data)
                current_data.update(result)
                self.results[stage.id] = result
                logger.info(f"Stage {stage.name} completed successfully")
                
            except Exception as e:
                logger.error(f"Stage {stage.name} failed: {str(e)}")
                if not self.config.get('continue_on_error', False):
                    raise
                logger.warning("Continuing execution due to error tolerance setting")
                
        logger.info("Pipeline execution completed")
        return current_data