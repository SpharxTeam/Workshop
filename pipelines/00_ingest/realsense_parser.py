#!/usr/bin/env python3
"""
数据导入模块：真实解析 .bag 文件，提取 RGB 视频、深度图和 IMU 数据。
增强版：统一日志、异常处理。
"""
import argparse
import os
import sys
import traceback
import cv2
import numpy as np
import pandas as pd
import pyrealsense2 as rs

# 日志配置
import logging
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

def parse_bag(bag_path, output_dir):
    """解析真实 bag 文件，带详细错误处理"""
    logger.info(f"开始解析 bag: {bag_path}")
    logger.info(f"输出目录: {output_dir}")

    if not os.path.exists(bag_path):
        logger.error(f"输入文件 {bag_path} 不存在")
        return False

    file_size = os.path.getsize(bag_path)
    logger.info(f"bag 文件大小: {file_size} 字节")
    if file_size == 0:
        logger.error("bag 文件为空")
        return False

    depth_dir = os.path.join(output_dir, "depth")
    os.makedirs(depth_dir, exist_ok=True)
    logger.info(f"深度图目录已创建: {depth_dir}")

    pipeline = rs.pipeline()
    config = rs.config()
    try:
        logger.info("尝试启用设备从文件...")
        rs.config.enable_device_from_file(config, bag_path, repeat_playback=False)
        logger.info("启用成功，配置所有流...")
        config.enable_all_streams()
    except Exception as e:
        logger.error(f"配置 bag 文件时出错: {e}")
        traceback.print_exc()
        return False

    try:
        logger.info("启动 pipeline...")
        profile = pipeline.start(config)
        logger.info("pipeline 启动成功")

        device = profile.get_device()
        playback = device.as_playback()
        if playback:
            playback.set_real_time(False)
            logger.info("已禁用实时播放")
        else:
            logger.warning("设备不支持 playback 模式")

        video_writer = None
        timestamps = []
        imu_data = []
        frame_count = 0

        while True:
            try:
                frames = pipeline.wait_for_frames()
                timestamp_ms = frames.get_timestamp()
                if frame_count % 100 == 0:
                    logger.info(f"已处理 {frame_count} 帧...")

                color_frame = frames.get_color_frame()
                if color_frame:
                    color_image = np.asanyarray(color_frame.get_data())
                    if video_writer is None:
                        height, width = color_image.shape[:2]
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        video_path = os.path.join(output_dir, "rgb.mp4")
                        video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, (width, height))
                        logger.info(f"初始化视频写入器: {video_path}, 尺寸 {width}x{height}")
                    video_writer.write(color_image)
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
                traceback.print_exc()
                break

    except Exception as e:
        logger.error(f"pipeline 运行出错: {e}")
        traceback.print_exc()
        return False
    finally:
        logger.info("停止 pipeline...")
        pipeline.stop()
        if video_writer:
            video_writer.release()
            logger.info("视频写入器已释放")

    if timestamps:
        pd.DataFrame({'timestamp': timestamps}).to_csv(
            os.path.join(output_dir, "timestamps.csv"), index=False
        )
        logger.info(f"时间戳已保存，共 {len(timestamps)} 条")
    if imu_data:
        pd.DataFrame(imu_data).to_csv(os.path.join(output_dir, "imu.csv"), index=False)
        logger.info(f"IMU 数据已保存，共 {len(imu_data)} 条")
    else:
        logger.info("bag 中未找到 IMU 数据，不生成 imu.csv")

    logger.info(f"解析完成：{frame_count} 帧，RGB 视频已保存，深度图已保存到 {depth_dir}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入bag文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    args = parser.parse_args()

    logger.info(f"Python 版本: {sys.version}")
    logger.info(f"pyrealsense2 版本: {rs.__version__ if hasattr(rs, '__version__') else 'unknown'}")

    try:
        success = parse_bag(args.input, args.output)
        exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"未捕获的异常: {e}", exc_info=True)
        exit(1)