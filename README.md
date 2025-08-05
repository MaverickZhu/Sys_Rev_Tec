# 政府采购项目审查分析系统

[![CI/CD](https://github.com/your-org/Sys_Rev_Tec/workflows/CI/badge.svg)](https://github.com/your-org/Sys_Rev_Tec/actions)
[![codecov](https://codecov.io/gh/your-org/Sys_Rev_Tec/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/Sys_Rev_Tec)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个现代化的政府采购项目审查分析系统，基于 FastAPI 构建，支持文档管理、OCR 识别、智能分析和实时监控。

## ✨ 特性


## 🚀 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (前端开发)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Sys_Rev_Tec
```

2. **安装依赖**
```bash
# 后端依赖
pip install -r requirements.txt

# AI服务依赖
pip install -r requirements-ai.txt

# 前端依赖
cd frontend
npm install
```

3. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库等信息
```

4. **初始化数据库**
```bash
alembic upgrade head
python scripts/init_db.py
```

5. **启动服务**
```bash
# 启动主应用
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动AI服务
cd ai_service
uvicorn main:app --host 0.0.0.0 --port 8001

# 启动前端（开发模式）
cd frontend
npm run dev
```

- 🚀 **高性能**: 基于 FastAPI 的异步架构
- 📄 **文档管理**: 支持多格式文档上传、存储和管理
- 🔍 **OCR 识别**: 集成 PaddleOCR 进行文档内容提取
- 🔐 **安全认证**: JWT 认证 + RBAC 权限控制
- 📊 **实时监控**: Prometheus + Grafana 监控仪表板
- 🧪 **高质量**: 90%+ 测试覆盖率，完整的 CI/CD 流程
- 🐳 **容器化**: Docker 部署，支持生产环境
- 📝 **API 文档**: 自动生成的 OpenAPI/Swagger 文档

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+ (主数据库) + Redis 7+ (缓存)
- **ORM**: SQLAlchemy 2.0 (异步)
- **认证**: JWT + OAuth2
- **OCR**: PaddleOCR 3.1.0
- **监控**: Prometheus + Grafana
- **日志**: 结构化日志 (JSON 格式)

### 开发工具
- **代码质量**: Black, isort, Flake8, MyPy, Bandit
- **测试**: pytest + pytest-cov
- **CI/CD**: GitHub Actions
- **容器**: Docker + Docker Compose
- **文档**: OpenAPI/Swagger

## 🚀 快速开始

### 使用 Docker (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd Sys_Rev_Tec

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

服务地址:
- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Grafana 监控**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### 本地开发

```bash
# 1. 设置虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库等信息

# 4. 数据库迁移
alembic upgrade head

# 5. 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


## 📚 文档

- [API文档](http://localhost:8000/docs) - Swagger UI
- [用户指南](docs/USER_GUIDE.md) - 详细使用说明
- [部署指南](README_Docker.md) - Docker部署说明
- [开发文档](DEVELOPMENT.md) - 开发环境配置



```
.
├── app/                     # 应用代码
│   ├── main.py             # FastAPI 应用入口
│   ├── core/               # 核心配置
│   │   ├── config.py       # 环境配置
│   │   └── security.py     # 安全相关
│   ├── db/                 # 数据库
│   │   ├── base.py         # 数据库基类
│   │   ├── session.py      # 数据库会话
│   │   └── init_db.py      # 数据库初始化
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic 模式
│   ├── crud/               # CRUD 操作
│   ├── api/                # API 路由
│   │   └── v1/endpoints/   # API 端点
│   ├── services/           # 业务逻辑服务
│   ├── middleware/         # 中间件
│   └── utils/              # 工具函数
├── tests/                  # 测试代码
├── alembic/                # 数据库迁移
├── docker/                 # Docker 配置
├── scripts/                # 脚本工具
├── docs/                   # 文档
└── monitoring/             # 监控配置
```

## 📖 文档

- [开发者指南](DEVELOPMENT.md) - 详细的开发环境设置和开发流程
- [API 文档](docs/API.md) - RESTful API 接口文档
- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署指南
- [架构设计](docs/ARCHITECTURE.md) - 系统架构和设计文档

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ -v --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

当前测试覆盖率: **90%+** ✅

## 🔧 开发工具

```bash
# 代码格式化
make format

# 代码质量检查
make lint

# 运行测试
make test

# 启动开发服务器
make run-dev

# 查看所有可用命令
make help
```

## 📊 监控

系统集成了完整的监控和日志系统:

- **Prometheus**: 指标收集和存储
- **Grafana**: 可视化监控仪表板
- **结构化日志**: JSON 格式日志，便于分析
- **错误追踪**: 自动错误检测和报警

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详细信息。

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问，请:

1. 查看 [文档](docs/)
2. 搜索 [Issues](https://github.com/your-org/Sys_Rev_Tec/issues)
3. 创建新的 [Issue](https://github.com/your-org/Sys_Rev_Tec/issues/new)

---

**版本**: v1.0.0-beta  
**最后更新**: 2025-01-25