# ============================================================================
# workshop 打包模块 (04_pack)
# 基于 workshop-base，将处理后的数据打包成数据集并生成 manifest
# 版本：1.1
# ============================================================================

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/04_pack /app/module
COPY partdata/deps /app/deps
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

# 显式设置日志目录权限（关键！）
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]