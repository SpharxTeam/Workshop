# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 交付模块 (05_delivery) 基于 workshop-base，预留 OSS 上传等功能

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/run_05_delivery /app/module
COPY partdata/deps /app/deps

RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]