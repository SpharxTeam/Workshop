# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 流式处理入口：使用生产者-消费者模型并行处理帧，并生成 COCO 格式标注

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

# 配置日志格式（只配置一次）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("streaming")

# 抑制 Ultralytics 初始化信息
os.environ['ULTRALYTICS_VERBOSE'] = 'False'

def main():
    parser = argparse.ArgumentParser(description="流式处理RGB图像序列")
    parser.add_argument("--input", required=True, help="输入RGB图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--model", default="/data/model/weights/yolo/current/yolov8n.pt", help="模型路径")
    parser.add_argument("--config", help="配置文件路径（可选）")
    parser.add_argument("--queue-size", type=int, default=30, help="队列大小")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        logger.error(f"输入目录不存在: {args.input}")
        sys.exit(1)

    logger.info(f"加载模型: {args.model}")
    try:
        model = YOLO(args.model)
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        sys.exit(1)

    config = {}
    if args.config and os.path.exists(args.config):
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"配置文件已加载: {args.config}")

    orchestrator = PipelineOrchestrator(args.input, max_queue_size=args.queue_size)
    quality_config = config.get('quality', {})
    quality_consumer = orchestrator.add_quality_consumer(quality_config)
    enhance_config = config.get('enhance', {})
    enhance_consumer = orchestrator.add_enhance_consumer(model, enhance_config)

    logger.info("启动流式流水线...")
    results = orchestrator.run()

    os.makedirs(args.output, exist_ok=True)

    if quality_consumer.results:
        quality_path = os.path.join(args.output, "quality_results.json")
        with open(quality_path, "w") as f:
            json.dump(quality_consumer.results, f, indent=2)
        logger.info(f"质量结果已保存 ({len(quality_consumer.results)} 帧)")

    if enhance_consumer.results:
        detections_path = os.path.join(args.output, "detections.json")
        with open(detections_path, "w") as f:
            json.dump(enhance_consumer.results, f, indent=2)
        logger.info(f"检测结果已保存 ({len(enhance_consumer.results)} 帧)")

        # 生成 COCO 标注
        from pipelines.run_02_enhance.algorithm.yolo_detector import convert_to_coco
        coco_path = os.path.join(args.output, "annotations.json")
        convert_to_coco(enhance_consumer.results, model.names, coco_path)
        logger.info(f"COCO 标注已保存")

    logger.info(f"流式处理完成，处理帧数: {len(enhance_consumer.results)}")

if __name__ == "__main__":
    main()