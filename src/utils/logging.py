"""
日志工具模块
提供结构化的日志记录功能
"""

import logging
import logging.config
import yaml
from pathlib import Path
import sys
import os
from typing import Optional, Dict, Any

def setup_logging(config_path: Optional[str] = None, default_level=logging.INFO):
    """
    设置日志配置
    
    Args:
        config_path: 日志配置文件路径
        default_level: 默认日志级别
    """
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 处理路径中的变量
        config_str = yaml.dump(config)
        config_str = config_str.replace('${SPHARX_WORKSHOP_ROOT}', 
                                       os.getenv('SPHARX_WORKSHOP_ROOT', '/home/SpharxWorkshop'))
        
        config = yaml.safe_load(config_str)
        logging.config.dictConfig(config)
    else:
        # 默认配置
        logging.basicConfig(
            level=default_level,
            format='[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('/tmp/spharx.log')
            ]
        )
    
    # 创建自定义日志记录器
    logger = logging.getLogger('spharx')
    logger.info("日志系统初始化完成")

class PipelineLogger:
    """流水线专用日志记录器"""
    
    def __init__(self, pipeline_name: str, scene_id: str = None):
        self.logger = logging.getLogger(f"pipelines.{pipeline_name}")
        self.scene_id = scene_id
        self.metrics: Dict[str, Any] = {}
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        extra = {'scene_id': self.scene_id, **kwargs}
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """记录错误日志"""
        extra = {'scene_id': self.scene_id, **kwargs}
        if exception:
            self.logger.error(f"{message}: {exception}", extra=extra, exc_info=True)
        else:
            self.logger.error(message, extra=extra)
    
    def start_stage(self, stage_name: str):
        """记录阶段开始"""
        self.info(f"开始阶段: {stage_name}", stage=stage_name, event="stage_start")
    
    def end_stage(self, stage_name: str, success: bool, metrics: dict = None):
        """记录阶段结束"""
        status = "success" if success else "failed"
        self.info(f"结束阶段: {stage_name} - {status}", 
                 stage=stage_name, event="stage_end", status=status, metrics=metrics)
    
    def record_metric(self, name: str, value: float):
        """记录性能指标"""
        self.metrics[name] = value
        self.info(f"指标记录: {name}={value}", metric_name=name, metric_value=value)