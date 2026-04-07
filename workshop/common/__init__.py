# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Workshop 通用模块
================

提供通用的工具、配置、仪表板等功能。

子模块:
    - core: 核心基础设施
    - configs: 配置文件管理
    - schemas: 数据模式定义
    - dashboard: Web 监控仪表板
    - scripts: 通用脚本工具
"""

from . import core
from . import configs
from . import schemas
from . import dashboard

__all__ = ['core', 'configs', 'schemas', 'dashboard']
