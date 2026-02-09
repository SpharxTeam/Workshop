#!/bin/bash
# 文件: scripts/health_check.sh
# 用途: 完整的系统健康检查脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$WORKSHOP_ROOT"

echo "=========================================="
echo "SpharxWorkshop 系统健康检查脚本"
echo "=========================================="
echo "开始时间: $(date)"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/tmp/spharx_health_check_$(date +%Y%m%d_%H%M%S).log"

# 记录函数
log_message() {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "SUCCESS") color=$GREEN ;;
        "ERROR") color=$RED ;;
        "WARNING") color=$YELLOW ;;
        "INFO") color=$BLUE ;;
    esac
    
    echo -e "${color}[$level]${NC} $message" | tee -a "$LOG_FILE"
}

# 检查函数
check_docker() {
    echo "🔍 检查 Docker..."
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_message "INFO" "Docker 版本: $docker_version"
        
        # 检查Docker服务状态
        if docker info &> /dev/null; then
            log_message "SUCCESS" "Docker 服务运行正常"
        else
            log_message "ERROR" "Docker 服务未运行"
            return 1
        fi
    else
        log_message "ERROR" "Docker 未安装"
        return 1
    fi
    echo ""
}

check_docker_compose() {
    echo "🔍 检查 Docker Compose..."
    if command -v docker-compose &> /dev/null; then
        compose_version=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')
        log_message "INFO" "Docker Compose 版本: $compose_version"
    else
        log_message "ERROR" "Docker Compose 未安装"
        return 1
    fi
    echo ""
}

check_python() {
    echo "🔍 检查 Python..."
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        log_message "INFO" "Python 版本: $python_version"
        
        # 检查Python包
        echo "   检查 Python 包..."
        required_packages=("pydantic" "loguru" "opencv-python" "numpy")
        for pkg in "${required_packages[@]}"; do
            if python3 -c "import $pkg" &> /dev/null; then
                log_message "SUCCESS" "   ✓ $pkg 已安装"
            else
                log_message "ERROR" "   ✗ $pkg 未安装"
            fi
        done
    else
        log_message "ERROR" "Python3 未安装"
        return 1
    fi
    echo ""
}

check_directory_structure() {
    echo "📁 检查目录结构..."
    
    required_dirs=(
        "$WORKSHOP_ROOT/src"
        "$WORKSHOP_ROOT/src/schemas"
        "$WORKSHOP_ROOT/src/pipelines"
        "$WORKSHOP_ROOT/src/utils"
        "$WORKSHOP_ROOT/configs"
        "$WORKSHOP_ROOT/configs/2d_annotation"
        "$WORKSHOP_ROOT/configs/3d_reconstruction"
        "$WORKSHOP_ROOT/configs/physics"
        "$WORKSHOP_ROOT/deploy"
        "$WORKSHOP_ROOT/scripts"
        "$WORKSHOP_ROOT/docs"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_message "SUCCESS" "   ✓ $(basename "$dir")/"
        else
            log_message "ERROR" "   ✗ $(basename "$dir")/ 不存在"
        fi
    done
    echo ""
}

check_required_files() {
    echo "📄 检查必要文件..."
    
    required_files=(
        "$WORKSHOP_ROOT/.env.template"
        "$WORKSHOP_ROOT/docker-compose.yml"
        "$WORKSHOP_ROOT/Dockerfile"
        "$WORKSHOP_ROOT/requirements.txt"
        "$WORKSHOP_ROOT/README.md"
        "$WORKSHOP_ROOT/src/main.py"
        "$WORKSHOP_ROOT/configs/logging.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_message "SUCCESS" "   ✓ $(basename "$file")"
        else
            log_message "ERROR" "   ✗ $(basename "$file") 不存在"
        fi
    done
    echo ""
}

check_environment() {
    echo "🌍 检查环境变量..."
    
    # 检查.env文件
    if [ -f "$WORKSHOP_ROOT/.env" ]; then
        log_message "SUCCESS" ".env 文件存在"
        
        # 检查关键环境变量
        source "$WORKSHOP_ROOT/.env" 2>/dev/null || true
        
        critical_vars=(
            "PROJECT_NAME"
            "OSS_ENDPOINT"
            "OSS_BUCKET"
            "SPHARX_INPUT_DIR"
            "SPHARX_OUTPUT_DIR"
        )
        
        for var in "${critical_vars[@]}"; do
            if [ -n "${!var}" ]; then
                log_message "SUCCESS" "   ✓ $var 已设置"
            else
                log_message "WARNING" "   ⚠ $var 未设置"
            fi
        done
    else
        log_message "WARNING" ".env 文件不存在 (请复制 .env.template)"
    fi
    echo ""
}

check_data_directories() {
    echo "💾 检查数据目录..."
    
    # 从环境变量获取路径，或使用默认值
    INPUT_DIR=${SPHARX_INPUT_DIR:-"/home/SpharxWorkshop/data/input/scenes"}
    OUTPUT_DIR=${SPHARX_OUTPUT_DIR:-"/home/SpharxWorkshop/data/output/datasets"}
    WORKSPACE_DIR=${SPHARX_WORKSPACE_DIR:-"/home/SpharxWorkshop/workspace"}
    
    directories=("$INPUT_DIR" "$OUTPUT_DIR" "$WORKSPACE_DIR")
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            # 检查权限
            if [ -w "$dir" ]; then
                size=$(du -sh "$dir" 2>/dev/null | cut -f1)
                log_message "SUCCESS" "   ✓ $dir (可写, 大小: $size)"
            else
                log_message "WARNING" "   ⚠ $dir (存在但不可写)"
            fi
        else
            log_message "INFO" "   ℹ $dir (不存在，将自动创建)"
            mkdir -p "$dir"
        fi
    done
    echo ""
}

check_docker_containers() {
    echo "🐳 检查 Docker 容器..."
    
    if [ -f "docker-compose.yml" ]; then
        # 检查服务定义
        services=$(docker-compose config --services 2>/dev/null || echo "")
        
        if [ -n "$services" ]; then
            log_message "INFO" "定义的服务: $services"
            
            # 检查运行状态
            running_containers=$(docker-compose ps --services --filter "status=running" 2>/dev/null || echo "")
            stopped_containers=$(docker-compose ps --services --filter "status=stopped" 2>/dev/null || echo "")
            
            if [ -n "$running_containers" ]; then
                log_message "SUCCESS" "运行中的容器: $running_containers"
            fi
            
            if [ -n "$stopped_containers" ]; then
                log_message "WARNING" "停止的容器: $stopped_containers"
            fi
            
            if [ -z "$running_containers" ] && [ -z "$stopped_containers" ]; then
                log_message "INFO" "没有容器在运行"
            fi
        else
            log_message "WARNING" "docker-compose.yml 中没有定义服务"
        fi
    else
        log_message "WARNING" "docker-compose.yml 不存在"
    fi
    echo ""
}

check_disk_space() {
    echo "💽 检查磁盘空间..."
    
    # 检查根目录空间
    root_space=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$root_space" -lt 80 ]; then
        log_message "SUCCESS" "根目录磁盘使用率: ${root_space}% (正常)"
    elif [ "$root_space" -lt 95 ]; then
        log_message "WARNING" "根目录磁盘使用率: ${root_space}% (较高)"
    else
        log_message "ERROR" "根目录磁盘使用率: ${root_space}% (严重)"
    fi
    
    # 检查数据目录所在磁盘空间
    data_dir="/home/SpharxWorkshop"
    if [ -d "$data_dir" ]; then
        data_space=$(df -h "$data_dir" | tail -1 | awk '{print $5}' | tr -d '%' 2>/dev/null || echo "N/A")
        if [ "$data_space" != "N/A" ]; then
            if [ "$data_space" -lt 80 ]; then
                log_message "SUCCESS" "数据目录磁盘使用率: ${data_space}% (正常)"
            else
                log_message "WARNING" "数据目录磁盘使用率: ${data_space}% (较高)"
            fi
        fi
    fi
    echo ""
}

check_network() {
    echo "🌐 检查网络连接..."
    
    # 检查互联网连接
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        log_message "SUCCESS" "互联网连接正常"
    else
        log_message "WARNING" "互联网连接失败"
    fi
    
    # 检查Docker Hub连接
    if curl -s --connect-timeout 5 https://hub.docker.com/ &> /dev/null; then
        log_message "SUCCESS" "Docker Hub 可访问"
    else
        log_message "WARNING" "Docker Hub 访问失败"
    fi
    
    # 检查阿里云OSS连接
    if [ -n "$OSS_ENDPOINT" ]; then
        if curl -s --connect-timeout 5 "https://$OSS_ENDPOINT" &> /dev/null; then
            log_message "SUCCESS" "阿里云OSS 可访问"
        else
            log_message "WARNING" "阿里云OSS 访问失败"
        fi
    fi
    echo ""
}

run_python_health_check() {
    echo "🐍 运行 Python 健康检查..."
    
    if [ -f "src/main.py" ]; then
        if python3 src/main.py health-check 2>&1 | tee -a "$LOG_FILE"; then
            log_message "SUCCESS" "Python 健康检查通过"
        else
            log_message "ERROR" "Python 健康检查失败"
        fi
    else
        log_message "ERROR" "src/main.py 不存在，无法运行Python健康检查"
    fi
    echo ""
}

generate_report() {
    echo "=========================================="
    echo "📊 健康检查报告汇总"
    echo "=========================================="
    
    # 统计日志中的结果
    success_count=$(grep -c "\[SUCCESS\]" "$LOG_FILE" || true)
    error_count=$(grep -c "\[ERROR\]" "$LOG_FILE" || true)
    warning_count=$(grep -c "\[WARNING\]" "$LOG_FILE" || true)
    
    echo "✅ 成功: $success_count"
    echo "⚠️  警告: $warning_count"
    echo "❌ 错误: $error_count"
    echo ""
    echo "日志文件: $LOG_FILE"
    echo ""
    
    if [ "$error_count" -eq 0 ]; then
        if [ "$warning_count" -eq 0 ]; then
            echo "🎉 所有检查通过！系统状态优秀。"
            return 0
        else
            echo "👍 系统基本正常，但有需要注意的警告。"
            return 0
        fi
    else
        echo "🔧 系统存在错误，需要修复。"
        
        # 显示错误摘要
        echo ""
        echo "错误摘要:"
        grep "\[ERROR\]" "$LOG_FILE" | head -10
        
        if [ "$error_count" -gt 10 ]; then
            echo "... 还有 $(($error_count - 10)) 个错误"
        fi
        
        return 1
    fi
}

main() {
    echo "开始系统健康检查..."
    echo "工作目录: $WORKSHOP_ROOT"
    echo "日志文件: $LOG_FILE"
    echo ""
    
    # 运行所有检查
    check_docker
    check_docker_compose
    check_python
    check_directory_structure
    check_required_files
    check_environment
    check_data_directories
    check_docker_containers
    check_disk_space
    check_network
    run_python_health_check
    
    # 生成报告
    echo ""
    generate_report
    
    return $?
}

# 执行主函数
if main; then
    echo ""
    echo "✅ 健康检查完成，系统正常。"
    exit 0
else
    echo ""
    echo "❌ 健康检查发现错误，请查看日志文件。"
    exit 1
fi