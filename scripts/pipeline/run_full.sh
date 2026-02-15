#!/bin/bash
set -e

# 使用第一个命令行参数作为 bag 路径，如果没提供则使用默认值
BAG_PATH=${1:-/data/raw/D435i_Walking.bag}
SCENE_ID="scene_$(date +%Y%m%d_%H%M%S)"

echo "========================================="
echo "开始处理场景: $SCENE_ID"
echo "输入 bag: $BAG_PATH"
echo "========================================="

cd ~/workshop

# 1. Ingest
echo "[1/5] 运行 ingest ..."
docker-compose run --rm ingest --input "$BAG_PATH" --output "/data/processed/$SCENE_ID"

# 2. Quality
echo "[2/5] 运行 quality ..."
docker-compose run --rm quality --input "/data/processed/$SCENE_ID" --output "/data/processed/$SCENE_ID/quality"

# 3. Enhance
echo "[3/5] 运行 enhance ..."
docker-compose run --rm -e TORCH_FORCE_NO_WEIGHTS_ONLY=1 enhance \
  --input "/data/processed/$SCENE_ID" \
  --output "/data/processed/$SCENE_ID/enhanced" \
  --conf 0.25

# 4. Calibrate (使用虚拟标定图像，如需真实请修改路径)
echo "[4/5] 运行 calibrate ..."
docker-compose run --rm calibrate --input "/data/calibration_images" --output "/data/processed/$SCENE_ID/calib" --chessboard 9,6 --square_size 0.025

# 5. Pack
echo "[5/5] 运行 pack ..."
docker-compose run --rm pack --input "/data/processed/$SCENE_ID" --output "/data/datasets/$SCENE_ID" --formats ros,coco

echo "========================================="
echo "✅ 全部完成！数据集位于: /data/datasets/$SCENE_ID"
echo "========================================="