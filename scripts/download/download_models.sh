# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# Workshop 模型下载脚本（最终修复版）
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 加载公共函数库
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
MODEL_DIR="$PROJECT_ROOT/partdata/models"

log_info "=== Workshop 模型下载脚本 ==="
log_info "模型将保存到: $MODEL_DIR"
ensure_dir "$MODEL_DIR"

# 定义模型信息（名称 | 预期最小大小字节）
MODEL_NAME="yolov8n.pt"
EXPECTED_MIN_SIZE=6000000  # 约 6MB

# 定义多个下载源 URL（按优先级排序）
DOWNLOAD_URLS=(
    "https://mirrors.tuna.tsinghua.edu.cn/github-release/ultralytics/assets/v8.3.0/yolov8n.pt"
    "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    "https://hub.fastgit.xyz/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    "https://ghproxy.com/https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    "https://download.fastgit.org/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
)

download_model() {
    local target_file="$MODEL_DIR/$MODEL_NAME"

    # 如果文件已存在且大小合理，则跳过
    if [ -f "$target_file" ]; then
        local actual_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
        if [ "$actual_size" -ge "$EXPECTED_MIN_SIZE" ] 2>/dev/null; then
            log_info "$MODEL_NAME 已存在且大小正常（${actual_size} 字节），跳过下载"
            return 0
        else
            log_warn "$MODEL_NAME 文件不完整（${actual_size} 字节），重新下载"
            rm -f "$target_file"
        fi
    fi

    log_info "开始下载 $MODEL_NAME ..."

    for url in "${DOWNLOAD_URLS[@]}"; do
        log_info "尝试从 $url 下载"
        # 使用 wget 下载，显示进度，超时 30 秒，重试 2 次
        if wget --progress=dot:giga --timeout=30 --tries=2 -O "$target_file" "$url"; then
            local downloaded_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
            if [ "$downloaded_size" -ge "$EXPECTED_MIN_SIZE" ] 2>/dev/null; then
                log_success "$MODEL_NAME 下载成功（${downloaded_size} 字节）"
                return 0
            else
                log_warn "下载文件过小（${downloaded_size} 字节），可能不完整"
                rm -f "$target_file"
            fi
        else
            log_warn "从 $url 下载失败，尝试下一个源"
            rm -f "$target_file" 2>/dev/null
        fi
    done

    log_error "所有下载源均无法成功下载 $MODEL_NAME"
    return 1
}

# 执行下载
if download_model; then
    log_success "模型下载完成"
else
    log_error "模型下载失败，请检查网络或手动下载"
    exit 1
fi