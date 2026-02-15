#!/usr/bin/env python3
"""
数据导入模块：解析 .bag 文件，提取 RGB、深度、IMU。
若输入文件不存在，则生成模拟数据以便后续模块测试。
"""
import argparse
import os
import cv2
import numpy as np
import pandas as pd
from pathlib import Path

def generate_mock_data(output_dir, num_frames=100):
    """生成模拟的 RGB、深度、IMU 数据，用于无硬件时测试"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成时间戳
    timestamps = [i * 33.33 for i in range(num_frames)]  # 30fps ≈ 33.33ms
    pd.DataFrame({'timestamp': timestamps}).to_csv(
        os.path.join(output_dir, "timestamps.csv"), index=False
    )
    
    # 生成深度图目录
    depth_dir = os.path.join(output_dir, "depth")
    os.makedirs(depth_dir, exist_ok=True)
    for i in range(num_frames):
        # 生成随机深度图（模拟）
        depth = np.random.randint(0, 65535, (720, 1280), dtype=np.uint16)
        cv2.imwrite(os.path.join(depth_dir, f"frame_{i:06d}.png"), depth)
    
    # 生成模拟 IMU 数据
    imu_data = []
    for i in range(num_frames * 3):  # IMU 通常频率更高，此处简化
        imu_data.append({
            'timestamp': i * 10.0,
            'accel_x': np.random.randn(),
            'accel_y': np.random.randn(),
            'accel_z': np.random.randn(),
            'gyro_x': np.random.randn(),
            'gyro_y': np.random.randn(),
            'gyro_z': np.random.randn()
        })
    pd.DataFrame(imu_data).to_csv(
        os.path.join(output_dir, "imu.csv"), index=False
    )
    
    # 生成 RGB 视频（模拟，实际应提取自 bag）
    # 这里简单生成一些随机帧合成视频
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(os.path.join(output_dir, "rgb.mp4"),
                          fourcc, 30.0, (1920, 1080))
    for i in range(num_frames):
        frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    
    print(f"模拟数据已生成到 {output_dir}")

def parse_bag(bag_path, output_dir):
    """解析 bag 文件，若无真实 bag 则生成模拟数据"""
    if not os.path.exists(bag_path):
        print(f"输入文件 {bag_path} 不存在，生成模拟数据。")
        generate_mock_data(output_dir)
        return True
    
    # 真实解析逻辑（当硬件到位后实现）
    print(f"解析真实 bag: {bag_path}")
    # TODO: 调用 pyrealsense2 解析
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据导入模块")
    parser.add_argument("--input", required=True, help="输入bag文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    args = parser.parse_args()
    
    parse_bag(args.input, args.output)