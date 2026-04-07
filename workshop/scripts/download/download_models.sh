# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop 模型下载脚本

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
BASE_WEIGHT_DIR="$PROJECT_ROOT/partdata/model/weights"
DOWNLOAD_LOG="/tmp/download_models.log"

log_info "=== Workshop 模型下载脚本（稳健版） ==="
log_info "权重将保存到: $BASE_WEIGHT_DIR"
ensure_dir "$BASE_WEIGHT_DIR"

# 定义模型列表（格式：文件名|版本|模型系列|最小大小|备用名称）
# 备用名称用于从镜像源查找，因为镜像源可能使用不同文件名
MODELS=(
    "yolov8n.pt|v8.3.0|yolo|5000000"
    "yolov8n-seg.pt|v8.3.0|yolo|5000000"
)

# 下载源列表（按优先级）
# 每个源是一个 URL 模板，其中 {filename} 和 {version} 会被替换
SOURCES=(
    # GitHub 直连（使用 curl -L 跟随重定向）
    "https://github.com/ultralytics/assets/releases/download/{version}/{filename}"
    # 国内镜像（清华源，已验证路径）
    "https://mirrors.tuna.tsinghua.edu.cn/github-release/ultralytics/assets/{version}/{filename}"
    # 中科大源
    "https://mirrors.ustc.edu.cn/github-release/ultralytics/assets/{version}/{filename}"
    # 北外源
    "https://mirrors.bfsu.edu.cn/github-release/ultralytics/assets/{version}/{filename}"
    # 阿里云源
    "https://mirrors.aliyun.com/github-release/ultralytics/assets/{version}/{filename}"
)

# 使用 curl 下载，带重试和超时
curl_with_retry() {
    local url="$1"
    local output="$2"
    local retries=3
    local timeout=60
    curl -L --connect-timeout 30 --max-time $timeout --retry $retries --retry-delay 5 \
         -o "$output" "$url" 2>&1 | tee -a "$DOWNLOAD_LOG"
    return ${PIPESTATUS[0]}
}

download_model() {
    local filename="$1"
    local version="$2"
    local family="$3"
    local min_size="$4"

    local target_dir="$BASE_WEIGHT_DIR/$family/$version"
    local target_file="$target_dir/$filename"
    ensure_dir "$target_dir"

    # 检查是否已存在且完整
    if [ -f "$target_file" ]; then
        local actual_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
        if [ "$actual_size" -ge "$min_size" ] 2>/dev/null; then
            log_info "$filename 已存在于 $target_dir，大小正常，跳过下载"
            return 0
        else
            log_warn "$filename 不完整（$actual_size 字节），重新下载"
            rm -f "$target_file"
        fi
    fi

    log_info "开始下载 $filename ($family $version) ..."

    local success=0
    for source_template in "${SOURCES[@]}"; do
        # 替换模板中的 {filename} 和 {version}
        url="${source_template//\{filename\}/$filename}"
        url="${url//\{version\}/$version}"
        log_info "尝试从 $url 下载"
        if curl_with_retry "$url" "$target_file"; then
            local downloaded_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
            if [ "$downloaded_size" -ge "$min_size" ]; then
                log_success "下载成功，大小 $downloaded_size 字节"
                success=1
                break
            else
                log_warn "下载文件过小（$downloaded_size 字节），可能不完整"
                rm -f "$target_file"
            fi
        else
            log_warn "从 $url 下载失败"
            rm -f "$target_file" 2>/dev/null
        fi
    done

    if [ $success -eq 0 ]; then
        log_error "所有源均无法成功下载 $filename"
        return 1
    fi

    # 更新 current 软链接
    local current_link="$BASE_WEIGHT_DIR/$family/current"
    ln -snf "$version" "$current_link"
    log_info "更新软链接 $current_link -> $version"

    return 0
}

main() {
    local overall_success=0
    > "$DOWNLOAD_LOG"
    for entry in "${MODELS[@]}"; do
        IFS='|' read -r name version family min_size <<< "$entry"
        if ! download_model "$name" "$version" "$family" "$min_size"; then
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