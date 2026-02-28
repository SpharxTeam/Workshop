# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# workshop 标定模块 (03_calibrate)
# 基于 workshop-base，进行棋盘格内参标定
# ============================================================================

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

COPY pipelines/03_calibrate /app/module

RUN pip install --no-cache-dir -r /app/module/requirements.txt || \
    (pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple -r /app/module/requirements.txt) || \
    (pip install --no-cache-dir -i https://mirrors.ustc.edu.cn/pypi/web/simple -r /app/module/requirements.txt) || \
    (pip install --no-cache-dir -i https://mirrors.bfsu.edu.cn/pypi/web/simple -r /app/module/requirements.txt) || true

RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]