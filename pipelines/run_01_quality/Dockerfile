# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 质量检测模块 (01_quality)，基于 workshop-base，进行模糊检测、曝光检测、丢帧统计

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/run_01_quality /app/module
COPY partdata/deps /app/deps

RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]