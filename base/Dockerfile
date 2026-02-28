# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# workshop 基础镜像（最终版）
# 基于 Python 3.10 slim，包含所有模块共享的依赖和系统库
# 版本：2.0
# ============================================================================

FROM python:3.10-slim

ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=5 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖（供 OpenCV、pyrealsense2 等使用）
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
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 镜像（仅作后备）
RUN pip config set global.index-url https://pypi.org/simple || \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装通用 Python 包（所有模块共享）
RUN pip install --no-cache-dir \
    numpy==1.26.0 \
    pyyaml==6.0.2 \
    opencv-python==4.10.0.84

# 创建公共目录结构（包含 models）
RUN mkdir -p /app/common/{configs,schemas,scripts,tests,logs,models} \
    && mkdir -p /app/logs \
    && chmod 777 /app/logs

# 创建数据挂载点目录（所有卷挂载点）
RUN mkdir -p /data/raw /data/processed /data/datasets /data/calibration_images /data/models

# 创建非 root 用户，使用传入的 UID/GID
RUN groupadd -g ${GID} appgroup && \
    useradd -m -u ${UID} -g appgroup appuser && \
    chown -R appuser:appgroup /app /data

# 设置目录权限
RUN chmod 755 /app /data

WORKDIR /app
CMD ["/bin/bash"]