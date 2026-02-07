# Segment Anything 模型服务
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# 安装依赖
RUN pip install \
    segment-anything \
    opencv-python \
    fastapi \
    uvicorn \
    python-multipart

# 下载模型（可运行时下载，这里预下载加快启动）
RUN python -c "from segment_anything import sam_model_registry; \
    sam = sam_model_registry['vit_h'](checkpoint='sam_vit_h_4b8939.pth')"

# 复制服务代码
COPY docker/sam_server.py .

# SAM模型服务
EXPOSE 8000
CMD ["uvicorn", "sam_server:app", "--host", "0.0.0.0", "--port", "8000"]