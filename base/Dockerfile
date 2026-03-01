# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# =================================================================================
# workshop 基础镜像（重构版）
# 包含所有模块共享的系统库、Python 包，并预装 ffmpeg 和 OpenCV 完整支持
# 版本：3.0 (2026.03.01)
# =================================================================================
FROM python:3.10-slim

ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/cuda/bin:${PATH}" \
    YOLO_CONFIG_DIR="/home/appuser/.config/Ultralytics"

# 安装系统依赖（包括 ffmpeg 和 OpenCV 所需的所有库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    ca-certificates \
    libgl1 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libusb-1.0-0-dev \
    udev \
    curl \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libx264-dev \
    libx265-dev \
    libvpx-dev \
    libtheora-dev \
    libvorbis-dev \
    libmp3lame-dev \
    libopencore-amrnb-dev \
    libopencore-amrwb-dev \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 镜像（优先使用清华源）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Python 包（确保 OpenCV 具有完整解码能力）
RUN pip install --no-cache-dir \
    numpy==1.26.0 \
    pyyaml==6.0.2 \
    opencv-python==4.10.0.84 \
    opencv-contrib-python==4.10.0.84  # 包含更多解码器

# 创建公共目录结构
RUN mkdir -p /app/common/{configs,schemas,scripts,tests,logs,models} \
    && mkdir -p /app/logs \
    && chmod 777 /app/logs

# 创建数据挂载点目录
RUN mkdir -p /data/raw /data/processed /data/datasets /data/calibration_images /data/models

# 创建非 root 用户，并预设 YOLO 配置目录
RUN groupadd -g ${GID} appgroup && \
    useradd -m -u ${UID} -g appgroup appuser && \
    mkdir -p /home/appuser/.config/Ultralytics && \
    chown -R appuser:appgroup /home/appuser/.config /app /data

# 设置环境变量指向可写目录
ENV YOLO_CONFIG_DIR="/home/appuser/.config/Ultralytics"

WORKDIR /app
CMD ["/bin/bash"]