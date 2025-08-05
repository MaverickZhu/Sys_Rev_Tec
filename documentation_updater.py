#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档和部署指南更新优化工具

功能:
1. 分析现有文档结构和内容
2. 检查文档完整性和一致性
3. 更新API文档和用户指南
4. 生成部署指南和配置文档
5. 创建文档更新报告

作者: 系统优化团队
日期: 2025-01-04
版本: 1.0.0
"""

import os
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DocumentInfo:
    """文档信息数据类"""
    path: str
    name: str
    size: int
    last_modified: datetime
    content_type: str
    completeness_score: float
    issues: List[str]

@dataclass
class DocumentationReport:
    """文档更新报告数据类"""
    total_documents: int
    updated_documents: int
    new_documents: int
    issues_found: int
    issues_fixed: int
    completeness_score: float
    recommendations: List[str]
    timestamp: datetime

class DocumentationAnalyzer:
    """文档分析器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.documents = []
        self.issues = []
        
    def analyze_documents(self) -> List[DocumentInfo]:
        """分析项目中的所有文档"""
        logger.info("开始分析项目文档...")
        
        # 文档文件模式
        doc_patterns = [
            '*.md', '*.rst', '*.txt', '*.pdf',
            '*.docx', '*.html', '*.xml'
        ]
        
        documents = []
        
        for pattern in doc_patterns:
            for doc_path in self.project_root.rglob(pattern):
                if self._should_analyze_file(doc_path):
                    doc_info = self._analyze_single_document(doc_path)
                    if doc_info:
                        documents.append(doc_info)
        
        self.documents = documents
        logger.info(f"分析完成，找到 {len(documents)} 个文档文件")
        return documents
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """判断是否应该分析该文件"""
        # 排除的目录
        exclude_dirs = {
            '.git', '__pycache__', 'node_modules', '.pytest_cache',
            'venv', '.venv', 'env', '.env', 'build', 'dist'
        }
        
        # 检查是否在排除目录中
        for part in file_path.parts:
            if part in exclude_dirs:
                return False
        
        return True
    
    def _analyze_single_document(self, doc_path: Path) -> Optional[DocumentInfo]:
        """分析单个文档"""
        try:
            stat = doc_path.stat()
            
            # 读取文档内容
            content = ""
            if doc_path.suffix.lower() in ['.md', '.rst', '.txt', '.html', '.xml']:
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(doc_path, 'r', encoding='gbk') as f:
                            content = f.read()
                    except:
                        content = "[无法读取内容]"
            
            # 分析文档完整性
            completeness_score, issues = self._analyze_completeness(content, doc_path)
            
            return DocumentInfo(
                path=str(doc_path),
                name=doc_path.name,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                content_type=self._get_content_type(doc_path),
                completeness_score=completeness_score,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"分析文档 {doc_path} 时出错: {e}")
            return None
    
    def _analyze_completeness(self, content: str, doc_path: Path) -> tuple[float, List[str]]:
        """分析文档完整性"""
        issues = []
        score = 100.0
        
        # 检查文档长度
        if len(content) < 100:
            issues.append("文档内容过短")
            score -= 20
        
        # 检查标题结构
        if doc_path.suffix.lower() == '.md':
            if not re.search(r'^#\s+', content, re.MULTILINE):
                issues.append("缺少主标题")
                score -= 15
            
            # 检查代码块
            code_blocks = re.findall(r'```[\s\S]*?```', content)
            if len(code_blocks) == 0 and 'README' in doc_path.name.upper():
                issues.append("README文档缺少代码示例")
                score -= 10
        
        # 检查链接有效性
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        for link_text, link_url in links:
            if link_url.startswith('http'):
                # 外部链接暂不检查
                continue
            elif link_url.startswith('/'):
                # 绝对路径
                full_path = self.project_root / link_url.lstrip('/')
                if not full_path.exists():
                    issues.append(f"链接目标不存在: {link_url}")
                    score -= 5
            else:
                # 相对路径
                full_path = doc_path.parent / link_url
                if not full_path.exists():
                    issues.append(f"链接目标不存在: {link_url}")
                    score -= 5
        
        return max(0, score), issues
    
    def _get_content_type(self, doc_path: Path) -> str:
        """获取文档内容类型"""
        name_lower = doc_path.name.lower()
        
        if 'readme' in name_lower:
            return 'README文档'
        elif 'api' in name_lower:
            return 'API文档'
        elif 'user' in name_lower or 'guide' in name_lower:
            return '用户指南'
        elif 'deploy' in name_lower or '部署' in name_lower:
            return '部署文档'
        elif 'config' in name_lower or '配置' in name_lower:
            return '配置文档'
        elif doc_path.suffix.lower() == '.md':
            return 'Markdown文档'
        else:
            return '其他文档'

class DocumentationUpdater:
    """文档更新器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.updated_count = 0
        self.new_count = 0
        self.fixed_issues = 0
        
    def update_readme(self) -> bool:
        """更新README文档"""
        logger.info("更新README文档...")
        
        readme_path = self.project_root / 'README.md'
        if not readme_path.exists():
            logger.warning("README.md文件不存在")
            return False
        
        try:
            # 读取现有内容
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新徽章
            updated_content = self._update_badges(content)
            
            # 更新安装说明
            updated_content = self._update_installation_guide(updated_content)
            
            # 更新API文档链接
            updated_content = self._update_api_links(updated_content)
            
            # 如果内容有变化，写入文件
            if updated_content != content:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                self.updated_count += 1
                logger.info("README.md已更新")
            
            return True
            
        except Exception as e:
            logger.error(f"更新README时出错: {e}")
            return False
    
    def _update_badges(self, content: str) -> str:
        """更新徽章信息"""
        # 更新Python版本徽章
        content = re.sub(
            r'\[!\[Python [0-9.]+\].*?\]\(.*?\)',
            '[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)',
            content
        )
        
        # 添加最后更新时间
        current_date = datetime.now().strftime('%Y-%m-%d')
        if '最后更新' not in content:
            badge_section = f"\n[![Last Updated](https://img.shields.io/badge/last%20updated-{current_date}-green.svg)]()\n"
            # 在第一个换行后插入
            lines = content.split('\n')
            if len(lines) > 1:
                lines.insert(1, badge_section.strip())
                content = '\n'.join(lines)
        
        return content
    
    def _update_installation_guide(self, content: str) -> str:
        """更新安装指南"""
        # 检查是否有安装部分
        if '## 安装' not in content and '## Installation' not in content:
            # 添加安装部分
            installation_section = """
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
"""
            
            # 在特性部分后插入
            content = re.sub(
                r'(## ✨ 特性.*?\n\n)',
                r'\1' + installation_section + '\n',
                content,
                flags=re.DOTALL
            )
        
        return content
    
    def _update_api_links(self, content: str) -> str:
        """更新API文档链接"""
        # 确保有API文档链接
        if 'API文档' not in content and 'API Documentation' not in content:
            api_section = """
## 📚 文档

- [API文档](http://localhost:8000/docs) - Swagger UI
- [用户指南](docs/USER_GUIDE.md) - 详细使用说明
- [部署指南](README_Docker.md) - Docker部署说明
- [开发文档](DEVELOPMENT.md) - 开发环境配置
"""
            
            # 在项目结构前插入
            content = re.sub(
                r'(## 📁 项目结构)',
                api_section + '\n\1',
                content
            )
        
        return content
    
    def create_deployment_guide(self) -> bool:
        """创建部署指南"""
        logger.info("创建部署指南...")
        
        deployment_guide = """
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
docker run -d --name postgres \
  -e POSTGRES_DB=sys_rev_tech \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:13

# 启动Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:6-alpine

# 启动应用
docker run -d --name sys-rev-tec \
  --link postgres:postgres \
  --link redis:redis \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:your_password@postgres:5432/sys_rev_tech \
  -e REDIS_URL=redis://redis:6379/0 \
  sys-rev-tec:latest
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
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    $SOURCE_DIR

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
"""
        
        deployment_path = self.project_root / 'DEPLOYMENT.md'
        try:
            with open(deployment_path, 'w', encoding='utf-8') as f:
                f.write(deployment_guide)
            self.new_count += 1
            logger.info("部署指南已创建")
            return True
        except Exception as e:
            logger.error(f"创建部署指南时出错: {e}")
            return False
    
    def update_api_documentation(self) -> bool:
        """更新API文档"""
        logger.info("更新API文档...")
        
        api_doc_path = self.project_root / 'docs' / 'API.md'
        if not api_doc_path.exists():
            logger.warning("API.md文件不存在")
            return False
        
        try:
            # 读取现有内容
            with open(api_doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加AI服务API文档
            if 'AI服务API' not in content:
                ai_api_section = """
## AI服务API

### 文档分析

**端点**: `POST /api/v1/ai/analyze`

**描述**: 对上传的文档进行智能分析

**请求参数**:
```json
{
  "document_id": 1,
  "analysis_type": "full",
  "options": {
    "extract_entities": true,
    "sentiment_analysis": true,
    "risk_assessment": true
  }
}
```

**响应示例**:
```json
{
  "status": "success",
  "analysis_id": "uuid-string",
  "results": {
    "entities": [...],
    "sentiment": "neutral",
    "risk_score": 0.3,
    "summary": "文档摘要"
  }
}
```

### 智能报告生成

**端点**: `POST /api/v1/ai/generate-report`

**描述**: 基于项目数据生成智能分析报告

**请求参数**:
```json
{
  "project_id": 1,
  "report_type": "summary",
  "template_id": "default",
  "options": {
    "include_charts": true,
    "format": "pdf"
  }
}
```

**响应示例**:
```json
{
  "status": "success",
  "report_id": "uuid-string",
  "download_url": "/api/v1/reports/download/uuid-string",
  "generated_at": "2025-01-04T10:30:00Z"
}
```

### 语义搜索

**端点**: `POST /api/v1/ai/search`

**描述**: 基于语义理解的智能搜索

**请求参数**:
```json
{
  "query": "搜索关键词",
  "project_id": 1,
  "limit": 10,
  "filters": {
    "document_type": "contract",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**响应示例**:
```json
{
  "status": "success",
  "results": [
    {
      "document_id": 1,
      "title": "文档标题",
      "relevance_score": 0.95,
      "snippet": "相关内容片段"
    }
  ],
  "total": 25
}
```
"""
                content += ai_api_section
                
                with open(api_doc_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.updated_count += 1
                logger.info("API文档已更新")
            
            return True
            
        except Exception as e:
            logger.error(f"更新API文档时出错: {e}")
            return False

class DocumentationReportGenerator:
    """文档报告生成器"""
    
    def __init__(self):
        self.report_data = {}
    
    def generate_report(self, analyzer: DocumentationAnalyzer, 
                       updater: DocumentationUpdater) -> DocumentationReport:
        """生成文档更新报告"""
        logger.info("生成文档更新报告...")
        
        documents = analyzer.documents
        total_issues = sum(len(doc.issues) for doc in documents)
        avg_completeness = sum(doc.completeness_score for doc in documents) / len(documents) if documents else 0
        
        # 生成建议
        recommendations = self._generate_recommendations(documents)
        
        report = DocumentationReport(
            total_documents=len(documents),
            updated_documents=updater.updated_count,
            new_documents=updater.new_count,
            issues_found=total_issues,
            issues_fixed=updater.fixed_issues,
            completeness_score=avg_completeness,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        return report
    
    def _generate_recommendations(self, documents: List[DocumentInfo]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 分析文档类型分布
        doc_types = {}
        for doc in documents:
            doc_type = doc.content_type
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        # 检查缺失的文档类型
        required_types = {'README文档', 'API文档', '用户指南', '部署文档'}
        missing_types = required_types - set(doc_types.keys())
        
        for missing_type in missing_types:
            recommendations.append(f"建议添加{missing_type}")
        
        # 检查文档质量
        low_quality_docs = [doc for doc in documents if doc.completeness_score < 60]
        if low_quality_docs:
            recommendations.append(f"有{len(low_quality_docs)}个文档质量较低，建议改进")
        
        # 检查过期文档
        old_docs = [doc for doc in documents 
                   if (datetime.now() - doc.last_modified).days > 90]
        if old_docs:
            recommendations.append(f"有{len(old_docs)}个文档超过90天未更新，建议检查")
        
        # 通用建议
        recommendations.extend([
            "建议定期更新文档内容",
            "建议添加更多代码示例",
            "建议完善API文档的错误码说明",
            "建议添加常见问题解答(FAQ)部分",
            "建议增加部署和运维相关文档"
        ])
        
        return recommendations[:10]  # 返回前10个建议
    
    def save_report(self, report: DocumentationReport, output_path: str) -> bool:
        """保存报告到文件"""
        try:
            report_data = {
                'documentation_update_report': {
                    'summary': {
                        'total_documents': report.total_documents,
                        'updated_documents': report.updated_documents,
                        'new_documents': report.new_documents,
                        'issues_found': report.issues_found,
                        'issues_fixed': report.issues_fixed,
                        'completeness_score': round(report.completeness_score, 2),
                        'timestamp': report.timestamp.isoformat()
                    },
                    'recommendations': report.recommendations,
                    'status': 'completed'
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"报告已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存报告时出错: {e}")
            return False

def main():
    """主函数"""
    logger.info("开始文档和部署指南更新优化...")
    
    project_root = os.getcwd()
    
    try:
        # 1. 分析现有文档
        analyzer = DocumentationAnalyzer(project_root)
        documents = analyzer.analyze_documents()
        
        logger.info(f"文档分析完成，共找到 {len(documents)} 个文档")
        
        # 2. 更新文档
        updater = DocumentationUpdater(project_root)
        
        # 更新README
        updater.update_readme()
        
        # 创建部署指南
        updater.create_deployment_guide()
        
        # 更新API文档
        updater.update_api_documentation()
        
        # 3. 生成报告
        report_generator = DocumentationReportGenerator()
        report = report_generator.generate_report(analyzer, updater)
        
        # 保存报告
        report_path = os.path.join(project_root, 'documentation_update_report.json')
        report_generator.save_report(report, report_path)
        
        # 4. 输出结果
        logger.info("=" * 50)
        logger.info("文档更新完成！")
        logger.info(f"总文档数: {report.total_documents}")
        logger.info(f"更新文档数: {report.updated_documents}")
        logger.info(f"新建文档数: {report.new_documents}")
        logger.info(f"发现问题数: {report.issues_found}")
        logger.info(f"完整性评分: {report.completeness_score:.1f}/100")
        logger.info("=" * 50)
        
        # 输出建议
        if report.recommendations:
            logger.info("改进建议:")
            for i, rec in enumerate(report.recommendations, 1):
                logger.info(f"{i}. {rec}")
        
        return True
        
    except Exception as e:
        logger.error(f"文档更新过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)