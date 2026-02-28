# ============================================================================
# workshop 标定模块 (03_calibrate)
# 基于 workshop-base，进行棋盘格内参标定
# 版本：1.1
# ============================================================================

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/03_calibrate /app/module
COPY partdata/deps /app/deps

# 03_calibrate 的 requirements.txt 可能为空，安装命令仍可正常运行
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

# 显式设置日志目录权限（关键！）
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]