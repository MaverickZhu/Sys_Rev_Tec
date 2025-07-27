# 安全指南

本文档详细描述了政府采购项目审查分析系统的安全策略、最佳实践和安全配置指南。

## 目录

- [安全概述](#安全概述)
- [认证和授权](#认证和授权)
- [数据安全](#数据安全)
- [网络安全](#网络安全)
- [应用安全](#应用安全)
- [基础设施安全](#基础设施安全)
- [安全监控](#安全监控)
- [合规性](#合规性)
- [安全事件响应](#安全事件响应)
- [安全最佳实践](#安全最佳实践)

## 安全概述

### 安全目标

政府采购项目审查分析系统的安全目标遵循 CIA 三元组原则：

- **机密性 (Confidentiality)**: 确保敏感信息只能被授权用户访问
- **完整性 (Integrity)**: 保证数据的准确性和完整性，防止未授权修改
- **可用性 (Availability)**: 确保系统和数据在需要时可用

### 安全架构

```
┌─────────────────────────────────────────────────────────────┐
│                      安全防护层级                            │
├─────────────────────────────────────────────────────────────┤
│ 第一层: 网络安全 (防火墙、DDoS 防护、入侵检测)                │
├─────────────────────────────────────────────────────────────┤
│ 第二层: 应用安全 (WAF、API 安全、输入验证)                    │
├─────────────────────────────────────────────────────────────┤
│ 第三层: 认证授权 (多因素认证、RBAC、JWT)                      │
├─────────────────────────────────────────────────────────────┤
│ 第四层: 数据安全 (加密存储、传输加密、备份加密)                │
├─────────────────────────────────────────────────────────────┤
│ 第五层: 监控审计 (日志记录、异常检测、合规审计)                │
└─────────────────────────────────────────────────────────────┘
```

### 威胁模型

#### 主要威胁类型

1. **外部威胁**
   - 恶意攻击者尝试未授权访问
   - DDoS 攻击导致服务不可用
   - 数据泄露和隐私侵犯
   - 恶意软件和病毒感染

2. **内部威胁**
   - 内部人员滥用权限
   - 意外的数据泄露
   - 配置错误导致的安全漏洞
   - 社会工程学攻击

3. **技术威胁**
   - SQL 注入攻击
   - 跨站脚本攻击 (XSS)
   - 跨站请求伪造 (CSRF)
   - 文件上传漏洞

## 认证和授权

### 用户认证

#### 密码策略

```python
# 密码复杂度要求
PASSWORD_POLICY = {
    "min_length": 8,           # 最小长度
    "max_length": 128,         # 最大长度
    "require_uppercase": True,  # 需要大写字母
    "require_lowercase": True,  # 需要小写字母
    "require_digits": True,     # 需要数字
    "require_special": True,    # 需要特殊字符
    "forbidden_patterns": [     # 禁止的模式
        "123456", "password", "admin", "qwerty"
    ],
    "history_check": 5,         # 检查最近5次密码
    "expiry_days": 90,          # 密码过期天数
    "max_attempts": 5,          # 最大尝试次数
    "lockout_duration": 1800,   # 锁定时间（秒）
}

# 密码哈希配置
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 增加哈希轮数提高安全性
)
```

#### JWT 令牌安全

```python
# JWT 配置
JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,   # 访问令牌过期时间
    "refresh_token_expire_days": 7,      # 刷新令牌过期时间
    "secret_key": os.getenv("JWT_SECRET_KEY"),  # 从环境变量获取
    "issuer": "sys-rev-tec",
    "audience": "sys-rev-tec-users",
}

# 令牌黑名单机制
class TokenBlacklist:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def add_token(self, jti: str, exp: int):
        """将令牌添加到黑名单"""
        ttl = exp - int(time.time())
        if ttl > 0:
            await self.redis.setex(f"blacklist:{jti}", ttl, "1")
    
    async def is_blacklisted(self, jti: str) -> bool:
        """检查令牌是否在黑名单中"""
        return await self.redis.exists(f"blacklist:{jti}")
```

#### 多因素认证 (MFA)

```python
# TOTP 配置
import pyotp

class MFAService:
    def generate_secret(self) -> str:
        """生成 MFA 密钥"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """生成 QR 码 URL"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name="政府采购审查系统"
        )
    
    def verify_token(self, secret: str, token: str) -> bool:
        """验证 TOTP 令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

### 基于角色的访问控制 (RBAC)

#### 权限模型设计

```python
from enum import Enum
from typing import List, Dict

class Permission(Enum):
    # 系统管理
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"
    
    # 项目管理
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_MEMBERS = "project:manage_members"
    
    # 文档管理
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_DOWNLOAD = "document:download"
    
    # OCR 服务
    OCR_PROCESS = "ocr:process"
    OCR_RESULTS = "ocr:results"
    
    # 审计日志
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

class Role(Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    USER = "user"
    VIEWER = "viewer"
    AUDITOR = "auditor"

# 角色权限映射
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.SUPER_ADMIN: [p for p in Permission],  # 超级管理员拥有所有权限
    
    Role.ADMIN: [
        Permission.SYSTEM_CONFIG,
        Permission.USER_CREATE, Permission.USER_READ, 
        Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE, Permission.DOCUMENT_DELETE,
        Permission.OCR_PROCESS, Permission.OCR_RESULTS,
        Permission.AUDIT_READ,
    ],
    
    Role.PROJECT_MANAGER: [
        Permission.PROJECT_CREATE, Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE, Permission.PROJECT_MANAGE_MEMBERS,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE, Permission.DOCUMENT_DELETE,
        Permission.OCR_PROCESS, Permission.OCR_RESULTS,
    ],
    
    Role.USER: [
        Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE, Permission.DOCUMENT_DOWNLOAD,
        Permission.OCR_PROCESS, Permission.OCR_RESULTS,
    ],
    
    Role.VIEWER: [
        Permission.PROJECT_READ,
        Permission.DOCUMENT_READ, Permission.DOCUMENT_DOWNLOAD,
        Permission.OCR_RESULTS,
    ],
    
    Role.AUDITOR: [
        Permission.PROJECT_READ,
        Permission.DOCUMENT_READ,
        Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
    ],
}
```

#### 权限检查装饰器

```python
from functools import wraps
from fastapi import HTTPException, status

def require_permission(permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中获取当前用户
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 检查用户权限
            user_permissions = get_user_permissions(current_user)
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {permission.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.delete("/users/{user_id}")
@require_permission(Permission.USER_DELETE)
async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    # 删除用户逻辑
    pass
```

## 数据安全

### 数据加密

#### 传输加密

```nginx
# Nginx SSL/TLS 配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS 配置
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # 其他安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # CSP 配置
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';";
}
```

#### 存储加密

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    def __init__(self, password: bytes, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)
        self.salt = salt
    
    def encrypt(self, data: str) -> bytes:
        """加密数据"""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data).decode()

# 敏感字段加密
class EncryptedField:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_value(self, value: str) -> str:
        if not value:
            return value
        encrypted = self.cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        if not encrypted_value:
            return encrypted_value
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        return self.cipher.decrypt(encrypted_bytes).decode()
```

#### 数据库加密

```python
# PostgreSQL 透明数据加密 (TDE)
# postgresql.conf 配置
"""
# 启用数据加密
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'ca.crt'

# 连接加密
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
"""

# 应用层字段加密
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    # 加密存储敏感信息
    phone = Column(EncryptedType(String, secret_key, AesEngine, 'pkcs5'))
    id_number = Column(EncryptedType(String, secret_key, AesEngine, 'pkcs5'))
```

### 数据备份和恢复

#### 备份策略

```bash
#!/bin/bash
# 数据库备份脚本

BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="sys_rev_tec"
DB_USER="backup_user"
DB_HOST="localhost"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 加密备份文件
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
    --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric \
    --output $BACKUP_DIR/db_backup_$DATE.sql.gz.gpg \
    $BACKUP_DIR/db_backup_$DATE.sql.gz

# 删除未加密的备份文件
rm $BACKUP_DIR/db_backup_$DATE.sql.gz

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete

# 文件备份
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /app/uploads

# 上传到远程存储
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz.gpg s3://backup-bucket/database/
aws s3 cp $BACKUP_DIR/files_backup_$DATE.tar.gz s3://backup-bucket/files/
```

#### 恢复流程

```bash
#!/bin/bash
# 数据恢复脚本

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 解密备份文件
gpg --decrypt $BACKUP_FILE > temp_backup.sql.gz

# 解压备份文件
gunzip temp_backup.sql.gz

# 恢复数据库
psql -h localhost -U postgres -d sys_rev_tec < temp_backup.sql

# 清理临时文件
rm temp_backup.sql

echo "Database restored successfully"
```

## 网络安全

### 防火墙配置

```bash
#!/bin/bash
# iptables 防火墙规则

# 清除现有规则
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# 设置默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许本地回环
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许 SSH (限制源 IP)
iptables -A INPUT -p tcp --dport 22 -s 192.168.1.0/24 -j ACCEPT

# 允许 HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许数据库连接（仅内网）
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s 10.0.0.0/8 -j ACCEPT

# 防止 DDoS 攻击
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# 防止端口扫描
iptables -A INPUT -m recent --name portscan --rcheck --seconds 86400 -j DROP
iptables -A INPUT -m recent --name portscan --remove
iptables -A INPUT -p tcp -m tcp --dport 139 -m recent --name portscan --set -j LOG --log-prefix "portscan:"
iptables -A INPUT -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP

# 保存规则
iptables-save > /etc/iptables/rules.v4
```

### DDoS 防护

```nginx
# Nginx DDoS 防护配置
http {
    # 限制请求频率
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # 限制连接数
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    
    server {
        # API 接口限流
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            limit_conn conn_limit_per_ip 10;
        }
        
        # 登录接口限流
        location /api/v1/auth/login {
            limit_req zone=login burst=5 nodelay;
            limit_conn conn_limit_per_ip 5;
        }
        
        # 文件上传限制
        location /api/v1/documents/upload {
            client_max_body_size 100M;
            client_body_timeout 60s;
            client_header_timeout 60s;
        }
    }
}
```

### 入侵检测

```python
# 异常行为检测
from datetime import datetime, timedelta
from collections import defaultdict

class IntrusionDetection:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.thresholds = {
            'failed_login': 5,      # 5次失败登录
            'api_requests': 1000,   # 每小时1000次API请求
            'file_uploads': 50,     # 每小时50次文件上传
        }
    
    async def track_failed_login(self, ip_address: str, user_id: str = None):
        """跟踪失败登录"""
        key = f"failed_login:{ip_address}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1小时过期
        
        if count >= self.thresholds['failed_login']:
            await self.trigger_alert('failed_login', {
                'ip_address': ip_address,
                'user_id': user_id,
                'count': count,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def track_api_usage(self, ip_address: str, endpoint: str):
        """跟踪 API 使用"""
        key = f"api_usage:{ip_address}:{datetime.utcnow().hour}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 3600)
        
        if count >= self.thresholds['api_requests']:
            await self.trigger_alert('api_abuse', {
                'ip_address': ip_address,
                'endpoint': endpoint,
                'count': count,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def trigger_alert(self, alert_type: str, data: dict):
        """触发安全告警"""
        alert = {
            'type': alert_type,
            'severity': 'high',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 发送告警到监控系统
        await self.send_to_monitoring(alert)
        
        # 记录到安全日志
        logger.warning(f"Security alert: {alert_type}", extra=alert)
```

## 应用安全

### 输入验证和清理

```python
from pydantic import BaseModel, validator
import re
import html

class DocumentUpload(BaseModel):
    filename: str
    description: str = None
    category: str
    
    @validator('filename')
    def validate_filename(cls, v):
        # 文件名安全检查
        if not v or len(v) > 255:
            raise ValueError('Invalid filename length')
        
        # 禁止的字符
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in v for char in forbidden_chars):
            raise ValueError('Filename contains forbidden characters')
        
        # 禁止的文件名
        forbidden_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
        if v.upper() in forbidden_names:
            raise ValueError('Forbidden filename')
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v:
            # HTML 转义
            v = html.escape(v)
            # 长度限制
            if len(v) > 1000:
                raise ValueError('Description too long')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        # 分类白名单
        allowed_categories = [
            'tender_document', 'bid_document', 'contract', 
            'specification', 'evaluation', 'other'
        ]
        if v not in allowed_categories:
            raise ValueError('Invalid category')
        return v

# SQL 注入防护
from sqlalchemy import text

class SecureQuery:
    @staticmethod
    def search_documents(db_session, query: str, project_id: int):
        # 使用参数化查询防止 SQL 注入
        sql = text("""
            SELECT * FROM documents 
            WHERE project_id = :project_id 
            AND (filename ILIKE :query OR extracted_text ILIKE :query)
            ORDER BY upload_time DESC
        """)
        
        return db_session.execute(sql, {
            'project_id': project_id,
            'query': f'%{query}%'
        }).fetchall()
```

### 文件上传安全

```python
import magic
from pathlib import Path
import hashlib

class SecureFileUpload:
    ALLOWED_EXTENSIONS = {
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'jpg': ['image/jpeg'],
        'png': ['image/png'],
        'txt': ['text/plain'],
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def validate_file(self, file_content: bytes, filename: str) -> dict:
        """验证上传文件"""
        # 文件大小检查
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {len(file_content)} bytes")
        
        # 文件类型检查
        file_type = magic.from_buffer(file_content, mime=True)
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension not allowed: {file_ext}")
        
        if file_type not in self.ALLOWED_EXTENSIONS[file_ext]:
            raise ValueError(f"File type mismatch: {file_type}")
        
        # 恶意文件检查
        await self.scan_for_malware(file_content)
        
        # 计算文件哈希
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        return {
            'file_type': file_type,
            'file_size': len(file_content),
            'file_hash': file_hash,
            'is_safe': True
        }
    
    async def scan_for_malware(self, file_content: bytes):
        """恶意软件扫描"""
        # 简单的恶意文件特征检测
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'<?php',
            b'<%',
        ]
        
        for pattern in malicious_patterns:
            if pattern in file_content.lower():
                raise ValueError("Potentially malicious content detected")
    
    def generate_safe_filename(self, original_filename: str) -> str:
        """生成安全的文件名"""
        # 移除路径信息
        filename = Path(original_filename).name
        
        # 生成唯一文件名
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        name, ext = Path(filename).stem, Path(filename).suffix
        safe_filename = f"{timestamp}_{random_str}_{name[:50]}{ext}"
        
        return safe_filename
```

### API 安全

```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time

class APISecurityMiddleware:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.request_validator = RequestValidator()
    
    async def __call__(self, request: Request, call_next):
        # 请求验证
        await self.request_validator.validate(request)
        
        # 速率限制
        await self.rate_limiter.check_rate_limit(request)
        
        # 请求大小限制
        if request.headers.get('content-length'):
            content_length = int(request.headers['content-length'])
            if content_length > 100 * 1024 * 1024:  # 100MB
                raise HTTPException(status_code=413, detail="Request too large")
        
        # 处理请求
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 添加安全头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

class RequestValidator:
    async def validate(self, request: Request):
        # User-Agent 检查
        user_agent = request.headers.get('user-agent', '')
        if not user_agent or len(user_agent) > 500:
            raise HTTPException(status_code=400, detail="Invalid User-Agent")
        
        # 检查可疑的 User-Agent
        suspicious_agents = ['sqlmap', 'nikto', 'nmap', 'masscan']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            raise HTTPException(status_code=403, detail="Suspicious User-Agent")
        
        # Host 头检查
        host = request.headers.get('host', '')
        allowed_hosts = ['localhost', '127.0.0.1', 'your-domain.com']
        if host not in allowed_hosts:
            raise HTTPException(status_code=400, detail="Invalid Host header")
```

## 基础设施安全

### Docker 安全配置

```dockerfile
# 安全的 Dockerfile
FROM python:3.11-slim

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装安全更新
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=appuser:appuser . .

# 设置文件权限
RUN chmod -R 755 /app && \
    chmod -R 700 /app/uploads

# 切换到非 root 用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose 安全配置
version: '3.8'

services:
  app:
    build: .
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    user: "1000:1000"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./uploads:/app/uploads:rw
    networks:
      - app-network
    restart: unless-stopped
    
  db:
    image: postgres:15
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    cap_drop:
      - ALL
    cap_add:
      - SETUID
      - SETGID
    security_opt:
      - no-new-privileges:true
    environment:
      - POSTGRES_DB=sys_rev_tec
      - POSTGRES_USER=app_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  postgres_data:
    driver: local
```

### 系统加固

```bash
#!/bin/bash
# 系统安全加固脚本

# 更新系统
apt update && apt upgrade -y

# 安装安全工具
apt install -y fail2ban ufw rkhunter chkrootkit

# 配置防火墙
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 配置 fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

systemctl enable fail2ban
systemctl start fail2ban

# 禁用不必要的服务
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon

# 设置文件权限
chmod 700 /root
chmod 644 /etc/passwd
chmod 600 /etc/shadow
chmod 644 /etc/group

# 配置内核参数
cat >> /etc/sysctl.conf << EOF
# 网络安全参数
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.tcp_syncookies = 1
EOF

sysctl -p

echo "System hardening completed"
```

## 安全监控

### 日志监控

```python
import structlog
from datetime import datetime
from enum import Enum

class SecurityEventType(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PERMISSION_DENIED = "permission_denied"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "config_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class SecurityLogger:
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    def log_event(self, event_type: SecurityEventType, user_id: str = None, 
                  ip_address: str = None, details: dict = None):
        """记录安全事件"""
        event_data = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {}
        }
        
        self.logger.info("Security event", **event_data)
    
    def log_login_attempt(self, username: str, ip_address: str, 
                         success: bool, details: dict = None):
        """记录登录尝试"""
        event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILURE
        
        self.log_event(
            event_type=event_type,
            user_id=username,
            ip_address=ip_address,
            details={
                "username": username,
                "success": success,
                **(details or {})
            }
        )
    
    def log_file_operation(self, operation: str, user_id: str, 
                          file_path: str, ip_address: str):
        """记录文件操作"""
        event_type = SecurityEventType.FILE_UPLOAD if operation == "upload" else SecurityEventType.FILE_DOWNLOAD
        
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "operation": operation,
                "file_path": file_path
            }
        )

# 使用示例
security_logger = SecurityLogger()

@router.post("/auth/login")
async def login(credentials: UserCredentials, request: Request):
    ip_address = request.client.host
    
    try:
        user = await authenticate_user(credentials.username, credentials.password)
        if user:
            security_logger.log_login_attempt(
                username=credentials.username,
                ip_address=ip_address,
                success=True
            )
            return {"access_token": create_access_token(user.id)}
        else:
            security_logger.log_login_attempt(
                username=credentials.username,
                ip_address=ip_address,
                success=False,
                details={"reason": "invalid_credentials"}
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        security_logger.log_login_attempt(
            username=credentials.username,
            ip_address=ip_address,
            success=False,
            details={"reason": "system_error", "error": str(e)}
        )
        raise
```

### 异常检测

```python
from sklearn.ensemble import IsolationForest
import numpy as np
from datetime import datetime, timedelta

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
    
    def extract_features(self, user_activity: dict) -> np.array:
        """提取用户行为特征"""
        features = [
            user_activity.get('login_count', 0),
            user_activity.get('api_requests', 0),
            user_activity.get('file_uploads', 0),
            user_activity.get('file_downloads', 0),
            user_activity.get('unique_ips', 0),
            user_activity.get('session_duration', 0),
            user_activity.get('failed_requests', 0),
        ]
        return np.array(features).reshape(1, -1)
    
    def train(self, historical_data: list):
        """训练异常检测模型"""
        features = []
        for activity in historical_data:
            feature_vector = self.extract_features(activity)
            features.append(feature_vector.flatten())
        
        X = np.array(features)
        self.model.fit(X)
        self.is_trained = True
    
    def detect_anomaly(self, user_activity: dict) -> dict:
        """检测异常行为"""
        if not self.is_trained:
            return {"is_anomaly": False, "score": 0, "reason": "Model not trained"}
        
        features = self.extract_features(user_activity)
        anomaly_score = self.model.decision_function(features)[0]
        is_anomaly = self.model.predict(features)[0] == -1
        
        return {
            "is_anomaly": is_anomaly,
            "score": float(anomaly_score),
            "threshold": -0.1,
            "features": user_activity
        }

# 实时异常检测
class RealTimeAnomalyDetection:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.detector = AnomalyDetector()
        self.alert_threshold = -0.1
    
    async def track_user_activity(self, user_id: str, activity_type: str, 
                                 ip_address: str, details: dict = None):
        """跟踪用户活动"""
        today = datetime.utcnow().date().isoformat()
        key = f"user_activity:{user_id}:{today}"
        
        # 更新活动计数
        await self.redis.hincrby(key, f"{activity_type}_count", 1)
        await self.redis.expire(key, 86400 * 7)  # 保留7天
        
        # 记录 IP 地址
        ip_key = f"user_ips:{user_id}:{today}"
        await self.redis.sadd(ip_key, ip_address)
        await self.redis.expire(ip_key, 86400 * 7)
        
        # 检查异常
        await self.check_for_anomalies(user_id)
    
    async def check_for_anomalies(self, user_id: str):
        """检查用户行为异常"""
        today = datetime.utcnow().date().isoformat()
        activity_key = f"user_activity:{user_id}:{today}"
        ip_key = f"user_ips:{user_id}:{today}"
        
        # 获取今日活动数据
        activity_data = await self.redis.hgetall(activity_key)
        unique_ips = await self.redis.scard(ip_key)
        
        user_activity = {
            'login_count': int(activity_data.get('login_count', 0)),
            'api_requests': int(activity_data.get('api_request_count', 0)),
            'file_uploads': int(activity_data.get('file_upload_count', 0)),
            'file_downloads': int(activity_data.get('file_download_count', 0)),
            'unique_ips': unique_ips,
            'failed_requests': int(activity_data.get('failed_request_count', 0)),
        }
        
        # 异常检测
        result = self.detector.detect_anomaly(user_activity)
        
        if result['is_anomaly']:
            await self.trigger_anomaly_alert(user_id, result)
    
    async def trigger_anomaly_alert(self, user_id: str, anomaly_result: dict):
        """触发异常告警"""
        alert = {
            'type': 'user_behavior_anomaly',
            'user_id': user_id,
            'anomaly_score': anomaly_result['score'],
            'features': anomaly_result['features'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 发送告警
        security_logger.log_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            details=alert
        )
```

## 合规性

### 数据保护法规

#### GDPR 合规

```python
class GDPRCompliance:
    """GDPR 合规性管理"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def handle_data_subject_request(self, request_type: str, 
                                        user_email: str) -> dict:
        """处理数据主体请求"""
        user = await self.get_user_by_email(user_email)
        if not user:
            return {"status": "user_not_found"}
        
        if request_type == "access":
            return await self.export_user_data(user.id)
        elif request_type == "deletion":
            return await self.delete_user_data(user.id)
        elif request_type == "portability":
            return await self.export_portable_data(user.id)
        elif request_type == "rectification":
            return {"status": "manual_review_required"}
        
        return {"status": "invalid_request_type"}
    
    async def export_user_data(self, user_id: int) -> dict:
        """导出用户数据"""
        user_data = {
            "personal_info": await self.get_user_info(user_id),
            "projects": await self.get_user_projects(user_id),
            "documents": await self.get_user_documents(user_id),
            "activity_logs": await self.get_user_activity(user_id),
            "export_timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "success",
            "data": user_data,
            "format": "json"
        }
    
    async def delete_user_data(self, user_id: int) -> dict:
        """删除用户数据（被遗忘权）"""
        try:
            # 匿名化而非删除，保持数据完整性
            await self.anonymize_user_data(user_id)
            
            return {
                "status": "success",
                "message": "User data has been anonymized",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def anonymize_user_data(self, user_id: int):
        """匿名化用户数据"""
        # 更新用户信息
        await self.db.execute(
            "UPDATE users SET "
            "username = :anon_username, "
            "email = :anon_email, "
            "full_name = :anon_name, "
            "phone = NULL, "
            "id_number = NULL "
            "WHERE id = :user_id",
            {
                "anon_username": f"anonymous_{user_id}",
                "anon_email": f"anonymous_{user_id}@deleted.local",
                "anon_name": "Anonymous User",
                "user_id": user_id
            }
        )
        
        # 清理活动日志中的敏感信息
        await self.db.execute(
            "UPDATE activity_logs SET "
            "ip_address = '0.0.0.0', "
            "user_agent = 'anonymized' "
            "WHERE user_id = :user_id",
            {"user_id": user_id}
        )
```

#### 数据保留策略

```python
class DataRetentionPolicy:
    """数据保留策略"""
    
    RETENTION_PERIODS = {
        "user_activity_logs": 365,      # 1年
        "security_logs": 2555,          # 7年
        "document_metadata": 3650,      # 10年
        "audit_trails": 2555,           # 7年
        "backup_files": 90,             # 3个月
    }
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def cleanup_expired_data(self):
        """清理过期数据"""
        for data_type, retention_days in self.RETENTION_PERIODS.items():
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            if data_type == "user_activity_logs":
                await self.cleanup_activity_logs(cutoff_date)
            elif data_type == "security_logs":
                await self.cleanup_security_logs(cutoff_date)
            elif data_type == "backup_files":
                await self.cleanup_backup_files(cutoff_date)
    
    async def cleanup_activity_logs(self, cutoff_date: datetime):
        """清理活动日志"""
        result = await self.db.execute(
            "DELETE FROM activity_logs WHERE created_at < :cutoff_date",
            {"cutoff_date": cutoff_date}
        )
        
        logger.info(f"Cleaned up {result.rowcount} activity log records")
    
    async def archive_old_documents(self, cutoff_date: datetime):
        """归档旧文档"""
        # 移动到归档存储
        old_documents = await self.db.execute(
            "SELECT id, file_path FROM documents WHERE upload_time < :cutoff_date",
            {"cutoff_date": cutoff_date}
        )
        
        for doc in old_documents:
            await self.move_to_archive_storage(doc.id, doc.file_path)
```

### 审计日志

```python
class AuditLogger:
    """审计日志记录"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.logger = structlog.get_logger("audit")
    
    async def log_data_access(self, user_id: int, resource_type: str, 
                            resource_id: int, action: str, ip_address: str):
        """记录数据访问"""
        audit_record = {
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow(),
            "session_id": self.get_session_id()
        }
        
        # 存储到数据库
        await self.db.execute(
            "INSERT INTO audit_logs (user_id, resource_type, resource_id, "
            "action, ip_address, timestamp, session_id) "
            "VALUES (:user_id, :resource_type, :resource_id, :action, "
            ":ip_address, :timestamp, :session_id)",
            audit_record
        )
        
        # 结构化日志
        self.logger.info("Data access", **audit_record)
    
    async def log_configuration_change(self, user_id: int, setting_name: str, 
                                     old_value: str, new_value: str):
        """记录配置变更"""
        change_record = {
            "user_id": user_id,
            "setting_name": setting_name,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.utcnow()
        }
        
        await self.db.execute(
            "INSERT INTO configuration_changes (user_id, setting_name, "
            "old_value, new_value, timestamp) "
            "VALUES (:user_id, :setting_name, :old_value, :new_value, :timestamp)",
            change_record
        )
        
        self.logger.info("Configuration change", **change_record)
```

## 安全事件响应

### 事件响应流程

```python
from enum import Enum
from typing import List, Dict

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentType(Enum):
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE_DETECTION = "malware_detection"
    DDOS_ATTACK = "ddos_attack"
    SYSTEM_COMPROMISE = "system_compromise"
    INSIDER_THREAT = "insider_threat"

class SecurityIncidentResponse:
    """安全事件响应"""
    
    def __init__(self, notification_service):
        self.notification_service = notification_service
        self.response_teams = {
            IncidentSeverity.CRITICAL: ["security_team", "management", "legal"],
            IncidentSeverity.HIGH: ["security_team", "it_team"],
            IncidentSeverity.MEDIUM: ["security_team"],
            IncidentSeverity.LOW: ["security_team"]
        }
    
    async def handle_incident(self, incident_type: IncidentType, 
                            severity: IncidentSeverity, details: dict):
        """处理安全事件"""
        incident_id = self.generate_incident_id()
        
        # 记录事件
        incident_record = {
            "incident_id": incident_id,
            "type": incident_type.value,
            "severity": severity.value,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "open"
        }
        
        # 立即响应
        await self.immediate_response(incident_type, severity, details)
        
        # 通知相关团队
        await self.notify_response_teams(severity, incident_record)
        
        # 启动调查
        await self.start_investigation(incident_id, incident_type, details)
        
        return incident_id
    
    async def immediate_response(self, incident_type: IncidentType, 
                               severity: IncidentSeverity, details: dict):
        """立即响应措施"""
        if incident_type == IncidentType.DATA_BREACH:
            await self.handle_data_breach(details)
        elif incident_type == IncidentType.UNAUTHORIZED_ACCESS:
            await self.handle_unauthorized_access(details)
        elif incident_type == IncidentType.DDOS_ATTACK:
            await self.handle_ddos_attack(details)
        elif incident_type == IncidentType.MALWARE_DETECTION:
            await self.handle_malware_detection(details)
    
    async def handle_data_breach(self, details: dict):
        """处理数据泄露"""
        # 立即隔离受影响的系统
        affected_systems = details.get('affected_systems', [])
        for system in affected_systems:
            await self.isolate_system(system)
        
        # 重置受影响用户的密码
        affected_users = details.get('affected_users', [])
        for user_id in affected_users:
            await self.force_password_reset(user_id)
        
        # 撤销所有活动会话
        await self.revoke_all_sessions()
    
    async def handle_unauthorized_access(self, details: dict):
        """处理未授权访问"""
        user_id = details.get('user_id')
        ip_address = details.get('ip_address')
        
        if user_id:
            # 锁定用户账户
            await self.lock_user_account(user_id)
        
        if ip_address:
            # 封禁 IP 地址
            await self.block_ip_address(ip_address)
    
    async def handle_ddos_attack(self, details: dict):
        """处理 DDoS 攻击"""
        attack_source = details.get('source_ips', [])
        
        # 启用 DDoS 防护
        await self.enable_ddos_protection()
        
        # 封禁攻击源 IP
        for ip in attack_source:
            await self.block_ip_address(ip)
        
        # 限制连接数
        await self.apply_connection_limits()
    
    async def handle_malware_detection(self, details: dict):
        """处理恶意软件检测"""
        infected_files = details.get('infected_files', [])
        
        # 隔离感染文件
        for file_path in infected_files:
            await self.quarantine_file(file_path)
        
        # 扫描整个系统
        await self.full_system_scan()
    
    def generate_incident_id(self) -> str:
        """生成事件 ID"""
        import uuid
        return f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    async def notify_response_teams(self, severity: IncidentSeverity, incident: dict):
        """通知响应团队"""
        teams = self.response_teams.get(severity, [])
        
        for team in teams:
            await self.notification_service.send_alert(
                team=team,
                subject=f"Security Incident - {severity.value.upper()}",
                message=f"Incident ID: {incident['incident_id']}\n"
                       f"Type: {incident['type']}\n"
                       f"Severity: {incident['severity']}\n"
                       f"Time: {incident['timestamp']}",
                priority="high" if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL] else "normal"
            )

### 事件恢复流程

```python
class IncidentRecovery:
    """事件恢复管理"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def create_recovery_plan(self, incident_id: str, incident_type: IncidentType) -> dict:
        """创建恢复计划"""
        recovery_steps = self.get_recovery_steps(incident_type)
        
        plan = {
            "incident_id": incident_id,
            "recovery_steps": recovery_steps,
            "estimated_duration": self.estimate_recovery_time(incident_type),
            "required_resources": self.get_required_resources(incident_type),
            "status": "planned",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 保存恢复计划
        await self.save_recovery_plan(plan)
        
        return plan
    
    def get_recovery_steps(self, incident_type: IncidentType) -> List[dict]:
        """获取恢复步骤"""
        steps_map = {
            IncidentType.DATA_BREACH: [
                {"step": 1, "action": "评估数据泄露范围", "duration": 60},
                {"step": 2, "action": "通知受影响用户", "duration": 120},
                {"step": 3, "action": "修复安全漏洞", "duration": 480},
                {"step": 4, "action": "恢复系统服务", "duration": 240},
                {"step": 5, "action": "验证系统安全性", "duration": 180},
            ],
            IncidentType.UNAUTHORIZED_ACCESS: [
                {"step": 1, "action": "重置受影响账户密码", "duration": 30},
                {"step": 2, "action": "审查访问日志", "duration": 120},
                {"step": 3, "action": "加强访问控制", "duration": 60},
                {"step": 4, "action": "监控异常活动", "duration": 1440},
            ],
            IncidentType.DDOS_ATTACK: [
                {"step": 1, "action": "启用 DDoS 防护", "duration": 15},
                {"step": 2, "action": "分析攻击模式", "duration": 60},
                {"step": 3, "action": "调整防护策略", "duration": 30},
                {"step": 4, "action": "恢复正常服务", "duration": 60},
            ]
        }
        
        return steps_map.get(incident_type, [])
    
    async def execute_recovery_step(self, incident_id: str, step_number: int) -> dict:
        """执行恢复步骤"""
        # 记录步骤开始
        await self.log_step_start(incident_id, step_number)
        
        try:
            # 执行具体恢复操作
            result = await self.perform_recovery_action(incident_id, step_number)
            
            # 记录步骤完成
            await self.log_step_completion(incident_id, step_number, "success")
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            # 记录步骤失败
            await self.log_step_completion(incident_id, step_number, "failed", str(e))
            
            return {"status": "failed", "error": str(e)}

## 安全最佳实践

### 开发安全最佳实践

#### 安全编码规范

```python
# 1. 输入验证
def validate_input(data: str, max_length: int = 255, 
                  allowed_chars: str = None) -> str:
    """安全的输入验证"""
    if not data:
        raise ValueError("Input cannot be empty")
    
    if len(data) > max_length:
        raise ValueError(f"Input too long: {len(data)} > {max_length}")
    
    if allowed_chars:
        if not all(c in allowed_chars for c in data):
            raise ValueError("Input contains forbidden characters")
    
    # HTML 转义
    return html.escape(data)

# 2. 安全的数据库查询
from sqlalchemy import text

def safe_database_query(db_session, user_input: str):
    """安全的数据库查询"""
    # 使用参数化查询
    query = text("SELECT * FROM users WHERE username = :username")
    result = db_session.execute(query, {"username": user_input})
    return result.fetchall()

# 3. 安全的文件操作
import os
from pathlib import Path

def safe_file_path(base_dir: str, filename: str) -> str:
    """安全的文件路径处理"""
    # 规范化路径
    base_path = Path(base_dir).resolve()
    file_path = (base_path / filename).resolve()
    
    # 检查路径遍历攻击
    if not str(file_path).startswith(str(base_path)):
        raise ValueError("Path traversal detected")
    
    return str(file_path)

# 4. 安全的随机数生成
import secrets

def generate_secure_token(length: int = 32) -> str:
    """生成安全的随机令牌"""
    return secrets.token_urlsafe(length)

def generate_secure_password(length: int = 16) -> str:
    """生成安全的密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```

#### 安全测试

```python
import pytest
from unittest.mock import patch

class TestSecurityFeatures:
    """安全功能测试"""
    
    def test_sql_injection_prevention(self):
        """测试 SQL 注入防护"""
        malicious_input = "'; DROP TABLE users; --"
        
        # 应该安全处理恶意输入
        result = safe_database_query(db_session, malicious_input)
        assert result == []  # 没有找到匹配的用户
    
    def test_xss_prevention(self):
        """测试 XSS 防护"""
        malicious_script = "<script>alert('xss')</script>"
        
        cleaned_input = validate_input(malicious_script)
        assert "<script>" not in cleaned_input
        assert "&lt;script&gt;" in cleaned_input
    
    def test_path_traversal_prevention(self):
        """测试路径遍历防护"""
        malicious_path = "../../../etc/passwd"
        
        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_file_path("/app/uploads", malicious_path)
    
    def test_rate_limiting(self):
        """测试速率限制"""
        # 模拟大量请求
        for i in range(100):
            response = client.post("/api/v1/auth/login", json={
                "username": "test",
                "password": "wrong"
            })
            
            if i > 10:  # 超过限制后应该被阻止
                assert response.status_code == 429
    
    def test_authentication_bypass(self):
        """测试认证绕过"""
        # 尝试访问受保护的端点
        response = client.get("/api/v1/users/profile")
        assert response.status_code == 401
        
        # 使用无效令牌
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 401
```

### 运维安全最佳实践

#### 安全配置检查清单

```yaml
# security_checklist.yml
security_checklist:
  system:
    - name: "系统更新"
      description: "确保系统和软件包是最新版本"
      command: "apt list --upgradable"
      expected: "无可升级包"
    
    - name: "防火墙状态"
      description: "确保防火墙已启用并正确配置"
      command: "ufw status"
      expected: "Status: active"
    
    - name: "SSH 配置"
      description: "检查 SSH 安全配置"
      files:
        - "/etc/ssh/sshd_config"
      checks:
        - "PermitRootLogin no"
        - "PasswordAuthentication no"
        - "Protocol 2"
  
  application:
    - name: "HTTPS 配置"
      description: "确保使用 HTTPS"
      command: "curl -I https://your-domain.com"
      expected: "HTTP/2 200"
    
    - name: "安全头检查"
      description: "检查 HTTP 安全头"
      headers:
        - "Strict-Transport-Security"
        - "X-Frame-Options"
        - "X-Content-Type-Options"
        - "Content-Security-Policy"
    
    - name: "数据库连接"
      description: "确保数据库连接使用 SSL"
      command: "psql -c 'SHOW ssl;'"
      expected: "on"
  
  monitoring:
    - name: "日志记录"
      description: "确保安全事件被正确记录"
      files:
        - "/var/log/auth.log"
        - "/var/log/nginx/access.log"
        - "/var/log/application.log"
    
    - name: "监控告警"
      description: "确保监控系统正常工作"
      checks:
        - "fail2ban status"
        - "systemctl status prometheus"
        - "systemctl status grafana-server"
```

#### 自动化安全检查

```bash
#!/bin/bash
# security_audit.sh - 自动化安全审计脚本

LOG_FILE="/var/log/security_audit.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting security audit" >> $LOG_FILE

# 1. 检查系统更新
echo "Checking system updates..." >> $LOG_FILE
UPDATES=$(apt list --upgradable 2>/dev/null | grep -c upgradable)
if [ $UPDATES -gt 0 ]; then
    echo "WARNING: $UPDATES packages need updates" >> $LOG_FILE
fi

# 2. 检查失败登录
echo "Checking failed login attempts..." >> $LOG_FILE
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    echo "WARNING: $FAILED_LOGINS failed login attempts detected" >> $LOG_FILE
fi

# 3. 检查磁盘使用
echo "Checking disk usage..." >> $LOG_FILE
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%" >> $LOG_FILE
fi

# 4. 检查网络连接
echo "Checking network connections..." >> $LOG_FILE
SUSPICIOUS_CONNECTIONS=$(netstat -an | grep ESTABLISHED | wc -l)
if [ $SUSPICIOUS_CONNECTIONS -gt 100 ]; then
    echo "WARNING: $SUSPICIOUS_CONNECTIONS active connections" >> $LOG_FILE
fi

# 5. 检查进程
echo "Checking running processes..." >> $LOG_FILE
ps aux --sort=-%cpu | head -10 >> $LOG_FILE

# 6. 检查文件完整性
echo "Checking file integrity..." >> $LOG_FILE
if command -v aide >/dev/null 2>&1; then
    aide --check >> $LOG_FILE 2>&1
fi

echo "[$DATE] Security audit completed" >> $LOG_FILE

# 发送报告
if [ -s $LOG_FILE ]; then
    mail -s "Security Audit Report - $(hostname)" admin@company.com < $LOG_FILE
fi
```

### 用户安全培训

#### 安全意识培训内容

1. **密码安全**
   - 使用强密码
   - 启用多因素认证
   - 不共享账户信息
   - 定期更换密码

2. **钓鱼邮件识别**
   - 识别可疑邮件
   - 验证发件人身份
   - 不点击可疑链接
   - 报告安全事件

3. **数据保护**
   - 分类敏感数据
   - 安全传输数据
   - 定期备份重要数据
   - 遵循数据保留政策

4. **设备安全**
   - 锁定工作站
   - 安装安全更新
   - 使用公司批准的软件
   - 报告丢失或被盗设备

## 总结

本安全指南涵盖了政府采购项目审查分析系统的全面安全策略，包括：

- **多层次安全防护**：从网络到应用的全方位保护
- **严格的认证授权**：基于角色的访问控制和多因素认证
- **数据安全保护**：端到端加密和安全备份
- **实时安全监控**：异常检测和事件响应
- **合规性管理**：满足相关法规要求
- **持续安全改进**：定期评估和更新安全措施

安全是一个持续的过程，需要定期评估、更新和改进。建议：

1. **定期安全评估**：每季度进行一次全面的安全评估
2. **安全培训**：为所有用户提供定期的安全意识培训
3. **事件演练**：定期进行安全事件响应演练
4. **技术更新**：及时更新安全技术和工具
5. **合规审计**：定期进行合规性审计

通过实施这些安全措施，可以确保系统的机密性、完整性和可用性，保护敏感的政府采购数据，并满足相关的法规要求