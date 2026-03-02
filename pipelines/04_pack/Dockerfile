# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 打包模块 (04_pack)
# 基于 workshop-base，将处理后的数据打包成数据集并生成 manifest

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs

COPY pipelines/04_pack /app/module

RUN pip install --no-cache-dir -r /app/module/requirements.txt || \
    (pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple -r /app/module/requirements.txt) || \
    (pip install --no-cache-dir -i https://mirrors.ustc.edu.cn/pypi/web/simple -r /app/module/requirements.txt) || \
    (pip install --no-cache-dir -i https://mirrors.bfsu.edu.cn/pypi/web/simple -r /app/module/requirements.txt)

RUN mkdir -p /app/logs && chmod 777 /app/logs

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]