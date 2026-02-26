# Workshop Scripts 结构优化方案

## 当前结构分析

### Deepness Scripts 结构（标杆项目）
```
deepness/scripts/
├── dispose/                    # 清理相关脚本
│   ├── dispose_build_all.sh    # 构建所有镜像
│   └── dispose_deploy.sh       # 部署生产线
└── download/                   # 下载相关脚本
    ├── download_deps.sh        # 下载依赖
    ├── download_models.sh      # 下载模型
    └── download_sources.sh     # 下载源码
```

### Workshop Scripts 当前结构
```
workshop/scripts/
├── pipeline/                   # 流水线相关
│   └── run_full.sh            # 运行完整流水线
├── utils/                      # 工具脚本
│   ├── config_loader.py       # 配置加载器
│   ├── generate_realistic_calibration.py  # 标定生成
│   └── github_fetch.sh        # GitHub获取
├── bootstrap.sh               # 项目初始化
├── build_all.sh               # 构建所有镜像
├── build_base.sh              # 构建基础镜像
├── deploy.sh                  # 部署脚本
├── download_deps.sh           # 下载依赖
├── download_models.sh         # 下载模型
├── download_sources.sh        # 下载源码
├── optimize_structure.bat     # 结构优化(windows)
└── optimize_structure.sh      # 结构优化(linux)
```

## 结构优化建议

### 1. 目录结构调整

#### 1.1 创建功能性子目录
将脚本按功能分类到相应目录中：

```
workshop/scripts/
├── build/                     # 构建相关脚本（新增）
│   ├── build_all.sh          # 构建所有镜像
│   └── build_base.sh         # 构建基础镜像
├── deploy/                    # 部署相关脚本（新增）
│   └── deploy.sh             # 部署脚本
├── dispose/                   # 清理相关脚本（新增）
│   └── dispose_structure.sh  # 结构清理优化
├── download/                  # 下载相关脚本（移动）
│   ├── download_deps.sh      # 下载依赖
│   ├── download_models.sh    # 下载模型
│   └── download_sources.sh   # 下载源码
├── init/                      # 初始化相关脚本（新增）
│   └── bootstrap.sh          # 项目初始化
├── pipeline/                  # 流水线相关脚本（保持）
│   └── run_full.sh           # 运行完整流水线
├── utils/                     # 工具脚本（保持）
│   ├── config_loader.py
│   ├── generate_realistic_calibration.py
│   └── github_fetch.sh
└── validate/                  # 验证相关脚本（新增）
    └── validate_setup.sh     # 环境验证
```

### 2. 脚本命名规范化

#### 2.1 命名约定
- **动词开头**: `build_`, `deploy_`, `download_`, `validate_`
- **功能明确**: 名称应清楚表达脚本用途
- **一致性**: 与 Deepness 项目保持命名风格一致

#### 2.2 具体调整建议
```
当前名称                    →    建议名称
bootstrap.sh               →    init_project.sh
build_all.sh               →    build_images.sh
build_base.sh              →    build_base_image.sh
deploy.sh                  →    deploy_production.sh
optimize_structure.sh      →    dispose_structure.sh
optimize_structure.bat     →    dispose_structure.bat
```

### 3. 脚本内容标准化

#### 3.1 统一头部信息
所有脚本应包含：
```bash
#!/bin/bash
set -euo pipefail  # 严格错误处理

# 脚本描述
# 作者: Spharx Team
# 版本: 1.0
# 日期: 2026-02-22

# 颜色定义（可选）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 日志函数
log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
```

#### 3.2 统一路径处理
```bash
# 标准化路径获取
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

#### 3.3 统一错误处理
```bash
# 检查必要命令
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "未找到命令: $1，请先安装。"
        exit 1
    fi
}

# 检查必要目录
check_directory() {
    if [ ! -d "$1" ]; then
        log_error "目录不存在: $1"
        exit 1
    fi
}
```

### 4. 新增必要脚本

#### 4.1 验证脚本
创建 `validate/validate_setup.sh`：
- 检查系统环境
- 验证依赖安装
- 确认配置文件

#### 4.2 清理脚本
创建 `dispose/dispose_structure.sh`：
- 清理构建产物
- 清理临时文件
- 重置项目状态

## 实施步骤

### 第一阶段：目录结构调整
```bash
# 1. 创建新目录结构
mkdir -p scripts/{build,deploy,dispose,init,validate}

# 2. 移动现有脚本
mv scripts/build_all.sh scripts/build/build_images.sh
mv scripts/build_base.sh scripts/build/build_base_image.sh
mv scripts/deploy.sh scripts/deploy/deploy_production.sh
mv scripts/bootstrap.sh scripts/init/init_project.sh
mv scripts/download_*.sh scripts/download/

# 3. 处理优化脚本
mv scripts/optimize_structure.sh scripts/dispose/dispose_structure.sh
mv scripts/optimize_structure.bat scripts/dispose/dispose_structure.bat
```

### 第二阶段：脚本标准化
1. 为所有脚本添加标准头部
2. 统一路径处理逻辑
3. 添加错误处理机制
4. 标准化日志输出格式

### 第三阶段：新增脚本开发
1. 开发验证脚本 `validate/validate_setup.sh`
2. 完善清理脚本 `dispose/dispose_structure.sh`
3. 更新相关文档和README

## 预期收益

1. **结构一致性**: 与 Deepness 项目保持相同的脚本组织方式
2. **维护性提升**: 功能分类清晰，便于查找和维护
3. **标准化程度**: 统一的脚本格式和错误处理机制
4. **扩展性增强**: 为未来新增脚本预留清晰的目录结构
5. **团队协作**: 统一的命名规范便于团队成员理解和使用

## 注意事项

1. 修改前备份重要脚本
2. 更新所有脚本间的相互调用路径
3. 同步更新文档中的脚本引用
4. 测试所有功能确保兼容性
5. 考虑向后兼容性，必要时提供迁移指南