"""
配置数据模型定义
使用Pydantic进行配置验证和类型检查
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from pathlib import Path
import yaml
import os

class SAMConfig(BaseModel):
    """SAM模型配置"""
    model_type: str = Field(default="vit_h", description="模型类型: vit_h, vit_l, vit_b")
    checkpoint_path: str = Field(default="/models/sam_vit_h_4b8939.pth", description="模型检查点路径")
    device: str = Field(default="cuda", description="运行设备: cuda 或 cpu")
    points_per_side: int = Field(default=32, description="每边采样点数")
    pred_iou_thresh: float = Field(default=0.88, description="预测IoU阈值")
    batch_size: int = Field(default=4, description="批处理大小")

class COLMAPConfig(BaseModel):
    """COLMAP配置"""
    max_image_size: int = Field(default=1600, description="最大图像尺寸")
    max_num_features: int = Field(default=8192, description="最大特征点数")
    camera_model: str = Field(default="SIMPLE_RADIAL", description="相机模型")
    
    @validator('camera_model')
    def validate_camera_model(cls, v):
        valid_models = ["SIMPLE_PINHOLE", "PINHOLE", "SIMPLE_RADIAL", "RADIAL"]
        if v not in valid_models:
            raise ValueError(f"相机模型必须是以下之一: {valid_models}")
        return v

class PipelineStageConfig(BaseModel):
    """流水线阶段配置"""
    enabled: bool = Field(default=True, description="是否启用该阶段")
    timeout: int = Field(default=3600, description="超时时间(秒)")
    retry_count: int = Field(default=3, description="重试次数")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="阶段特定参数")

class PipelineConfig(BaseModel):
    """完整流水线配置"""
    
    # 项目配置
    project_name: str = Field(default_factory=lambda: os.getenv("PROJECT_NAME", "SpharxWorkshop"))
    project_stage: str = Field(default_factory=lambda: os.getenv("PROJECT_STAGE", "DEVELOPMENT"))
    
    # 路径配置
    input_dir: str = Field(default_factory=lambda: os.getenv("SPHARX_INPUT_DIR", "/home/SpharxWorkshop/data/input/scenes"))
    output_dir: str = Field(default_factory=lambda: os.getenv("SPHARX_OUTPUT_DIR", "/home/SpharxWorkshop/data/output/datasets"))
    workspace_dir: str = Field(default_factory=lambda: os.getenv("SPHARX_WORKSPACE_DIR", "/home/SpharxWorkshop/workspace"))
    
    # 各阶段配置
    preprocessing: PipelineStageConfig = Field(default_factory=PipelineStageConfig)
    annotation_2d: PipelineStageConfig = Field(default_factory=PipelineStageConfig)
    reconstruction_3d: PipelineStageConfig = Field(default_factory=PipelineStageConfig)
    physics_generation: PipelineStageConfig = Field(default_factory=PipelineStageConfig)
    
    # 组件配置
    sam_config: SAMConfig = Field(default_factory=SAMConfig)
    colmap_config: COLMAPConfig = Field(default_factory=COLMAPConfig)
    
    # 性能配置
    max_concurrent_tasks: int = Field(default=4, description="最大并发任务数")
    enable_gpu: bool = Field(default=True, description="是否启用GPU加速")
    
    # 质量控制
    enable_quality_check: bool = Field(default=True, description="是否启用质量检查")
    min_quality_score: float = Field(default=0.8, description="最低质量分数")
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "PipelineConfig":
        """从YAML文件加载配置"""
        if not yaml_path or not Path(yaml_path).exists():
            return cls()
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f) or {}
        
        return cls(**config_dict)
    
    def to_yaml(self, yaml_path: str):
        """保存配置到YAML文件"""
        config_dict = self.dict(exclude_none=True)
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    def get_scene_input_path(self, scene_id: str) -> Path:
        """获取场景输入路径"""
        return Path(self.input_dir) / scene_id
    
    def get_scene_output_path(self, scene_id: str) -> Path:
        """获取场景输出路径"""
        return Path(self.output_dir) / f"SPHARX_PHYSICS_{scene_id}"
        