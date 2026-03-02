# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# =================================================================================
# 生成真实的棋盘格标定图像（带内角点），用于测试相机标定模块。
# 图像尺寸：1280x960，棋盘格内角点 9x6，方格大小 100 像素。
# 图像保存为灰度 JPEG。
# =================================================================================
import cv2
import numpy as np
import os
import argparse
import random

def generate_chessboard_images(output_dir, num_images=20, pattern_size=(9,6), square_size=100, image_size=(1280,960)):
    """
    生成带有完整棋盘格的灰度图像。
    pattern_size: 内角点数 (宽, 高)，因此方格数为 (宽+1) x (高+1)
    """
    os.makedirs(output_dir, exist_ok=True)

    board_width = (pattern_size[0] + 1) * square_size
    board_height = (pattern_size[1] + 1) * square_size

    if board_width > image_size[0] or board_height > image_size[1]:
        raise ValueError(f"棋盘格尺寸 ({board_width}x{board_height}) 超出图像尺寸 {image_size}")

    for i in range(num_images):
        # 创建灰度背景（白色）
        img = np.ones((image_size[1], image_size[0]), dtype=np.uint8) * 255

        # 随机平移棋盘格位置
        max_x = image_size[0] - board_width
        max_y = image_size[1] - board_height
        offset_x = random.randint(0, max_x)
        offset_y = random.randint(0, max_y)

        # 绘制完整的棋盘格方格
        for row in range(pattern_size[1] + 1):
            for col in range(pattern_size[0] + 1):
                x0 = offset_x + col * square_size
                y0 = offset_y + row * square_size
                x1 = x0 + square_size
                y1 = y0 + square_size
                # 颜色：偶数行列黑色，奇数行列白色
                color = 0 if (row + col) % 2 == 0 else 255
                img[y0:y1, x0:x1] = color

        # 添加轻微噪声
        noise = np.random.randint(0, 5, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)

        filename = os.path.join(output_dir, f"chessboard_{i:02d}.jpg")
        cv2.imwrite(filename, img)
        print(f"生成图像: {filename}")

    print(f"完成：已生成 {num_images} 张棋盘格图像到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成棋盘格标定图像")
    parser.add_argument("--output", default="data/calibration_images", help="输出目录")
    parser.add_argument("--num", type=int, default=20, help="图像数量")
    parser.add_argument("--chessboard", default="9,6", help="内角点数，如 9,6")
    parser.add_argument("--square_size", type=int, default=100, help="方格尺寸（像素）")
    parser.add_argument("--image_size", default="1280,960", help="图像尺寸（宽,高）")
    args = parser.parse_args()

    pattern = tuple(map(int, args.chessboard.split(',')))
    img_size = tuple(map(int, args.image_size.split(',')))
    generate_chessboard_images(args.output, args.num, pattern, args.square_size, img_size)