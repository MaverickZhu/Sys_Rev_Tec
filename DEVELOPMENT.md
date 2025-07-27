# 开发者指南

本文档为政府采购项目审查分析系统的开发者提供详细的开发指南。

## 目录

- [快速开始](#快速开始)
- [开发环境设置](#开发环境设置)
- [代码质量](#代码质量)
- [测试](#测试)
- [调试](#调试)
- [部署](#部署)
- [贡献指南](#贡献指南)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Sys_Rev_Tec
```

### 2. 设置虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装生产依赖
pip install -r requirements.txt

# 或使用 Makefile
make install-dev
```

### 4. 设置环境变量

复制 `.env.example` 到 `.env` 并配置必要的环境变量：

```bash
cp .env.example .env
```

### 5. 启动开发服务器

```bash
# 使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Makefile
make run-dev
```

## 开发环境设置

### 推荐的开发工具

- **IDE**: Visual Studio Code (已配置项目设置)
- **Python**: 3.8+ (推荐 3.11)
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7+
- **容器**: Docker & Docker Compose

### VSCode 扩展

项目已配置推荐扩展列表，首次打开项目时 VSCode 会提示安装。主要扩展包括：

- Python 开发套件
- 代码质量检查工具
- Git 和 GitHub 集成
- Docker 支持
- 数据库客户端

### Pre-commit Hooks

设置 pre-commit hooks 确保代码质量：

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 或使用 Makefile
make setup-pre-commit
```

## 代码质量

### 代码风格

项目使用以下工具确保代码质量：

- **Black**: 代码格式化 (行长度: 88)
- **isort**: 导入语句排序
- **Flake8**: 代码风格检查
- **MyPy**: 类型检查
- **Bandit**: 安全检查
- **Ruff**: 快速代码检查 (可选)

### 运行代码质量检查

```bash
# 运行所有检查
make lint

# 自动修复问题
make format

# 使用自定义脚本
python scripts/quality_check.py --fix --verbose

# 使用 Ruff (更快)
make lint-ruff
```

### 配置文件

- `.pre-commit-config.yaml`: Pre-commit hooks 配置
- `pyproject.toml`: 工具统一配置
- `.vscode/settings.json`: VSCode 项目设置

## 测试

### 测试结构

```
tests/
├── unit/           # 单元测试
├── integration/    # 集成测试
├── e2e/           # 端到端测试
├── fixtures/      # 测试数据
└── conftest.py    # pytest 配置
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行测试并生成覆盖率报告
pytest tests/ -v --cov=app --cov-report=html

# 使用 Makefile
make test
make test-cov
make test-unit
make test-integration
```

### 测试标记

使用 pytest 标记组织测试：

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass

@pytest.mark.slow
def test_slow_function():
    pass
```

### 测试覆盖率

- 目标覆盖率: 90%+
- 覆盖率报告: `htmlcov/index.html`
- CI/CD 自动上传到 Codecov

## 调试

### VSCode 调试配置

项目已配置多种调试场景：

- FastAPI 开发服务器调试
- 当前文件调试
- 测试调试
- OCR 处理调试
- 数据库操作调试

### 日志调试

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 性能分析

```bash
# 使用 cProfile
python -m cProfile -o profile.stats app/main.py

# 分析结果
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

## 部署

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 使用 Makefile
make docker-build
make docker-up
make docker-down
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 使用 Makefile
make db-revision
make db-upgrade
make db-downgrade
```

### 监控

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **应用日志**: `logs/app.log`

## 贡献指南

### 分支策略

- `main`: 生产分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支
- `hotfix/*`: 热修复分支

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式化
refactor: 重构代码
test: 添加测试
chore: 构建过程或辅助工具的变动
```

### Pull Request 流程

1. 从 `develop` 创建功能分支
2. 开发并测试功能
3. 运行代码质量检查
4. 提交 Pull Request
5. 代码审查
6. 合并到 `develop`

### 代码审查清单

- [ ] 代码符合项目风格
- [ ] 添加了适当的测试
- [ ] 测试通过
- [ ] 文档已更新
- [ ] 没有安全问题
- [ ] 性能影响可接受

## 常见问题

### Q: 如何添加新的 API 端点？

A: 
1. 在 `app/api/v1/` 下创建或修改路由文件
2. 添加相应的 Pydantic 模型
3. 实现业务逻辑
4. 添加测试
5. 更新 API 文档

### Q: 如何添加新的数据库模型？

A:
1. 在 `app/models/` 下创建模型文件
2. 运行 `alembic revision --autogenerate -m "描述"`
3. 检查生成的迁移文件
4. 运行 `alembic upgrade head`

### Q: 如何添加新的监控指标？

A:
1. 在 `app/core/monitoring.py` 中定义指标
2. 在相应的服务中记录指标
3. 更新 Grafana 仪表板

### Q: 测试失败怎么办？

A:
1. 检查测试输出和错误信息
2. 确保测试环境正确设置
3. 检查数据库和 Redis 连接
4. 运行单个测试进行调试

## 资源链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pytest 文档](https://docs.pytest.org/)
- [Docker 文档](https://docs.docker.com/)
- [Prometheus 文档](https://prometheus.io/docs/)
- [Grafana 文档](https://grafana.com/docs/)

## 联系方式

如有问题，请通过以下方式联系：

- 创建 GitHub Issue
- 发送邮件到开发团队
- 在团队聊天群中讨论

---

**注意**: 请确保在提交代码前运行所有质量检查和测试！