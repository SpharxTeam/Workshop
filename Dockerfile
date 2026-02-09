# ============================================
# SpharxWorkshop 主控制器 Dockerfile
# 目标：构建一个包含所有运行时依赖的生产线控制镜像
# ============================================

# 第一阶段：构建依赖层（优化镜像层缓存）
FROM python:3.11-slim AS builder

# 设置构建环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（最小化安装）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础编译工具
    gcc \
    g++ \
    make \
    cmake \
    # 图像处理库
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # 通用工具
    wget \
    curl \
    git \
    # OpenCV依赖
    libopencv-dev \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖（使用国内镜像加速）
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# 第二阶段：运行时镜像（更轻量）
FROM python:3.11-slim AS runtime

# 设置运行时环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    TZ=Asia/Shanghai

# 安装运行时系统依赖（比构建阶段少很多）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础运行时库
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # 网络工具
    curl \
    # 时间数据
    tzdata \
    # 清理
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    # 设置时区
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

# 创建非root用户（增强安全性）
RUN groupadd -r spharx && \
    useradd -r -g spharx -u 1001 -m -s /bin/bash spharx && \
    mkdir -p /home/SpharxWorkshop && \
    chown -R spharx:spharx /home/SpharxWorkshop

# 设置工作目录
WORKDIR /app

# 从构建阶段复制已安装的Python包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=spharx:spharx . .

# 切换到非root用户
USER spharx

# 创建必要的目录结构
RUN mkdir -p /home/spharx/.cache && \
    mkdir -p /home/spharx/.config && \
    chmod 755 /home/spharx/.cache /home/spharx/.config

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; import socket; \
    try: socket.create_connection(('localhost', 8080), timeout=5); \
    print('Healthy'); sys.exit(0) \
    except: print('Unhealthy'); sys.exit(1)"

# 暴露端口（主API端口）
EXPOSE 8080

# 默认命令（在docker-compose中会被覆盖）
CMD ["python", "src/main.py", "--mode", "standalone"]

# ============================================
# 镜像标签信息
LABEL org.label-schema.name="SpharxWorkshop Controller" \
      org.label-schema.description="Spatial Intelligence Data Production Pipeline" \
      org.label-schema.version="1.0.0" \
      org.label-schema.vcs-url="https://gitee.com/spharx/toolchain" \
      org.label-schema.docker.cmd="docker run -d --env-file .env spharx-controller:latest" \
      maintainer="Spharx Team <team@spharx.com>"