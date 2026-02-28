# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
#YOLOv8 目标检测核心算法。
# ============================================================================

import os
import cv2
import json
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)

def process_video(video_path, output_dir, config=None, **kwargs):
    if config is None:
        config = {}
    conf_thres = kwargs.get('conf', config.get('conf_threshold', 0.25))
    model_path = kwargs.get('model', config.get('model_path', 'yolov8n.pt'))

    # 优先使用环境变量指定的模型路径
    env_model = os.environ.get('YOLO_MODEL_PATH')
    if env_model and os.path.exists(env_model):
        model_path = env_model
        logger.info(f"使用环境变量指定模型: {model_path}")
    elif not os.path.isabs(model_path) and not os.path.exists(model_path):
        local_model = os.path.join('/data/models', os.path.basename(model_path))
        if os.path.exists(local_model):
            model_path = local_model
            logger.info(f"使用挂载的模型: {model_path}")
        else:
            logger.error(f"模型文件不存在: {model_path} 或 {local_model}")
            raise FileNotFoundError(f"模型文件 {model_path} 不存在")

    logger.info(f"加载模型 {model_path}")
    try:
        model = YOLO(model_path)
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise

    # 尝试打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"无法打开视频: {video_path}，可能文件损坏或缺少解码器")

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