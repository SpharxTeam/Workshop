# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

#!/bin/bash
set -e

# ============================================================================
# Workshop 源码下载脚本（预留）
# Workshop 项目所有依赖均通过 pip 管理，无需下载源码。
# 此脚本仅作占位，保持与 deepness 结构一致。
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

log_info "Workshop 无源码依赖，跳过下载。"