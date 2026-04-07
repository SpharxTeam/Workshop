# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 生产线构建脚本
# 功能：自动检查依赖、源码、补丁，下载缺失项，构建基础镜像，依次构建各模块，输出汇总报告
# 用法：./scripts/build/workshop_build_all.sh

set -e

# 确保所有脚本可执行
find scripts -name "*.sh" -exec chmod +x {} \;

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

# 检查并安装 unzip（用于模型下载的 ZIP 解压）
if ! command -v unzip &> /dev/null; then
    log_warn "unzip 未安装，尝试自动安装..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y unzip
    else
        log_error "无法自动安装 unzip，请手动安装后重试"
        exit 1
    fi
fi

PROJECT_ROOT="$(get_project_root)"
cd "$PROJECT_ROOT"

MODULES=(
    "base:base:workshop-base"
    "ingest:pipelines/run_00_ingest:workshop-ingest"
    "quality:pipelines/run_01_quality:workshop-quality"
    "enhance:pipelines/run_02_enhance:workshop-enhance"
    "calibrate:pipelines/run_03_calibrate:workshop-calibrate"
    "pack:pipelines/run_04_pack:workshop-pack"
    "delivery:pipelines/run_05_delivery:workshop-delivery"
)

check_command docker
check_command git

log_info "========== workshop 生产线构建开始 =========="

# 步骤1: 下载离线依赖包（失败则终止）
log_info "步骤1: 下载所有 Python 依赖（离线包）..."
if ! "$PROJECT_ROOT/scripts/download/download_deps.sh" --clean; then
    log_error "依赖下载失败，终止构建"
    exit 1
fi

# 步骤2: 下载模型（必须成功）
log_info "步骤2: 下载模型权重..."
if ! "$PROJECT_ROOT/scripts/download/download_models.sh"; then
    log_error "模型下载失败，终止构建"
    exit 1
fi

# 步骤3: 构建基础镜像
log_info "步骤3: 构建基础镜像..."
docker build --no-cache -t workshop-base -f base/Dockerfile .

# 步骤4: 构建各模块
declare -A results
for module in "${MODULES[@]}"; do
    if [[ "$module" == base:* ]]; then
        results["base"]="✅ 成功"
        continue
    fi
    IFS=':' read -r name path image <<< "$module"
    log_info "开始构建模块: $name (镜像: $image)"
    if docker build -t "$image" -f "$path/Dockerfile" .; then
        log_success "构建成功: $name"
        results["$name"]="✅ 成功"
    else
        log_error "构建失败: $name"
        results["$name"]="❌ 失败"
    fi
done

echo ""
log_info "========== 构建汇总 =========="
for key in "${!results[@]}"; do
    echo -e "${results[$key]} $key"
done | sort
log_info "================================"

for result in "${results[@]}"; do
    if [[ "$result" == *"❌"* ]]; then
        exit 1
    fi
done
log_success "所有模块构建成功！"