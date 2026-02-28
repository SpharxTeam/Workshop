# ============================================================================
# workshop 数据导入模块 (00_ingest)
# 基于 workshop-base，实现 RealSense bag 文件解析
# 版本：1.1 (使用离线依赖，修正权限)
# ============================================================================

FROM workshop-base:latest

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/app/common/scripts

# 复制公共资源
COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

# 复制模块代码
COPY pipelines/00_ingest /app/module

# 复制离线依赖包（用于离线安装）
COPY partdata/deps /app/deps

# 安装依赖（离线模式）
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

# 显式设置日志目录权限（关键！）
RUN mkdir -p /app/logs && chmod 777 /app/logs

# 切换到非 root 用户
USER appuser

WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]