# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# YOLOv8 目标检测核心算法

import os
import cv2
import json
import numpy as np
from ultralytics import YOLO
import logging
from .segmentation_auditor import SegmentationAuditor, TemporalConsistencyAuditor
from .hdvs_segmenter import HDVSSegmenter
import torch

# 自定义JSON编码器以处理numpy类型
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

logger = logging.getLogger(__name__)

def process_video(scene_dir, output_dir, config=None, **kwargs):
    """
    处理场景目录中的 RGB 图像序列，生成 COCO 格式标注并审计质量。
    scene_dir: 场景目录，包含 rgb/ 子目录
    output_dir: 输出目录（用于保存 annotations.json 和质量报告）
    """
    rgb_dir = os.path.join(scene_dir, "rgb")
    if not os.path.exists(rgb_dir):
        raise FileNotFoundError(f"RGB 图像目录不存在: {rgb_dir}")

    conf_thres = kwargs.get('conf', config.get('conf_threshold', 0.25))
    model_path = kwargs.get('model', config.get('model_path', 'yolov8n.pt'))
    use_enhanced_seg = config.get('use_enhanced_segmentation', False)

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

    # 初始化质量审计器
    auditor = SegmentationAuditor(confidence_threshold=conf_thres)
    consistency_auditor = TemporalConsistencyAuditor(window_size=10)

    # 初始化HDVS分割增强（如果启用）
    segmenter = None
    if use_enhanced_seg:
        try:
            segmenter = HDVSSegmenter(num_classes=len(model.names))
            segmenter.eval()
            logger.info("HDVS增强分割器已初始化")
        except Exception as e:
            logger.warning(f"HDVS分割器初始化失败，将使用标准YOLO: {e}")

    # 获取所有图像文件列表
    frame_files = sorted([f for f in os.listdir(rgb_dir) if f.startswith('frame_') and f.endswith(('.jpg', '.webp', '.png'))])
    total_frames = len(frame_files)
    if total_frames == 0:
        raise IOError("RGB 目录中没有图像文件")

    # 读取第一帧获取尺寸
    first_frame = cv2.imread(os.path.join(rgb_dir, frame_files[0]))
    height, width = first_frame.shape[:2]
    logger.info(f"找到 {total_frames} 帧图像，分辨率: {width}x{height}")

    # 准备 COCO 输出
    coco = {
        "images": [],
        "annotations": [],
        "categories": [{"id": int(i), "name": str(v), "supercategory": "object"} for i, v in enumerate(model.names.values())]
    }
    ann_id = 0

    # 质量指标收集
    quality_metrics = {
        'frame_metrics': [],
        'temporal_consistency': [],
        'overall_stats': {}
    }

    for frame_id, frame_name in enumerate(frame_files):
        frame_path = os.path.join(rgb_dir, frame_name)
        frame = cv2.imread(frame_path)
        if frame is None:
            logger.warning(f"无法读取图像 {frame_name}，跳过")
            continue

        # YOLO推理
        results = model(frame, conf=conf_thres, verbose=False)
        
        # 基础图像信息
        coco["images"].append({
            "id": int(frame_id),
            "file_name": str(frame_name),
            "width": int(width),
            "height": int(height)
        })

        # 处理检测结果
        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            
            # 如果有掩码，进行质量审计
            masks = None
            if results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
            
            for i, (box, conf, cls_id) in enumerate(zip(boxes, confs, cls_ids)):
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

                # 如果有掩码且启用了审计
                if masks is not None and i < len(masks):
                    mask = masks[i]
                    # 将掩码缩放到原图尺寸
                    mask_resized = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST)
                    # 审计该掩码
                    metrics = auditor.audit_mask(mask_resized, frame)
                    quality_metrics['frame_metrics'].append({
                        'frame_id': frame_id,
                        'annotation_id': ann_id - 1,
                        **metrics
                    })
                    
                    # 时序一致性（需要累积）
                    temporal_score = consistency_auditor.audit_temporal_consistency(mask_resized)
                    quality_metrics['temporal_consistency'].append({
                        'frame_id': frame_id,
                        'annotation_id': ann_id - 1,
                        'score': temporal_score
                    })

        # 如果启用了HDVS分割增强且没有掩码，可尝试生成细化掩码
        if use_enhanced_seg and segmenter is not None and results[0].boxes is not None:
            # 将图像转换为tensor
            frame_tensor = torch.from_numpy(frame).permute(2,0,1).unsqueeze(0).float() / 255.0
            with torch.no_grad():
                _, _, refined = segmenter(frame_tensor)
            # 这里可以选择将细化结果集成到标注中，暂时略

        if frame_id % 100 == 0:
            logger.info(f"已处理 {frame_id}/{total_frames} 帧")

    logger.info(f"检测完成，共 {ann_id} 个目标")

    # 保存标注
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "annotations.json")
    with open(out_path, "w") as f:
        json.dump(coco, f, indent=2, cls=NumpyEncoder)
    logger.info(f"标注已保存: {out_path}")

    # 保存质量报告
    if quality_metrics['frame_metrics']:
        quality_metrics['overall_stats'] = {
            'avg_mask_quality': float(np.mean([m['overall_quality'] for m in quality_metrics['frame_metrics']])),
            'avg_edge_completeness': float(np.mean([m['edge_completeness'] for m in quality_metrics['frame_metrics']])),
            'avg_internal_consistency': float(np.mean([m['internal_consistency'] for m in quality_metrics['frame_metrics']])),
            'avg_shape_regularity': float(np.mean([m['shape_regularity'] for m in quality_metrics['frame_metrics']])),
            'avg_temporal_consistency': float(np.mean([t['score'] for t in quality_metrics['temporal_consistency']])) if quality_metrics['temporal_consistency'] else 0,
            'total_frames': total_frames,
            'detected_objects': ann_id
        }
        quality_path = os.path.join(output_dir, "segmentation_quality.json")
        with open(quality_path, "w") as f:
            json.dump(quality_metrics, f, indent=2, cls=NumpyEncoder)
        logger.info(f"分割质量报告已保存: {quality_path}")

    return True