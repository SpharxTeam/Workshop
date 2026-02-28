#!/bin/bash
set -e
# ============================================================================
# 导出所有数据集从 Docker 命名卷到宿主机目录
# 功能：将 datasets_data 卷中的全部内容复制到宿主机的 ./exports/ 目录
# 用法：./scripts/utils/export_datasets.sh [目标目录]
# 示例：./scripts/utils/export_datasets.sh /mnt/d/exported_data
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/../lib/workshop_common.sh" ]; then
    source "$SCRIPT_DIR/../lib/workshop_common.sh"
else
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
fi

EXPORT_BASE="${1:-$(pwd)/exports}"
EXPORT_DIR="$EXPORT_BASE/datasets_$(date +%Y%m%d_%H%M%S)"

if ! docker volume inspect datasets_data &>/dev/null; then
    log_error "Docker 卷 datasets_data 不存在，请先运行流水线生成数据。"
    exit 1
fi

mkdir -p "$EXPORT_DIR"
log_info "导出目标目录: $EXPORT_DIR"

log_info "正在从卷 datasets_data 复制数据..."
if docker run --rm \
    -v datasets_data:/source:ro \
    -v "$EXPORT_DIR":/target \
    alpine \
    sh -c "cp -av /source/. /target/"; then
    log_success "数据已成功导出到: $EXPORT_DIR"
    log_info "目录内容："
    ls -la "$EXPORT_DIR"
else
    log_error "导出过程中发生错误"
    exit 1
fi