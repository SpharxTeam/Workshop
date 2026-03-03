# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop数据导入模块(00_ingest)，基于workshop-base，实现RealSense bag文件解析

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

# 复制公共资源
COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

# 复制模块代码（包含 algorithm 子目录）
COPY pipelines/run_00_ingest /app/module

# 复制离线依赖包
COPY partdata/deps /app/deps

# 离线安装依赖（多源重试已预先下载）
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

# 确保日志目录存在且可写
RUN mkdir -p /app/logs && chmod 777 /app/logs

# 切换到非 root 用户
USER appuser

WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]