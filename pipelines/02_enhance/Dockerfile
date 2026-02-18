# pipelines/02_enhance/Dockerfile
FROM python:3.10-slim
WORKDIR /app

# 安装运行时系统依赖（包括 curl，供 Ultralytics 下载使用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用清华源加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config_loader.py .
COPY *.py .

ENTRYPOINT ["python", "yolo_annotator.py"]