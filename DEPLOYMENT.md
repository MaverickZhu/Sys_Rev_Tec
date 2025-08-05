
# 系统部署指南

本文档提供了政府采购项目审查分析系统的详细部署指南。

## 🏗️ 部署架构

### 生产环境架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   负载均衡器    │───▶│   Web服务器     │───▶│   应用服务器    │
│   (Nginx)       │    │   (Nginx)       │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据库服务    │    │   缓存服务      │    │   AI服务模块    │
│  (PostgreSQL)   │    │   (Redis)       │    │  (FastAPI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🐳 Docker部署

### 1. 使用Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd Sys_Rev_Tec

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 构建和启动服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec app alembic upgrade head
docker-compose exec app python scripts/init_db.py
```

### 2. 手动Docker部署

```bash
# 构建镜像
docker build -t sys-rev-tec:latest .

# 启动PostgreSQL
docker run -d --name postgres   -e POSTGRES_DB=sys_rev_tech   -e POSTGRES_USER=postgres   -e POSTGRES_PASSWORD=your_password   -p 5432:5432   postgres:13

# 启动Redis
docker run -d --name redis   -p 6379:6379   redis:6-alpine

# 启动应用
docker run -d --name sys-rev-tec   --link postgres:postgres   --link redis:redis   -p 8000:8000   -e DATABASE_URL=postgresql://postgres:your_password@postgres:5432/sys_rev_tech   -e REDIS_URL=redis://redis:6379/0   sys-rev-tec:latest
```

## 🖥️ 传统部署

### 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.8+
- **数据库**: PostgreSQL 12+
- **缓存**: Redis 6+
- **Web服务器**: Nginx 1.18+
- **内存**: 最少4GB，推荐8GB+
- **存储**: 最少50GB，推荐100GB+

### 1. 环境准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y nginx

# CentOS/RHEL
sudo yum update
sudo yum install -y python38 python38-devel
sudo yum install -y postgresql postgresql-server postgresql-contrib
sudo yum install -y redis
sudo yum install -y nginx
```

### 2. 数据库配置

```bash
# 启动PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE sys_rev_tech;
CREATE USER sys_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sys_rev_tech TO sys_user;
\q
```

### 3. 应用部署

```bash
# 创建应用目录
sudo mkdir -p /opt/sys_rev_tec
sudo chown $USER:$USER /opt/sys_rev_tec
cd /opt/sys_rev_tec

# 克隆代码
git clone <repository-url> .

# 创建虚拟环境
python3.8 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-ai.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 初始化数据库
alembic upgrade head
python scripts/init_db.py
```

### 4. 系统服务配置

创建systemd服务文件：

```bash
# 主应用服务
sudo tee /etc/systemd/system/sys-rev-tec.service > /dev/null <<EOF
[Unit]
Description=Sys Rev Tec Main Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/sys_rev_tec
Environment=PATH=/opt/sys_rev_tec/venv/bin
ExecStart=/opt/sys_rev_tec/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# AI服务
sudo tee /etc/systemd/system/sys-rev-tec-ai.service > /dev/null <<EOF
[Unit]
Description=Sys Rev Tec AI Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/sys_rev_tec/ai_service
Environment=PATH=/opt/sys_rev_tec/venv/bin
ExecStart=/opt/sys_rev_tec/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable sys-rev-tec sys-rev-tec-ai
sudo systemctl start sys-rev-tec sys-rev-tec-ai
```

### 5. Nginx配置

```bash
# 创建Nginx配置
sudo tee /etc/nginx/sites-available/sys-rev-tec > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # 主应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # AI服务
    location /ai/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/sys-rev-tec /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 配置优化

### PostgreSQL优化

```sql
-- postgresql.conf 优化配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
```

### Redis优化

```bash
# redis.conf 优化配置
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 📊 监控配置

### Prometheus配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sys-rev-tec'
    static_configs:
      - targets: ['localhost:8000', 'localhost:8001']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Grafana仪表板

导入预配置的仪表板：
- 系统性能监控
- 应用指标监控
- 数据库性能监控
- AI服务监控

## 🔒 安全配置

### 1. 防火墙配置

```bash
# UFW配置
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### 2. SSL证书

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 数据库安全

```bash
# PostgreSQL安全配置
sudo -u postgres psql
ALTER USER postgres PASSWORD 'strong_password';
\q

# 编辑 pg_hba.conf
sudo nano /etc/postgresql/12/main/pg_hba.conf
# 修改认证方式为 md5
```

## 🔄 备份策略

### 数据库备份

```bash
#!/bin/bash
# backup_db.sh
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -h localhost -U sys_user -d sys_rev_tech > $BACKUP_DIR/db_backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

### 文件备份

```bash
#!/bin/bash
# backup_files.sh
BACKUP_DIR="/opt/backups"
SOURCE_DIR="/opt/sys_rev_tec"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份应用文件
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz     --exclude='venv'     --exclude='__pycache__'     --exclude='.git'     $SOURCE_DIR

# 删除30天前的备份
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +30 -delete
```

## 🚨 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口占用：`sudo netstat -tlnp | grep :8000`
   - 查看服务日志：`sudo journalctl -u sys-rev-tec -f`

2. **数据库连接失败**
   - 检查PostgreSQL状态：`sudo systemctl status postgresql`
   - 测试连接：`psql -h localhost -U sys_user -d sys_rev_tech`

3. **AI服务异常**
   - 检查模型文件：确保AI模型文件存在
   - 查看AI服务日志：`sudo journalctl -u sys-rev-tec-ai -f`

### 性能调优

1. **数据库性能**
   - 定期执行VACUUM ANALYZE
   - 监控慢查询日志
   - 优化索引策略

2. **应用性能**
   - 调整worker进程数
   - 优化缓存策略
   - 监控内存使用

## 📞 技术支持

如遇到部署问题，请联系：
- 技术支持邮箱：support@example.com
- 文档更新：docs@example.com
- 紧急联系：emergency@example.com

---

**文档版本**: 1.0.0  
**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**维护团队**: 系统运维团队
