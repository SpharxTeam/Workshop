# Workshop 测试指南

## 📋 测试数据说明

测试数据位于: `workshop/partdata/tests/raw/`

包含以下测试文件：

| 文件名 | 大小 | 类型 | 用途 |
|--------|------|------|------|
| `.gitkeep` | 102B | 占位文件 | 保持目录结构 |
| `VID20260219152049.mp4` | 17.3MB | 视频文件 | 通用视频测试数据 |
| `d435i_walk_around.bag` | 722MB | ROS Bag | RealSense D435i 环绕行走数据 |
| `d435i_walking.bag` | 841MB | ROS Bag | RealSense D435i 行走数据 |
| `depth_under_water.bag` | 1.7GB | ROS Bag | 水下深度数据测试 |
| `outdoors.bag` | 4.2GB | ROS Bag | 户外环境数据 |
| `stairs.bag` | 4.1GB | ROS Bag | 楼梯场景数据 |

## 🚀 测试启动方式

### 方法一：使用 Docker 容器测试（推荐）

```bash
# 1. 进入 workshop 目录
cd workshop

# 2. 构建基础镜像（如果尚未构建）
docker-compose build base

# 3. 构建测试模块镜像
docker-compose build ingest

# 4. 使用测试数据运行特定模块
# 测试数据导入模块
docker run --rm -v "$(pwd)/partdata/tests/raw:/data/input:ro" \
  -v "$(pwd)/partdata/workshop_output:/data/output" \
  workshop-ingest:latest \
  --input /data/input/d435i_walk_around.bag \
  --output /data/output/test_scene_001

# 5. 查看处理结果
ls -la partdata/workshop_output/
```

### 方法二：本地 Python 环境测试

```bash
# 1. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt
pip install -r requirements.dev.txt

# 3. 设置环境变量
export PYTHONPATH=./common/scripts
export CONFIG_DIR=./common/configs

# 4. 运行单个模块测试
python -m pipelines.00_ingest.runner \
  --input partdata/tests/raw/d435i_walk_around.bag \
  --output partdata/workshop_output/test_scene_001

# 5. 运行完整流水线测试
./scripts/pipeline/run_full.sh partdata/tests/raw/d435i_walk_around.bag
```

### 方法三：使用 pytest 单元测试

```bash
# 1. 安装测试依赖
pip install pytest pytest-cov

# 2. 运行所有测试
pytest common/tests/ -v

# 3. 运行特定模块测试
pytest common/tests/test_ingest.py::TestIngestModule -v

# 4. 生成覆盖率报告
pytest --cov=workshop --cov-report=html common/tests/
```

## 🧪 模块测试说明

### 1. 数据导入模块 (00_ingest) 测试

```bash
# 测试不同类型的输入文件
python -m pipelines.00_ingest.runner \
  --input partdata/tests/raw/d435i_walk_around.bag \
  --output partdata/workshop_output/test_import_bag

python -m pipelines.00_ingest.runner \
  --input partdata/tests/raw/VID20260219152049.mp4 \
  --output partdata/workshop_output/test_import_video
```

### 2. 质量检测模块 (01_quality) 测试

```bash
# 需要先运行数据导入生成中间数据
python -m pipelines.01_quality.runner \
  --input partdata/workshop_output/test_scene_001 \
  --output partdata/workshop_output/test_quality_report
```

### 3. 完整流水线测试

```bash
# 使用脚本运行完整处理流程
./scripts/pipeline/run_full.sh partdata/tests/raw/stairs.bag

# 或手动依次运行各模块
python -m pipelines.00_ingest.runner --input partdata/tests/raw/outdoors.bag --output temp_output/scene1
python -m pipelines.01_quality.runner --input temp_output/scene1 --output temp_output/scene1_quality
python -m pipelines.02_enhance.runner --input temp_output/scene1 --output temp_output/scene1_enhanced
```

## 📊 测试验证

### 输出结果检查

```bash
# 检查生成的文件结构
tree partdata/workshop_output/test_scene_001/

# 验证关键输出文件
ls -la partdata/workshop_output/test_scene_001/
# 应包含：
# - rgb_videos/     # RGB视频序列
# - depth_maps/     # 深度图序列
# - imu_data/       # IMU数据
# - timestamps.csv  # 时间戳文件
# - metadata.json   # 元数据
```

### 日志查看

```bash
# 查看处理日志
tail -f logs/pipeline.log

# Docker容器日志
docker-compose logs -f ingest
docker-compose logs -f quality
```

## ⚙️ 测试配置

### 环境变量设置

```bash
# 创建测试专用环境文件
cp .env.template .env.test

# 编辑 .env.test 文件，设置测试相关配置
LOG_LEVEL=DEBUG
MAX_WORKERS=2
MEMORY_LIMIT_GB=4
PARALLEL_PROCESSING=false
```

### 测试资源配置

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-runner:
    build: .
    environment:
      - TEST_MODE=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./partdata/tests/raw:/data/input:ro
      - ./partdata/test_output:/data/output
    command: ["python", "-m", "pytest", "tests/", "-v"]
```

## 🛠️ 故障排除

### 常见问题

1. **权限问题**
   ```bash
   # 确保输出目录可写
   chmod 755 partdata/workshop_output/
   sudo chown -R $USER partdata/
   ```

2. **依赖缺失**
   ```bash
   # 重新安装依赖
   pip install --force-reinstall -r requirements.txt
   ```

3. **Docker构建失败**
   ```bash
   # 清理并重新构建
   docker-compose down
   docker-compose build --no-cache
   ```

4. **内存不足**
   ```bash
   # 调整资源配置
   export MAX_WORKERS=1
   export MEMORY_LIMIT_GB=2
   ```

## 📈 性能测试

### 基准测试脚本

```bash
#!/bin/bash
# benchmark_test.sh

echo "🚀 开始性能基准测试"

# 测试不同大小的文件
for file in partdata/tests/raw/*.bag; do
    echo "测试文件: $(basename $file)"
    start_time=$(date +%s)
    
    python -m pipelines.00_ingest.runner \
        --input "$file" \
        --output "partdata/workshop_output/bench_$(basename $file .bag)" \
        --benchmark
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo "处理时间: ${duration}秒"
    echo "---"
done
```

## 📝 测试报告

测试完成后，系统会自动生成测试报告：

- **处理报告**: `partdata/workshop_output/*/processing_report.json`
- **质量报告**: `partdata/workshop_output/*/quality_report.json`
- **性能统计**: `partdata/workshop_output/*/performance_stats.json`

可以通过以下方式查看：

```bash
# 查看JSON格式报告
cat partdata/workshop_output/test_scene_001/processing_report.json | jq .

# 生成HTML报告
python scripts/generate_test_report.py partdata/workshop_output/test_scene_001
```

---
**最后更新**: 2026年2月22日  
**测试负责人**: Spharx 测试团队