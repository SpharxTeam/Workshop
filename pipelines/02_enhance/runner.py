#!/usr/bin/env python3
"""
增强模块：使用 YOLOv8 对视频进行目标检测，生成 COCO 格式标注。
"""
import argparse
import os
import cv2
import json
import numpy as np
from ultralytics import YOLO
import logging
import sys
from config_loader import load_config

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
    if config is None:
        config = {}
    conf_thres = kwargs.get('conf', config.get('conf_threshold', 0.25))
    model_path = kwargs.get('model', config.get('model_path', 'yolov8n.pt'))

    # 优先使用本地预下载模型
    if not os.path.isabs(model_path) and not os.path.exists(model_path):
        local_model = os.path.join('/app/common/models', os.path.basename(model_path))
        if os.path.exists(local_model):
            model_path = local_model
            logger.info(f"使用本地模型: {model_path}")

    logger.info(f"加载模型 {model_path}")
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
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"视频信息: {width}x{height}, 总帧数 {total_frames}")

    coco = {
        "images": [],
        "annotations": [],
        "categories": [{"id": i, "name": v, "supercategory": "object"} for i, v in enumerate(model.names.values())]
    }
    ann_id = 0
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, conf=conf_thres, verbose=False)
        coco["images"].append({
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
                w, h = x2 - x1, y2 - y1
                coco["annotations"].append({
                    "id": ann_id,
                    "image_id": frame_id,
                    "category_id": int(cls_id),
                    "bbox": [float(x1), float(y1), float(w), float(h)],
                    "area": w * h,
                    "segmentation": [],
                    "iscrowd": 0,
                    "score": float(conf)
                })
                ann_id += 1
        frame_id += 1
        if frame_id % 100 == 0:
            logger.info(f"已处理 {frame_id}/{total_frames} 帧")

    cap.release()
    logger.info(f"检测完成，共 {ann_id} 个目标")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "annotations.json")
    with open(out_path, "w") as f:
        json.dump(coco, f, indent=2)
    logger.info(f"标注已保存: {out_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="场景目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--conf", type=float, help="置信度阈值")
    parser.add_argument("--model", help="模型路径")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(module_name="02_enhance") if not args.config else load_config(config_path=args.config)
    video_path = os.path.join(args.input, "rgb.mp4")
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        sys.exit(1)

    kwargs = {}
    if args.conf is not None:
        kwargs['conf'] = args.conf
    if args.model is not None:
        kwargs['model'] = args.model

    try:
        success = process_video(video_path, args.output, config=config, **kwargs)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"处理失败: {e}", exc_info=True)
        sys.exit(1)