import cv2
import numpy as np
import os

def generate_chessboard_images(output_dir, num_images=20, pattern_size=(9,6), square_size=100):
    os.makedirs(output_dir, exist_ok=True)
    for i in range(num_images):
        img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        # 绘制简单的棋盘格（可替换为真实渲染）
        cv2.putText(img, f"Mock {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        cv2.imwrite(os.path.join(output_dir, f"board_{i:02d}.jpg"), img)
    print(f"已生成 {num_images} 张虚拟棋盘格图像到 {output_dir}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/calibration_images", help="输出目录")
    args = parser.parse_args()
    generate_chessboard_images(args.output)