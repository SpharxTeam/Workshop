# ============================================================================
# workshop 基础镜像
# 基于 Python 3.10 slim，包含所有模块共享的依赖和系统库
# 版本：1.0
# ============================================================================

FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=5

LABEL maintainer="Spharx Team" \
      description="Workshop Pipeline Base Image" \
      version="1.0"

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

# 配置 pip 使用国内镜像（优先官方，失败回退清华）
RUN pip config set global.index-url https://pypi.org/simple || \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装通用 Python 包（所有模块共享）
# numpy, pyyaml, opencv, torch, torchvision 均锁定版本以确保一致性
RUN pip install --no-cache-dir \
    numpy==1.26.0 \
    pyyaml==6.0.2 \
    opencv-python==4.10.0.84 \
    torch==2.5.1 \
    torchvision==0.20.1

# 创建公共目录结构
RUN mkdir -p /app/common/{configs,schemas,scripts,tests,logs,models}

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser /app

WORKDIR /app
CMD ["/bin/bash"]