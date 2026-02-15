"""
数据脱敏工具：使用 Haar Cascade 检测人脸并模糊。
"""
import cv2
import os

def blur_faces(image_path, output_path):
    """检测图像中的人脸并模糊"""
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    for (x, y, w, h) in faces:
        roi = img[y:y+h, x:x+w]
        roi = cv2.GaussianBlur(roi, (51, 51), 30)
        img[y:y+h, x:x+w] = roi
    cv2.imwrite(output_path, img)