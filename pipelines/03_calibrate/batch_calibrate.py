#!/usr/bin/env python3
"""
标定模块：基于棋盘格图像进行相机内参标定。
增强版：支持配置文件、统一日志、异常处理。
"""
import argparse
import os
import cv2
import numpy as np
import json
import glob

# 本地配置加载模块
import config_loader

import logging
import sys
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

def calibrate_camera(image_dir, chessboard_size=(9,6), square_size=0.025, output_dir=None, config=None):
    """
    标定相机，chessboard_size: 内角点数 (宽, 高)
    config: 可选，用于从配置读取参数（已通过函数参数传递，不再使用）
    """
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
    objp *= square_size

    objpoints = []
    imgpoints = []
    image_paths = glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png"))

    if len(image_paths) == 0:
        logger.error(f"在 {image_dir} 中未找到图像文件")
        return False

    # 检测标志
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK

    valid_images = []
    for fname in image_paths:
        img = cv2.imread(fname)
        if img is None:
            logger.warning(f"无法读取图像: {fname}")
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None, flags=flags)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
            valid_images.append(fname)
            logger.info(f"成功检测: {fname}")
        else:
            logger.warning(f"未检测到棋盘格: {fname}")

    if len(objpoints) == 0:
        logger.error("没有有效的标定图像")
        return False

    # 标定
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

    # 计算重投影误差
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    reproj_error = mean_error / len(objpoints)

    result = {
        "camera_matrix": mtx.tolist(),
        "dist_coeffs": dist.tolist(),
        "reprojection_error": reproj_error,
        "image_size": gray.shape[::-1],
        "valid_images": len(valid_images),
        "total_images": len(image_paths)
    }

    if output_dir is None:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "intrinsics.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"标定完成，重投影误差: {reproj_error:.4f} 像素")
    logger.info(f"结果已保存到 {output_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="标定图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--chessboard", help="棋盘格内角点，如 9,6")
    parser.add_argument("--square_size", type=float, help="方格尺寸（米）")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        logger.error(f"输入目录不存在: {args.input}")
        exit(1)

    config = config_loader.load_config(args.config, "calibrate")

    # 命令行参数优先
    chessboard = args.chessboard if args.chessboard else config.get('chessboard', '9,6')
    if isinstance(chessboard, str):
        chessboard = tuple(map(int, chessboard.split(',')))
    square_size = args.square_size if args.square_size is not None else config.get('square_size', 0.025)

    try:
        calibrate_camera(args.input, chessboard_size=chessboard,
                         square_size=square_size, output_dir=args.output, config=config)
    except Exception as e:
        logger.critical(f"标定失败: {e}", exc_info=True)
        exit(1)