# 系统审查技术项目 - Docker 容器化部署指南

本文档详细介绍如何使用 Docker 容器化部署系统审查技术项目，包括数据库、OCR 服务和应用程序的完整容器化解决方案。

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [服务架构](#服务架构)
- [部署步骤](#部署步骤)
- [管理命令](#管理命令)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排除](#故障排除)
- [性能优化](#性能优化)

## 🔧 系统要求

### 硬件要求
- **CPU**: 4核心以上（推荐8核心）
- **内存**: 8GB以上（推荐16GB）
- **存储**: 50GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **Python**: 3.9+ (用于部署脚本)

### 安装 Docker

#### Ubuntu/Debian
```bash
# 更新包索引
sudo apt update

# 安装必要的包
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 设置稳定版仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将用户添加到 docker 组
sudo usermod -aG docker $USER
```

#### Windows
1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 启动 Docker Desktop
3. 确保启用 WSL 2 后端（推荐）

#### macOS
1. 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 启动 Docker Desktop

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd Sys_Rev_Tec
```

### 2. 配置环境变量
```bash
# 复制环境配置文件
cp .env.docker .env

# 编辑环境变量（根据需要修改）
nano .env
```

### 3. 构建和启动服务
```bash
# 使用部署脚本（推荐）
python scripts/docker_deploy.py --env production --action deploy

# 或者使用 Docker Compose
docker-compose up -d
```

### 4. 验证部署
```bash
# 检查服务状态
python scripts/docker_deploy.py --action status

# 执行健康检查
python scripts/docker_deploy.py --action health
```

### 5. 访问应用
- **应用主页**: http://localhost
- **API 文档**: http://localhost/docs
- **健康检查**: http://localhost/health
- **监控指标**: http://localhost/metrics

## ⚙️ 环境配置

### 环境文件说明

项目支持多个环境配置文件：
- `.env` - 默认环境配置
- `.env.docker` - Docker 容器化环境配置
- `.env.production` - 生产环境配置
- `.env.development` - 开发环境配置

### 关键配置项

```bash
# 应用配置
APP_NAME="系统审查技术"
APP_VERSION="1.0.0"
ENVIRONMENT="production"
DEBUG=false

# 数据库配置（PostgreSQL）
DATABASE_URL="postgresql://postgres:your_password@postgres:5432/sys_rev_tech"
DB_HOST="postgres"
DB_PORT=5432
DB_NAME="sys_rev_tech"
DB_USER="postgres"
DB_PASSWORD="your_password"

# Redis 配置
REDIS_URL="redis://redis:6379/0"
REDIS_HOST="redis"
REDIS_PORT=6379

# 安全配置
SECRET_KEY="your-secret-key-here"
JWT_SECRET_KEY="your-jwt-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OCR 配置
TESS_DATA_PATH="/usr/share/tesseract-ocr/4.00/tessdata"
PADDLE_OCR_MODEL_DIR="/app/models/paddleocr"
TROCR_MODEL_NAME="microsoft/trocr-base-printed"

# 文件上传配置
UPLOAD_DIR="/app/uploads"
MAX_FILE_SIZE=104857600
ALLOWED_FILE_TYPES="pdf,png,jpg,jpeg,tiff,bmp"

# 服务端口
APP_PORT=8000
NGINX_PORT=80
NGINX_SSL_PORT=443
```

## 🏗️ 服务架构

### 容器服务

| 服务 | 描述 | 端口 | 依赖 |
|------|------|------|------|
| **app** | FastAPI 应用程序 | 8000 | postgres, redis |
| **postgres** | PostgreSQL 数据库 | 5432 | - |
| **redis** | Redis 缓存服务 | 6379 | - |
| **nginx** | 反向代理和负载均衡 | 80, 443 | app |

### 网络架构

```
┌─────────────────┐
│     Nginx       │ ← 80/443
│  (反向代理)      │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   FastAPI App   │ ← 8000
│   (应用服务)     │
└─────┬───────┬───┘
      │       │
┌─────▼───┐ ┌─▼─────┐
│PostgreSQL│ │ Redis │
│  (数据库) │ │(缓存) │
└─────────┘ └───────┘
```

### 数据卷

- `postgres_data`: PostgreSQL 数据持久化
- `redis_data`: Redis 数据持久化
- `app_uploads`: 文件上传存储
- `app_logs`: 应用日志存储
- `nginx_logs`: Nginx 日志存储

## 📦 部署步骤

### 方法一：使用部署脚本（推荐）

```bash
# 1. 检查环境
python scripts/docker_deploy.py --env production --action build

# 2. 部署服务
python scripts/docker_deploy.py --env production --action deploy

# 3. 验证部署
python scripts/docker_deploy.py --action health
```

### 方法二：使用 Docker Compose

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 初始化数据库

```bash
# 数据库会在容器启动时自动初始化
# 如需手动执行迁移
docker-compose exec app python -m alembic upgrade head
```

## 🎛️ 管理命令

### 使用部署脚本

```bash
# 构建镜像
python scripts/docker_deploy.py --action build [--no-cache]

# 部署服务
python scripts/docker_deploy.py --action deploy [--recreate]

# 停止服务
python scripts/docker_deploy.py --action stop

# 重启服务
python scripts/docker_deploy.py --action restart [--service app]

# 查看状态
python scripts/docker_deploy.py --action status

# 查看日志
python scripts/docker_deploy.py --action logs [--service app] [--tail 100]

# 健康检查
python scripts/docker_deploy.py --action health

# 数据备份
python scripts/docker_deploy.py --action backup

# 清理镜像
python scripts/docker_deploy.py --action cleanup
```

### 使用 Docker Compose

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart [service_name]

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 执行命令
docker-compose exec app bash

# 扩展服务
docker-compose up -d --scale app=3
```

### 数据库管理

```bash
# 连接数据库
docker-compose exec postgres psql -U postgres -d sys_rev_tech

# 备份数据库
docker-compose exec postgres pg_dump -U postgres sys_rev_tech > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U postgres sys_rev_tech < backup.sql

# 查看数据库大小
docker-compose exec postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('sys_rev_tech'));"
```

## 📊 监控和日志

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f nginx

# 查看最近的日志
docker-compose logs --tail=100 app

# 查看实时日志
docker-compose logs -f --tail=0 app
```

### 监控指标

访问以下端点获取监控信息：

- **健康检查**: `GET /health`
- **就绪检查**: `GET /ready`
- **Prometheus 指标**: `GET /metrics`
- **系统信息**: `GET /info`

### 性能监控

```bash
# 查看容器资源使用情况
docker stats

# 查看特定容器资源使用
docker stats sys_rev_tec_app_1

# 查看容器进程
docker-compose top

# 查看磁盘使用
docker system df
```

## 💾 备份和恢复

### 自动备份

```bash
# 使用部署脚本备份
python scripts/docker_deploy.py --action backup

# 备份文件位置
# backups/YYYYMMDD_HHMMSS/
# ├── database.sql
# ├── uploads/
# ├── config/
# └── backup_info.json
```

### 手动备份

```bash
# 备份数据库
mkdir -p backups/$(date +%Y%m%d)
docker-compose exec postgres pg_dump -U postgres sys_rev_tech > backups/$(date +%Y%m%d)/database.sql

# 备份上传文件
cp -r uploads backups/$(date +%Y%m%d)/

# 备份配置文件
cp .env docker-compose.yml backups/$(date +%Y%m%d)/
```

### 数据恢复

```bash
# 恢复数据库
docker-compose exec -T postgres psql -U postgres sys_rev_tech < backups/20231201/database.sql

# 恢复上传文件
cp -r backups/20231201/uploads ./

# 恢复配置文件
cp backups/20231201/.env ./
cp backups/20231201/docker-compose.yml ./
```

### 定期备份设置

创建 cron 任务进行定期备份：

```bash
# 编辑 crontab
crontab -e

# 添加每日备份任务（凌晨2点）
0 2 * * * cd /path/to/Sys_Rev_Tec && python scripts/docker_deploy.py --action backup

# 添加每周清理旧备份任务（周日凌晨3点）
0 3 * * 0 find /path/to/Sys_Rev_Tec/backups -type d -mtime +30 -exec rm -rf {} +
```

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看容器状态
docker-compose ps

# 查看启动日志
docker-compose logs app

# 检查配置文件
docker-compose config
```

#### 2. 数据库连接失败

```bash
# 检查数据库容器状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试数据库连接
docker-compose exec app python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 3. 文件上传失败

```bash
# 检查上传目录权限
docker-compose exec app ls -la /app/uploads

# 修复权限
docker-compose exec app chown -R app:app /app/uploads
docker-compose exec app chmod -R 755 /app/uploads
```

#### 4. OCR 服务异常

```bash
# 检查 OCR 模型文件
docker-compose exec app ls -la /app/models

# 测试 OCR 功能
docker-compose exec app python -c "from app.services.ocr import OCRService; print(OCRService().test_connection())"
```

#### 5. 内存不足

```bash
# 查看内存使用
docker stats --no-stream

# 调整容器内存限制
# 在 docker-compose.yml 中添加：
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### 调试模式

```bash
# 启用调试模式
export DEBUG=true
docker-compose up

# 进入容器调试
docker-compose exec app bash

# 查看详细日志
docker-compose logs -f --tail=1000 app
```

### 重置环境

```bash
# 完全重置（删除所有数据）
docker-compose down -v
docker system prune -a
docker volume prune

# 重新部署
python scripts/docker_deploy.py --env production --action deploy --recreate
```

## ⚡ 性能优化

### 容器资源配置

在 `docker-compose.yml` 中调整资源限制：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 数据库优化

```bash
# 调整 PostgreSQL 配置
# 在 docker/postgres/postgresql.conf 中：
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

### 缓存优化

```bash
# 调整 Redis 配置
# 在 docker-compose.yml 中：
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 网络优化

```bash
# 使用自定义网络
docker network create --driver bridge sys_rev_tech_network

# 在 docker-compose.yml 中指定网络
networks:
  default:
    external:
      name: sys_rev_tech_network
```

### 镜像优化

```dockerfile
# 使用多阶段构建减小镜像大小
FROM python:3.9-slim as builder
# ... 构建阶段

FROM python:3.9-slim as runtime
# ... 运行阶段
```

## 📚 参考资料

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [PostgreSQL Docker 镜像](https://hub.docker.com/_/postgres)
- [Redis Docker 镜像](https://hub.docker.com/_/redis)
- [Nginx Docker 镜像](https://hub.docker.com/_/nginx)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)

## 📞 支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查容器日志：`docker-compose logs`
3. 验证配置文件：`docker-compose config`
4. 提交 Issue 到项目仓库

---

**注意**: 在生产环境中部署前，请确保：
- 修改所有默认密码
- 配置 SSL/TLS 证书
- 设置防火墙规则
- 配置监控和告警
- 制定备份策略