# 贡献指南

感谢您对 Workshop 项目的关注和支持！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了 Bug 或有功能建议，请：

1. 检查是否已有相关的 [Issue](https://gitee.com/spharx/spharxhub/issues)
2. 创建新的 Issue，提供详细的描述和复现步骤
3. 使用合适的标签分类（bug/feature/enhancement）

### 代码贡献

#### 开发流程

1. **Fork 项目**
   ```bash
   git clone https://gitee.com/your-username/spharxhub.git
   cd spharxhub/workshop
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **开发和测试**
   ```bash
   # 安装开发依赖
   pip install -r requirements.dev.txt
   
   # 运行测试
   pytest tests/
   
   # 代码检查
   flake8 .
   black .
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **发起 Pull Request**
   - 描述更改内容和解决的问题
   - 关联相关的 Issue
   - 等待代码审查

### 文档贡献

- 完善现有文档的不足之处
- 添加使用示例和最佳实践
- 翻译文档到其他语言
- 修正错别字和语法错误

## 📋 开发规范

### 代码风格

遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范：

```bash
# 自动格式化代码
black .
# 检查代码质量
flake8 .
# 类型检查
mypy .
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: 添加新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

### 测试要求

- 新功能必须包含单元测试
- 修复 Bug 需要添加回归测试
- 测试覆盖率应达到 80% 以上
- 确保所有测试通过后再提交

## 🛠️ 开发环境设置

### 本地开发

```bash
# 克隆项目
git clone https://gitee.com/spharx/spharxhub.git
cd spharxhub/workshop

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements.dev.txt

# 运行测试
pytest tests/
```

### Docker 开发

```bash
# 构建开发镜像
docker-compose -f docker-compose.dev.yml build

# 启动开发环境
docker-compose -f docker-compose.dev.yml up
```

## 📊 项目结构

```
workshop/
├── common/           # 公共组件
│   ├── configs/     # 配置文件
│   ├── schemas/     # 数据模型
│   └── scripts/     # 公共脚本
├── pipelines/        # 处理管道
├── hardware/         # 硬件控制
├── dashboard/        # 监控面板
├── tests/            # 测试文件
└── docs/             # 文档资料
```

## 🎯 贡献重点领域

### 🚀 急需帮助的领域

- **性能优化**: 提升数据处理速度和资源利用率
- **硬件支持**: 扩展更多传感器和设备支持
- **算法改进**: 优化质量检测和目标识别算法
- **文档完善**: 补充使用指南和技术文档
- **测试覆盖**: 增加单元测试和集成测试

### 🌟 新功能建议

- 实时流处理支持
- 多相机同步优化
- 云端部署方案
- 更多输出格式支持
- 可视化分析工具

## 📞 联系方式

- **Issue tracker**: [Gitee Issues](https://gitee.com/spharx/spharxhub/issues)
- **邮件**: contact@spharx.com
- **微信群**: 扫描二维码加入开发者群

## 📜 许可证

本项目采用 MIT 许可证，您的贡献也将遵循相同的许可证条款。

---

再次感谢您的贡献！让我们一起打造更好的物理世界数据基础设施。 🚀