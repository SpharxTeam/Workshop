# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# RealSense bag 文件解析核心算法（图像序列版 + 压缩优化）
# 将每一帧保存为压缩图像（WebP/PNG），并生成预览视频

import os
import cv2
import numpy as np
import pandas as pd
import pyrealsense2 as rs
import logging
from .image_compressor import ImageCompressor, StreamCompressor

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

    # 初始化压缩器（从配置读取预设）
    quality_preset = config.get('quality_preset', 'production') if config else 'production'
    compressor = ImageCompressor(quality_preset)
    logger.info(f"图像压缩预设: {quality_preset} (RGB: {compressor.rgb_format}, 深度: {compressor.depth_format})")

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
    saved_sizes = []  # 记录每帧大小用于统计

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
                    # 保存 RGB 图像（使用压缩器）
                    # 注意：compressor.save_rgb 会自动根据格式确定扩展名
                    rgb_path = os.path.join(rgb_dir, f"frame_{frame_count:06d}.jpg")  # 临时使用 .jpg，但实际格式由压缩器决定
                    success, size = compressor.save_rgb(color_image, rgb_path)
                    if success:
                        timestamps.append(timestamp_ms)
                        saved_frames += 1
                        saved_sizes.append(size)

                depth_frame = frames.get_depth_frame()
                if depth_frame:
                    depth_image = np.asanyarray(depth_frame.get_data())
                    depth_path = os.path.join(depth_dir, f"frame_{frame_count:06d}.png")
                    success, size = compressor.save_depth(depth_image, depth_path)
                    if success:
                        # 深度图大小不计入 saved_frames，但可记录
                        pass

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

    # 统计信息
    if saved_sizes:
        avg_size = np.mean(saved_sizes)
        total_mb = sum(saved_sizes) / (1024 * 1024)
        logger.info(f"图像压缩统计: 平均每帧 {avg_size:.0f} 字节，总计 {total_mb:.2f} MB")

    # 生成预览视频（可选）
    preview_dir = os.path.join(output_dir, "preview")
    os.makedirs(preview_dir, exist_ok=True)
    preview_path = os.path.join(preview_dir, "preview.mp4")
    stream_compressor = StreamCompressor()
    
    # 确定实际图像格式
    if compressor.rgb_format == 'webp':
        image_pattern = "*.webp"
    elif compressor.rgb_format == 'png':
        image_pattern = "*.png"
    else:
        image_pattern = "*.jpg"
    
    if stream_compressor.compress_video(rgb_dir, preview_path, fps=30, image_pattern=image_pattern):
        logger.info(f"预览视频已生成: {preview_path}")
    else:
        logger.warning("预览视频生成失败，但不影响主流程")

    logger.info(f"解析完成：总帧数 {frame_count}，保存图像 {saved_frames} 帧")
    return True