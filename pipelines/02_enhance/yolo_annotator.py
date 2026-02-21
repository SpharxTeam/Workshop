#!/usr/bin/env python3
"""
增强模块：使用 YOLOv8 对视频进行目标检测，生成 COCO 格式标注。
增强版：统一日志、异常处理、支持配置文件、优先使用本地预下载模型。
"""
import argparse
import os
import cv2
import json
import numpy as np
from ultralytics import YOLO

# 本地配置加载模块
import config_loader

import logging
import sys

MODULE_NAME = os.path.basename(__file__).replace('.py', '')
LOG_DIR = "/logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, f"{MODULE_NAME}.log"))
    ]
)
logger = logging.getLogger(MODULE_NAME)

def process_video(video_path, output_dir, config=None, **kwargs):
    """
    对视频逐帧进行目标检测，保存 COCO 格式标注
    config: 模块配置字典
    kwargs: 命令行参数覆盖（conf, model）
    """
    if config is None:
        config = {}
    conf_thres = kwargs.get('conf', config.get('conf_threshold', 0.25))
    model_path = kwargs.get('model', config.get('model_path', 'yolov8n.pt'))

    # 优先使用本地预下载的模型（位于 /app/models/）
    if not os.path.isabs(model_path) and not os.path.exists(model_path):
        local_model = os.path.join('/app/models', os.path.basename(model_path))
        if os.path.exists(local_model):
            model_path = local_model
            logger.info(f"使用本地预下载模型: {model_path}")

    logger.info(f"加载模型 {model_path}...")
    try:
        model = YOLO(model_path)
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"无法打开视频: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"视频信息: {width}x{height}, {fps} fps, 总帧数 {total_frames}")

    coco_output = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    # 获取类别名称
    categories = []
    for i, (k, v) in enumerate(model.names.items()):
        categories.append({"id": i, "name": v, "supercategory": "object"})
    coco_output["categories"] = categories

    annotation_id = 0
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=conf_thres, verbose=False)

        coco_output["images"].append({
            "id": frame_id,
            "file_name": f"frame_{frame_id:06d}.jpg",
            "width": width,
            "height": height
        })

        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)

            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                x1, y1, x2, y2 = box
                x, y, w, h = float(x1), float(y1), float(x2-x1), float(y2-y1)
                annotation = {
                    "id": annotation_id,
                    "image_id": frame_id,
                    "category_id": int(cls_id),
                    "bbox": [x, y, w, h],
                    "area": w * h,
                    "segmentation": [],
                    "iscrowd": 0,
                    "score": float(conf)
                }
                coco_output["annotations"].append(annotation)
                annotation_id += 1

        frame_id += 1
        if frame_id % 100 == 0:
            logger.info(f"已处理 {frame_id}/{total_frames} 帧")

    cap.release()
    logger.info(f"处理完成，共检测到 {annotation_id} 个目标")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "annotations.json")
    with open(output_path, "w") as f:
        json.dump(coco_output, f, indent=2)

    logger.info(f"标注文件已保存到 {output_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="场景目录（包含rgb.mp4）")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--conf", type=float, help="置信度阈值")
    parser.add_argument("--model", help="模型路径")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = config_loader.load_config(args.config, "enhance")
    video_path = os.path.join(args.input, "rgb.mp4")
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        exit(1)

    kwargs = {}
    if args.conf is not None:
        kwargs['conf'] = args.conf
    if args.model is not None:
        kwargs['model'] = args.model

    try:
        success = process_video(video_path, args.output, config=config, **kwargs)
        exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"处理失败: {e}", exc_info=True)
        exit(1)