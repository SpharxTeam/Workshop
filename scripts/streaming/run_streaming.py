# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 流式处理入口：使用生产者-消费者模型并行处理帧，并生成 COCO 格式标注

import argparse
import os
import sys
import json
import logging
from pathlib import Path
from ultralytics import YOLO

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipelines.streaming.frame_pipeline import PipelineOrchestrator

def convert_to_coco(detections_list, model_names, output_path):
    """
    将流式检测结果转换为 COCO 格式
    detections_list: list of dicts, each with 'frame_idx', 'frame_name', 'detections', 'width', 'height'
    """
    if not detections_list:
        return None
    
    # 获取统一尺寸（从第一帧获取）
    first = detections_list[0]
    img_width = first['width']
    img_height = first['height']
    
    coco = {
        "images": [],
        "annotations": [],
        "categories": [{"id": int(i), "name": str(v), "supercategory": "object"} for i, v in enumerate(model_names.values())]
    }
    ann_id = 0
    for item in detections_list:
        frame_idx = item['frame_idx']
        frame_name = item['frame_name']
        coco["images"].append({
            "id": int(frame_idx),
            "file_name": str(frame_name),
            "width": img_width,
            "height": img_height
        })
        for det in item['detections']:
            x1, y1, x2, y2 = det['bbox']
            w = x2 - x1
            h = y2 - y1
            coco["annotations"].append({
                "id": int(ann_id),
                "image_id": int(frame_idx),
                "category_id": int(det['class_id']),
                "bbox": [x1, y1, w, h],
                "area": float(w * h),
                "segmentation": [],
                "iscrowd": 0,
                "score": float(det['confidence'])
            })
            ann_id += 1
    with open(output_path, "w") as f:
        json.dump(coco, f, indent=2)
    return coco

def main():
    parser = argparse.ArgumentParser(description="流式处理RGB图像序列")
    parser.add_argument("--input", required=True, help="输入RGB图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--model", default="/data/models/yolov8n.pt", help="模型路径")
    parser.add_argument("--config", help="配置文件路径（可选）")
    parser.add_argument("--queue-size", type=int, default=30, help="队列大小")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("streaming")

    if not os.path.isdir(args.input):
        logger.error(f"输入目录不存在: {args.input}")
        sys.exit(1)

    try:
        model = YOLO(args.model)
        logger.info(f"模型加载完成: {args.model}")
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
        logger.info(f"质量结果已保存: {quality_path}")

    if enhance_consumer.results:
        detections_path = os.path.join(args.output, "detections.json")
        with open(detections_path, "w") as f:
            json.dump(enhance_consumer.results, f, indent=2)
        logger.info(f"检测结果已保存: {detections_path}")

        # 生成 COCO 格式标注（兼容传统模块）
        coco_path = os.path.join(args.output, "annotations.json")
        convert_to_coco(enhance_consumer.results, model.names, coco_path)
        logger.info(f"COCO 标注已保存: {coco_path}")

    logger.info(f"流式处理完成: 质量模块处理 {len(quality_consumer.results)} 帧, 增强模块处理 {len(enhance_consumer.results)} 帧")

if __name__ == "__main__":
    main()