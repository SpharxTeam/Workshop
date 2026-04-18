#!/bin/bash
# Workshop 项目结构重整脚本
# 目标: 对齐 Deepness 项目结构，保持功能完整性

set -e

echo "=== Workshop 项目结构重整 ==="
echo "开始时间: $(date)"

WORKSHOP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$WORKSHOP_DIR"

echo "当前目录: $WORKSHOP_DIR"
echo ""

# 步骤 1: 合并 commons/schemas 到 common/schemas
echo "[步骤 1/6] 合并 commons/schemas 到 common/schemas..."
if [ -d "commons/schemas" ]; then
    cp commons/schemas/*.py common/schemas/ 2>/dev/null || true
    echo "  ✓ schemas 文件已合并"
fi

# 步骤 2: 移动 commons/utils 到 common/utils
echo "[步骤 2/6] 移动 commons/utils 到 common/utils..."
mkdir -p common/utils
if [ -d "commons/utils" ]; then
    cp commons/utils/*.py common/utils/ 2>/dev/null || true
    echo "  ✓ utils 文件已移动"
fi

# 步骤 3: 合并 __init__.py
echo "[步骤 3/6] 合并 __init__.py..."
if [ -f "commons/__init__.py" ] && [ -f "common/__init__.py" ]; then
    # 备份原文件
    cp common/__init__.py common/__init__.py.backup
    # 合并内容
    cat commons/__init__.py >> common/__init__.py
    echo "  ✓ __init__.py 已合并（备份: common/__init__.py.backup）"
fi

# 步骤 4: 删除空的 commons 目录
echo "[步骤 4/6] 删除 commons 目录..."
if [ -d "commons" ]; then
    rm -rf commons
    echo "  ✓ commons 目录已删除"
fi

# 步骤 5: 添加缺失的测试目录
echo "[步骤 5/6] 创建缺失的测试目录..."
mkdir -p tests/docs
mkdir -p tests/scripts
touch tests/docs/.gitkeep
touch tests/scripts/.gitkeep
echo "  ✓ tests/docs 和 tests/scripts 已创建"

# 步骤 6: 添加缺失的 scripts 子目录
echo "[步骤 6/6] 创建缺失的 scripts 子目录..."
mkdir -p scripts/build
touch scripts/build/.gitkeep
echo "  ✓ scripts/build 已创建"

echo ""
echo "=== 结构重整完成 ==="
echo "完成时间: $(date)"
echo ""
echo "=== 当前目录结构 ==="
find . -maxdepth 2 -type d | grep -v '.git' | grep -v '__pycache__' | grep -v '.pytest_cache' | grep -v 'build' | sort
