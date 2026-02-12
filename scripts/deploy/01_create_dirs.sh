#!/bin/bash
set -e

source .env 2>/dev/null || {
    echo "警告: .env文件不存在，使用默认路径"
    DATA_ROOT="${HOME}/SpharxWorkshop/data"
    WORKSPACE_ROOT="${HOME}/SpharxWorkshop/workspace"
}

echo "[1/4] 创建数据目录结构..."

# 输入数据目录
mkdir -p ${DATA_ROOT}/input/scenes
mkdir -p ${DATA_ROOT}/input/archives

# 输出数据集目录
mkdir -p ${DATA_ROOT}/output/datasets
mkdir -p ${DATA_ROOT}/output/logs

# 运行时工作区
mkdir -p ${WORKSPACE_ROOT}/cache/colmap
mkdir -p ${WORKSPACE_ROOT}/cache/sam
mkdir -p ${WORKSPACE_ROOT}/processing
mkdir -p ${WORKSPACE_ROOT}/logs/{pipeline,services,cvat}

# 模型权重缓存（避免重复下载）
mkdir -p ${WORKSPACE_ROOT}/models/sam
mkdir -p ${WORKSPACE_ROOT}/models/sa3d

echo "目录创建完成。"
echo "  DATA_ROOT = ${DATA_ROOT}"
echo "  WORKSPACE_ROOT = ${WORKSPACE_ROOT}"