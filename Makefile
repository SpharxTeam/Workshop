# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

# ============================================================================
# workshop 生产线 Makefile
# 目标：自动化构建所有 Docker 镜像，支持模型下载（可选）
# 用法：
#   make all        # 构建所有（默认）
#   make base       # 构建基础镜像
#   make ingest     # 构建数据导入模块
#   make quality    # 构建质检模块
#   make enhance    # 构建增强模块
#   make calibrate  # 构建标定模块
#   make pack       # 构建打包模块
#   make delivery   # 构建交付模块（预留）
#   make models     # 下载 YOLO 模型（需网络）
#   make clean      # 删除所有 workshop 镜像
#   make clean-all  # 删除镜像并清理 Docker 构建缓存
# ============================================================================

.PHONY: all base ingest quality enhance calibrate pack delivery models clean clean-all

# 项目根目录（相对于 Makefile 的位置）
ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# 定义模块列表（名称:子目录:镜像标签）
MODULES := \
    base:base:workshop-base \
    ingest:pipelines/00_ingest:workshop-ingest \
    quality:pipelines/01_quality:workshop-quality \
    enhance:pipelines/02_enhance:workshop-enhance \
    calibrate:pipelines/03_calibrate:workshop-calibrate \
    pack:pipelines/04_pack:workshop-pack \
    delivery:pipelines/05_delivery:workshop-delivery

# 默认目标：构建所有模块
all: $(foreach module,$(filter-out base,$(MODULES)),$(word 1,$(subst :, ,$(module))))
	@echo "🎉 所有镜像构建完成！"
	@docker images --filter=reference='workshop-*' --format="table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 构建基础镜像
base:
	@echo "🔨 构建基础镜像 workshop-base ..."
	@docker build -t workshop-base -f base/Dockerfile .

# 构建数据导入模块
ingest: base
	@echo "🔨 构建数据导入模块 workshop-ingest ..."
	@docker build -t workshop-ingest -f pipelines/00_ingest/Dockerfile .

# 构建质检模块
quality: base
	@echo "🔨 构建质检模块 workshop-quality ..."
	@docker build -t workshop-quality -f pipelines/01_quality/Dockerfile .

# 构建增强模块
enhance: base
	@echo "🔨 构建增强模块 workshop-enhance ..."
	@docker build -t workshop-enhance -f pipelines/02_enhance/Dockerfile .

# 构建标定模块
calibrate: base
	@echo "🔨 构建标定模块 workshop-calibrate ..."
	@docker build -t workshop-calibrate -f pipelines/03_calibrate/Dockerfile .

# 构建打包模块
pack: base
	@echo "🔨 构建打包模块 workshop-pack ..."
	@docker build -t workshop-pack -f pipelines/04_pack/Dockerfile .

# 构建交付模块（预留）
delivery: base
	@echo "🔨 构建交付模块 workshop-delivery ..."
	@docker build -t workshop-delivery -f pipelines/05_delivery/Dockerfile .

# 下载 YOLO 模型（需网络）
models:
	@echo "📥 下载 YOLO 模型到 partdata/models ..."
	@$(ROOT_DIR)/scripts/download/download_models.sh

# 删除所有 workshop 镜像
clean:
	@echo "🧹 删除 workshop 相关镜像..."
	@docker images -q --filter='reference=workshop-*' | xargs -r docker rmi -f

# 删除镜像并清理 Docker 构建缓存
clean-all: clean
	@echo "🧹 清理 Docker 构建缓存..."
	@docker builder prune -a -f