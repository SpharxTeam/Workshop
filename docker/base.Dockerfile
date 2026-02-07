# Spharx 生产线基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY config/ ./config/

# 创建非root用户
RUN useradd -m -u 1000 spharx && \
    chown -R spharx:spharx /app
USER spharx

# 默认命令
CMD ["python", "-m", "src.main", "--help"]