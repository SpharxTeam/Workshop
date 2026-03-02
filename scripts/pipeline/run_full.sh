# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# =================================================================================
# workshop 完整数据采集流水线运行脚本（produce 版）
# 功能：按顺序执行 ingest → quality → enhance → calibrate → pack
#       所有输入输出均在 produce/ 目录下
# 用法：./scripts/pipeline/run_full.sh [选项] <bag文件名> [场景ID]
# 示例：./scripts/pipeline/run_full.sh d435i_walking.bag scene_001
# =================================================================================
set -e

export COMPOSE_PROJECT_NAME=workshop

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

show_help() {
    echo "用法: $0 [选项] <bag文件名> [场景ID]"
    echo ""
    echo "选项:"
    echo "  --config CONFIG_PATH   指定配置文件路径（默认 /configs/pipeline_config.yaml）"
    echo "  -h, --help             显示帮助信息"
    echo ""
    echo "参数:"
    echo "  bag文件名    bag 文件名（必须位于 produce/input/raw/ 目录下）"
    echo "  场景ID       可选，自定义场景标识符，默认为 scene_<时间戳>"
    exit 0
}

# 默认值
BAG_NAME=""
SCENE_ID=""
CONFIG_PATH="/configs/pipeline_config.yaml"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            if [ -z "$BAG_NAME" ]; then
                BAG_NAME="$1"
                shift
            elif [ -z "$SCENE_ID" ]; then
                SCENE_ID="$1"
                shift
            else
                log_error "未知参数: $1"
                show_help
                exit 1
            fi
            ;;
    esac
done

if [ -z "$BAG_NAME" ]; then
    log_error "请指定 bag 文件名"
    show_help
    exit 1
fi

HOST_BAG_PATH="$PROJECT_ROOT/produce/input/raw/$BAG_NAME"
if [ ! -f "$HOST_BAG_PATH" ]; then
    log_error "宿主机 bag 文件不存在: $HOST_BAG_PATH"
    exit 1
fi

# 容器内 bag 路径（由 docker-compose 挂载决定）
CONTAINER_BAG_PATH="/data/raw/$BAG_NAME"

# 生成场景 ID（如果未指定）
if [ -z "$SCENE_ID" ]; then
    SCENE_ID="scene_$(date +%Y%m%d_%H%M%S)"
fi

export SCENE_ID
export BAG_FILE="$BAG_NAME"   # 传递给 docker-compose 用于命令替换

# 检查 docker 和 docker-compose
check_command docker
check_command docker-compose

# 确保必要的输出目录存在并设置权限
log_info "确保输出目录存在并设置权限..."
mkdir -p produce/output/processed produce/output/datasets produce/input/calibration
chmod 777 produce/output/processed produce/output/datasets produce/input/calibration

# 检查标定图像目录是否为空，若空则生成默认棋盘格图像
log_info "检查标定图像目录内容..."
if [ -z "$(ls -A produce/input/calibration 2>/dev/null)" ]; then
    log_warn "标定图像目录为空，正在生成棋盘格图像（约 20 张）..."
    docker run --rm \
        -v "$PROJECT_ROOT/produce/input/calibration:/output" \
        -v "$PROJECT_ROOT:/workspace" \
        workshop-base \
        python /workspace/scripts/utils/generate_realistic_calibration.py --output /output
    log_success "标定图像生成完成"
else
    log_info "标定图像目录已存在文件，跳过生成"
fi

# 确保模型文件存在（提示）
if [ ! -f "partdata/models/yolov8n.pt" ]; then
    log_warn "模型文件 partdata/models/yolov8n.pt 不存在，enhance 模块将失败！"
    log_info "请先运行 ./scripts/download/download_models.sh 下载模型"
fi

log_info "========================================="
log_info "开始处理场景: $SCENE_ID"
log_info "宿主机 bag 路径: $HOST_BAG_PATH"
log_info "容器内 bag 路径: $CONTAINER_BAG_PATH"
log_info "配置文件: $CONFIG_PATH"
log_info "中间数据目录: produce/output/processed"
log_info "最终数据集目录: produce/output/datasets"
log_info "========================================="

# 1. Ingest
log_info "[1/5] 运行 ingest ..."
if ! docker-compose run --rm ingest \
    --input "$CONTAINER_BAG_PATH" \
    --output "/data/processed/$SCENE_ID" \
    --config "$CONFIG_PATH"; then
    log_error "Ingest 失败"
    exit 1
fi

# 验证 Ingest 输出
log_info "验证 Ingest 输出..."
if docker-compose run --rm --entrypoint sh ingest -c "test -d /data/processed/$SCENE_ID/rgb"; then
    log_success "场景目录 /data/processed/$SCENE_ID/rgb 存在"
    FRAME_COUNT=$(docker-compose run --rm --entrypoint sh ingest -c "ls -1 /data/processed/$SCENE_ID/rgb/frame_*.jpg 2>/dev/null | wc -l")
    if [ "$FRAME_COUNT" -gt 0 ]; then
        log_success "找到 $FRAME_COUNT 帧图像"
    else
        log_error "RGB 图像目录为空"
        exit 1
    fi
else
    log_error "RGB 图像目录 /data/processed/$SCENE_ID/rgb 不存在"
    exit 1
fi
log_success "Ingest 输出验证通过"

# 2. Quality
log_info "[2/5] 运行 quality ..."
if ! docker-compose run --rm quality \
    --input "/data/processed/$SCENE_ID" \
    --output "/data/processed/$SCENE_ID/quality" \
    --config "$CONFIG_PATH"; then
    log_error "Quality 失败"
    exit 1
fi

# 3. Enhance
log_info "[3/5] 运行 enhance ..."
if ! docker-compose run --rm enhance \
    --input "/data/processed/$SCENE_ID" \
    --output "/data/processed/$SCENE_ID/enhanced" \
    --config "$CONFIG_PATH"; then
    log_error "Enhance 失败"
    exit 1
fi

# 4. Calibrate
log_info "[4/5] 运行 calibrate ..."
if ! docker-compose run --rm calibrate \
    --input "/data/calibration_images" \
    --output "/data/processed/$SCENE_ID/calib" \
    --config "$CONFIG_PATH"; then
    log_error "Calibrate 失败"
    exit 1
fi

# 5. Pack
log_info "[5/5] 运行 pack ..."
if ! docker-compose run --rm pack \
    --input "/data/processed/$SCENE_ID" \
    --output "/data/datasets/$SCENE_ID" \
    --config "$CONFIG_PATH"; then
    log_error "Pack 失败"
    exit 1
fi

log_success "========================================="
log_success "✅ 全部完成！"
log_success "场景 $SCENE_ID 的数据集已存储在 ./produce/output/datasets/$SCENE_ID"
log_success "您可以通过以下命令查看或导出数据："
log_success "  ls -la produce/output/datasets/$SCENE_ID"
log_success "  ./scripts/utils/export_datasets.sh  # 导出所有数据集到 ./exports/"
log_success "========================================="