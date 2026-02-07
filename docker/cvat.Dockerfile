# CVAT 自定义镜像
# 基于官方CVAT镜像，添加自定义插件和配置

FROM openvino/cvat_server:latest

# 安装额外依赖
USER root
RUN apt-get update && apt-get install -y \
    python3-opencv \
    python3-scipy \
    python3-sklearn \
    && rm -rf /var/lib/apt/lists/*

# 复制自定义插件
COPY docker/plugins/cvat/ /home/django/plugins/

# 复制自定义配置
COPY config/cvat_config.py /home/django/

# 设置权限
RUN chown -R django:django /home/django/plugins/ \
    && chmod +x /home/django/plugins/*/install.sh

# 切换回django用户
USER django

# 安装Python依赖
COPY requirements-cvat.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-cvat.txt

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/server/about || exit 1

# 默认启动命令
CMD ["/usr/bin/supervisord", "-c", "/home/django/supervisor.conf"]