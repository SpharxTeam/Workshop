# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# workshop 完整数据采集流水线运行脚本（最终版）
# 统一使用 docker-compose 操作卷，避免卷名混乱
# 用法：./scripts/pipeline/run_full.sh [选项] <宿主机bag路径> [场景ID]
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载公共函数库
if [ -f "$SCRIPT_DIR/../lib/workshop_common.sh" ]; then
    source "$SCRIPT_DIR/../lib/workshop_common.sh"
else
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
    log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
fi

show_help() {
    echo "用法: $0 [选项] <宿主机bag路径> [场景ID]"
    echo ""
    echo "选项:"
    echo "  --config CONFIG_PATH   指定配置文件路径（默认 /configs/pipeline_config.yaml）"
    echo "  -h, --help             显示帮助信息"
    exit 0
}

# 默认值
HOST_BAG_PATH=""
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
            if [ -z "$HOST_BAG_PATH" ]; then
                HOST_BAG_PATH="$1"
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

if [ -z "$HOST_BAG_PATH" ]; then
    log_error "请指定宿主机 bag 文件路径"
    show_help
    exit 1
fi

if [ ! -f "$HOST_BAG_PATH" ]; then
    log_error "宿主机 bag 文件不存在: $HOST_BAG_PATH"
    exit 1
fi

# 提取文件名，构建容器内路径
BAG_FILENAME=$(basename "$HOST_BAG_PATH")
CONTAINER_BAG_PATH="/data/raw/$BAG_FILENAME"

# 生成场景 ID（如果未指定）
if [ -z "$SCENE_ID" ]; then
    SCENE_ID="scene_$(date +%Y%m%d_%H%M%S)"
fi

export SCENE_ID

# 检查 docker 和 docker-compose
check_command docker
check_command docker-compose

# 确保必要的 Docker 命名卷存在（通过 docker-compose 自动创建）
log_info "确保 Docker 命名卷存在（由 docker-compose 自动创建）..."
docker-compose up --no-start 2>/dev/null || true

# 修正挂载点权限（使用 docker-compose run 临时容器）
log_info "修正挂载点权限，确保 appuser 可写入..."
docker-compose run --rm --user root --entrypoint sh ingest -c "chown 1000:1000 /data/processed /data/datasets /data/calibration_images 2>/dev/null || true"

# 检查标定图像卷是否为空，若空则生成默认棋盘格图像
log_info "检查标定图像卷内容..."
CALIB_IMG_COUNT=$(docker-compose run --rm --entrypoint sh alpine -c "ls -1 /data/calibration_images 2>/dev/null | wc -l" 2>/dev/null || echo 0)
if [ "$CALIB_IMG_COUNT" -eq 0 ]; then
    log_warn "标定图像卷为空，正在生成棋盘格图像（约 20 张）..."
    docker-compose run --rm \
        -v "$PROJECT_ROOT:/workspace" \
        --entrypoint python \
        workshop-base \
        /workspace/scripts/utils/generate_realistic_calibration.py --output /data/calibration_images
    log_success "标定图像生成完成"
else
    log_info "标定图像卷已存在 $CALIB_IMG_COUNT 个文件，跳过生成"
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
log_info "中间数据卷: processed_data (由 docker-compose 管理)"
log_info "最终数据集卷: datasets_data (由 docker-compose 管理)"
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

# 验证 Ingest 输出（使用 ingest 容器，确保访问正确卷）
log_info "验证 Ingest 输出..."
if docker-compose run --rm --entrypoint sh ingest -c "test -d /data/processed/$SCENE_ID"; then
    log_success "场景目录 /data/processed/$SCENE_ID 存在"
    FILE_SIZE=$(docker-compose run --rm --entrypoint sh ingest -c "stat -c%s /data/processed/$SCENE_ID/rgb.mp4 2>/dev/null || echo 0")
    if [ "$FILE_SIZE" -gt 1024 ]; then
        log_success "rgb.mp4 存在，大小: ${FILE_SIZE} 字节"
    else
        log_error "rgb.mp4 不存在或大小异常 (${FILE_SIZE} 字节)"
        exit 1
    fi
else
    log_error "场景目录 /data/processed/$SCENE_ID 不存在"
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
log_success "场景 $SCENE_ID 的数据集已存储在 Docker 卷中（由 docker-compose 管理）。"
log_success "您可以通过以下命令查看或导出数据："
log_success "  docker-compose run --rm --entrypoint ls alpine /data/datasets/$SCENE_ID"
log_success "  ./scripts/utils/export_datasets.sh  # 导出所有数据集到 ./exports/"
log_success "========================================="