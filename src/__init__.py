"""
SpharxWorkshop 空间智能数据生产线
"""

__version__ = "1.0.0"
__author__ = "Spharx Team"
__email__ = "team@spharx.com"

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)