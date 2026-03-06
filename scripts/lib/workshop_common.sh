# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 项目公共函数库（纯自动化版）
# 提供日志、命令检查、目录操作等基础功能


if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'  # No Color
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; NC=''
fi

# 带时间戳的日志函数
log_info()    { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}[INFO]${NC} $1"; }
log_success() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${YELLOW}[WARN]${NC} $1" >&2; }
log_error()   { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${RED}[ERROR]${NC} $1" >&2; }

# 打印节标题（用等号线包裹）
print_section() {
    log_info "========== $1 =========="
}

# 步骤开始：仅输出开始信息，不记录时间（耗时在结束时计算）
step_start() {
    log_info "开始步骤 $1: $2"
    STEP_START_TIME=$(date +%s)
}

# 步骤结束：输出完成信息和耗时
step_end() {
    local step_num=$1
    local end_time=$(date +%s)
    local elapsed=$((end_time - STEP_START_TIME))
    log_success "步骤 $step_num 完成 (耗时 ${elapsed}s)"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "未找到命令: $1，请先安装。"
        exit 1
    fi
}

# 确保目录存在
ensure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" || { log_error "无法创建目录: $dir"; return 1; }
    fi
    return 0
}

# 获取项目根目录
get_project_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
    echo "$(cd "$script_dir/../.." && pwd)"
}