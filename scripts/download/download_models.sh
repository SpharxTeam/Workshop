# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop 模型下载脚本

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
BASE_MODEL_DIR="$PROJECT_ROOT/partdata/models"
DOWNLOAD_LOG="/tmp/download_models.log"

log_info "=== Workshop 模型下载脚本（增强版） ==="
log_info "基础模型目录: $BASE_MODEL_DIR"
ensure_dir "$BASE_MODEL_DIR"

# 定义模型列表（名称 | 版本标签 | 最小大小（字节））
MODELS=(
    "yolov8n.pt|v8.3.0|5000000"
    "yolov8n-seg.pt|v8.3.0|5000000"
)

# 镜像源列表（按优先级）
# 注意：对于 GitHub ZIP，我们使用固定格式：https://github.com/ultralytics/assets/archive/refs/tags/${version}.zip
MIRRORS=(
    "https://github.com"                 # 直连
    "GITHUB_ZIP"                         # 特殊标记，表示尝试下载 ZIP
    "https://mirrors.tuna.tsinghua.edu.cn/github-release/ultralytics/assets"  # 清华源
    "https://mirrors.ustc.edu.cn/github-release/ultralytics/assets"           # 中科大源
    "https://mirrors.bfsu.edu.cn/github-release/ultralytics/assets"           # 北外源
    "https://mirrors.aliyun.com/github-release/ultralytics/assets"            # 阿里云源
)

# 带超时和进度显示的 wget
wget_with_progress() {
    local url=$1
    local output=$2
    wget --progress=dot:giga --timeout=30 --tries=2 -O "$output" "$url" 2>&1 | tee -a "$DOWNLOAD_LOG"
    return ${PIPESTATUS[0]}
}

# 从 GitHub ZIP 包中提取指定模型
extract_from_zip() {
    local zip_file=$1
    local model_name=$2
    local target_dir=$3
    local temp_extract="/tmp/extract_models_$$"
    mkdir -p "$temp_extract"
    
    # 解压 ZIP（假设 ZIP 内目录结构为 assets-版本号/ 或类似）
    unzip -q "$zip_file" -d "$temp_extract"
    
    # 查找模型文件（通常在 assets-<version>/ 下）
    found=$(find "$temp_extract" -name "$model_name" -type f | head -1)
    if [ -n "$found" ]; then
        cp "$found" "$target_dir/$model_name"
        local size=$(wc -c < "$target_dir/$model_name")
        rm -rf "$temp_extract"
        return 0
    fi
    rm -rf "$temp_extract"
    return 1
}

download_model() {
    local model_name="$1"
    local version="$2"
    local min_size="$3"
    local model_dir="$BASE_MODEL_DIR/${model_name%.*}"   # 去掉 .pt 后缀作为子目录
    local target_file="$model_dir/$model_name"
    
    # 创建模型专属目录
    ensure_dir "$model_dir"
    
    # 如果文件已存在且大小合理，则跳过
    if [ -f "$target_file" ]; then
        local actual_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
        if [ "$actual_size" -ge "$min_size" ] 2>/dev/null; then
            log_info "$model_name 已存在于 $model_dir，大小正常（${actual_size} 字节），跳过下载"
            return 0
        else
            log_warn "$model_name 文件不完整（${actual_size} 字节），重新下载"
            rm -f "$target_file"
        fi
    fi

    log_info "开始下载 $model_name (版本 $version) ..."

    # 遍历镜像源
    for mirror in "${MIRRORS[@]}"; do
        local success=0
        local file_size=0
        
        if [ "$mirror" = "GITHUB_ZIP" ]; then
            # 特殊方式：下载整个 release 的 ZIP 包
            local zip_url="https://github.com/ultralytics/assets/archive/refs/tags/${version}.zip"
            local zip_file="/tmp/${version}.zip"
            log_info "尝试从 $zip_url 下载 ZIP 包..."
            if wget_with_progress "$zip_url" "$zip_file"; then
                log_info "ZIP 包下载成功，尝试提取 $model_name ..."
                if extract_from_zip "$zip_file" "$model_name" "$model_dir"; then
                    file_size=$(wc -c < "$target_file")
                    if [ "$file_size" -ge "$min_size" ]; then
                        log_success "从 ZIP 中提取 $model_name 成功（${file_size} 字节）"
                        success=1
                    else
                        log_warn "提取的 $model_name 大小异常（${file_size} 字节），可能不完整"
                        rm -f "$target_file"
                    fi
                else
                    log_warn "在 ZIP 中未找到 $model_name"
                fi
                rm -f "$zip_file"
            else
                log_warn "ZIP 包下载失败"
            fi
        else
            # 普通直连或镜像下载（直接下载 .pt 文件）
            local url
            if [[ "$mirror" == *"github.com"* ]]; then
                # GitHub 直连：使用 release 下载链接
                url="${mirror}/ultralytics/assets/releases/download/${version}/${model_name}"
            else
                # 国内镜像源：使用 github-release 的路径格式
                url="${mirror}/${version}/${model_name}"
            fi
            log_info "尝试从 $url 下载"
            if wget_with_progress "$url" "$target_file"; then
                file_size=$(wc -c < "$target_file" 2>/dev/null || echo 0)
                if [ "$file_size" -ge "$min_size" ]; then
                    log_success "$model_name 下载成功（${file_size} 字节）"
                    success=1
                else
                    log_warn "从 $url 下载的文件过小（${file_size} 字节），可能不完整"
                    rm -f "$target_file"
                fi
            else
                log_warn "从 $url 下载失败"
            fi
        fi

        if [ $success -eq 1 ]; then
            return 0
        fi
        # 继续下一个源
    done

    log_error "所有镜像源均无法成功下载 $model_name"
    return 1
}

main() {
    local overall_success=0
    > "$DOWNLOAD_LOG"  # 清空日志
    
    for entry in "${MODELS[@]}"; do
        IFS='|' read -r name version min_size <<< "$entry"
        if ! download_model "$name" "$version" "$min_size"; then
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