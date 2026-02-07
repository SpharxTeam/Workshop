"""
02 2D产品打包阶段
将2D标注结果打包成标准数据集格式
"""
from ..stage_base import PipelineStage
from typing import Dict, Any

class ProductAssembly2DStage(PipelineStage):
    """2D产品打包阶段"""
    
    def __init__(self):
        super().__init__(
            stage_id="02_2d_product_assembly",
            name="2D产品打包",
            description="打包2D标注产品（COCO/YOLO格式）"
        )
        
    def validate(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        return 'annotations' in input_data
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行产品打包"""
        self.validate(input_data)
        
        # 生成COCO格式数据集
        coco_dataset = {
            'info': {
                'description': 'Spharx 2D标注数据集',
                'version': '1.0'
            },
            'images': [],
            'annotations': input_data['annotations'],
            'categories': []
        }
        
        return {
            'coco_dataset': coco_dataset,
            'product_path': './output/2d_dataset',
            'assembly_time': self.get_timestamp()
        }