#!/bin/bash
# 挂载阿里云OSS到本地目录

set -e

# 加载环境变量
WORKSHOP_ROOT="${WORKSHOP_ROOT:-/home/spharx/SpharxWorkshop}"
ENV_FILE="$WORKSHOP_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "错误：找不到环境变量文件 $ENV_FILE"
    exit 1
fi

source "$ENV_FILE"

# 检查必需的环境变量
if [ -z "$OSS_ENDPOINT" ] || [ -z "$OSS_BUCKET" ] || [ -z "$OSS_ACCESS_KEY_ID" ] || [ -z "$OSS_ACCESS_KEY_SECRET" ]; then
    echo "错误：OSS配置不完整，请检查.env文件"
    exit 1
fi

# 安装ossfs
if ! command -v ossfs &> /dev/null; then
    echo "安装 ossfs..."
    wget http://gosspublic.alicdn.com/ossfs/ossfs_1.80.6_ubuntu20.04_amd64.deb
    sudo apt-get install -f ./ossfs_1.80.6_ubuntu20.04_amd64.deb
    rm ./ossfs_1.80.6_ubuntu20.04_amd64.deb
fi

# 创建挂载点
MOUNT_POINT="$WORKSHOP_ROOT/data"
sudo mkdir -p "$MOUNT_POINT"

# 配置OSS凭证
echo "$OSS_BUCKET:$OSS_ACCESS_KEY_ID:$OSS_ACCESS_KEY_SECRET" | sudo tee /etc/passwd-ossfs
sudo chmod 640 /etc/passwd-ossfs

# 挂载OSS
echo "挂载 OSS 到 $MOUNT_POINT..."
sudo ossfs "$OSS_BUCKET" "$MOUNT_POINT" -o url="$OSS_ENDPOINT" -o allow_other

echo "挂载完成！"
echo "数据目录：$MOUNT_POINT"