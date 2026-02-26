#!/bin/bash
set -e

# ============================================================================
# Workshop 本地开发环境初始化脚本（可选）
# 创建必要的目录结构和虚拟环境
# 用法：./scripts/init/init_project.sh
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

PROJECT_ROOT="$(get_project_root)"
cd "$PROJECT_ROOT"

log_info "🚀 初始化 Workshop 本地开发环境..."

# 创建数据目录（partdata）
log_info "创建数据目录..."
ensure_dir "partdata/raw"
ensure_dir "partdata/processed"
ensure_dir "partdata/datasets"
ensure_dir "partdata/models"
ensure_dir "partdata/calibration_images"

# 创建虚拟环境（可选）
if [ ! -d "venv" ] && confirm_action "是否创建 Python 虚拟环境 (venv)？" "n"; then
    check_command python3
    python3 -m venv venv
    log_success "虚拟环境已创建，使用 'source venv/bin/activate' 激活。"
    # 可选：安装基础依赖
    if [ -f "requirements.txt" ]; then
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
    fi
fi

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ] && [ -f ".env.template" ] && confirm_action "是否从模板创建 .env 文件？" "n"; then
    cp .env.template .env
    log_info ".env 文件已创建，请编辑填写实际配置。"
fi

log_success "初始化完成！"