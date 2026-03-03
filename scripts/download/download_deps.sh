# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 依赖下载脚本
# 功能：合并所有 requirements.txt，使用多源重试下载所有依赖包
# 用法：./scripts/download/download_deps.sh [--clean]
# 此脚本已废弃，因为改为在线安装。保留为空避免错误。

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
DEPS_DIR="$PROJECT_ROOT/partdata/deps"
TEMP_DIR="/tmp/workshop_deps_$$"

log_info "=== 开始下载所有模块依赖 ==="
ensure_dir "$DEPS_DIR"
ensure_dir "$TEMP_DIR"

# 定义所有 requirements.txt 路径（已更新为新目录名）
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

# 下载单个 requirements 文件（无平台约束）
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

    for index_url in "${PIP_INDEX_URLS[@]}"; do
        log_info "尝试镜像源: $index_url"
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
                log_success "从 $index_url 下载成功"
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

# 合并所有 requirements 以生成离线安装清单（用于记录）
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

    # 复制所有下载的文件（wheel、源码包）到 DEPS_DIR，并显示详细信息
    log_info "复制依赖文件到 $DEPS_DIR ..."
    find "$TEMP_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) -exec cp -v {} "$DEPS_DIR" \;

    # 同时复制合并的 requirements.txt 用于记录
    cp "$TEMP_DIR/requirements.txt" "$DEPS_DIR/requirements.txt" 2>/dev/null || true

    # 验证关键包是否存在（可选）
    log_info "验证依赖文件列表："
    ls -lh "$DEPS_DIR" | head -20

    rm -rf "$TEMP_DIR"

    if [ $failed -eq 0 ]; then
        log_success "所有依赖下载完成，保存在 $DEPS_DIR"
    else
        log_error "部分依赖下载失败，请检查网络后重试"
        exit 1
    fi
}

main "$@"