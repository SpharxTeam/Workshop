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

def process_video(video_path, output_dir, model_path='yolov8n.pt', conf_thres=0.25):
    """对视频逐帧进行目标检测，保存 COCO 格式标注"""
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    coco_output = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    # 获取类别名称（COCO 标准80类）
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
            print(f"已处理 {frame_id}/{total_frames} 帧")

    cap.release()

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "annotations.json")
    with open(output_path, "w") as f:
        json.dump(coco_output, f, indent=2)

    print(f"检测完成，共处理 {frame_id} 帧，生成标注 {annotation_id} 个")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="场景目录（包含rgb.mp4）")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值")
    args = parser.parse_args()

    video_path = os.path.join(args.input, "rgb.mp4")
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        exit(1)

    success = process_video(video_path, args.output, conf_thres=args.conf)
    exit(0 if success else 1)