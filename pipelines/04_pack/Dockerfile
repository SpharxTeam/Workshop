FROM python:3.10-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir --user --default-timeout=200 -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY config_loader.py .
COPY *.py .
ENTRYPOINT ["python", "ros_bag_packer.py"]