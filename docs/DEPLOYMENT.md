# 部署指南

本文档详细介绍了政府采购项目审查分析系统的部署方法，包括开发环境、测试环境和生产环境的部署配置。

## 目录

- [系统要求](#系统要求)
- [环境配置](#环境配置)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排除](#故障排除)
- [性能优化](#性能优化)

## 系统要求

### 最低配置

- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Linux (Ubuntu 20.04+), Windows 10+, macOS 10.15+

### 推荐配置

- **CPU**: 4 核心或更多
- **内存**: 8GB RAM 或更多
- **存储**: 50GB SSD
- **网络**: 稳定的互联网连接

### 生产环境配置

- **CPU**: 8 核心或更多
- **内存**: 16GB RAM 或更多
- **存储**: 100GB SSD (数据库) + 500GB (文件存储)
- **网络**: 高带宽、低延迟连接
- **负载均衡**: Nginx 或 HAProxy

## 环境配置

### 依赖软件

#### 必需软件

- **Python**: 3.8+ (推荐 3.11)
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Docker**: 20.10+ (可选，推荐)
- **Docker Compose**: 2.0+ (可选，推荐)

#### 可选软件

- **Nginx**: 反向代理和负载均衡
- **Prometheus**: 监控指标收集
- **Grafana**: 监控仪表板
- **Elasticsearch**: 日志聚合 (可选)

### 环境变量

创建 `.env` 文件并配置以下环境变量：

```bash
# 应用配置
APP_NAME="政府采购项目审查分析系统"
APP_VERSION="1.0.0"
ENVIRONMENT="production"  # development, testing, production
DEBUG=false
SECRET_KEY="your-super-secret-key-here"

# 服务器配置
HOST="0.0.0.0"
PORT=8000
WORKERS=4

# 数据库配置
DATABASE_URL="postgresql+asyncpg://username:password@localhost:5432/dbname"
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis 配置
REDIS_URL="redis://localhost:6379/0"
REDIS_PASSWORD="your-redis-password"

# JWT 配置
JWT_SECRET_KEY="your-jwt-secret-key"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=60

# 文件存储配置
UPLOAD_DIR="/app/uploads"
MAX_FILE_SIZE=50  # MB
ALLOWED_EXTENSIONS=".jpg,.jpeg,.png,.pdf,.doc,.docx,.txt"

# OCR 配置
OCR_SERVICE_URL="http://localhost:8001"
OCR_TIMEOUT=30

# 监控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# 日志配置
LOG_LEVEL="INFO"
LOG_FORMAT="json"
LOG_FILE="/var/log/app/app.log"

# 邮件配置 (可选)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# 安全配置
CORS_ORIGINS="http://localhost:3000,https://your-domain.com"
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW=60
```

## Docker 部署

### 快速开始

1. **克隆项目**

```bash
git clone <repository-url>
cd Sys_Rev_Tec
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **启动服务**

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

4. **初始化数据库**

```bash
# 运行数据库迁移
docker-compose exec app alembic upgrade head

# 创建初始数据
docker-compose exec app python -m app.initial_data
```

### 服务访问

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Docker Compose 配置

项目包含以下 Docker Compose 文件：

- `docker-compose.yml`: 开发环境配置
- `docker-compose.prod.yml`: 生产环境配置
- `docker-compose.override.yml`: 本地开发覆盖配置

### 生产环境 Docker 部署

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 或使用 make 命令
make deploy-prod
```

## 生产环境部署

### 1. 服务器准备

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必需软件
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql-15 redis-server nginx git curl

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### CentOS/RHEL

```bash
# 更新系统
sudo yum update -y

# 安装必需软件
sudo yum install -y python3.11 python3-pip postgresql15-server \
    redis nginx git curl

# 安装 Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 2. 数据库设置

#### PostgreSQL 配置

```bash
# 初始化数据库 (仅首次)
sudo postgresql-setup --initdb

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
```

```sql
-- 在 PostgreSQL 中执行
CREATE DATABASE sys_rev_tec;
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE sys_rev_tec TO app_user;
ALTER USER app_user CREATEDB;
\q
```

#### Redis 配置

```bash
# 编辑 Redis 配置
sudo nano /etc/redis/redis.conf

# 设置密码
requirepass your_redis_password

# 启动服务
sudo systemctl start redis
sudo systemctl enable redis
```

### 3. 应用部署

#### 方式一：Docker 部署 (推荐)

```bash
# 1. 克隆代码
git clone <repository-url> /opt/sys_rev_tec
cd /opt/sys_rev_tec

# 2. 配置环境变量
cp .env.example .env.production
# 编辑 .env.production 文件

# 3. 构建和启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. 初始化数据库
docker-compose exec app alembic upgrade head
docker-compose exec app python -m app.initial_data
```

#### 方式二：传统部署

```bash
# 1. 创建应用用户
sudo useradd -m -s /bin/bash appuser
sudo su - appuser

# 2. 克隆代码
git clone <repository-url> ~/sys_rev_tec
cd ~/sys_rev_tec

# 3. 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 6. 数据库迁移
alembic upgrade head
python -m app.initial_data

# 7. 创建 systemd 服务
sudo nano /etc/systemd/system/sys-rev-tec.service
```

#### Systemd 服务配置

```ini
[Unit]
Description=政府采购项目审查分析系统
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=appuser
Group=appuser
WorkingDirectory=/home/appuser/sys_rev_tec
Environment=PATH=/home/appuser/sys_rev_tec/venv/bin
EnvironmentFile=/home/appuser/sys_rev_tec/.env
ExecStart=/home/appuser/sys_rev_tec/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl start sys-rev-tec
sudo systemctl enable sys-rev-tec

# 检查状态
sudo systemctl status sys-rev-tec
```

### 4. Nginx 配置

```nginx
# /etc/nginx/sites-available/sys-rev-tec
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 客户端最大请求体大小
    client_max_body_size 50M;
    
    # 代理到应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件
    location /static/ {
        alias /opt/sys_rev_tec/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 上传文件
    location /uploads/ {
        alias /opt/sys_rev_tec/uploads/;
        expires 1d;
        add_header Cache-Control "public";
    }
    
    # 健康检查
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }
    
    # 监控端点 (限制访问)
    location /metrics {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://127.0.0.1:8000/metrics;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/sys-rev-tec /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL 证书

#### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

## 监控和日志

### Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sys-rev-tec'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
      
  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
```

### Grafana 配置

1. **访问 Grafana**: http://localhost:3000
2. **默认登录**: admin/admin
3. **添加数据源**: Prometheus (http://prometheus:9090)
4. **导入仪表板**: 使用项目中的 `monitoring/grafana/dashboards/performance-monitoring.json`

### 日志管理

#### 日志轮转配置

```bash
# /etc/logrotate.d/sys-rev-tec
/var/log/sys-rev-tec/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 appuser appuser
    postrotate
        systemctl reload sys-rev-tec
    endscript
}
```

#### 集中日志收集 (可选)

使用 ELK Stack 或 Loki + Grafana 进行日志聚合。

## 备份和恢复

### 数据库备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/database"
DB_NAME="sys_rev_tec"
DB_USER="app_user"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 保留最近 30 天的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: db_backup_$DATE.sql.gz"
```

### 文件备份

```bash
#!/bin/bash
# file_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/files"
UPLOAD_DIR="/opt/sys_rev_tec/uploads"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 文件备份
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz -C $UPLOAD_DIR .

# 保留最近 7 天的备份
find $BACKUP_DIR -name "files_backup_*.tar.gz" -mtime +7 -delete

echo "Files backup completed: files_backup_$DATE.tar.gz"
```

### 自动备份

```bash
# 添加到 crontab
sudo crontab -e

# 每天凌晨 2 点备份数据库
0 2 * * * /opt/scripts/backup.sh

# 每天凌晨 3 点备份文件
0 3 * * * /opt/scripts/file_backup.sh
```

### 恢复数据

```bash
# 恢复数据库
gunzip -c /backup/database/db_backup_20250125_020000.sql.gz | psql -h localhost -U app_user -d sys_rev_tec

# 恢复文件
tar -xzf /backup/files/files_backup_20250125_030000.tar.gz -C /opt/sys_rev_tec/uploads/
```

## 故障排除

### 常见问题

#### 1. 应用无法启动

```bash
# 检查日志
sudo journalctl -u sys-rev-tec -f

# 检查配置
python -m app.core.config

# 检查数据库连接
psql -h localhost -U app_user -d sys_rev_tec -c "SELECT 1;"
```

#### 2. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U app_user -d sys_rev_tec

# 检查配置
sudo nano /etc/postgresql/15/main/postgresql.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

#### 3. Redis 连接失败

```bash
# 检查 Redis 状态
sudo systemctl status redis

# 测试连接
redis-cli ping

# 检查配置
sudo nano /etc/redis/redis.conf
```

#### 4. 文件上传失败

```bash
# 检查目录权限
ls -la /opt/sys_rev_tec/uploads/

# 修复权限
sudo chown -R appuser:appuser /opt/sys_rev_tec/uploads/
sudo chmod -R 755 /opt/sys_rev_tec/uploads/
```

#### 5. OCR 服务不可用

```bash
# 检查 OCR 容器
docker ps | grep ocr

# 查看 OCR 日志
docker logs sys_rev_tec_ocr_1

# 重启 OCR 服务
docker-compose restart ocr
```

### 性能问题诊断

```bash
# 检查系统资源
top
htop
iostat -x 1

# 检查数据库性能
psql -U app_user -d sys_rev_tec -c "SELECT * FROM pg_stat_activity;"

# 检查应用指标
curl http://localhost:8000/metrics
```

## 性能优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_documents_project_id ON documents(project_id);
CREATE INDEX CONCURRENTLY idx_documents_created_at ON documents(created_at);
CREATE INDEX CONCURRENTLY idx_ocr_results_document_id ON ocr_results(document_id);

-- 分析表统计信息
ANALYZE;

-- 查看慢查询
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 应用优化

```python
# 连接池配置
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30

# Redis 连接池
REDIS_POOL_SIZE = 10
REDIS_POOL_TIMEOUT = 5

# 缓存配置
CACHE_TTL_SHORT = 300    # 5 分钟
CACHE_TTL_MEDIUM = 1800  # 30 分钟
CACHE_TTL_LONG = 7200    # 2 小时
```

### Nginx 优化

```nginx
# worker 进程数
worker_processes auto;

# 连接数
events {
    worker_connections 1024;
    use epoll;
}

# 缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m max_size=1g inactive=60m;

# 压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

### 监控告警

配置 Prometheus 告警规则：

```yaml
# alerts.yml
groups:
  - name: sys-rev-tec
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
```

---

**最后更新**: 2025-01-25  
**版本**: v1.0.0