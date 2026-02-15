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

def calibrate_camera(image_dir, chessboard_size=(9,6), square_size=0.025, output_dir=None):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
    objp *= square_size

    objpoints = []
    imgpoints = []
    image_paths = glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png"))

    if len(image_paths) == 0:
        print(f"在 {image_dir} 中未找到图像文件")
        return False

    valid_images = []
    for fname in image_paths:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
            valid_images.append(fname)

    if len(objpoints) == 0:
        print("没有有效的标定图像")
        return False

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

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

    print(f"标定完成，重投影误差: {reproj_error:.4f} 像素")
    print(f"结果已保存到 {output_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="标定图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--chessboard", default="9,6", help="棋盘格内角点，如 9,6")
    parser.add_argument("--square_size", type=float, default=0.025, help="方格尺寸（米）")
    args = parser.parse_args()

    chessboard = tuple(map(int, args.chessboard.split(',')))
    calibrate_camera(args.input, chessboard_size=chessboard,
                     square_size=args.square_size, output_dir=args.output)