# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 增强模块 (02_enhance)，基于 workshop-base（已包含 ffmpeg 和完整 OpenCV）

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
# 复制模型配置文件（enhance模块需要）
COPY common/configs/model_config.yaml /app/configs/model_config.yaml
COPY pipelines/run_02_enhance /app/module
COPY partdata/deps /app/deps

RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]