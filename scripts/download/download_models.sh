# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# Workshop 模型下载脚本（最终修复版）
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
MODEL_DIR="$PROJECT_ROOT/partdata/models"

log_info "=== Workshop 模型下载脚本 ==="
log_info "模型将保存到: $MODEL_DIR"
ensure_dir "$MODEL_DIR"

YOLO_MODELS=(
    "yolov8n.pt|https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt|6000000"
)

MIRRORS=(
    "https://github.com"
    "https://hub.fastgit.xyz"
    "https://ghproxy.com/https://github.com"
    "https://download.fastgit.org"
)

download_model() {
    local model_name="$1"
    local official_url="$2"
    local min_size="$3"
    local target_file="$MODEL_DIR/$model_name"

    if [ -f "$target_file" ]; then
        local actual_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
        if [ "$actual_size" -ge "$min_size" ] 2>/dev/null; then
            log_info "$model_name 已存在且大小正常（${actual_size} 字节），跳过下载"
            return 0
        else
            log_warn "$model_name 文件不完整（${actual_size} 字节），重新下载"
            rm -f "$target_file"
        fi
    fi

    log_info "下载 $model_name ..."
    for mirror in "${MIRRORS[@]}"; do
        local mirror_url="${mirror}/${official_url#https://github.com/}"
        log_info "尝试从 $mirror_url 下载"
        if wget --progress=dot:giga --timeout=30 --tries=3 -O "$target_file" "$mirror_url"; then
            local downloaded_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
            if [ "$downloaded_size" -ge "$min_size" ] 2>/dev/null; then
                log_success "$model_name 下载成功（${downloaded_size} 字节）"
                return 0
            else
                log_warn "下载文件过小（${downloaded_size} 字节），可能不完整"
                rm -f "$target_file"
            fi
        else
            log_warn "下载失败，尝试下一个镜像"
        fi
    done

    log_error "所有镜像源均无法下载 $model_name"
    return 1
}

main() {
    local success=0
    for entry in "${YOLO_MODELS[@]}"; do
        IFS='|' read -r name url min_size <<< "$entry"
        if ! download_model "$name" "$url" "$min_size"; then
            success=1
        fi
    done

    if [ $success -eq 0 ]; then
        log_success "所有模型下载完成"
    else
        log_error "模型下载失败"
        exit 1
    fi
}

main "$@"