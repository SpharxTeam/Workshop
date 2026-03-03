# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 数据导入模块 (00_ingest)
# 基于 workshop-base，实现 RealSense bag 文件解析

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

# 复制公共资源
COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

# 复制模块代码（包含 algorithm 子目录）
COPY pipelines/run_00_ingest /app/module

# 在线安装依赖（多镜像源重试）
RUN pip install --no-cache-dir -r /app/module/requirements.txt || \
    (pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple -r /app/module/requirements.txt) || \
    (pip install --no-cache-dir -i https://mirrors.ustc.edu.cn/pypi/web/simple -r /app/module/requirements.txt) || \
    (pip install --no-cache-dir -i https://mirrors.bfsu.edu.cn/pypi/web/simple -r /app/module/requirements.txt)

# 确保日志目录存在且可写
RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]