# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop基础镜像，包含系统依赖、pip镜像配置和通用Python包

FROM python:3.10-slim

ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/cuda/bin:${PATH}" \
    TZ=Asia/Shanghai \
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
    tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && echo "Asia/Shanghai" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 镜像（仅作后备，实际构建使用离线包）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装通用 Python 包（所有模块共享）
RUN pip install --no-cache-dir \
    numpy==1.26.0 \
    pyyaml==6.0.2 \
    opencv-python==4.10.0.84

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