#!/bin/bash
# 文件: toolchain/deploy/03-setup-directories.sh
# 用途: 创建运行时目录结构

set -e

WORKSHOP_ROOT="/home/SpharxWorkshop"
USER="spharx"

echo "=========================================="
echo "SpharxWorkshop 目录结构创建脚本"
echo "=========================================="
echo ""

# 检查是否在正确目录
cd $WORKSHOP_ROOT/workshop
if [ $? -ne 0 ]; then
    echo "❌ 错误: 请先克隆仓库并进入workshop目录"
    exit 1
fi

echo "[1/6] 创建数据目录..."
mkdir -p $WORKSHOP_ROOT/data/input/scenes
mkdir -p $WORKSHOP_ROOT/data/output/datasets
mkdir -p $WORKSHOP_ROOT/data/backup

echo "[2/6] 创建运行时工作区..."
mkdir -p $WORKSHOP_ROOT/workspace/cache
mkdir -p $WORKSHOP_ROOT/workspace/processing
mkdir -p $WORKSHOP_ROOT/workspace/logs/{pipeline,services,errors}
mkdir -p $WORKSHOP_ROOT/workspace/visualizations/{sam,colmap,physics}
mkdir -p $WORKSHOP_ROOT/workspace/temp

echo "[3/6] 创建模型缓存目录..."
mkdir -p $WORKSHOP_ROOT/.cache/models
mkdir -p $WORKSHOP_ROOT/.cache/datasets

echo "[4/6] 设置目录权限..."
chown -R $USER:$USER $WORKSHOP_ROOT/data
chown -R $USER:$USER $WORKSHOP_ROOT/workspace
chown -R $USER:$USER $WORKSHOP_ROOT/.cache
chmod -R 755 $WORKSHOP_ROOT/data
chmod -R 755 $WORKSHOP_ROOT/workspace

echo "[5/6] 初始化环境配置文件..."
if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        cp .env.template .env
        echo "✅ 环境配置文件已创建: .env"
        echo "⚠️  请编辑 .env 文件，配置您的OSS密钥和路径！"
    else
        echo "❌ 错误: .env.template 文件不存在"
        exit 1
    fi
else
    echo "ℹ️  .env 文件已存在，跳过创建"
fi

echo "[6/6] 创建符号链接（便于访问）..."
ln -sf $WORKSHOP_ROOT/workspace /tmp/spharx_workspace 2>/dev/null || true
ln -sf $WORKSHOP_ROOT/data /tmp/spharx_data 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ 目录结构创建完成！"
echo "=========================================="
echo ""
echo "创建的目录结构:"
echo "📁 $WORKSHOP_ROOT/data/              # 数据目录"
echo "   ├── input/scenes/               # 原始数据输入"
echo "   └── output/datasets/            # 成品数据集"
echo ""
echo "📁 $WORKSHOP_ROOT/workspace/         # 运行时工作区"
echo "   ├── cache/                      # 处理缓存"
echo "   ├── processing/                 # 正在处理的任务"
echo "   ├── logs/                       # 结构化日志"
echo "   └── visualizations/             # 可视化结果"
echo ""
echo "📁 $WORKSHOP_ROOT/.cache/            # 系统缓存"
echo "   └── models/                     # AI模型缓存"
echo ""
echo "下一步操作："
echo "1. 编辑环境变量: nano .env"
echo "2. 构建Docker镜像: docker-compose build"
echo "3. 启动服务: docker-compose up -d"
echo "4. 检查服务状态: docker-compose ps"