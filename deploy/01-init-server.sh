#!/bin/bash
# 文件: toolchain/deploy/01-init-server.sh
# 用途: 服务器基础环境初始化

set -e

WORKSHOP_ROOT="/home/SpharxWorkshop"
USER="spharx"

echo "=========================================="
echo "SpharxWorkshop 服务器初始化脚本"
echo "=========================================="
echo ""

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  请使用sudo或以root身份运行此脚本"
    exit 1
fi

echo "[1/6] 创建用户和组..."
if ! id "$USER" &>/dev/null; then
    useradd -m -s /bin/bash "$USER"
    echo "✅ 用户 $USER 创建成功"
else
    echo "ℹ️  用户 $USER 已存在"
fi

echo "[2/6] 创建基础目录结构..."
mkdir -p $WORKSHOP_ROOT
chown -R $USER:$USER $WORKSHOP_ROOT
chmod 755 $WORKSHOP_ROOT
echo "✅ 目录结构创建完成: $WORKSHOP_ROOT"

echo "[3/6] 安装系统依赖..."
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    libopencv-dev \
    nvidia-driver-535 \
    nvidia-docker2

echo "✅ 系统依赖安装完成"

echo "[4/6] 安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    echo "✅ Docker安装完成"
else
    echo "ℹ️  Docker已安装"
fi

echo "[5/6] 安装Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d'"' -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
echo "✅ Docker Compose安装完成"

echo "[6/6] 配置用户权限和组..."
usermod -aG docker $USER
systemctl enable docker
systemctl start docker

# 配置Git
sudo -u $USER git config --global user.name "Spharx Server"
sudo -u $USER git config --global user.email "server@spharx.com"
sudo -u $USER git config --global pull.rebase false

echo ""
echo "=========================================="
echo "✅ 服务器初始化完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 重新登录或执行: newgrp docker"
echo "2. 运行部署脚本: ./deploy/02-clone-repos.sh"
echo "3. 配置环境变量: cp .env.template .env && nano .env"
echo ""
echo "注意：如果使用GPU，请确保NVIDIA驱动已正确安装"
echo "运行检查: nvidia-smi"