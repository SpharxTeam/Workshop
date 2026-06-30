# Workshop V2.0 - 开发工具 Makefile
# ================================
#
# 使用方法:
#   make help        显示所有可用命令
#   make install     安装项目
#   make test        运行测试
#   make lint        代码检查
#   make format      自动格式化
#   make quality     完整质量检查

.PHONY: help install install-dev test lint format quality clean build docs

# 默认目标
.DEFAULT_GOAL := help

help:
	@echo "╔══════════════════════════════════════════════════╗"
	@echo "║    Workshop V2.0 - 开发命令参考                  ║"
	@echo "╠══════════════════════════════════════════════════╣"
	@echo "║                                                  ║"
	@echo "║  安装相关:                                       ║"
	@echo "║    make install       安装核心依赖               ║"
	@echo "║    make install-dev   安装完整开发环境           ║"
	@echo "║    make install-ml    安装机器学习依赖           ║"
	@echo "║                                                  ║"
	@echo "║  代码质量:                                       ║"
	@echo "║    make lint          运行 Linting (ruff)        ║"
	@echo "║    make format        自动格式化 (black+isort)   ║"
	@echo "║    make typecheck     类型检查 (mypy)            ║"
	@echo "║    make security      安全扫描                   ║"
	@echo "║    make quality       完整质量检查               ║"
	@echo "║                                                  ║"
	@echo "║  测试相关:                                       ║"
	@echo "║    make test          运行单元测试               ║"
	@echo "║    make test-all      运行完整测试套件           ║"
	@echo "║    make test-cov      测试 + 覆盖率报告          ║"
	@echo "║    make test-integ    集成测试                   ║"
	@echo "║                                                  ║"
	@echo "║  构建和部署:                                     ║"
	@echo "║    make build         构建 Docker 镜像           ║"
	@echo "║    make up            启动 Docker 服务           ║"
	@echo "║    make down          停止 Docker 服务           ║"
	@echo "║    make docs           构建文档                   ║"
	@echo "║                                                  ║"
	@echo "║  工具:                                           ║"
	@echo "║    make clean         清理临时文件               ║"
	@echo "║    make benchmark     性能基准测试                ║"
	@echo "║    make load-test     负载测试                   ║"
	@echo "║                                                  ║"
	@echo "╚══════════════════════════════════════════════════╝"

# ==============
# 安装命令
# ==============

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

install-ml:
	pip install -e ".[ml]"

install-hardware:
	pip install -e ".[hardware]"

install-all:
	pip install -e ".[all]"

# ==============
# 代码质量
# ==============

lint:
	@echo "▶ Running Ruff Linting..."
	ruff check .
	@echo "✅ Linting passed!"

format:
	@echo "▶ Formatting code with Black..."
	black .
	@echo "▶ Sorting imports with isort..."
	isort .
	@echo "✅ Code formatted!"

format-check:
	@echo "▶ Checking formatting..."
	black --check .
	isort --check-only .

typecheck:
	@echo "▶ Running mypy type checking..."
	mypy core_workshop/core/ --ignore-missing-imports
	@echo "✅ Type checking passed!"

security:
	@echo "▶ Running security audit..."
	python scripts/quality_check.py --skip-tests

quality:
	@echo "▶ Running full quality check..."
	python scripts/quality_check.py

quality-fix:
	@echo "▶ Running quality check with auto-fix..."
	python scripts/quality_check.py --fix

# ==============
# 测试命令
# ==============

test:
	@echo "▶ Running unit tests..."
	pytest tests/unit/ -v

test-all:
	@echo "▶ Running all tests..."
	pytest tests/ -v --cov=core_workshop --cov-report=term-missing

test-cov:
	@echo "▶ Running tests with coverage report..."
	pytest tests/ -v --cov=core_workshop --cov-report=html --cov-fail-under=80
	@echo "📄 Coverage report: htmlcov/index.html"

test-integ:
	@echo "▶ Running integration tests..."
	pytest tests/integration/ -v

test-parallel:
	@echo "▶ Running tests in parallel..."
	pytest tests/ -v -n auto

test-fast:
	@echo "▶ Running fast tests only..."
	pytest tests/ -v -m "not slow" -x

# ==============
# 构建和部署
# ==============

build:
	@echo "▶ Building Docker image..."
	docker build -t workshop:latest .
	@echo "✅ Build complete!"

build-no-cache:
	docker build --no-cache -t workshop:latest .

up:
	@echo "▶ Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📊 Dashboard: http://localhost:3000"
	@echo "📈 Prometheus: http://localhost:9091"
	@echo "📝 Logs: docker-compose logs -f workshop-app"

down:
	@echo "▶ Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped!"

restart:
	docker-compose restart

logs:
	docker-compose logs -f workshop-app

status:
	docker-compose ps

# ==============
# 文档构建
# ==============

docs:
	@echo "▶ Building documentation..."
	cd docs && make html
	@echo "📄 Documentation built: docs/build/html/index.html"

docs-clean:
	cd docs && make clean

api-docs:
	@echo "▶ Generating API documentation..."
	pdoc core_workshop -o docs/api

# ==============
# 工具命令
# ==============

clean:
	@echo "▶ Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info .coverage htmlcov/
	rm -rf reports/ coverage.xml
	@echo "✅ Clean complete!"

benchmark:
	@echo "▶ Running performance benchmarks..."
	python scripts/performance_benchmark_v1_vs_v2.py

load-test:
	@echo "▶ Starting load tester..."
	python scripts/load_tester.py --full-suite

ops-daily:
	@echo "▶ Running daily maintenance..."
	python scripts/ops_toolkit.py --daily-maintenance

ops-health:
	@echo "▶ Running health check..."
	python scripts/ops_toolkit.py --health-check

ops-backup:
	@echo "▶ Creating backup..."
	python scripts/ops_toolkit.py --backup --type full

code-quality:
	@echo "▶ Running code quality checker..."
	python scripts/code_quality_checker.py core_workshop/core/

# ==============
# Git 辅助
# ==============

prepare-commit:
	make format
	make lint
	test-fast

pre-push:
	make quality
	test-all

# ==============
# 信息显示
# ==============

info:
	@echo "╔═══════════════════════════════════════════╗"
	@echo "║    Workshop V2.0 项目信息                 ║"
	@echo "╠═══════════════════════════════════════════╣"
	@echo "║  版本:     2.0.0                          ║"
	@echo "║  Python:   ≥3.8                           ║"
	@echo "║  许可证:   GPL-3.0                        ║"
	@echo "║                                          ║"
	@echo "║  核心模块:                                ║"
	@echo "║    - BasePipeline (ABC)                   ║"
	@echo "║    - ConfigManager                       ║"
	@echo "║    - InputValidator                      ║"
	@echo "║    - IOManager                           ║"
	@echo "║    - WorkshopMetrics                     ║"
	@echo "║    - BenchmarkSuite                      ║"
	@echo "║    - CodeSecurityScanner                 ║"
	@echo "║                                          ║"
	@echo "║  Pipeline 模块:                          ║"
	@echo "║    - Ingest / Quality / Enhance          ║"
	@echo "║    - Calibrate / Pack / Delivery         ║"
	@echo "║                                          ║"
	@echo "║  文档:                                    ║"
	@echo "║    - README.md                           ║"
	@echo "║    - API_REFERENCE.md                    ║"
	@echo "║    - DEVELOPER_GUIDE.md                  ║"
	@echo "║    - CONTRIBUTING.md                     ║"
	@echo "║    - CHANGELOG.md                        ║"
	@echo "╚═══════════════════════════════════════════╝"

version:
	@python -c "from core_workshop import get_info; import json; print(json.dumps(get_info(), indent=2, ensure_ascii=False))"
