# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 生产线一键部署脚本
# 功能：拉取代码、下载模型、构建镜像、启动服务
# 用法：./scripts/deploy/workshop_deploy.sh [--workspace PATH] [--repo URL] [--branch NAME]

set -e

# 颜色定义
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 默认配置
WORKSPACE="$(pwd)"
REPO_URL="https://gitee.com/spharx/spharxhub.git"
BRANCH="main"
MODEL_DIR="${WORKSPACE}/partdata/models"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace)
            WORKSPACE="$2"
            shift 2
            ;;
        --repo)
            REPO_URL="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [--workspace PATH] [--repo URL] [--branch NAME]"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# 检查必要命令
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "未找到命令: $1，请先安装。"
        exit 1
    fi
}
check_command git
check_command docker
check_command wget
check_command python3

# 创建工作目录
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

log_info "工作目录: $WORKSPACE"

# 1. 克隆/更新代码仓库
if [ -d "spharxhub" ]; then
    log_info "仓库已存在，正在更新..."
    cd spharxhub
    git fetch --all
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    git submodule update --init --recursive
    cd ..
else
    log_info "正在克隆仓库 $REPO_URL (分支: $BRANCH) ..."
    git clone --recursive -b "$BRANCH" "$REPO_URL" spharxhub
fi

cd spharxhub/workshop

# 2. 准备脚本执行权限
find scripts -name "*.sh" -exec chmod +x {} \;

# 3. 下载模型权重（如果存在下载脚本）
if [ -f "scripts/download/download_models.sh" ]; then
    log_info "下载模型权重..."
    ./scripts/download/download_models.sh
else
    log_warn "未找到模型下载脚本，跳过模型下载"
fi

# 4. 构建 Docker 镜像
log_info "构建 Docker 镜像..."
./scripts/build/workshop_build_all.sh

# 5. 准备 docker-compose.yml（如果不存在则生成默认）
if [ ! -f "docker-compose.yml" ]; then
    log_info "未找到 docker-compose.yml，生成默认配置..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

networks:
  workshop-net:
    driver: bridge

services:
  ingest:
    image: workshop-ingest:latest
    container_name: workshop-ingest
    restart: unless-stopped
    networks:
      - workshop-net
    volumes:
      - ./partdata/raw:/data/raw
      - ./partdata/processed:/data/processed
      - ./common/configs:/app/common/configs:ro
    environment:
      - SCENE_ID=${SCENE_ID:-scene_001}
    command: ["--input", "/data/raw/sample.bag", "--output", "/data/processed/${SCENE_ID}"]

  quality:
    image: workshop-quality:latest
    container_name: workshop-quality
    restart: unless-stopped
    networks:
      - workshop-net
    volumes:
      - ./partdata/processed:/data/processed
      - ./common/configs:/app/common/configs:ro
    command: ["--input", "/data/processed/${SCENE_ID}", "--output", "/data/processed/${SCENE_ID}/quality"]
    depends_on:
      - ingest

  enhance:
    image: workshop-enhance:latest
    container_name: workshop-enhance
    restart: unless-stopped
    networks:
      - workshop-net
    volumes:
      - ./partdata/processed:/data/processed
      - ./common/configs:/app/common/configs:ro
      - ./partdata/models:/app/common/models
    command: ["--input", "/data/processed/${SCENE_ID}", "--output", "/data/processed/${SCENE_ID}/enhanced"]
    depends_on:
      - quality

  calibrate:
    image: workshop-calibrate:latest
    container_name: workshop-calibrate
    restart: unless-stopped
    networks:
      - workshop-net
    volumes:
      - ./partdata/processed:/data/processed
      - ./common/configs:/app/common/configs:ro
      - ./partdata/calibration_images:/data/calibration_images:ro
    command: ["--input", "/data/calibration_images", "--output", "/data/processed/${SCENE_ID}/calib"]
    depends_on:
      - enhance

  pack:
    image: workshop-pack:latest
    container_name: workshop-pack
    restart: unless-stopped
    networks:
      - workshop-net
    volumes:
      - ./partdata/processed:/data/processed
      - ./partdata/datasets:/data/datasets
      - ./common/configs:/app/common/configs:ro
    command: ["--input", "/data/processed/${SCENE_ID}", "--output", "/data/datasets/${SCENE_ID}"]
    depends_on:
      - calibrate

  delivery:
    image: workshop-delivery:latest
    container_name: workshop-delivery
    restart: unless-stopped
    networks:
      - workshop-net
    volumes:
      - ./partdata/datasets:/data/datasets
      - ./common/configs:/app/common/configs:ro
    command: ["--input", "/data/datasets/${SCENE_ID}"]
    depends_on:
      - pack
EOF
fi

# 创建必要的数据目录
mkdir -p partdata/{raw,processed,datasets,models,calibration_images}

# 6. 启动服务
log_info "启动 Docker Compose 服务..."
docker-compose up -d

log_info "部署完成！"
docker-compose ps