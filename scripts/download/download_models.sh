# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop 模型下载脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 加载公共函数库
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
MODEL_DIR="$PROJECT_ROOT/partdata/models"

log_info "=== Workshop 模型下载脚本（完整版） ==="
log_info "模型将保存到: $MODEL_DIR"
ensure_dir "$MODEL_DIR"

# 定义模型列表（名称 | 版本标签 | 最小大小（字节））
# 版本标签可随时更新，URL 中的版本号将替换为 ${version}
MODELS=(
    "yolov8n.pt|v8.3.0|5000000"
    "yolov8n-seg.pt|v8.3.0|5000000"
)

# 镜像源列表（按优先级）
# 构造方式：镜像源 + "/ultralytics/assets/releases/download/${version}/${model_name}"
MIRRORS=(
    "https://mirrors.tuna.tsinghua.edu.cn/github-release"
    "https://github.com"
    "https://hub.fastgit.xyz"
    "https://ghproxy.com/https://github.com"
    "https://download.fastgit.org"
)

# 下载单个模型
download_model() {
    local model_name="$1"
    local version="$2"
    local min_size="$3"
    local target_file="$MODEL_DIR/$model_name"

    # 如果文件已存在且大小大于最小要求，则跳过
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

    log_info "开始下载 $model_name (版本 $version) ..."

    # 遍历镜像源
    for mirror in "${MIRRORS[@]}"; do
        # 构造下载 URL
        # 注意：清华源的路径为 /github-release/ultralytics/assets/${version}/${model_name}
        # GitHub 官方路径为 /ultralytics/assets/releases/download/${version}/${model_name}
        # 需要根据镜像特点调整，但多数镜像直接拼接即可。
        # 这里采用统一拼接：${mirror}/ultralytics/assets/releases/download/${version}/${model_name}
        # 但清华源需要特殊处理，因为它使用了 /github-release/ 结构
        if [[ "$mirror" == *"tuna"* ]]; then
            url="${mirror}/ultralytics/assets/${version}/${model_name}"
        else
            url="${mirror}/ultralytics/assets/releases/download/${version}/${model_name}"
        fi

        log_info "尝试从 $url 下载"
        # 使用 wget 下载，显示进度，超时 30 秒，重试 2 次
        if wget --progress=dot:giga --timeout=30 --tries=2 -O "$target_file" "$url"; then
            local downloaded_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
            if [ "$downloaded_size" -ge "$min_size" ] 2>/dev/null; then
                log_success "$model_name 下载成功（${downloaded_size} 字节）"
                return 0
            else
                log_warn "从 $url 下载的文件过小（${downloaded_size} 字节），可能不完整"
                rm -f "$target_file"
            fi
        else
            log_warn "从 $url 下载失败，尝试下一个镜像"
            rm -f "$target_file" 2>/dev/null
        fi
    done

    log_error "所有镜像源均无法成功下载 $model_name"
    return 1
}

# 主循环：下载所有模型
main() {
    local overall_success=0
    for entry in "${MODELS[@]}"; do
        IFS='|' read -r name version min_size <<< "$entry"
        if ! download_model "$name" "$version" "$min_size"; then
            log_error "模型 $name 下载失败"
            overall_success=1
        fi
    done

    if [ $overall_success -eq 0 ]; then
        log_success "所有模型下载完成"
    else
        log_error "部分模型下载失败，请检查网络或手动下载"
        exit 1
    fi
}

main "$@"