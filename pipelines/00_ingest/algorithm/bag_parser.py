# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# RealSense bag 文件解析核心算法。
# ============================================================================

import os
import cv2
import numpy as np
import pandas as pd
import pyrealsense2 as rs
import logging

logger = logging.getLogger(__name__)

def parse_bag(bag_path, output_dir, config=None):
    """解析 bag 文件，生成 RGB 视频、深度图和 IMU 数据"""
    logger.info(f"开始解析 bag: {bag_path}")
    if not os.path.exists(bag_path):
        logger.error(f"输入文件不存在: {bag_path}")
        return False

    depth_dir = os.path.join(output_dir, "depth")
    os.makedirs(depth_dir, exist_ok=True)
    logger.info(f"深度图保存目录: {depth_dir}")

    pipeline = rs.pipeline()
    cfg = rs.config()
    try:
        rs.config.enable_device_from_file(cfg, bag_path, repeat_playback=False)
        cfg.enable_all_streams()
    except Exception as e:
        logger.error(f"配置 bag 文件时出错: {e}")
        return False

    video_writer = None
    timestamps = []
    imu_data = []
    frame_count = 0
    frames_written = 0

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
                    if video_writer is None:
                        h, w = color_image.shape[:2]
                        fps = 30.0  # 可从配置或 bag 元数据获取
                        video_path = os.path.join(output_dir, "rgb.mp4")
                        # 尝试多种编码器
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        video_writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
                        if not video_writer.isOpened():
                            logger.warning("mp4v 编码器初始化失败，尝试 X264")
                            fourcc = cv2.VideoWriter_fourcc(*'X264')
                            video_writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
                        if not video_writer.isOpened():
                            raise RuntimeError("无法初始化视频写入器，所有编码器均失败")
                        logger.info(f"视频写入器初始化成功，输出: {video_path}, 分辨率: {w}x{h}, fps: {fps}")

                    video_writer.write(color_image)
                    frames_written += 1
                    timestamps.append(timestamp_ms)

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
        if video_writer:
            video_writer.release()
            logger.info(f"视频写入器已释放，共写入 {frames_written} 帧")

            # 验证视频文件是否可被 OpenCV 打开
            video_path = os.path.join(output_dir, "rgb.mp4")
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
                logger.info(f"视频文件已保存，大小: {file_size} 字节")
                if file_size < 1024:
                    logger.error(f"视频文件大小异常 ({file_size} 字节)，可能写入失败")
                    return False
                # 使用 OpenCV 检查文件是否可读
                cap_check = cv2.VideoCapture(video_path)
                if not cap_check.isOpened():
                    logger.error(f"生成的视频文件 {video_path} 无法被 OpenCV 打开")
                    return False
                cap_check.release()
                logger.info("视频文件完整性验证通过")
            else:
                logger.error(f"视频文件 {video_path} 未生成")
                return False

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

    logger.info(f"解析完成：总帧数 {frame_count}，写入视频帧 {frames_written}")
    return True