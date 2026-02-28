# ============================================================================
# workshop 交付模块 (05_delivery)
# 基于 workshop-base，预留 OSS 上传等功能
# 版本：1.1
# ============================================================================

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/05_delivery /app/module
COPY partdata/deps /app/deps

# 若 requirements.txt 不存在则跳过安装（占位模块）
RUN if [ -f /app/module/requirements.txt ]; then \
        pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt; \
    fi

# 显式设置日志目录权限（关键！）
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]