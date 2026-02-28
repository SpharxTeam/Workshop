#!/bin/bash
set -e
# ============================================================================
# 依赖下载脚本（最终版）
# 功能：为所有模块下载 Python 依赖包，支持多镜像源、自动重试、降级源码
# 用法：./scripts/download/download_deps.sh [--clean]
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
DEPS_DIR="$PROJECT_ROOT/partdata/deps"
TEMP_DIR="/tmp/workshop_deps_$$"

log_info "=== 开始下载所有模块依赖 ==="
ensure_dir "$DEPS_DIR"
ensure_dir "$TEMP_DIR"

REQUIREMENT_FILES=(
    "$PROJECT_ROOT/pipelines/00_ingest/requirements.txt"
    "$PROJECT_ROOT/pipelines/01_quality/requirements.txt"
    "$PROJECT_ROOT/pipelines/02_enhance/requirements.txt"
    "$PROJECT_ROOT/pipelines/03_calibrate/requirements.txt"
    "$PROJECT_ROOT/pipelines/04_pack/requirements.txt"
    "$PROJECT_ROOT/pipelines/05_delivery/requirements.txt"
)

PIP_INDEX_URLS=(
    "https://pypi.org/simple"
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.ustc.edu.cn/pypi/web/simple"
    "https://mirrors.bfsu.edu.cn/pypi/web/simple"
    "https://mirrors.aliyun.com/pypi/simple"
)

download_req() {
    local req_file="$1"
    local temp_dir="$2"
    local max_retries=3
    local retry_delay=5
    local timeout_seconds=600

    if [ ! -s "$req_file" ]; then
        log_info "文件 $(basename "$req_file") 为空，跳过下载"
        return 0
    fi

    log_info "处理: $(basename "$req_file")"

    # 尝试 wheel 模式
    local wheel_success=0
    for index_url in "${PIP_INDEX_URLS[@]}"; do
        log_info "尝试镜像源 (wheel模式): $index_url"
        local attempt=1
        while [ $attempt -le $max_retries ]; do
            log_info "  第 $attempt 次尝试（最大 $max_retries），超时 ${timeout_seconds}s..."
            if timeout "$timeout_seconds" pip download \
                -r "$req_file" \
                -d "$temp_dir" \
                --no-cache-dir \
                --retries 2 \
                --timeout 60 \
                --index-url "$index_url" \
                --python-version 3.10 \
                --platform manylinux2014_x86_64 \
                --implementation cp \
                --abi cp310 \
                --only-binary=:all: \
                -v 2>&1 | tee -a /tmp/pip_download.log; then
                log_success "从 $index_url (wheel模式) 下载成功"
                wheel_success=1
                break 2
            else
                log_warn "下载失败，$retry_delay 秒后重试..."
                sleep $retry_delay
                attempt=$((attempt + 1))
            fi
        done
    done

    if [ $wheel_success -eq 1 ]; then
        return 0
    fi

    log_warn "wheel 模式全部失败，尝试源码模式（无平台约束）..."

    for index_url in "${PIP_INDEX_URLS[@]}"; do
        log_info "尝试镜像源 (源码模式): $index_url"
        local attempt=1
        while [ $attempt -le $max_retries ]; do
            log_info "  第 $attempt 次尝试（最大 $max_retries），超时 ${timeout_seconds}s..."
            if timeout "$timeout_seconds" pip download \
                -r "$req_file" \
                -d "$temp_dir" \
                --no-cache-dir \
                --retries 2 \
                --timeout 60 \
                --index-url "$index_url" \
                -v 2>&1 | tee -a /tmp/pip_download.log; then
                log_success "从 $index_url (源码模式) 下载成功"
                return 0
            else
                log_warn "下载失败，$retry_delay 秒后重试..."
                sleep $retry_delay
                attempt=$((attempt + 1))
            fi
        done
    done

    log_error "所有镜像源均无法下载 $(basename "$req_file") 的依赖"
    return 1
}

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
    if [[ "$1" == "--clean" ]]; then
        log_info "清空现有依赖目录 $DEPS_DIR"
        rm -rf "$DEPS_DIR"/*
    fi

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

    find "$TEMP_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) -exec cp -n {} "$DEPS_DIR" \;
    cp "$TEMP_DIR/requirements.txt" "$DEPS_DIR/requirements.txt" 2>/dev/null || true

    rm -rf "$TEMP_DIR"

    if [ $failed -eq 0 ]; then
        log_success "所有依赖下载完成，保存在 $DEPS_DIR"
    else
        log_error "部分依赖下载失败，请检查网络后重试"
        exit 1
    fi
}

main "$@"