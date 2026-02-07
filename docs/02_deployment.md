# Spharx Toolchain 部署指南

## 环境准备

### 系统要求
- **操作系统**: Ubuntu 18.04+/CentOS 7+/Windows 10+
- **内存**: 最少8GB，推荐16GB以上
- **存储**: 最少100GB可用空间
- **GPU**: NVIDIA GPU（推荐RTX 3060以上）

### 软件依赖
```bash
# Docker安装
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose安装
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# NVIDIA Container Toolkit（GPU支持）
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## 快速部署

### 1. 克隆项目
```bash
git clone https://gitee.com/spharx/toolchain.git
cd toolchain
```

### 2. 配置环境变量
```bash
cp .env.template .env
# 编辑.env文件，设置必要的参数
vim .env
```

### 3. 最小化部署（仅2D服务）
```bash
# 构建并启动2D服务栈
make deploy-2d

# 验证服务状态
make health-check
```

### 4. 完整部署（2D+3D服务）
```bash
# 构建并启动完整服务栈
make deploy-full

# 验证所有服务
./scripts/health_check.sh
```

## 服务访问

### 默认端口映射
- **CVAT**: http://localhost:8080
- **API服务**: http://localhost:8000
- **监控面板**: http://localhost:3000
- **日志系统**: http://localhost:5601

### 初始账户
```
用户名: admin
密码: Spharx@2024
```

## 数据目录结构

```
/workspace/
├── data/              # 原始数据存储
│   ├── raw/          # 原始图像文件
│   └── processed/    # 处理后数据
├── models/           # 模型权重文件
├── outputs/          # 输出结果
│   ├── 2d_datasets/  # 2D标注数据集
│   └── 3d_datasets/  # 3D数据集
└── logs/             # 运行日志
```

## 性能调优

### GPU资源配置
```yaml
# docker-compose.yml 中的GPU配置示例
services:
  colmap:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

### 内存和CPU限制
```yaml
services:
  pipeline-worker:
    mem_limit: 8g
    mem_reservation: 4g
    cpus: 2.0
```

## 故障排除

### 常见问题

1. **Docker权限问题**
   ```bash
   sudo usermod -aG docker $USER
   # 重新登录或执行: newgrp docker
   ```

2. **GPU无法识别**
   ```bash
   # 检查NVIDIA驱动
   nvidia-smi
   
   # 重启Docker服务
   sudo systemctl restart docker
   ```

3. **端口冲突**
   ```bash
   # 查看端口占用
   netstat -tulpn | grep :8080
   
   # 修改docker-compose.yml中的端口映射
   ```

4. **存储空间不足**
   ```bash
   # 清理Docker缓存
   docker system prune -a
   
   # 清理构建缓存
   docker builder prune
   ```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f cvat
docker-compose logs -f pipeline-worker
```

## 生产环境建议

### 安全配置
- 修改默认密码
- 启用HTTPS
- 配置防火墙规则
- 定期备份重要数据

### 监控告警
- 设置CPU/内存使用率告警
- 监控磁盘空间
- 跟踪GPU利用率
- 配置服务可用性检测

### 备份策略
```bash
# 定期备份脚本示例
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/toolchain_$DATE"

# 备份配置和数据
rsync -av /workspace/data/ $BACKUP_DIR/data/
rsync -av /workspace/models/ $BACKUP_DIR/models/
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
```

---
*最后更新: 2026-02-07*
*版本: 1.0*