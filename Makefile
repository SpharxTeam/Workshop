# SPHARX TOOLCHAIN Makefile
# 标准化操作命令集合

# ========== 配置变量 ==========
ENV_FILE ?= .env
COMPOSE_FILE ?= docker-compose.yml
COMPOSE_2D_FILE ?= docker-compose.2d.yml

# ========== 部署命令 ==========

.PHONY: init
init: ## 初始化环境：复制模板、创建目录
	@echo "🚀 初始化Toolchain环境..."
	cp .env.template .env || true
	mkdir -p /data/spharx /workspace /output logs
	@echo "✅ 环境初始化完成"

.PHONY: deploy-2d
deploy-2d: ## 部署最小2D服务栈
	@echo "📦 部署2D标注服务栈..."
	docker-compose -f $(COMPOSE_2D_FILE) up -d
	@echo "✅ 2D服务部署完成"
	@echo "应用查看: http://localhost:8080 (CVAT)"
	@echo "API端点: http://localhost:8081 (UI)"

.PHONY: deploy-full
deploy-full: ## 部署完整服务栈（2D+3D+AI）
	@echo "📦 部署完整Toolchain服务栈..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ 完整服务栈部署完成"
	@echo "应用查看: http://localhost:8080 (CVAT)"
	@echo "MinIO控制台: http://localhost:9001"
	@echo "Prometheus: http://localhost:9090"

.PHONY: stop
stop: ## 停止所有服务
	@echo "🛑 停止所有服务..."
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_2D_FILE) down
	@echo "✅ 服务已停止"

.PHONY: clean
clean: ## 清理所有数据和容器（危险操作）
	@echo "⚠️  警告：即将删除所有数据！"
	@read -p "确认继续？(yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker-compose -f $(COMPOSE_2D_FILE) down -v --remove-orphans
	rm -rf /data/spharx/* /workspace/* /output/*
	@echo "✅ 清理完成"

# ========== 流水线命令 ==========

.PHONY: run-pipeline
run-pipeline: ## 运行完整流水线处理
	@echo "⚙️  启动流水线处理..."
	python src/main.py --config config/pipeline_default.yaml
	@echo "✅ 流水线执行完成"

.PHONY: run-stage
run-stage: ## 运行指定阶段 (usage: make run-stage STAGE=01_2d_annotation)
	@if [ -z "$(STAGE)" ]; then \
		echo "❌ 请指定阶段: make run-stage STAGE=阶段名称"; \
		exit 1; \
	fi
	@echo "⚙️  运行阶段: $(STAGE)"
	python src/main.py --stage $(STAGE)
	@echo "✅ 阶段执行完成"

# ========== 开发与测试 ==========

.PHONY: test
test: ## 运行所有测试
	@echo "🧪 运行测试套件..."
	pytest tests/ -v --tb=short
	@echo "✅ 测试完成"

.PHONY: test-unit
test-unit: ## 运行单元测试
	@echo "🔬 运行单元测试..."
	pytest tests/test_pipeline_stages.py tests/test_services.py -v

.PHONY: lint
lint: ## 代码风格检查
	@echo "🎨 执行代码检查..."
	flake8 src/ tests/
	mypy src/
	@echo "✅ 代码检查通过"

.PHONY: dev-install
dev-install: ## 安装开发依赖
	@echo "📥 安装开发环境..."
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "✅ 开发环境安装完成"

# ========== 运维命令 ==========

.PHONY: status
status: ## 查看服务状态
	@echo "📊 服务状态:"
	docker-compose -f $(COMPOSE_FILE) ps
	@echo "\n📊 2D服务状态:"
	docker-compose -f $(COMPOSE_2D_FILE) ps

.PHONY: logs
logs: ## 查看服务日志 (usage: make logs SERVICE=cvat)
	@if [ -z "$(SERVICE)" ]; then \
		docker-compose -f $(COMPOSE_FILE) logs -f; \
	else \
		docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE); \
	fi

.PHONY: health
health: ## 健康检查
	@echo "🏥 执行健康检查..."
	bash scripts/health_check.sh

.PHONY: backup
backup: ## 备份重要数据
	@echo "💾 执行数据备份..."
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		/data/spharx/config/ \
		/data/spharx/models/ \
		--exclude='*.tmp' --exclude='*.log'
	@echo "✅ 备份完成"

# ========== 帮助信息 ==========

.PHONY: help
help: ## 显示帮助信息
	@echo "SPHARX TOOLCHAIN 命令帮助"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ========== 默认目标 ==========
.DEFAULT_GOAL := help