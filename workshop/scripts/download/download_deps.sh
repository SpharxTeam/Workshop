# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 依赖下载脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
DEPS_DIR="$PROJECT_ROOT/partdata/deps"
TEMP_DIR="/tmp/workshop_deps_$$"

log_info "=== 开始下载所有模块依赖 ==="
ensure_dir "$DEPS_DIR"
ensure_dir "$TEMP_DIR"

REQUIREMENT_FILES=(
    "$PROJECT_ROOT/pipelines/run_00_ingest/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_01_quality/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_02_enhance/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_03_calibrate/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_04_pack/requirements.txt"
    "$PROJECT_ROOT/pipelines/run_05_delivery/requirements.txt"
)

PIP_INDEX_URLS=(
    "https://pypi.org/simple"
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.ustc.edu.cn/pypi/web/simple"
    "https://mirrors.bfsu.edu.cn/pypi/web/simple"
    "https://mirrors.aliyun.com/pypi/simple"
)

# 合并 requirements
merge_requirements() {
    local temp_req="$TEMP_DIR/requirements_all.txt"
    > "$temp_req"
    for f in "${REQUIREMENT_FILES[@]}"; do
        if [ -f "$f" ] && [ -s "$f" ]; then
            grep -v '^\s*#' "$f" | grep -v '^\s*$' >> "$temp_req" || true
        fi
    done
    sort -u "$temp_req" > "$TEMP_DIR/requirements.txt"
    local line_count=$(wc -l < "$TEMP_DIR/requirements.txt")
    log_info "合并后的 requirements.txt 已生成，共 $line_count 行"
    if [ $line_count -eq 0 ]; then
        log_error "合并后无任何依赖项，请检查各模块 requirements.txt"
        exit 1
    fi
}

# 尝试下载（先 wheel 模式，失败则源码模式）
try_download() {
    local index_url="$1"
    local wheel_opts="--python-version 3.10 --platform manylinux2014_x86_64 --implementation cp --abi cp310 --only-binary=:all:"
    local src_opts=""  # 源码模式无平台限制

    log_info "尝试从 $index_url 下载 (wheel 模式，Python 3.10)..."
    if pip download -r "$TEMP_DIR/requirements.txt" -d "$TEMP_DIR" --no-cache-dir --retries 3 --timeout 60 --index-url "$index_url" $wheel_opts -v 2>&1 | tee -a /tmp/pip_download.log; then
        log_success "wheel 模式下载成功"
        return 0
    fi

    log_warn "wheel 模式失败，尝试源码模式..."
    if pip download -r "$TEMP_DIR/requirements.txt" -d "$TEMP_DIR" --no-cache-dir --retries 3 --timeout 60 --index-url "$index_url" $src_opts -v 2>&1 | tee -a /tmp/pip_download.log; then
        log_success "源码模式下载成功"
        return 0
    fi

    return 1
}

# 检查是否所有包都已下载
check_all_downloaded() {
    local missing=0
    while IFS= read -r line; do
        pkg=$(echo "$line" | sed 's/[>=<].*//' | tr -d ' ')
        if ! find "$TEMP_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) | grep -qi "$pkg"; then
            log_warn "缺少包: $pkg"
            missing=1
        fi
    done < "$TEMP_DIR/requirements.txt"
    return $missing
}

main() {
    if [[ "$1" == "--clean" ]]; then
        log_info "清空现有依赖目录 $DEPS_DIR"
        rm -rf "$DEPS_DIR"/*
    fi

    merge_requirements

    local success=0
    for url in "${PIP_INDEX_URLS[@]}"; do
        if try_download "$url"; then
            if check_all_downloaded; then
                success=1
                break
            else
                log_warn "从 $url 下载后仍有缺失，尝试下一个源"
            fi
        fi
        # 不清空临时目录，继续累积
    done

    if [ $success -eq 0 ]; then
        log_error "所有镜像源均无法下载完整的依赖包"
        exit 1
    fi

    log_info "复制依赖文件到 $DEPS_DIR ..."
    find "$TEMP_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) -exec cp -v {} "$DEPS_DIR" \;
    cp "$TEMP_DIR/requirements.txt" "$DEPS_DIR/requirements.txt"

    log_info "依赖文件列表："
    ls -lh "$DEPS_DIR"
    rm -rf "$TEMP_DIR"
    log_success "所有依赖下载完成，保存在 $DEPS_DIR"
}

main "$@"