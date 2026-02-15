#!/bin/bash

# Workshop 项目初始化脚本

set -e  # 遇到错误时退出

echo "🚀 开始初始化 Workshop 项目..."

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "🔧 升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "🔧 安装项目依赖..."
pip install -r requirements.txt

# 复制环境变量模板
if [ ! -f ".env" ]; then
    echo "🔧 创建环境变量文件..."
    cp .env.template .env
    echo "⚠️  请编辑 .env 文件填写实际配置"
fi

# 创建数据目录
echo "🔧 创建数据目录结构..."
mkdir -p data/{raw,processed,datasets}
mkdir -p logs

# 初始化日志文件
echo "🔧 初始化日志文件..."
touch logs/pipeline.log

# 安装硬件驱动（可选）
echo ""
echo "🔧 是否安装硬件驱动？(y/n)"
read -r install_drivers
if [[ $install_drivers == "y" ]] || [[ $install_drivers == "Y" ]]; then
    echo "🔧 安装 RealSense 驱动..."
    bash hardware/scripts/install_drivers.sh
fi

# 运行测试
echo ""
echo "🧪 是否运行测试？(y/n)"
read -r run_tests
if [[ $run_tests == "y" ]] || [[ $run_tests == "Y" ]]; then
    echo "🧪 运行单元测试..."
    pytest tests/ -v
fi

echo ""
echo "🎉 项目初始化完成！"
echo ""
echo "下一步操作："
echo "1. 编辑 .env 文件配置环境变量"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 启动监控面板: streamlit run dashboard/app.py"
echo "4. 运行数据处理管道: python -m pipelines.00_ingest.realsense_parser"