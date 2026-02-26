# ============================================================================
# workshop 交付模块 (05_delivery) 预留
# 基于 workshop-base，实现数据集上传至 OSS 等
# ============================================================================

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/05_delivery /app/module
COPY partdata/deps /app/deps
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt || true

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]