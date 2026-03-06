# 开发指南

## 项目结构

- `pipelines/`: 核心模块代码
- `scripts/`: 自动化脚本
- `tests/`: 单元测试
- `common/`: 公共组件
- `produce/`: 数据输入输出

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交代码并添加测试
4. 提交 Pull Request

## 开发环境设置

### 安装依赖
pip install -r scripts/requirements-dev.txt

### 运行测试
make test

### 虚拟环境管理建议

当前 `venv/` 目录位于项目根目录，虽然已被 `.gitignore` 忽略，但为了更干净的项目结构，建议将虚拟环境放置在项目外部（例如 `~/venvs/workshop`）。您可以选择：

- **保留当前**：只要 `.gitignore` 正确，不影响版本控制。
- **迁移外部**：
  deactivate
  mv venv ~/venvs/workshop
  # 以后激活使用
  source ~/venvs/workshop/bin/activate

### 验证优化结果

执行以下命令确保一切正常：

source venv/bin/activate   # 如果还在原位置
make test
make docs

如果测试和文档都能正常工作，则优化成功。