# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 增强模块 (02_enhance)
# 基于 workshop-base（已包含 ffmpeg 和完整 OpenCV）

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

# 复制公共资源
COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

# 复制模块代码
COPY pipelines/run_02_enhance /app/module

# 安装模块特定的 Python 依赖（ultralytics 等）
RUN pip install --no-cache-dir -r /app/module/requirements.txt || \
    (pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple -r /app/module/requirements.txt)

# 确保日志目录存在
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]