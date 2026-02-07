"""
产品基类
定义所有产品的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import json

class BaseProduct(ABC):
    """产品基类"""
    
    def __init__(self, name: str, version: str, output_path: str):
        self.name = name
        self.version = version
        self.output_path = output_path
        
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """验证产品数据"""
        pass
        
    @abstractmethod
    def export(self, data: Dict[str, Any]) -> str:
        """导出产品"""
        pass
        
    def get_metadata(self) -> Dict[str, Any]:
        """获取产品元数据"""
        return {
            'name': self.name,
            'version': self.version,
            'type': self.__class__.__name__,
            'export_time': self._get_current_time()
        }
        
    def _get_current_time(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()