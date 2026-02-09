# SPHARX 部署指南

## 🎯 部署概览

本文档详细介绍如何在生产环境中部署SPHARX Toolchain。

## 🖥️ 系统要求

### 硬件要求
- **CPU**: Intel Xeon 或 AMD EPYC，16核以上
- **GPU**: NVIDIA RTX 3090/4090 或 A100 (24GB显存以上)
- **内存**: 64GB DDR4 ECC
- **存储**: 
  - 系统盘: 500GB SSD
  - 数据盘: 2TB NVMe SSD
- **网络**: 1Gbps带宽

### 软件要求
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 8
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **NVIDIA驱动**: 470+ (支持CUDA 11.4+)
- **Python**: 3.9+

## 🚀 部署步骤

### 1. 服务器初始化

```bash
# 下载并运行初始化脚本
wget https://raw.githubusercontent.com/spharx/toolchain/main/deploy/01-init-server.sh
chmod +x 01-init-server.sh
./01-init-server.sh
```

脚本将自动完成：
- ✅ 创建目录结构
- ✅ 安装Docker和Docker Compose
- ✅ 安装基础依赖
- ✅ 配置用户权限

### 2. 克隆代码仓库

```bash
# 运行克隆脚本
wget https://raw.githubusercontent.com/spharx/toolchain/main/deploy/02-clone-repos.sh
chmod +x 02-clone-repos.sh
./02-clone-repos.sh
```

### 3. 配置环境变量

```bash
cd /opt/spharx/toolchain

# 复制配置模板
cp .env.template .env

# 编辑配置文件
vim .env
```

关键配置项：
```bash
# 基础配置
PROJECT_NAME=spharx-toolchain
VERSION=1.0.0

# 数据目录
DATA_ROOT=/data/spharx
INPUT_DIR=/data/spharx/input
OUTPUT_DIR=/data/spharx/output

# 数据库配置
DATABASE_URL=postgresql://spharx:password@localhost:5432/spharx
REDIS_URL=redis://localhost:6379/0

# 服务端口
API_PORT=8000
CVAT_PORT=8080
```

### 4. 构建Docker镜像

```bash
# 运行构建脚本
./deploy/04-build-images.sh
```

或者手动构建：
```bash
# 构建基础镜像
docker build -t spharx/base:latest -f docker/base/Dockerfile .

# 构建主服务镜像
docker build -t spharx/toolchain:latest -f Dockerfile .
```

### 5. 启动服务

#### 方案一：快速启动（仅2D服务）

```bash
# 启动2D流水线
./scripts/run_2d_pipeline.sh
```

#### 方案二：完整启动（2D+3D服务）

```bash
# 启动完整流水线
./scripts/run_full_pipeline.sh
```

#### 方案三：手动启动

```bash
# 启动核心服务
docker-compose up -d

# 启动2D服务
docker-compose -f docker-compose.2d-only.yml up -d

# 启动完整服务
docker-compose -f docker-compose.full.yml up -d
```

### 6. 验证部署

```bash
# 运行健康检查
./scripts/health_check.sh

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🔧 服务配置

### 端口映射

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|----------|----------|------|
| API | 8000 | 8000 | 主API服务 |
| CVAT | 8080 | 8080 | 图像标注平台 |
| COLMAP | 8081 | 8081 | 3D重建服务 |
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存服务 |

### 数据卷挂载

```yaml
volumes:
  - /data/spharx/input:/app/data/input
  - /data/spharx/output:/app/data/output
  - /data/spharx/models:/app/models
  - /data/spharx/logs:/app/logs
```

## 🛡️ 安全配置

### 1. 防火墙设置

```bash
# 开放必要端口
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # API
sudo ufw allow 8080  # CVAT
sudo ufw enable
```

### 2. SSL证书配置

```bash
# 安装certbot
sudo apt install certbot

# 获取SSL证书
sudo certbot certonly --standalone -d your-domain.com
```

### 3. 用户权限管理

```bash
# 创建专用用户
sudo useradd -r -s /bin/false spharx
sudo usermod -aG docker spharx

# 设置目录权限
sudo chown -R spharx:spharx /opt/spharx
sudo chmod -R 750 /opt/spharx
```

## 📊 监控与维护

### 1. 日志管理

```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api

# 日志轮转配置
sudo vim /etc/logrotate.d/spharx
```

### 2. 性能监控

```bash
# 系统资源监控
htop
iotop
nvidia-smi

# Docker资源使用
docker stats

# 应用性能监控
curl http://localhost:8000/metrics
```

### 3. 备份策略

```bash
# 数据备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/spharx_data_$DATE.tar.gz /data/spharx
```

## 🆘 故障排除

### 常见问题

1. **Docker服务无法启动**
   ```bash
   sudo systemctl status docker
   sudo journalctl -u docker
   ```

2. **GPU不可用**
   ```bash
   nvidia-smi
   docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

3. **端口冲突**
   ```bash
   sudo netstat -tlnp | grep :8080
   ```

4. **存储空间不足**
   ```bash
   df -h
   docker system prune -a
   ```

### 紧急恢复

```bash
# 停止所有服务
docker-compose down

# 清理数据（谨慎操作）
# rm -rf /data/spharx/*

# 重新部署
./deploy/04-build-images.sh
docker-compose up -d
```

## 📈 扩展部署

### 多节点部署

```yaml
# docker-compose.cluster.yml
version: '3.8'
services:
  api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### 负载均衡

```nginx
# nginx.conf
upstream spharx_api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://spharx_api;
    }
}
```

---
*部署版本: v1.0*  
*最后更新: 2024年*