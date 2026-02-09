#!/bin/bash
# 文件: scripts/run_2d_pipeline.sh
# 用途: 运行2D标注流水线

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$WORKSHOP_ROOT"

echo "=========================================="
echo "SpharxWorkshop 2D标注流水线启动脚本"
echo "=========================================="
echo ""

# 检查参数
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <scene_id> [config_file]"
    echo ""
    echo "参数:"
    echo "  scene_id    场景ID（对应data/input/scenes/下的目录名）"
    echo "  config_file 可选，配置文件路径（默认使用configs/pipeline_2d.yaml）"
    echo ""
    echo "示例:"
    echo "  $0 scene_001"
    echo "  $0 demo_office configs/custom_2d.yaml"
    exit 1
fi

SCENE_ID=$1
CONFIG_FILE=${2:-"configs/pipeline_2d.yaml"}

# 检查场景目录是否存在
SCENE_DIR="$WORKSHOP_ROOT/data/input/scenes/$SCENE_ID"
if [ ! -d "$SCENE_DIR" ]; then
    echo "❌ 错误: 场景目录不存在: $SCENE_DIR"
    echo "请确保场景数据已放置在正确位置"
    exit 1
fi

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️  配置文件不存在: $CONFIG_FILE，将使用默认配置"
    CONFIG_FILE=""
fi

echo "📁 场景: $SCENE_ID"
echo "📁 目录: $SCENE_DIR"
echo "⚙️  配置: ${CONFIG_FILE:-默认配置}"
echo ""

# 检查Docker服务是否运行
if ! docker-compose ps | grep -q "spharx-controller"; then
    echo "⚠️  主控制器服务未运行，正在启动..."
    docker-compose up -d spharx-controller
    sleep 5
fi

echo "[1/4] 检查场景数据..."
IMAGE_COUNT=$(find "$SCENE_DIR/images" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "❌ 错误: 场景中没有图像文件"
    exit 1
fi
echo "✅ 发现 $IMAGE_COUNT 张图像"

echo "[2/4] 准备处理环境..."
docker-compose exec spharx-controller mkdir -p /home/SpharxWorkshop/workspace/processing/$SCENE_ID

echo "[3/4] 启动2D标注流水线..."
if [ -n "$CONFIG_FILE" ]; then
    docker-compose exec spharx-controller python src/main.py pipeline --type 2d --scene $SCENE_ID --config $CONFIG_FILE
else
    docker-compose exec spharx-controller python src/main.py pipeline --type 2d --scene $SCENE_ID
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "[4/4] 流水线执行完成！"
    echo ""
    
    # 显示输出信息
    OUTPUT_DIR="$WORKSHOP_ROOT/data/output/datasets/SPHARX_2D_${SCENE_ID}"
    if [ -d "$OUTPUT_DIR" ]; then
        echo "📊 输出结果:"
        echo "   标注文件: $OUTPUT_DIR/annotations.json"
        echo "   摘要报告: $OUTPUT_DIR/summary.json"
        echo "   可视化结果: $OUTPUT_DIR/visualizations/"
        echo ""
        echo "📈 统计信息:"
        if [ -f "$OUTPUT_DIR/summary.json" ]; then
            cat "$OUTPUT_DIR/summary.json" | python3 -m json.tool | grep -E "(total_images|total_annotations|avg_quality_score)"
        fi
    fi
    
    echo ""
    echo "✅ 2D标注流水线执行成功！"
else
    echo ""
    echo "❌ 2D标注流水线执行失败"
    echo "查看日志: docker-compose logs spharx-controller"
    exit 1
fi