#!/usr/bin/env python3
"""
标定模块：基于棋盘格图像进行相机内参标定。
"""
import argparse
import os
import cv2
import numpy as np
import json
import glob
import logging
import sys
from config_loader import load_config

MODULE_NAME = os.path.basename(__file__).replace('.py', '')
LOG_DIR = "/app/logs"
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

def calibrate_camera(image_dir, chessboard_size=(9,6), square_size=0.025, output_dir=None):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2) * square_size

    objpoints = []
    imgpoints = []
    images = glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png"))
    if not images:
        logger.error("未找到标定图像")
        return False

    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
    valid = []
    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None, flags=flags)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
            valid.append(fname)
            logger.info(f"成功检测: {fname}")
        else:
            logger.warning(f"未检测到棋盘格: {fname}")

    if not objpoints:
        logger.error("没有有效的标定图像")
        return False

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    # 重投影误差
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
        "valid_images": len(valid),
        "total_images": len(images)
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "intrinsics.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"标定结果已保存: {out_path}")

    report = {
        "reprojection_error": reproj_error,
        "camera_matrix": mtx.tolist(),
        "dist_coeffs": dist.tolist(),
        "image_count": len(objpoints),
        "chessboard_size": list(chessboard_size),
        "square_size": square_size
    }
    report_path = os.path.join(output_dir, "calibration_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"标定报告已保存: {report_path}")

    logger.info(f"标定完成，重投影误差: {reproj_error:.4f} 像素")
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
        sys.exit(1)

    config = load_config(module_name="03_calibrate") if not args.config else load_config(config_path=args.config)

    chessboard = args.chessboard if args.chessboard else config.get('chessboard', '9,6')
    if isinstance(chessboard, str):
        chessboard = tuple(map(int, chessboard.split(',')))
    square_size = args.square_size if args.square_size is not None else config.get('square_size', 0.025)

    try:
        success = calibrate_camera(args.input, chessboard_size=chessboard, square_size=square_size, output_dir=args.output)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"标定失败: {e}", exc_info=True)
        sys.exit(1)