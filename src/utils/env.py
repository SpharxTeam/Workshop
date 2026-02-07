"""
环境变量管理工具
加载和验证环境配置
"""
import os
from typing import Optional, Dict, Any

class EnvironmentManager:
    """环境变量管理器"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self._load_env_file()
        
    def _load_env_file(self):
        """加载环境变量文件"""
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                            
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量"""
        return os.environ.get(key, default)
        
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔型环境变量"""
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
        
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整型环境变量"""
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default
            
    def validate_required(self, required_vars: list) -> Dict[str, str]:
        """验证必需的环境变量"""
        missing = []
        env_values = {}
        
        for var in required_vars:
            value = self.get(var)
            if value is None:
                missing.append(var)
            else:
                env_values[var] = value
                
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        return env_values