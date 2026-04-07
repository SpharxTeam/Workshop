# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Workshop 数据处理管道模块
========================

包含 6 个标准数据处理阶段：

1. Ingest (数据摄入): 解析 ROS bag，压缩图像，隐私脱敏
2. Quality (质量检测): 模糊检测，曝光分析，帧丢弃检测
3. Enhance (增强): YOLO 目标检测，HDVS 分割
4. Calibrate (校准): 棋盘格相机校准，重投影误差评估
5. Pack (打包): 多格式数据集打包 (ROS/COCO/YOLO/VOC/KITTI)
6. Delivery (交付): OSS 上传，通知发送

使用示例:
    from workshop.pipelines.run_00_ingest.runner_v2 import IngestPipeline
    from workshop.pipelines.run_01_quality.runner_v2 import QualityPipeline
    
    # 顺序执行多个 Pipeline
    with IngestPipeline() as ingest:
        result = ingest.run(input_data)
    
    with QualityPipeline() as quality:
        result = quality.run(result.data)
"""

# 导出所有 Pipeline 模块
__all__ = [
    'run_00_ingest',
    'run_01_quality',
    'run_02_enhance',
    'run_03_calibrate',
    'run_04_pack',
    'run_05_delivery',
    'streaming',
]
