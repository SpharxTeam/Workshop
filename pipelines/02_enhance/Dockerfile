# ============================================================================
# workshop 增强模块 (02_enhance)
# 基于 workshop-base，使用 YOLOv8 进行目标检测，生成 COCO 标注
# ============================================================================

FROM workshop-base:latest

ENV PYTHONPATH=/app/common/scripts

COPY common/scripts /app/common/scripts
COPY common/configs /app/common/configs
COPY pipelines/02_enhance /app/module
COPY partdata/deps /app/deps
RUN pip install --no-cache-dir --no-index --find-links /app/deps -r /app/module/requirements.txt

USER appuser
WORKDIR /app/module
ENTRYPOINT ["python", "runner.py"]