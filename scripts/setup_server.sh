#!/bin/bash
# SpharxWorkshop 服务器目录初始化脚本
# 用法：./setup_server.sh [目标路径]

set -e  # 遇到错误退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 参数检查
WORKSHOP_ROOT="${1:-/home/spharx/SpharxWorkshop}"
if [ ! -d "$(dirname "$WORKSHOP_ROOT")" ]; then
    print_error "父目录不存在: $(dirname "$WORKSHOP_ROOT")"
    exit 1
fi

print_info "开始初始化 SpharxWorkshop 目录结构..."
print_info "工作目录: $WORKSHOP_ROOT"

# 检查是否以正确用户运行
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" != "spharx" ]; then
    print_warning "当前用户是 $CURRENT_USER，建议使用 spharx 用户运行"
    read -p "是否继续？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 创建主目录结构
print_info "1. 创建主目录结构..."
mkdir -p "$WORKSHOP_ROOT"
mkdir -p "$WORKSHOP_ROOT/data/input/scenes"
mkdir -p "$WORKSHOP_ROOT/data/output/datasets"
mkdir -p "$WORKSHOP_ROOT/data/cache"
mkdir -p "$WORKSHOP_ROOT/workspace/processing"
mkdir -p "$WORKSHOP_ROOT/workspace/logs/pipeline"
mkdir -p "$WORKSHOP_ROOT/workspace/logs/services"
mkdir -p "$WORKSHOP_ROOT/workspace/logs/system"
mkdir -p "$WORKSHOP_ROOT/workspace/archive"
mkdir -p "$WORKSHOP_ROOT/docker/volumes"
mkdir -p "$WORKSHOP_ROOT/docker/images"

# 2. 克隆仓库（如果不存在）
print_info "2. 设置代码仓库..."
if [ ! -d "$WORKSHOP_ROOT/toolchain" ]; then
    print_info "  克隆 Toolchain 仓库..."
    git clone git@gitee.com:spharx/toolchain.git "$WORKSHOP_ROOT/toolchain"
else
    print_info "  Toolchain 仓库已存在，跳过克隆"
fi

if [ ! -d "$WORKSHOP_ROOT/library" ]; then
    print_info "  克隆 Library 仓库..."
    git clone git@gitee.com:spharx/library.git "$WORKSHOP_ROOT/library"
else
    print_info "  Library 仓库已存在，跳过克隆"
fi

# 3. 复制环境变量模板
print_info "3. 设置环境变量..."
if [ ! -f "$WORKSHOP_ROOT/.env" ] && [ -f "$WORKSHOP_ROOT/toolchain/.env.template" ]; then
    cp "$WORKSHOP_ROOT/toolchain/.env.template" "$WORKSHOP_ROOT/.env.template"
    print_info "  环境变量模板已复制到 $WORKSHOP_ROOT/.env.template"
    print_warning "  请编辑 $WORKSHOP_ROOT/.env.template 并保存为 $WORKSHOP_ROOT/.env"
else
    print_info "  环境变量文件已存在"
fi

# 4. 设置权限
print_info "4. 设置目录权限..."
if [ "$CURRENT_USER" = "spharx" ]; then
    chown -R spharx:spharx "$WORKSHOP_ROOT"
fi
chmod -R 755 "$WORKSHOP_ROOT"
chmod -R 777 "$WORKSHOP_ROOT/workspace"  # 允许所有用户写入工作区
chmod -R 777 "$WORKSHOP_ROOT/data"       # 允许所有用户读写数据

# 5. 创建示例场景目录（用于测试）
print_info "5. 创建测试场景结构..."
mkdir -p "$WORKSHOP_ROOT/data/input/scenes/sample_scene_001"
mkdir -p "$WORKSHOP_ROOT/data/input/scenes/sample_scene_001/images"
cat > "$WORKSHOP_ROOT/data/input/scenes/sample_scene_001/metadata.json" << EOF
{
    "scene_id": "sample_scene_001",
    "description": "示例场景 - 用于测试生产线",
    "capture_date": "$(date -I)",
    "capture_device": "test_camera",
    "scene_type": "indoor",
    "num_images": 0,
    "note": "这是一个测试场景，请用实际图像替换"
}
EOF

# 6. 创建必要的符号链接（可选）
print_info "6. 创建便捷访问链接..."
ln -sf "$WORKSHOP_ROOT/toolchain/scripts" "$WORKSHOP_ROOT/scripts" 2>/dev/null || true

# 7. 生成目录结构报告
print_info "7. 生成目录结构报告..."
tree -L 3 "$WORKSHOP_ROOT" > "$WORKSHOP_ROOT/directory_structure.txt" 2>/dev/null || {
    ls -la "$WORKSHOP_ROOT" > "$WORKSHOP_ROOT/directory_structure.txt"
    ls -la "$WORKSHOP_ROOT/data" >> "$WORKSHOP_ROOT/directory_structure.txt"
    ls -la "$WORKSHOP_ROOT/workspace" >> "$WORKSHOP_ROOT/directory_structure.txt"
}

print_info "=========================================="
print_info "SpharxWorkshop 服务器目录初始化完成！"
print_info "=========================================="
echo ""
echo "下一步操作："
echo "1. 编辑环境变量："
echo "   cd $WORKSHOP_ROOT"
echo "   cp .env.template .env"
echo "   nano .env  # 或使用你喜欢的编辑器"
echo ""
echo "2. 部署2D服务栈："
echo "   cd $WORKSHOP_ROOT/toolchain"
echo "   docker-compose -f docker-compose.2d.yml up -d"
echo ""
echo "3. 运行测试流水线："
echo "   cd $WORKSHOP_ROOT/toolchain"
echo "   python src/main.py --scene-id sample_scene_001 --2d-only"
echo ""
print_info "详细指南请参考：$WORKSHOP_ROOT/toolchain/docs/DEPLOYMENT.md"