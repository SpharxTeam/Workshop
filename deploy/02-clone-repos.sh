#!/bin/bash
# 文件: toolchain/deploy/02-clone-repos.sh
# 用途: 克隆或更新仓库

set -e

WORKSHOP_ROOT="/home/SpharxWorkshop"
cd $WORKSHOP_ROOT

echo "=========================================="
echo "SpharxWorkshop 仓库克隆脚本"
echo "=========================================="
echo ""

# 检查是否在正确目录
if [ ! -d "$WORKSHOP_ROOT" ]; then
    echo "❌ 错误: 工作空间目录不存在: $WORKSHOP_ROOT"
    echo "请先运行 01-init-server.sh"
    exit 1
fi

echo "[1/4] 配置Git SSH密钥..."
SSH_DIR="/home/spharx/.ssh"
if [ ! -f "$SSH_DIR/id_rsa" ]; then
    echo "⚠️  未找到SSH密钥，如果需要从私有仓库克隆，请先配置SSH密钥"
    echo "运行: ssh-keygen -t rsa -b 4096 -C 'server@spharx.com'"
    echo "然后将公钥添加到Gitee/GitHub"
    read -p "是否继续使用HTTPS克隆? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[2/4] 克隆Toolchain仓库..."
if [ -d "workshop" ]; then
    echo "ℹ️  workshop目录已存在，尝试更新..."
    cd workshop
    git pull origin master || echo "⚠️  更新失败，请手动检查"
    cd ..
else
    echo "正在克隆 toolchain 仓库..."
    git clone https://gitee.com/spharx/toolchain.git workshop
    if [ $? -eq 0 ]; then
        echo "✅ toolchain 仓库克隆成功"
    else
        echo "❌ toolchain 仓库克隆失败"
        exit 1
    fi
fi

echo "[3/4] 克隆Library仓库..."
if [ -d "library" ]; then
    echo "ℹ️  library目录已存在，尝试更新..."
    cd library
    git pull origin master || echo "⚠️  更新失败，请手动检查"
    cd ..
else
    echo "正在克隆 library 仓库..."
    git clone https://gitee.com/spharx/library.git library
    if [ $? -eq 0 ]; then
        echo "✅ library 仓库克隆成功"
    else
        echo "❌ library 仓库克隆失败"
        exit 1
    fi
fi

echo "[4/4] 设置目录权限..."
chown -R spharx:spharx $WORKSHOP_ROOT/workshop
chown -R spharx:spharx $WORKSHOP_ROOT/library
chmod -R 755 $WORKSHOP_ROOT/workshop
chmod -R 755 $WORKSHOP_ROOT/library

echo ""
echo "=========================================="
echo "✅ 仓库克隆/更新完成！"
echo "=========================================="
echo ""
echo "目录结构:"
echo "  $WORKSHOP_ROOT/workshop/    # 生产线工具链"
echo "  $WORKSHOP_ROOT/library/     # 数据集规范"
echo ""
echo "下一步操作："
echo "1. 进入工具链目录: cd $WORKSHOP_ROOT/workshop"
echo "2. 复制环境配置: cp .env.template .env"
echo "3. 编辑环境变量: nano .env"
echo "4. 运行目录创建脚本: ./deploy/03-setup-directories.sh"