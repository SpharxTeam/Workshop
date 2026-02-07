"""流水线处理阶段基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging


class StageBase(ABC):
    """所有处理阶段的抽象基类"""
    
    def __init__(self, stage_id: str, name: str, description: str):
        self.stage_id = stage_id
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"stage.{stage_id}")
        self.dependencies = []  # 依赖的前置阶段
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据的完整性"""
        pass
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any], 
                config: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段核心逻辑"""
        pass
    
    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """验证输出数据的正确性"""
        pass
    
    def run(self, input_data: Dict[str, Any], 
            config: Dict[str, Any],
            skip_validation: bool = False) -> Dict[str, Any]:
        """运行阶段（模板方法模式）"""
        self.logger.info(f"🚀 开始执行阶段: {self.name}")
        
        # 输入验证
        if not skip_validation:
            if not self.validate_input(input_data):
                raise ValueError(f"输入数据验证失败: {self.stage_id}")
            self.logger.debug("✅ 输入数据验证通过")
        
        # 执行核心逻辑
        try:
            output_data = self.execute(input_data, config)
            self.logger.info(f"✅ 阶段执行完成: {self.name}")
        except Exception as e:
            self.logger.error(f"❌ 阶段执行失败: {self.name}")
            raise RuntimeError(f"阶段 {self.stage_id} 执行异常: {e}") from e
        
        # 输出验证
        if not skip_validation:
            if not self.validate_output(output_data):
                raise ValueError(f"输出数据验证失败: {self.stage_id}")
            self.logger.debug("✅ 输出数据验证通过")
        
        return output_data
    
    def get_stage_info(self) -> Dict[str, Any]:
        """获取阶段信息"""
        return {
            'id': self.stage_id,
            'name': self.name,
            'description': self.description,
            'dependencies': self.dependencies
        }


# 便捷的装饰器用于注册阶段
def register_stage(stage_id: str, name: str, description: str, 
                   dependencies: Optional[list] = None):
    """注册阶段的装饰器"""
    def decorator(cls):
        cls.stage_id = stage_id
        cls.name = name
        cls.description = description
        cls.dependencies = dependencies or []
        return cls
    return decorator