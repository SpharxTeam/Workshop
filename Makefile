# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# workshop 生产线 Makefile
# 目标：自动化构建、测试、文档生成等
# 用法：
#   make all        # 构建所有（默认）
#   make base       # 构建基础镜像
#   make ingest     # 构建数据导入模块
#   make quality    # 构建质检模块
#   make enhance    # 构建增强模块
#   make calibrate  # 构建标定模块
#   make pack       # 构建打包模块
#   make delivery   # 构建交付模块
#   make test       # 运行单元测试
#   make test-integration # 运行集成测试
#   make test-all   # 运行所有测试
#   make docs       # 构建 Sphinx 文档
#   make clean      # 删除所有 workshop 镜像
#   make clean-all  # 删除镜像并清理 Docker 构建缓存

.PHONY: all base ingest quality enhance calibrate pack delivery \
        test test-integration test-all docs clean clean-all

ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# 默认目标：构建所有镜像
all: base ingest quality enhance calibrate pack delivery
	@echo "🎉 所有镜像构建完成！"
	@docker images --filter=reference='workshop-*' --format="table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 构建基础镜像
base:
	@echo "🔨 构建基础镜像 workshop-base ..."
	@docker build --no-cache -t workshop-base -f base/Dockerfile .

# 构建数据导入模块
ingest: base
	@echo "🔨 构建数据导入模块 workshop-ingest ..."
	@docker build -t workshop-ingest -f pipelines/run_00_ingest/Dockerfile .

# 构建质检模块
quality: base
	@echo "🔨 构建质检模块 workshop-quality ..."
	@docker build -t workshop-quality -f pipelines/run_01_quality/Dockerfile .

# 构建增强模块
enhance: base
	@echo "🔨 构建增强模块 workshop-enhance ..."
	@docker build -t workshop-enhance -f pipelines/run_02_enhance/Dockerfile .

# 构建标定模块
calibrate: base
	@echo "🔨 构建标定模块 workshop-calibrate ..."
	@docker build -t workshop-calibrate -f pipelines/run_03_calibrate/Dockerfile .

# 构建打包模块
pack: base
	@echo "🔨 构建打包模块 workshop-pack ..."
	@docker build -t workshop-pack -f pipelines/run_04_pack/Dockerfile .

# 构建交付模块
delivery: base
	@echo "🔨 构建交付模块 workshop-delivery ..."
	@docker build -t workshop-delivery -f pipelines/run_05_delivery/Dockerfile .

# 运行单元测试
test:
	@echo "🧪 运行单元测试..."
	@PYTHONPATH=$(ROOT_DIR) python -m pytest tests/unit -c tests/pytest.ini -v --cov=pipelines --cov-report=term-missing

# 运行集成测试
test-integration:
	@echo "🧪 运行集成测试..."
	@PYTHONPATH=$(ROOT_DIR) python -m pytest tests/integration -c tests/pytest.ini -v

# 运行所有测试
test-all: test test-integration

# 构建 Sphinx 文档
docs:
	@echo "📖 构建文档..."
	@cd docs && make html
	@echo "文档已生成在 docs/build/html/index.html"

# 删除所有 workshop 镜像
clean:
	@echo "🧹 删除 workshop 相关镜像..."
	@docker images -q --filter='reference=workshop-*' | xargs -r docker rmi -f

# 删除镜像并清理构建缓存
clean-all: clean
	@echo "🧹 清理 Docker 构建缓存..."
	@docker builder prune -a -f