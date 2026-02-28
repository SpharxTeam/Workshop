# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# 导出所有数据集从 Docker 命名卷到宿主机目录
# 统一使用 docker-compose 管理卷
# ============================================================================

set -e

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

# 进入项目目录，确保 docker-compose 能找到正确配置
cd "$(dirname "$SCRIPT_DIR")/.."

# 检查卷是否存在
if ! docker-compose run --rm --entrypoint sh alpine -c "ls -d /data/datasets 2>/dev/null" >/dev/null; then
    log_error "Docker 卷 datasets_data 不可用，请先运行流水线生成数据。"
    exit 1
fi

mkdir -p "$EXPORT_DIR"
log_info "导出目标目录: $EXPORT_DIR"

log_info "正在从卷 datasets_data 复制数据..."
# 使用临时容器复制数据
if docker-compose run --rm --entrypoint sh alpine -c "cp -av /data/datasets/. /exports/" >/dev/null; then
    log_success "数据已成功导出到: $EXPORT_DIR"
    log_info "目录内容："
    ls -la "$EXPORT_DIR"
else
    log_error "导出过程中发生错误"
    exit 1
fi