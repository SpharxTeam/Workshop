FROM python:3.10-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir --user --default-timeout=200 -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY config_loader.py .
COPY *.py .
ENTRYPOINT ["python", "realsense_parser.py"]