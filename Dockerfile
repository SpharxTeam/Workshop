# ============================================
# Workshop V2.0 Production Docker Image
# Multi-stage build for optimized image size
# ============================================

# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim as runtime

LABEL maintainer="SPHARX DevOps <devops@spharx.cn>"
LABEL version="2.0.0"
LABEL description="Workshop V2.0 Data Processing Pipeline"
LABEL org.opencontainers.image.source="https://github.com/spharx-cn/workshop"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    # For hardware access (RealSense cameras)
    libusb-1.0-0 \
    # Compression utilities
    gzip zip unzip tar \
    # Process management
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r workshop && useradd -r -g workshop -d /app -s /sbin/nologin workshop

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY common/ ./common/
COPY pipelines/ ./pipelines/
COPY hardware/ ./hardware/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/backups /app/temp && \
    chown -R workshop:workshop /app

# Switch to non-root user
USER workshop

# Expose ports (if running web interface/API in future)
EXPOSE 8000 8080 9090

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WORKSHOP_ENV=production \
    WORKSHOP_LOG_LEVEL=INFO \
    WORKSHOP_DATA_DIR=/app/data \
    WORKSHOP_LOG_DIR=/app/logs \
    WORKSHOP_BACKUP_DIR=/app/backups \
    WORKSHOP_TEMP_DIR=/app/temp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from common.core.base_pipeline import BasePipeline; print('OK')" || exit 1

# Entry point
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["python", "-m", "scripts.demo_v2_full_pipeline", "--mode", "production"]
