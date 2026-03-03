# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
#流式处理入口：使用生产者-消费者模型并行处理帧

import argparse
import os
import sys
import json
import logging
from pathlib import Path
from ultralytics import YOLO

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipelines.streaming.frame_pipeline import PipelineOrchestrator

def main():
    parser = argparse.ArgumentParser(description="流式处理RGB图像序列")
    parser.add_argument("--input", required=True, help="输入RGB图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--model", default="/data/models/yolov8n.pt", help="模型路径")
    parser.add_argument("--config", help="配置文件路径（可选）")
    parser.add_argument("--queue-size", type=int, default=30, help="队列大小")
    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("streaming")

    # 检查输入目录
    if not os.path.isdir(args.input):
        logger.error(f"输入目录不存在: {args.input}")
        sys.exit(1)

    # 加载模型
    try:
        model = YOLO(args.model)
        logger.info(f"模型加载完成: {args.model}")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        sys.exit(1)

    # 读取配置（如果有）
    config = {}
    if args.config and os.path.exists(args.config):
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"配置文件已加载: {args.config}")

    # 创建流水线编排器
    orchestrator = PipelineOrchestrator(args.input, max_queue_size=args.queue_size)

    # 添加质检消费者（如果需要）
    quality_config = config.get('quality', {})
    quality_consumer = orchestrator.add_quality_consumer(quality_config)

    # 添加增强消费者
    enhance_config = config.get('enhance', {})
    enhance_consumer = orchestrator.add_enhance_consumer(model, enhance_config)

    logger.info("启动流式流水线...")
    results = orchestrator.run()

    # 保存结果
    os.makedirs(args.output, exist_ok=True)

    # 保存质量结果
    if quality_consumer.results:
        quality_path = os.path.join(args.output, "quality_results.json")
        with open(quality_path, "w") as f:
            json.dump(quality_consumer.results, f, indent=2)
        logger.info(f"质量结果已保存: {quality_path}")

    # 保存检测结果
    if enhance_consumer.results:
        detections_path = os.path.join(args.output, "detections.json")
        with open(detections_path, "w") as f:
            json.dump(enhance_consumer.results, f, indent=2)
        logger.info(f"检测结果已保存: {detections_path}")

    # 统计信息
    logger.info(f"流式处理完成: 质量模块处理 {len(quality_consumer.results)} 帧, 增强模块处理 {len(enhance_consumer.results)} 帧")

if __name__ == "__main__":
    main()