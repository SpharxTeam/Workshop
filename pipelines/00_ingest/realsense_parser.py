#!/usr/bin/env python3
"""
真实 bag 解析模块，包含详细错误处理和调试输出。
"""
import argparse
import os
import sys
import traceback
import cv2
import numpy as np
import pandas as pd
import pyrealsense2 as rs

def parse_bag(bag_path, output_dir):
    print(f"[DEBUG] 开始解析 bag: {bag_path}")
    print(f"[DEBUG] 输出目录: {output_dir}")

    if not os.path.exists(bag_path):
        print(f"错误：输入文件 {bag_path} 不存在")
        return False

    file_size = os.path.getsize(bag_path)
    print(f"[DEBUG] bag 文件大小: {file_size} 字节")
    if file_size == 0:
        print("错误：bag 文件为空")
        return False

    depth_dir = os.path.join(output_dir, "depth")
    os.makedirs(depth_dir, exist_ok=True)
    print(f"[DEBUG] 深度图目录已创建: {depth_dir}")

    pipeline = rs.pipeline()
    config = rs.config()
    try:
        print("[DEBUG] 尝试启用设备从文件...")
        rs.config.enable_device_from_file(config, bag_path, repeat_playback=False)
        print("[DEBUG] 启用成功，配置所有流...")
        config.enable_all_streams()
    except Exception as e:
        print(f"[ERROR] 配置 bag 文件时出错: {e}")
        traceback.print_exc()
        return False

    try:
        print("[DEBUG] 启动 pipeline...")
        profile = pipeline.start(config)
        print("[DEBUG] pipeline 启动成功")

        device = profile.get_device()
        playback = device.as_playback()
        if playback:
            playback.set_real_time(False)
            print("[DEBUG] 已禁用实时播放")
        else:
            print("[WARNING] 设备不支持 playback 模式")

        video_writer = None
        timestamps = []
        imu_data = []
        frame_count = 0

        while True:
            try:
                frames = pipeline.wait_for_frames()
                timestamp_ms = frames.get_timestamp()
                if frame_count % 100 == 0:
                    print(f"[DEBUG] 已处理 {frame_count} 帧...")

                color_frame = frames.get_color_frame()
                if color_frame:
                    color_image = np.asanyarray(color_frame.get_data())
                    if video_writer is None:
                        height, width = color_image.shape[:2]
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        video_path = os.path.join(output_dir, "rgb.mp4")
                        video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, (width, height))
                        print(f"[DEBUG] 初始化视频写入器: {video_path}, 尺寸 {width}x{height}")
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
                print(f"[INFO] 播放结束: {e}")
                break
            except Exception as e:
                print(f"[ERROR] 处理帧时出错: {e}")
                traceback.print_exc()
                break

    except Exception as e:
        print(f"[ERROR] pipeline 运行出错: {e}")
        traceback.print_exc()
        return False
    finally:
        print("[DEBUG] 停止 pipeline...")
        pipeline.stop()
        if video_writer:
            video_writer.release()
            print("[DEBUG] 视频写入器已释放")

    if timestamps:
        pd.DataFrame({'timestamp': timestamps}).to_csv(
            os.path.join(output_dir, "timestamps.csv"), index=False
        )
        print(f"[DEBUG] 时间戳已保存，共 {len(timestamps)} 条")
    if imu_data:
        pd.DataFrame(imu_data).to_csv(
            os.path.join(output_dir, "imu.csv"), index=False
        )
        print(f"[DEBUG] IMU 数据已保存，共 {len(imu_data)} 条")

    print(f"解析完成：{frame_count} 帧，RGB 视频已保存，深度图已保存到 {depth_dir}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入bag文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    args = parser.parse_args()

    print(f"[DEBUG] Python 版本: {sys.version}")
    print(f"[DEBUG] pyrealsense2 版本: {rs.__version__ if hasattr(rs, '__version__') else 'unknown'}")

    success = parse_bag(args.input, args.output)
    exit(0 if success else 1)