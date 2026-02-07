# SA3D 研究环境镜像
# 包含SA3D分割算法和相关研究工具

FROM nvidia/cuda:11.8-devel-ubuntu20.04

# 避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3.9-distutils \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 创建Python软链接
RUN ln -sf /usr/bin/python3.9 /usr/bin/python

# 升级pip
RUN python -m pip install --upgrade pip

# 安装PyTorch和相关依赖
RUN pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

# 克隆SA3D代码
WORKDIR /opt
RUN git clone https://github.com/spharx/sa3d.git \
    && cd sa3d \
    && pip install -e .

# 安装额外的研究工具
RUN pip install \
    open3d \
    trimesh \
    plyfile \
    scikit-learn \
    matplotlib \
    tensorboard

# 创建工作目录
WORKDIR /workspace

# 设置环境变量
ENV PYTHONPATH=/opt/sa3d:$PYTHONPATH

# 默认命令
CMD ["python", "-c", "import torch; print(f'SA3D environment ready. CUDA: {torch.cuda.is_available()}')"]