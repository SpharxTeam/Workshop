#!/bin/bash
set -e

# ============================================================================
# Workshop 模型下载脚本（增强版）
# 下载 YOLOv8 模型到 partdata/models/，支持多源重试和完整性校验
# 用法：./scripts/download/download_models.sh
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
MODEL_DIR="$PROJECT_ROOT/partdata/models"

log_info "=== Workshop 模型下载脚本 ==="
log_info "模型将保存到: $MODEL_DIR"
ensure_dir "$MODEL_DIR"

# YOLO 模型信息（版本和大小）
declare -A YOLO_MODELS=(
    ["yolov8n.pt"]="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt|6.2MB"
    ["yolov8s.pt"]="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt|21.5MB"
    ["yolov8m.pt"]="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8m.pt|49.7MB"
    ["yolov8l.pt"]="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8l.pt|81.8MB"
    ["yolov8x.pt"]="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8x.pt|127.5MB"
)

# 镜像源
MIRRORS=(
    "https://github.com"
    "https://hub.fastgit.xyz"
    "https://ghproxy.com/https://github.com"
)

download_model() {
    local model_name="$1"
    local url="$2"
    local expected_size="$3"
    local target_file="$MODEL_DIR/$model_name"

    if [ -f "$target_file" ]; then
        local actual_size
        actual_size=$(du -h "$target_file" | cut -f1)
        if [ "$actual_size" = "$expected_size" ] || [ -n "$(find "$target_file" -size +$(( $(echo "$expected_size" | sed 's/MB//') - 1 ))M)" ]; then
            log_info "$model_name 已存在且大小合理，跳过下载"
            return 0
        else
            log_warn "$model_name 文件不完整，重新下载"
            rm -f "$target_file"
        fi
    fi

    log_info "下载 $model_name ($expected_size) ..."
    for mirror in "${MIRRORS[@]}"; do
        local mirror_url="${mirror}/${url#https://github.com/}"
        log_debug "尝试从 $mirror_url 下载"
        if wget --progress=dot:giga --timeout=30 --tries=3 -O "$target_file" "$mirror_url"; then
            # 验证大小（粗略）
            local downloaded_size
            downloaded_size=$(du -h "$target_file" | cut -f1)
            if [ "$downloaded_size" = "$expected_size" ] || [ -n "$(find "$target_file" -size +$(( $(echo "$expected_size" | sed 's/MB//') - 1 ))M)" ]; then
                log_success "$model_name 下载成功"
                return 0
            else
                log_warn "下载完成但大小异常，可能不完整"
            fi
        fi
    done
    log_error "所有镜像源均无法下载 $model_name"
    return 1
}

# 下载默认模型（yolov8n.pt）
main() {
    local success=0
    for model in "${!YOLO_MODELS[@]}"; do
        IFS='|' read -r url size <<< "${YOLO_MODELS[$model]}"
        # 默认只下载轻量级模型，如需更多可取消注释
        if [ "$model" = "yolov8n.pt" ]; then
            download_model "$model" "$url" "$size" || success=1
        fi
    done

    # 可选：下载所有模型
    if [ "${DOWNLOAD_ALL:-false}" = "true" ]; then
        for model in "${!YOLO_MODELS[@]}"; do
            IFS='|' read -r url size <<< "${YOLO_MODELS[$model]}"
            download_model "$model" "$url" "$size" || success=1
        done
    fi

    if [ $success -eq 0 ]; then
        log_success "模型下载完成"
    else
        log_error "部分模型下载失败"
        exit 1
    fi
}

main "$@"