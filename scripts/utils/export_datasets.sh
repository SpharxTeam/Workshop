# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 导出所有数据集从 Docker 命名卷到宿主机目录
# 功能：将 datasets_data 卷中的全部内容复制到宿主机的 ./exports/ 目录
# 用法：./scripts/utils/export_datasets.sh [目标目录]
# 示例：./scripts/utils/export_datasets.sh /mnt/d/exported_data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$SCRIPT_DIR/../lib/workshop_common.sh" ]; then
    source "$SCRIPT_DIR/../lib/workshop_common.sh"
else
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
fi

SOURCE_DIR="$PROJECT_ROOT/produce/output/datasets"
if [ ! -d "$SOURCE_DIR" ]; then
    log_error "源目录不存在: $SOURCE_DIR"
    exit 1
fi

EXPORT_BASE="${1:-$PROJECT_ROOT/exports}"
EXPORT_DIR="$EXPORT_BASE/datasets_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXPORT_DIR"

log_info "导出目标目录: $EXPORT_DIR"
log_info "正在从 $SOURCE_DIR 复制数据..."

cp -av "$SOURCE_DIR"/* "$EXPORT_DIR/"

log_success "数据已成功导出到: $EXPORT_DIR"
log_info "目录内容："
ls -la "$EXPORT_DIR"