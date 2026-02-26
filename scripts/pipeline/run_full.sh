#!/bin/bash
set -e
# ============================================================================
# workshop 完整数据采集流水线运行脚本
# 按顺序执行 ingest → quality → enhance → calibrate → pack
# 用法：./scripts/pipeline/run_full.sh [选项] [bag路径]
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

show_help() {
    echo "用法: $0 [选项] [bag路径]"
    echo ""
    echo "选项:"
    echo "  --config CONFIG_PATH   指定配置文件路径（默认 /configs/pipeline_config.yaml）"
    echo "  -h, --help             显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 /partdata/raw/sample.bag"
    echo "  $0 --config /configs/my_config.yaml /partdata/raw/sample.bag"
}

# 默认值
BAG_PATH=""
CONFIG_PATH="/configs/pipeline_config.yaml"
PROJECT_ROOT="$(get_project_root)"
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
            exit 0
            ;;
        *)
            if [ -z "$BAG_PATH" ]; then
                BAG_PATH="$1"
                shift
            else
                log_error "未知参数: $1"
                show_help
                exit 1
            fi
            ;;
    esac
done

# 检查 docker-compose
check_command docker

if [ -z "$BAG_PATH" ]; then
    BAG_PATH="/partdata/raw/sample.bag"
    log_warn "未指定 bag 路径，使用默认值: $BAG_PATH"
fi

SCENE_ID="scene_$(date +%Y%m%d_%H%M%S)"

log_info "========================================="
log_info "开始处理场景: $SCENE_ID"
log_info "输入 bag: $BAG_PATH"
log_info "配置文件: $CONFIG_PATH"
log_info "========================================="

# 1. Ingest
log_info "[1/5] 运行 ingest ..."
docker-compose run --rm ingest \
    --input "$BAG_PATH" \
    --output "/partdata/processed/$SCENE_ID" \
    --config "$CONFIG_PATH" || { log_error "Ingest 失败"; exit 1; }

# 2. Quality
log_info "[2/5] 运行 quality ..."
docker-compose run --rm quality \
    --input "/partdata/processed/$SCENE_ID" \
    --output "/partdata/processed/$SCENE_ID/quality" \
    --config "$CONFIG_PATH" || { log_error "Quality 失败"; exit 1; }

# 3. Enhance
log_info "[3/5] 运行 enhance ..."
docker-compose run --rm enhance \
    --input "/partdata/processed/$SCENE_ID" \
    --output "/partdata/processed/$SCENE_ID/enhanced" \
    --config "$CONFIG_PATH" || { log_error "Enhance 失败"; exit 1; }

# 4. Calibrate
log_info "[4/5] 运行 calibrate ..."
docker-compose run --rm calibrate \
    --input "/partdata/calibration_images" \
    --output "/partdata/processed/$SCENE_ID/calib" \
    --config "$CONFIG_PATH" || { log_error "Calibrate 失败"; exit 1; }

# 5. Pack
log_info "[5/5] 运行 pack ..."
docker-compose run --rm pack \
    --input "/partdata/processed/$SCENE_ID" \
    --output "/partdata/datasets/$SCENE_ID" \
    --config "$CONFIG_PATH" || { log_error "Pack 失败"; exit 1; }

log_success "========================================="
log_success "✅ 全部完成！数据集位于: /partdata/datasets/$SCENE_ID"
log_success "========================================="