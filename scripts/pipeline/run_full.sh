# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 完整数据采集流水线运行脚本
# 功能：按顺序执行 ingest → quality → enhance → calibrate → pack
# 所有输入输出均在 produce/ 目录下
# 用法：./scripts/pipeline/run_full.sh [选项] <bag文件名> [场景ID]
# 示例：./scripts/pipeline/run_full.sh d435i_walking.bag scene_001

set -euo pipefail

export COMPOSE_PROJECT_NAME=workshop
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

# ---------- 帮助信息 ----------
show_help() {
    cat << EOF
用法: $0 [选项] <bag文件名> [场景ID]

选项:
  --config CONFIG_PATH   指定配置文件路径（默认 /configs/pipeline_config.yaml）
  --no-streaming         禁用流式处理模式（默认启用）
  --timeout SECONDS      每个模块的超时时间（默认 3600 秒）
  --clean                运行前清理旧场景数据（谨慎）
  -h, --help             显示帮助信息

参数:
  bag文件名    bag 文件名（必须位于 produce/input/raw/ 目录下）
  场景ID       可选，自定义场景标识符，默认为 scene_<时间戳>
EOF
    exit 0
}

# ---------- 默认值 ----------
BAG_NAME=""
SCENE_ID=""
CONFIG_PATH="/configs/pipeline_config.yaml"
STREAMING_MODE="true"
MODULE_TIMEOUT=3600
CLEAN_BEFORE_RUN="false"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# ---------- 解析参数 ----------
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --no-streaming)
            STREAMING_MODE="false"
            shift
            ;;
        --timeout)
            MODULE_TIMEOUT="$2"
            shift 2
            ;;
        --clean)
            CLEAN_BEFORE_RUN="true"
            shift
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

# ---------- 必要参数检查 ----------
if [ -z "$BAG_NAME" ]; then
    log_error "请指定 bag 文件名"
    show_help
    exit 1
fi

# ---------- 路径定义 ----------
HOST_BAG_PATH="$PROJECT_ROOT/produce/input/raw/$BAG_NAME"
CONTAINER_BAG_PATH="/data/raw/$BAG_NAME"
PROCESSED_DIR="$PROJECT_ROOT/produce/output/processed"
DATASETS_DIR="$PROJECT_ROOT/produce/output/datasets"

# ---------- 预检 ----------
log_info "========== 运行环境预检 =========="
# 检查 bag 文件
if [ ! -f "$HOST_BAG_PATH" ]; then
    log_error "宿主机 bag 文件不存在: $HOST_BAG_PATH"
    exit 1
fi
# 检查 Docker 服务
if ! docker info >/dev/null 2>&1; then
    log_error "Docker 服务未运行，请启动 Docker"
    exit 1
fi
# 检查磁盘空间（至少需要 10GB 空闲）
available_kb=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
if [ "$available_kb" -lt 10485760 ]; then
    log_warn "磁盘可用空间不足 10GB，当前仅 $(numfmt --to=iec $((available_kb*1024)))"
fi
# 检查模型文件
DETECT_MODEL="partdata/models/yolov8n.pt"
SEG_MODEL="partdata/models/yolov8n-seg.pt"
if [ ! -f "$SEG_MODEL" ]; then
    log_warn "分割模型 $SEG_MODEL 不存在，将使用检测模型 $DETECT_MODEL"
    if [ ! -f "$DETECT_MODEL" ]; then
        log_error "检测模型也不存在，请先运行 ./scripts/download/download_models.sh"
        exit 1
    fi
fi

# ---------- 清理选项 ----------
if [ "$CLEAN_BEFORE_RUN" = "true" ]; then
    log_warn "清理旧场景数据（--clean 选项）..."
    rm -rf "$PROCESSED_DIR"/* "$DATASETS_DIR"/*
fi

# ---------- 生成场景 ID ----------
if [ -z "$SCENE_ID" ]; then
    SCENE_ID="scene_$(date +%Y%m%d_%H%M%S)"
fi
export SCENE_ID
export BAG_FILE="$BAG_NAME"

# ---------- 获取当前用户 UID/GID（用于容器内用户映射） ----------
HOST_UID=$(id -u)
HOST_GID=$(id -g)

# ---------- 创建输出目录并设置权限 ----------
log_info "确保输出目录存在并设置权限..."
mkdir -p "$PROCESSED_DIR" "$DATASETS_DIR" produce/input/calibration
chown $HOST_UID:$HOST_GID "$PROCESSED_DIR" "$DATASETS_DIR" produce/input/calibration
chmod 755 "$PROCESSED_DIR" "$DATASETS_DIR" produce/input/calibration

# ---------- 标定图像检查 ----------
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

# ---------- 开始计时 ----------
START_TIME=$(date +%s)
log_info "========================================="
log_info "开始处理场景: $SCENE_ID"
log_info "宿主机 bag 路径: $HOST_BAG_PATH"
log_info "配置文件: $CONFIG_PATH"
log_info "中间数据目录: $PROCESSED_DIR"
log_info "最终数据集目录: $DATASETS_DIR"
log_info "流式模式: $STREAMING_MODE"
log_info "模块超时: ${MODULE_TIMEOUT}s"
log_info "宿主 UID:GID = $HOST_UID:$HOST_GID"
log_info "========================================="

# ---------- 定义执行函数（带超时） ----------
run_module() {
    local step_name=$1
    local cmd=$2
    log_info "[$step_name] 开始执行..."
    # 使用 timeout 命令限制执行时间
    if ! timeout "$MODULE_TIMEOUT" bash -c "$cmd"; then
        log_error "[$step_name] 执行失败（可能超时或错误）"
        exit 1
    fi
    log_success "[$step_name] 完成"
}

# ---------- 1. Ingest ----------
run_module "1/5 Ingest" "
docker-compose run --rm \
    -e HOST_UID=$HOST_UID -e HOST_GID=$HOST_GID \
    ingest \
    --input \"$CONTAINER_BAG_PATH\" \
    --output \"/data/processed/$SCENE_ID\" \
    --config \"$CONFIG_PATH\"
"

# ---------- 验证 Ingest 输出 ----------
log_info "验证 Ingest 输出..."
FRAME_COUNT=$(docker-compose run --rm --entrypoint sh ingest -c "find /data/processed/$SCENE_ID/rgb -type f \( -name '*.jpg' -o -name '*.webp' -o -name '*.png' \) 2>/dev/null | wc -l")
if [ "$FRAME_COUNT" -gt 0 ]; then
    log_success "找到 $FRAME_COUNT 帧图像"
else
    log_error "RGB 图像目录为空"
    exit 1
fi
log_success "Ingest 输出验证通过"

# ---------- 2. Quality ----------
run_module "2/5 Quality" "
docker-compose run --rm \
    -e HOST_UID=$HOST_UID -e HOST_GID=$HOST_GID \
    quality \
    --input \"/data/processed/$SCENE_ID\" \
    --output \"/data/processed/$SCENE_ID/quality\" \
    --config \"$CONFIG_PATH\"
"

# ---------- 3. Enhance ----------
if [ "$STREAMING_MODE" = "true" ]; then
    run_module "3/5 Enhance (流式模式，使用分割模型)" "
    docker run --rm \
        -v \"$PROJECT_ROOT/produce/output/processed:/data/processed\" \
        -v \"$PROJECT_ROOT/partdata/models:/data/models\" \
        -v \"$PROJECT_ROOT:/workspace\" \
        -w /workspace \
        --entrypoint python \
        workshop-enhance \
        scripts/streaming/run_streaming.py \
            --input \"/data/processed/$SCENE_ID/rgb\" \
            --output \"/data/processed/$SCENE_ID/enhanced\" \
            --model /data/models/yolov8n-seg.pt \
            --config \"$CONFIG_PATH\" \
            --queue-size 30
    "
else
    run_module "3/5 Enhance (传统模式)" "
    docker-compose run --rm \
        -e HOST_UID=$HOST_UID -e HOST_GID=$HOST_GID \
        enhance \
        --input \"/data/processed/$SCENE_ID\" \
        --output \"/data/processed/$SCENE_ID/enhanced\" \
        --config \"$CONFIG_PATH\"
    "
fi

# ---------- 验证 Enhance 输出 ----------
if [ ! -f "$PROCESSED_DIR/$SCENE_ID/enhanced/annotations.json" ]; then
    log_warn "Enhance 未生成 annotations.json，可能使用了检测模型或无检测结果"
fi

# ---------- 4. Calibrate ----------
run_module "4/5 Calibrate" "
docker-compose run --rm \
    -e HOST_UID=$HOST_UID -e HOST_GID=$HOST_GID \
    calibrate \
    --input \"/data/calibration_images\" \
    --output \"/data/processed/$SCENE_ID/calib\" \
    --config \"$CONFIG_PATH\"
"

# ---------- 5. Pack ----------
run_module "5/5 Pack" "
docker-compose run --rm \
    -e HOST_UID=$HOST_UID -e HOST_GID=$HOST_GID \
    pack \
    --input \"/data/processed/$SCENE_ID\" \
    --output \"/data/datasets/$SCENE_ID\" \
    --config \"$CONFIG_PATH\"
"

# ---------- 最终输出 ----------
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
DATASET_SIZE=$(du -sh "$DATASETS_DIR/$SCENE_ID" | cut -f1)
FILE_COUNT=$(find "$DATASETS_DIR/$SCENE_ID" -type f | wc -l)

log_success "========================================="
log_success "✅ 全部完成！用时 $(($ELAPSED/60))分 $(($ELAPSED%60))秒"
log_success "场景 $SCENE_ID 的数据集已存储在: $DATASETS_DIR/$SCENE_ID"
log_success "数据集大小: $DATASET_SIZE，包含 $FILE_COUNT 个文件"
log_success "您可以查看以下关键文件："
log_success "  - 质检报告: $DATASETS_DIR/$SCENE_ID/quality_report.json"
log_success "  - 标注文件: $DATASETS_DIR/$SCENE_ID/annotations.json"
log_success "  - 标定结果: $DATASETS_DIR/$SCENE_ID/intrinsics.json"
log_success "  - 数据清单: $DATASETS_DIR/$SCENE_ID/manifest.json"
log_success "导出数据: ./scripts/utils/export_datasets.sh"
log_success "========================================="