#!/bin/bash
set -e

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项] [bag路径]"
    echo ""
    echo "选项:"
    echo "  --config CONFIG_PATH   指定配置文件路径（默认使用环境变量或 /configs/pipeline_config.yaml）"
    echo "  -h, --help             显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 /data/raw/D435i_Walking.bag"
    echo "  $0 --config /configs/my_config.yaml /data/raw/D435i_Walking.bag"
}

# 解析命令行参数
BAG_PATH=""
CONFIG_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$BAG_PATH" ]; then
                BAG_PATH="$1"
                shift
            else
                echo "错误: 未知参数 $1"
                show_help
                exit 1
            fi
            ;;
    esac
done

# 设置默认值
if [ -z "$BAG_PATH" ]; then
    BAG_PATH="/data/raw/D435i_Walking.bag"
    echo "未指定 bag 路径，使用默认值: $BAG_PATH"
fi

if [ -z "$CONFIG_PATH" ]; then
    CONFIG_PATH="/configs/pipeline_config.yaml"
    echo "未指定配置文件路径，使用默认值: $CONFIG_PATH"
fi

SCENE_ID="scene_$(date +%Y%m%d_%H%M%S)"

echo "========================================="
echo "开始处理场景: $SCENE_ID"
echo "输入 bag: $BAG_PATH"
echo "配置文件: $CONFIG_PATH"
echo "========================================="

cd ~/workshop

# 1. Ingest
echo "[1/5] 运行 ingest ..."
docker-compose run --rm ingest \
  --input "$BAG_PATH" \
  --output "/data/processed/$SCENE_ID" \
  --config "$CONFIG_PATH"

# 2. Quality
echo "[2/5] 运行 quality ..."
docker-compose run --rm quality \
  --input "/data/processed/$SCENE_ID" \
  --output "/data/processed/$SCENE_ID/quality" \
  --config "$CONFIG_PATH"

# 3. Enhance
echo "[3/5] 运行 enhance ..."
docker-compose run --rm enhance \
  --input "/data/processed/$SCENE_ID" \
  --output "/data/processed/$SCENE_ID/enhanced" \
  --config "$CONFIG_PATH"

# 4. Calibrate
echo "[4/5] 运行 calibrate ..."
docker-compose run --rm calibrate \
  --input "/data/calibration_images" \
  --output "/data/processed/$SCENE_ID/calib" \
  --config "$CONFIG_PATH"

# 5. Pack
echo "[5/5] 运行 pack ..."
docker-compose run --rm pack \
  --input "/data/processed/$SCENE_ID" \
  --output "/data/datasets/$SCENE_ID" \
  --config "$CONFIG_PATH"

echo "========================================="
echo "✅ 全部完成！数据集位于: /data/datasets/$SCENE_ID"
echo "========================================="