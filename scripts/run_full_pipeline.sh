#!/bin/bash
# 运行完整流水线脚本

set -e

echo "🚀 启动完整流水线..."

# 检查环境变量
if [ -z "$DATA_ROOT" ]; then
    export DATA_ROOT="/data/spharx"
fi

# 启动完整服务
echo "🐳 启动完整服务..."
docker-compose -f docker-compose.full.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 60

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.full.yml ps

echo "✅ 完整流水线启动完成！"
echo "📊 可用服务："
echo "  - CVAT: http://localhost:8080"
echo "  - COLMAP: http://localhost:8081"
echo "  - API: http://localhost:8000"