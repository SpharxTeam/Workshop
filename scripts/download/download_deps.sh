#!/bin/bash
set -e
# ============================================================================
# 依赖下载脚本
# 功能：为所有模块下载 Python 3.10 的 wheel 包到 partdata/deps，用于离线安装
# 支持多镜像源、自动重试，确保网络容错
# 用法：./scripts/download/download_deps.sh
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
DEPS_DIR="$PROJECT_ROOT/partdata/deps"
TEMP_DIR="/tmp/workshop_deps_$$"

log_info "=== 开始下载所有模块依赖 ==="
ensure_dir "$DEPS_DIR"
ensure_dir "$TEMP_DIR"

# 定义所有 requirements.txt 路径
REQUIREMENT_FILES=(
    "$PROJECT_ROOT/pipelines/00_ingest/requirements.txt"
    "$PROJECT_ROOT/pipelines/01_quality/requirements.txt"
    "$PROJECT_ROOT/pipelines/02_enhance/requirements.txt"
    "$PROJECT_ROOT/pipelines/03_calibrate/requirements.txt"
    "$PROJECT_ROOT/pipelines/04_pack/requirements.txt"
    "$PROJECT_ROOT/pipelines/05_delivery/requirements.txt"
)

# 镜像源列表（按优先级）
PIP_INDEX_URLS=(
    "https://pypi.org/simple"
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.aliyun.com/pypi/simple"
)

# 下载单个 requirements 文件
download_req() {
    local req_file="$1"
    local temp_dir="$2"
    local max_retries=3
    local retry_delay=5

    if [ ! -s "$req_file" ]; then
        log_info "文件 $(basename "$req_file") 为空，跳过下载"
        return 0
    fi

    log_info "处理: $(basename "$req_file")"

    for index_url in "${PIP_INDEX_URLS[@]}"; do
        log_info "尝试镜像源: $index_url"
        local attempt=1
        while [ $attempt -le $max_retries ]; do
            log_info "  第 $attempt 次尝试（最大 $max_retries）..."
            if pip download \
                -r "$req_file" \
                -d "$temp_dir" \
                --no-cache-dir \
                --retries 5 \
                --timeout 60 \
                --index-url "$index_url" \
                --python-version 3.10 \
                --platform manylinux2014_x86_64 \
                --implementation cp \
                --abi cp310 \
                -v 2>&1 | tee -a /tmp/pip_download.log; then
                log_success "从 $index_url 下载成功"
                return 0
            else
                log_warn "下载失败，$retry_delay 秒后重试..."
                sleep $retry_delay
                attempt=$((attempt + 1))
            fi
        done
        log_warn "镜像源 $index_url 多次尝试失败，切换到下一个"
    done

    log_error "所有镜像源均无法下载 $(basename "$req_file") 的依赖"
    return 1
}

# 合并所有 requirements 以生成离线安装清单
merge_requirements() {
    local temp_req="$TEMP_DIR/requirements_all.txt"
    > "$temp_req"
    for f in "${REQUIREMENT_FILES[@]}"; do
        if [ -f "$f" ] && [ -s "$f" ]; then
            cat "$f" >> "$temp_req"
        fi
    done
    sort -u "$temp_req" > "$TEMP_DIR/requirements.txt"
    log_info "合并后的 requirements.txt 已生成，共 $(wc -l < "$TEMP_DIR/requirements.txt") 行"
}

main() {
    merge_requirements

    local failed=0
    for f in "${REQUIREMENT_FILES[@]}"; do
        if [ -f "$f" ]; then
            if ! download_req "$f" "$TEMP_DIR"; then
                log_error "下载 $(basename "$f") 失败"
                failed=1
            fi
        else
            log_warn "文件不存在，跳过: $f"
        fi
    done

    # 将所有 wheel 复制到 DEPS_DIR（不覆盖已有文件）
    find "$TEMP_DIR" -name "*.whl" -exec cp -n {} "$DEPS_DIR" \;
    cp "$TEMP_DIR/requirements.txt" "$DEPS_DIR/requirements.txt"

    rm -rf "$TEMP_DIR"

    if [ $failed -eq 0 ]; then
        log_success "所有依赖下载完成，保存在 $DEPS_DIR"
    else
        log_error "部分依赖下载失败，请检查网络后重试"
        exit 1
    fi
}

main "$@"