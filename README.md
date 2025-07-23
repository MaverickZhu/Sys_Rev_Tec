# 项目审查系统 (Python 重构)

这是一个使用 Python 技术栈重构的项目审查系统。

## 技术栈

- **后端框架:** FastAPI
- **数据库:** MongoDB (使用 Motor 异步驱动)
- **部署:** Docker

## 项目结构

```
.
├── app/                  # 应用代码
│   ├── __init__.py
│   ├── main.py           # FastAPI 应用入口
│   ├── core/             # 核心配置
│   │   ├── __init__.py
│   │   └── config.py     # 环境变量和配置
│   ├── db/               # 数据库连接和会话
│   │   ├── __init__.py
│   │   └── session.py
│   ├── models/           # 数据模型 (Pydantic)
│   │   └── __init__.py
│   ├── schemas/          # API 数据模式 (Pydantic)
│   │   └── __init__.py
│   ├── crud/             # 数据访问操作 (Create, Read, Update, Delete)
│   │   └── __init__.py
│   ├── api/              # API 路由
│   │   ├── __init__.py
│   │   └── v1/             # API 版本 1
│   │       ├── __init__.py
│   │       └── endpoints/  # 各个功能的路由
│   │           └── __init__.py
│   └── services/         # 业务逻辑服务
│       └── __init__.py
├── tests/                # 测试代码
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt      # Python 依赖
└── README.md
```

## 后续步骤

1.  **创建基础结构:** 创建上述目录结构和文件。
2.  **设置 FastAPI:** 初始化 FastAPI 应用并创建一个简单的健康检查端点。
3.  **添加依赖:** 在 `requirements.txt` 中添加 `fastapi` 和 `uvicorn`。
4.  **定义模型和模式:** 根据 `项目审查要点分析表.csv` 和之前的需求，定义数据模型和 API 模式。
5.  **实现 CRUD 操作:** 为核心模型实现数据库操作。
6.  **构建 API 端点:** 创建用于用户、文档、OCR 和审查流程的 API 端点。
7.  **集成 OCR 功能:** 将 OCR 功能作为一个独立的服务或模块集成进来。
8.  **实现认证和授权:** 使用 JWT 实现用户认证和基于角色的授权。
9.  **编写测试:** 为关键功能编写单元测试和集成测试。
10. **容器化:** 使用 Docker 和 Docker Compose 进行容器化部署。

让我们从创建 `requirements.txt` 文件开始。