# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 依赖下载脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
DEPS_DIR="$PROJECT_ROOT/partdata/deps"
TEMP_DIR="/tmp/workshop_deps_$$"
REQUIREMENTS_TXT="$TEMP_DIR/requirements.txt"

log_info "=== 开始下载所有模块依赖 ==="
ensure_dir "$DEPS_DIR"
ensure_dir "$TEMP_DIR"

# 定义所有 requirements.txt 路径
REQUIREMENT_FILES=(
    "$PROJECT_ROOT/pipelines/run_00_ingest/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_01_quality/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_02_enhance/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_03_calibrate/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_04_pack/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_05_delivery/requirements.txt"
)

# 镜像源列表（按优先级）
PIP_INDEX_URLS=(
    "https://pypi.org/simple"
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.ustc.edu.cn/pypi/web/simple"
    "https://mirrors.bfsu.edu.cn/pypi/web/simple"
    "https://mirrors.aliyun.com/pypi/simple"
)

# 合并所有 requirements 到一个文件，并去重
merge_requirements() {
    local temp_req="$TEMP_DIR/requirements_all.txt"
    > "$temp_req"
    for f in "${REQUIREMENT_FILES[@]}"; do
        if [ -f "$f" ] && [ -s "$f" ]; then
            grep -v '^\s*#' "$f" | grep -v '^\s*$' >> "$temp_req" || true
        fi
    done
    sort -u "$temp_req" > "$REQUIREMENTS_TXT"
    local line_count=$(wc -l < "$REQUIREMENTS_TXT")
    log_info "合并后的 requirements.txt 已生成，共 $line_count 行"
    if [ $line_count -eq 0 ]; then
        log_error "合并后无任何依赖项，请检查各模块 requirements.txt"
        exit 1
    fi
    cat "$REQUIREMENTS_TXT"
}

# 从指定源下载缺失的包
download_from_source() {
    local index_url="$1"
    local log_file="/tmp/pip_download_$$.log"
    
    log_info "尝试从 $index_url 下载缺失的包..."
    # 使用 pip download，如果已有包则跳过
    if pip download \
        -r "$REQUIREMENTS_TXT" \
        -d "$TEMP_DIR" \
        --no-cache-dir \
        --retries 3 \
        --timeout 60 \
        --index-url "$index_url" \
        -v 2>&1 | tee -a "$log_file"; then
        log_success "从 $index_url 下载成功"
        return 0
    else
        log_warn "从 $index_url 下载失败，查看日志: $log_file"
        return 1
    fi
}

# 检查是否所有包都已下载（通过检查 requirements.txt 中的包名是否在 TEMP_DIR 中存在对应的 wheel/源码）
check_all_downloaded() {
    local req_file="$REQUIREMENTS_TXT"
    local missing=0
    while IFS= read -r line; do
        # 提取包名（简单处理，忽略版本）
        pkg=$(echo "$line" | sed 's/[>=<].*//' | tr -d ' ')
        # 在 TEMP_DIR 中搜索包含该包名的文件
        if ! find "$TEMP_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) | grep -qi "$pkg"; then
            log_warn "缺少包: $pkg"
            missing=1
        fi
    done < "$req_file"
    
    if [ $missing -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

main() {
    if [[ "$1" == "--clean" ]]; then
        log_info "清空现有依赖目录 $DEPS_DIR"
        rm -rf "$DEPS_DIR"/*
    fi

    merge_requirements

    # 如果 TEMP_DIR 已有文件，先尝试检查是否完整
    if [ -n "$(ls -A "$TEMP_DIR" 2>/dev/null)" ]; then
        if check_all_downloaded; then
            log_info "临时目录已存在完整依赖，跳过下载"
        else
            log_warn "临时目录存在但不完整，继续下载缺失包"
        fi
    fi

    local success=0
    for url in "${PIP_INDEX_URLS[@]}"; do
        if download_from_source "$url"; then
            if check_all_downloaded; then
                success=1
                break
            else
                log_warn "从 $url 下载后仍有缺失，尝试下一个源"
            fi
        fi
        # 不清空 TEMP_DIR，继续尝试下一个源
    done

    if [ $success -eq 0 ]; then
        log_error "所有镜像源均无法下载完整的依赖包"
        exit 1
    fi

    # 将所有下载的文件复制到 DEPS_DIR
    log_info "复制依赖文件到 $DEPS_DIR ..."
    find "$TEMP_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) -exec cp -v {} "$DEPS_DIR" \;
    cp "$REQUIREMENTS_TXT" "$DEPS_DIR/requirements.txt"

    log_info "依赖文件列表："
    ls -lh "$DEPS_DIR"

    rm -rf "$TEMP_DIR"

    log_success "所有依赖下载完成，保存在 $DEPS_DIR"
}

main "$@"