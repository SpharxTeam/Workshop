# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# YOLOv8 目标检测核心算法

import os
import cv2
import json
import numpy as np
from ultralytics import YOLO
import logging
from .segmentation_auditor import SegmentationAuditor, TemporalConsistencyAuditor

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def process_video(scene_dir, output_dir, config=None, **kwargs):
    """
    处理场景目录中的 RGB 图像序列，生成 COCO 格式标注和分割质量报告。
    """
    rgb_dir = os.path.join(scene_dir, "rgb")
    if not os.path.exists(rgb_dir):
        raise FileNotFoundError(f"RGB 图像目录不存在: {rgb_dir}")

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

    is_seg_model = '-seg' in model_path
    logger.info(f"加载模型 {model_path} (分割模型: {is_seg_model})")
    try:
        model = YOLO(model_path)
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise

    frame_files = sorted([f for f in os.listdir(rgb_dir) if f.startswith('frame_') and f.endswith(('.jpg', '.webp', '.png'))])
    total_frames = len(frame_files)
    if total_frames == 0:
        raise IOError("RGB 目录中没有图像文件")

    first_frame = cv2.imread(os.path.join(rgb_dir, frame_files[0]))
    height, width = first_frame.shape[:2]
    logger.info(f"找到 {total_frames} 帧图像，分辨率: {width}x{height}")

    auditor = None
    consistency_auditor = None
    if is_seg_model:
        auditor = SegmentationAuditor(confidence_threshold=conf_thres)
        consistency_auditor = TemporalConsistencyAuditor(window_size=10)

    coco = {
        "images": [],
        "annotations": [],
        "categories": [{"id": int(i), "name": str(v), "supercategory": "object"} for i, v in enumerate(model.names.values())]
    }
    ann_id = 0
    quality_metrics = {
        'frame_metrics': [],
        'temporal_consistency': [],
        'overall_stats': {}
    } if is_seg_model else None

    for frame_id, frame_name in enumerate(frame_files):
        frame_path = os.path.join(rgb_dir, frame_name)
        frame = cv2.imread(frame_path)
        if frame is None:
            logger.warning(f"无法读取图像 {frame_name}，跳过")
            continue

        results = model(frame, conf=conf_thres, verbose=False)
        coco["images"].append({
            "id": int(frame_id),
            "file_name": str(frame_name),
            "width": int(width),
            "height": int(height)
        })

        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                x1, y1, x2, y2 = map(float, box)
                w = x2 - x1
                h = y2 - y1
                coco["annotations"].append({
                    "id": int(ann_id),
                    "image_id": int(frame_id),
                    "category_id": int(cls_id),
                    "bbox": [x1, y1, w, h],
                    "area": float(w * h),
                    "segmentation": [],
                    "iscrowd": 0,
                    "score": float(conf)
                })
                ann_id += 1

        if is_seg_model and results[0].masks is not None:
            # 假设取第一个目标的掩码作为示例（实际应处理所有目标）
            mask = results[0].masks.data[0].cpu().numpy()
            metrics = auditor.audit_mask(mask, frame)
            quality_metrics['frame_metrics'].append(metrics)
            temporal_score = consistency_auditor.audit_temporal_consistency(mask)
            quality_metrics['temporal_consistency'].append(temporal_score)

        if frame_id % 100 == 0:
            logger.info(f"已处理 {frame_id}/{total_frames} 帧")

    logger.info(f"检测完成，共 {ann_id} 个目标")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "annotations.json")
    with open(out_path, "w") as f:
        json.dump(coco, f, indent=2, cls=NumpyEncoder)
    logger.info(f"标注已保存: {out_path}")

    if is_seg_model and quality_metrics['frame_metrics']:
        quality_metrics['overall_stats'] = {
            'avg_mask_quality': float(np.mean([m['overall_quality'] for m in quality_metrics['frame_metrics']])),
            'avg_temporal_consistency': float(np.mean(quality_metrics['temporal_consistency'])) if quality_metrics['temporal_consistency'] else 0.0,
            'total_frames': total_frames,
            'detected_objects': ann_id
        }
        quality_path = os.path.join(output_dir, "segmentation_quality.json")
        with open(quality_path, "w") as f:
            json.dump(quality_metrics, f, indent=2, cls=NumpyEncoder)
        logger.info(f"分割质量报告已保存: {quality_path}")

    return True