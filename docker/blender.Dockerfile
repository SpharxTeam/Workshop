# Blender Python API 镜像
# 包含Blender和Python API环境

FROM ubuntu:20.04

# 避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    bzip2 \
    libfreetype6 \
    libgl1-mesa-dev \
    libglu1-mesa \
    libxi6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 下载并安装Blender
WORKDIR /opt
RUN curl -L "https://download.blender.org/release/Blender3.6/blender-3.6.0-linux-x64.tar.xz" -o blender.tar.xz \
    && tar -xf blender.tar.xz \
    && mv blender-3.6.0-linux-x64 blender \
    && rm blender.tar.xz

# 设置环境变量
ENV PATH=/opt/blender:$PATH
ENV BLENDER_SYSTEM_PYTHON=/opt/blender/3.6/python

# 安装Python依赖
RUN /opt/blender/3.6/python/bin/python -m ensurepip \
    && /opt/blender/3.6/python/bin/python -m pip install --upgrade pip

# 安装常用的Blender Python包
RUN /opt/blender/3.6/python/bin/python -m pip install \
    numpy \
    scipy \
    pillow \
    opencv-python-headless \
    requests

# 创建工作目录
WORKDIR /workspace

# 验证安装
RUN blender -v

# 默认命令
CMD ["blender", "-b", "--python-expr", "import bpy; print('Blender Python API ready')"]