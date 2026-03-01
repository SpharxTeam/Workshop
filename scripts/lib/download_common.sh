# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# 通用 GitHub 源码下载函数库
# 提供 download_repo 函数，支持官方 git、官方 ZIP、镜像 git 三种方式
# 所有下载操作均输出实时进度
# ============================================================================

# 加载日志函数（如果外部未提供，则定义）
if ! type log_info &>/dev/null; then
    if [ -t 1 ]; then
        RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    else
        RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
    fi
    log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
    log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
    log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
fi

# 镜像源列表（按优先级）
MIRRORS=(
    "https://hub.fastgit.xyz"
    "https://gitclone.com/github.com"
    "https://ghproxy.com/https://github.com"
    "https://hub.njuu.cf"
)

# 官方 ZIP 下载函数
# 参数：仓库URL, commit, 目标临时目录
# 返回：0成功，1失败
download_official_zip() {
    local repo_url=$1
    local commit=$2
    local tmp_dir=$3
    local repo_name=$(basename "$repo_url" .git)
    local zip_url="https://github.com/${repo_url#https://github.com/}/archive/${commit}.zip"
    local zip_file="/tmp/${repo_name}-${commit}.zip"

    log_info "尝试从官方 ZIP 下载 $repo_name (commit: $commit) ..."
    # 使用 --show-progress 显示 wget 进度条
    if wget --show-progress --progress=bar:force --timeout=30 --tries=3 -O "$zip_file" "$zip_url"; then
        mkdir -p "$tmp_dir"
        if unzip -q "$zip_file" -d "$tmp_dir"; then
            rm -f "$zip_file"
            return 0
        else
            log_warn "ZIP 解压失败"
        fi
    else
        log_warn "ZIP 下载失败"
    fi
    rm -f "$zip_file"
    return 1
}

# 从镜像源克隆
clone_from_mirror() {
    local name=$1
    local repo_url=$2
    local commit=$3
    local target_dir=$4

    for mirror in "${MIRRORS[@]}"; do
        local mirror_url="${mirror}/${repo_url#https://github.com/}"
        log_info "尝试从镜像 $mirror_url 克隆 $name ..."
        # git clone 默认显示进度，通过 --progress 确保输出
        if git clone --progress --depth 1 "$mirror_url" "$target_dir"; then
            cd "$target_dir"
            if [ -n "$commit" ]; then
                if ! git fetch --depth 1 origin "$commit" 2>&1; then
                    git fetch origin "$commit" 2>&1
                fi
                if git checkout "$commit" 2>&1; then
                    cd - >/dev/null
                    return 0
                else
                    log_warn "镜像中检出 commit $commit 失败，尝试下一个镜像"
                fi
            else
                cd - >/dev/null
                return 0
            fi
        fi
        # 如果克隆失败，清理可能产生的目录
        rm -rf "$target_dir"
    done
    return 1
}

# 主下载函数
# 参数：name, repo_url, commit, target_base
# 输出：最终将源码放在 $target_base/$name 下
download_repo() {
    local name=$1
    local repo_url=$2
    local commit=$3
    local target_base=$4
    local target_dir="$target_base/$name"

    if [ -d "$target_dir" ]; then
        log_info "目录 $target_dir 已存在，跳过下载"
        return 0
    fi

    mkdir -p "$target_base"
    local tmp_dir="${target_base}/.tmp_${name}_$$"

    # 优先级1：官方 git clone
    log_info "尝试从官方 git 克隆 $name ..."
    if git clone --progress --depth 1 "$repo_url" "$tmp_dir" 2>&1; then
        cd "$tmp_dir"
        if [ -n "$commit" ]; then
            if ! git fetch --depth 1 origin "$commit" 2>&1; then
                git fetch origin "$commit" 2>&1
            fi
            if git checkout "$commit" 2>&1; then
                log_success "官方 git 克隆成功 (commit: $commit)"
                rm -rf .git
                cd - >/dev/null
                mv "$tmp_dir" "$target_dir"
                return 0
            else
                log_warn "检出 commit 失败，尝试下一种方式"
            fi
        else
            log_success "官方 git 克隆成功 (最新版)"
            rm -rf .git
            cd - >/dev/null
            mv "$tmp_dir" "$target_dir"
            return 0
        fi
        cd - >/dev/null
        rm -rf "$tmp_dir"
    fi

    # 优先级2：官方 ZIP 下载（需要 commit）
    if [ -n "$commit" ]; then
        if download_official_zip "$repo_url" "$commit" "$tmp_dir"; then
            local extracted_dir=$(find "$tmp_dir" -maxdepth 1 -type d ! -name "$tmp_dir" | head -1)
            if [ -n "$extracted_dir" ]; then
                mv "$extracted_dir" "$target_dir"
                rm -rf "$tmp_dir"
                log_success "官方 ZIP 下载成功 (commit: $commit)"
                return 0
            else
                log_warn "ZIP 解压后未找到有效目录"
                rm -rf "$tmp_dir"
            fi
        else
            log_warn "官方 ZIP 下载失败"
        fi
    else
        log_warn "未指定 commit，跳过 ZIP 下载（无法确定版本）"
    fi

    # 优先级3：镜像 git clone
    if clone_from_mirror "$name" "$repo_url" "$commit" "$tmp_dir"; then
        rm -rf "$tmp_dir/.git"
        mv "$tmp_dir" "$target_dir"
        log_success "镜像 git 克隆成功"
        return 0
    fi

    log_error "所有方式均失败，无法下载 $name"
    return 1
}