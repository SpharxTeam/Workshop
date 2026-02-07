# COLMAP 3D重建镜像
# 基于CUDA环境，包含COLMAP和相关依赖

FROM nvidia/cuda:11.8-devel-ubuntu20.04

# 避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装COLMAP依赖
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libsuitesparse-dev \
    libfreeimage-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libatlas-base-dev \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# 克隆并构建COLMAP
WORKDIR /opt
RUN git clone https://github.com/colmap/colmap.git \
    && cd colmap \
    && git checkout dev \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && make install \
    && cd ../.. \
    && rm -rf colmap

# 验证安装
RUN colmap -h

# 设置环境变量
ENV PATH=/usr/local/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# 创建工作目录
WORKDIR /workspace

# 默认命令
CMD ["colmap", "--help"]