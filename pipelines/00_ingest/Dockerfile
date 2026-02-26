# ============================================================================
# workshop 数据导入模块 (00_ingest)
# 基于 workshop-base，实现 RealSense bag 文件解析
# ============================================================================

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

# 复制公共资源
COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

# 复制模块代码
COPY pipelines/00_ingest /app/module

# 复制离线依赖包
COPY partdata/deps /app/deps

# 离线安装依赖
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

# 切换非 root 用户
USER appuser

WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]