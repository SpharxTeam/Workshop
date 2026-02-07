# Spharx Toolchain Docker 镜像构建指南

## 镜像架构

Spharx Toolchain采用分层的Docker镜像架构：

```
base-image (Ubuntu 20.04 + Python 3.9)
├── colmap-image (基础镜像 + COLMAP + CUDA)
├── cvat-image (基础镜像 + CVAT + 自定义插件)
├── sa3d-image (基础镜像 + SA3D环境)
└── blender-image (基础镜像 + Blender + Python API)
```

## 构建顺序

1. **基础镜像** (`base.Dockerfile`)
   - Ubuntu 20.04 LTS
   - Python 3.9 + pip
   - 基础依赖库
   - 项目源代码

2. **专用镜像** (并行构建)
   - colmap.Dockerfile
   - cvat.Dockerfile  
   - sa3d.Dockerfile
   - blender.Dockerfile

## 构建命令

### 构建基础镜像
```bash
docker build -t spharx/base:latest -f docker/base.Dockerfile .
```

### 构建专用镜像
```bash
# COLMAP镜像
docker build -t spharx/colmap:latest -f docker/colmap.Dockerfile .

# CVAT镜像
docker build -t spharx/cvat:latest -f docker/cvat.Dockerfile .

# SA3D镜像
docker build -t spharx/sa3d:latest -f docker/sa3d.Dockerfile .

# Blender镜像
docker build -t spharx/blender:latest -f docker/blender.Dockerfile .
```

### 批量构建脚本
```bash
#!/bin/bash
# scripts/build_docker_images.sh

set -e

echo "开始构建Spharx Docker镜像..."

# 构建基础镜像
echo "1/5: 构建基础镜像..."
docker build -t spharx/base:latest -f docker/base.Dockerfile .

# 并行构建专用镜像
echo "2-5/5: 并行构建专用镜像..."
docker build -t spharx/colmap:latest -f docker/colmap.Dockerfile . &
docker build -t spharx/cvat:latest -f docker/cvat.Dockerfile . &
docker build -t spharx/sa3d:latest -f docker/sa3d.Dockerfile . &
docker build -t spharx/blender:latest -f docker/blender.Dockerfile . &

# 等待所有构建完成
wait

echo "所有镜像构建完成！"
docker images | grep spharx
```

## 镜像优化策略

### 多阶段构建
```dockerfile
# 使用多阶段构建减小最终镜像大小
FROM nvidia/cuda:11.8-devel-ubuntu20.04 as builder
# 编译阶段...

FROM ubuntu:20.04 as runtime
# 运行时阶段，只复制必要文件
```

### 缓存优化
```dockerfile
# 将不常变化的指令放在前面
COPY requirements.txt .
RUN pip install -r requirements.txt

# 将频繁变化的指令放在后面
COPY src/ ./src/
```

### 层压缩
```bash
# 构建时启用层压缩
docker build --compress -t spharx/base:latest .
```

## 镜像安全

### 基础安全措施
- 使用官方基础镜像
- 定期更新基础镜像
- 最小化安装包
- 使用非root用户运行

### 安全扫描
```bash
# 使用Trivy进行安全扫描
trivy image spharx/base:latest

# Docker Bench Security检查
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  docker/docker-bench-security
```

## 镜像推送

### 推送到私有仓库
```bash
# 标记镜像
docker tag spharx/base:latest registry.example.com/spharx/base:latest

# 推送镜像
docker push registry.example.com/spharx/base:latest
```

### 版本管理
```bash
# 按版本标记
docker tag spharx/base:latest spharx/base:v1.0.0
docker tag spharx/base:latest spharx/base:v1.0.0-$(date +%Y%m%d)

# 推送多个标签
docker push spharx/base:v1.0.0
docker push spharx/base:v1.0.0-$(date +%Y%m%d)
docker push spharx/base:latest
```

## 开发环境镜像

### 开发专用镜像
```dockerfile
# docker/dev.Dockerfile
FROM spharx/base:latest

# 安装开发工具
RUN apt-get update && apt-get install -y \
    vim \
    git \
    gdb \
    && rm -rf /var/lib/apt/lists/*

# 安装开发依赖
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# 设置开发环境
WORKDIR /app
CMD ["bash"]
```

## 故障排除

### 常见构建问题

1. **网络超时**
   ```bash
   # 使用国内镜像源
   docker build --build-arg HTTP_PROXY=http://proxy.company.com:8080 .
   ```

2. **存储空间不足**
   ```bash
   # 清理构建缓存
   docker builder prune
   ```

3. **权限问题**
   ```bash
   # 构建时指定用户
   docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .
   ```

### 调试技巧
```bash
# 进入构建中间层调试
docker build --target builder -t debug-builder .

# 运行临时容器检查文件
docker run --rm -it spharx/base:latest bash
```

---
*最后更新: 2026-02-07*
*版本: 1.0*