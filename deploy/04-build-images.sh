#!/bin/bash
# 文件: toolchain/deploy/04-build-images.sh
# 用途: 构建所有Docker镜像

set -e

WORKSHOP_ROOT="/home/SpharxWorkshop"
cd "$WORKSHOP_ROOT/workshop"

echo "=========================================="
echo "SpharxWorkshop Docker镜像构建脚本"
echo "=========================================="
echo "开始时间: $(date)"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/tmp/spharx_build_$(date +%Y%m%d_%H%M%S).log"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行"
        return 1
    fi
    
    log_info "Docker 检查通过"
    return 0
}

# 检查环境变量
check_environment() {
    if [ ! -f .env ]; then
        log_warning ".env 文件不存在，使用模板创建..."
        if [ -f .env.template ]; then
            cp .env.template .env
            log_warning "请编辑 .env 文件并设置必要的环境变量"
            return 1
        else
            log_error ".env.template 不存在"
            return 1
        fi
    fi
    
    # 加载环境变量
    set -a
    source .env
    set +a
    
    # 检查关键变量
    local missing_vars=()
    
    if [ -z "$PROJECT_NAME" ]; then
        missing_vars+=("PROJECT_NAME")
    fi
    
    if [ -z "$OSS_ENDPOINT" ]; then
        missing_vars+=("OSS_ENDPOINT")
    fi
    
    if [ -z "$OSS_BUCKET" ]; then
        missing_vars+=("OSS_BUCKET")
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_warning "以下环境变量未设置: ${missing_vars[*]}"
        return 1
    fi
    
    log_info "环境变量检查通过"
    return 0
}

# 检查基础依赖
check_dependencies() {
    log_info "检查构建依赖..."
    
    # 检查必要的文件
    local required_files=("Dockerfile" "docker-compose.yml" "requirements.txt")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "必要文件不存在: $file"
            return 1
        fi
    done
    
    # 检查目录结构
    local required_dirs=("src" "configs" "deploy")
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "必要目录不存在: $dir"
            return 1
        fi
    done
    
    log_success "依赖检查通过"
    return 0
}

# 清理旧的镜像和容器
cleanup_old() {
    log_info "清理旧的构建..."
    
    # 停止并删除旧容器
    if docker-compose down 2>/dev/null; then
        log_info "旧容器已停止"
    fi
    
    # 删除旧的none镜像
    dangling_images=$(docker images -f "dangling=true" -q)
    if [ -n "$dangling_images" ]; then
        docker rmi $dangling_images 2>/dev/null || true
        log_info "清理悬空镜像"
    fi
    
    # 清理构建缓存
    docker builder prune -f 2>/dev/null || true
}

# 构建基础镜像
build_base_image() {
    log_info "构建基础镜像..."
    
    local image_name="spharx-base"
    local dockerfile="Dockerfile"
    
    if [ ! -f "$dockerfile" ]; then
        log_error "Dockerfile 不存在: $dockerfile"
        return 1
    fi
    
    log_info "使用 Dockerfile: $dockerfile"
    
    # 构建镜像
    if docker build \
        --tag "$image_name:latest" \
        --tag "$image_name:$(date +%Y%m%d)" \
        --file "$dockerfile" \
        . 2>&1 | tee -a "$LOG_FILE"; then
        
        log_success "基础镜像构建成功: $image_name"
        return 0
    else
        log_error "基础镜像构建失败"
        return 1
    fi
}

# 构建SAM服务镜像
build_sam_image() {
    log_info "构建SAM服务镜像..."
    
    local sam_dir="docker/sam"
    
    if [ ! -d "$sam_dir" ]; then
        log_warning "SAM目录不存在: $sam_dir，跳过构建"
        return 0
    fi
    
    if [ ! -f "$sam_dir/Dockerfile" ]; then
        log_warning "SAM Dockerfile不存在，跳过构建"
        return 0
    fi
    
    local image_name="spharx-sam"
    
    if docker build \
        --tag "$image_name:latest" \
        --file "$sam_dir/Dockerfile" \
        "$sam_dir" 2>&1 | tee -a "$LOG_FILE"; then
        
        log_success "SAM镜像构建成功: $image_name"
        return 0
    else
        log_error "SAM镜像构建失败"
        return 1
    fi
}

# 使用docker-compose构建所有服务
build_all_services() {
    log_info "使用docker-compose构建所有服务..."
    
    if docker-compose build --no-cache --parallel 2>&1 | tee -a "$LOG_FILE"; then
        log_success "所有服务镜像构建成功"
        return 0
    else
        log_error "服务镜像构建失败"
        return 1
    fi
}

# 验证镜像
verify_images() {
    log_info "验证构建的镜像..."
    
    local expected_images=("spharx-controller")
    
    # 从docker-compose.yml中提取服务名
    if [ -f "docker-compose.yml" ]; then
        local services=$(docker-compose config --services 2>/dev/null || echo "")
        expected_images+=($services)
    fi
    
    local all_valid=true
    
    for image in "${expected_images[@]}"; do
        # 检查镜像是否存在
        if docker image inspect "$image:latest" &>/dev/null; then
            # 获取镜像信息
            local size=$(docker image inspect "$image:latest" --format='{{.Size}}' | numfmt --to=iec --format="%.2f")
            local created=$(docker image inspect "$image:latest" --format='{{.Created}}' | cut -d'T' -f1)
            
            log_success "镜像存在: $image:latest (大小: ${size}B, 创建于: $created)"
        else
            log_error "镜像不存在: $image:latest"
            all_valid=false
        fi
    done
    
    if $all_valid; then
        log_success "所有镜像验证通过"
        return 0
    else
        log_error "部分镜像验证失败"
        return 1
    fi
}

# 推送镜像到仓库（可选）
push_images() {
    local push=$1
    
    if [ "$push" != "true" ]; then
        log_info "跳过镜像推送 (使用 --push 参数启用)"
        return 0
    fi
    
    log_info "推送镜像到仓库..."
    
    # 这里可以添加推送逻辑
    # 例如: docker push spharx-controller:latest
    
    log_warning "镜像推送功能暂未实现"
    return 0
}

# 显示构建摘要
show_summary() {
    echo ""
    echo "=========================================="
    echo "📦 镜像构建摘要"
    echo "=========================================="
    
    # 显示所有镜像
    log_info "已构建的镜像:"
    docker images --filter "reference=spharx*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | tee -a "$LOG_FILE"
    
    # 显示磁盘使用情况
    echo ""
    log_info "Docker磁盘使用情况:"
    docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}" | tee -a "$LOG_FILE"
    
    echo ""
    log_info "构建日志: $LOG_FILE"
}

# 主函数
main() {
    local push_images=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --push)
                push_images=true
                shift
                ;;
            --help)
                echo "使用方法: $0 [--push]"
                echo ""
                echo "选项:"
                echo "  --push    推送镜像到仓库"
                echo "  --help    显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    echo "工作目录: $(pwd)"
    echo "日志文件: $LOG_FILE"
    echo ""
    
    # 运行检查
    check_docker || exit 1
    check_environment || log_warning "环境变量检查有警告，继续构建..."
    check_dependencies || exit 1
    
    # 清理
    cleanup_old
    
    # 构建镜像
    build_base_image || exit 1
    build_sam_image || log_warning "SAM镜像构建失败，继续其他构建..."
    build_all_services || exit 1
    
    # 验证
    verify_images || exit 1
    
    # 推送（可选）
    push_images "$push_images"
    
    # 显示摘要
    show_summary
    
    log_success "🎉 所有镜像构建完成！"
    echo ""
    echo "下一步:"
    echo "  1. 启动服务: docker-compose up -d"
    echo "  2. 检查状态: docker-compose ps"
    echo "  3. 查看日志: docker-compose logs -f"
    
    return 0
}

# 执行主函数
if main "$@"; then
    exit 0
else
    log_error "镜像构建失败"
    exit 1
fi