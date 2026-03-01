# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# =================================================================================
# RealSense bag 文件解析核心算法（图像序列版）。
# 将每一帧保存为 JPEG 图像，不再生成视频文件。
# =================================================================================
import os
import cv2
import numpy as np
import pandas as pd
import pyrealsense2 as rs
import logging

logger = logging.getLogger(__name__)

def parse_bag(bag_path, output_dir, config=None):
    """解析 bag 文件，生成 RGB 图像序列、深度图和 IMU 数据"""
    logger.info(f"开始解析 bag: {bag_path}")
    if not os.path.exists(bag_path):
        logger.error(f"输入文件不存在: {bag_path}")
        return False

    # 创建目录
    rgb_dir = os.path.join(output_dir, "rgb")
    depth_dir = os.path.join(output_dir, "depth")
    os.makedirs(rgb_dir, exist_ok=True)
    os.makedirs(depth_dir, exist_ok=True)
    logger.info(f"RGB 图像保存目录: {rgb_dir}")
    logger.info(f"深度图保存目录: {depth_dir}")

    pipeline = rs.pipeline()
    cfg = rs.config()
    try:
        rs.config.enable_device_from_file(cfg, bag_path, repeat_playback=False)
        cfg.enable_all_streams()
    except Exception as e:
        logger.error(f"配置 bag 文件时出错: {e}")
        return False

    timestamps = []
    imu_data = []
    frame_count = 0
    saved_frames = 0

    try:
        profile = pipeline.start(cfg)
        device = profile.get_device()
        playback = device.as_playback()
        if playback:
            playback.set_real_time(False)

        while True:
            try:
                frames = pipeline.wait_for_frames()
                timestamp_ms = frames.get_timestamp()
                if frame_count % 100 == 0:
                    logger.info(f"已处理 {frame_count} 帧")

                color_frame = frames.get_color_frame()
                if color_frame:
                    color_image = np.asanyarray(color_frame.get_data())
                    # 保存 RGB 图像为 JPEG
                    rgb_path = os.path.join(rgb_dir, f"frame_{frame_count:06d}.jpg")
                    cv2.imwrite(rgb_path, color_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    timestamps.append(timestamp_ms)
                    saved_frames += 1

                depth_frame = frames.get_depth_frame()
                if depth_frame:
                    depth_image = np.asanyarray(depth_frame.get_data())
                    depth_path = os.path.join(depth_dir, f"frame_{frame_count:06d}.png")
                    cv2.imwrite(depth_path, depth_image)

                imu_frame = frames.first_or_default(rs.stream.motion)
                if imu_frame:
                    imu = imu_frame.as_motion_frame().get_motion_data()
                    imu_data.append({
                        'timestamp': timestamp_ms,
                        'accel_x': imu.x,
                        'accel_y': imu.y,
                        'accel_z': imu.z,
                        'gyro_x': 0.0,
                        'gyro_y': 0.0,
                        'gyro_z': 0.0
                    })

                frame_count += 1
            except RuntimeError as e:
                logger.info(f"播放结束: {e}")
                break
            except Exception as e:
                logger.error(f"处理帧时出错: {e}")
                break
    finally:
        pipeline.stop()

    # 保存时间戳
    if timestamps:
        pd.DataFrame({'timestamp': timestamps}).to_csv(
            os.path.join(output_dir, "timestamps.csv"), index=False
        )
        logger.info(f"时间戳已保存，共 {len(timestamps)} 条")

    if imu_data:
        pd.DataFrame(imu_data).to_csv(
            os.path.join(output_dir, "imu.csv"), index=False
        )
        logger.info(f"IMU 数据已保存，共 {len(imu_data)} 条")
    else:
        logger.info("bag 中未找到 IMU 数据")

    logger.info(f"解析完成：总帧数 {frame_count}，保存图像 {saved_frames} 帧")
    return True