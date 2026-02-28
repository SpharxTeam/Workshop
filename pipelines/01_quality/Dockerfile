# ============================================================================
# workshop 质检模块 (01_quality)
# 基于 workshop-base，进行模糊检测、曝光检测、丢帧统计
# 版本：1.1
# ============================================================================

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/01_quality /app/module
COPY partdata/deps /app/deps
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

# 显式设置日志目录权限（关键！）
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]