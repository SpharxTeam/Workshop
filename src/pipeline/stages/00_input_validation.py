"""
00 输入数据验证阶段
验证输入数据的完整性和格式正确性
"""
from ..stage_base import PipelineStage
import os
from typing import Dict, Any

class InputValidationStage(PipelineStage):
    """输入数据验证阶段"""
    
    def __init__(self):
        super().__init__(
            stage_id="00_input_validation",
            name="输入数据验证",
            description="验证输入数据完整性"
        )
        
    def validate(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        input_path = input_data.get('input_path')
        if not input_path:
            raise ValueError("Missing input_path parameter")
            
        if not os.path.exists(input_path):
            raise ValueError(f"Input path does not exist: {input_path}")
            
        return True
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段逻辑"""
        self.validate(input_data)
        
        input_path = input_data['input_path']
        image_count = len([f for f in os.listdir(input_path) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        
        return {
            'validated': True,
            'image_count': image_count,
            'validation_time': self.get_timestamp()
        }