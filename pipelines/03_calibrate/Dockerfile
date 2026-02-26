# ============================================================================
# workshop 标定模块 (03_calibrate)
# 基于 workshop-base，进行棋盘格内参标定
# ============================================================================

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/03_calibrate /app/module
COPY partdata/deps /app/deps
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt || true

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]