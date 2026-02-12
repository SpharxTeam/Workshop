#!/bin/bash
set -euo pipefail

SPHARX_HOME="${HOME}/SpharxWorkshop"
REPO_URL="git@gitee.com:spharx/toolchain.git"

echo "[Spharx Bootstrap] 开始初始化空间智能数据生产线"
echo "=================================================="

# 阶段0: 前置检查（git, docker, docker-compose）
source ./scripts/deploy/00_check_prereqs.sh

# 阶段1: 创建工作空间并克隆代码
mkdir -p ${SPHARX_HOME}
cd ${SPHARX_HOME}
if [ ! -d "toolchain" ]; then
    git clone ${REPO_URL} toolchain
fi
cd toolchain

# 阶段2: 创建数据目录结构
source ./scripts/deploy/01_create_dirs.sh

# 阶段3: 生成.env（交互式，从模板复制）
source ./scripts/deploy/02_generate_env.sh

# 阶段4: 构建自定义Docker镜像
source ./scripts/deploy/03_build_images.sh

# 阶段5: 启动长期运行服务
source ./scripts/deploy/04_start_services.sh

echo "=================================================="
echo "[Spharx Bootstrap] 初始化完成！"
echo "下一步: 编辑 $(pwd)/.env 调整配置，然后运行 ./scripts/pipeline/run_2d.sh 测试2D流水线"