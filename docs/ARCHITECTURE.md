# 系统架构设计文档

本文档详细描述了政府采购项目审查分析系统的整体架构设计、技术选型和实现细节。

## 目录

- [系统概述](#系统概述)
- [架构设计](#架构设计)
- [技术栈](#技术栈)
- [数据模型](#数据模型)
- [API 设计](#api-设计)
- [安全架构](#安全架构)
- [性能设计](#性能设计)
- [监控和日志](#监控和日志)
- [部署架构](#部署架构)
- [扩展性设计](#扩展性设计)

## 系统概述

### 业务背景

政府采购项目审查分析系统是一个现代化的文档管理和分析平台，主要用于：

- **文档管理**: 支持多格式文档的上传、存储、检索和管理
- **OCR 识别**: 自动提取文档中的文本内容
- **智能分析**: 基于规则和AI的文档内容分析
- **审查流程**: 标准化的项目审查工作流
- **监控报告**: 实时监控和数据分析报告

### 设计目标

- **高性能**: 支持大量并发用户和文档处理
- **高可用**: 99.9% 的系统可用性
- **可扩展**: 支持水平扩展和模块化扩展
- **安全性**: 企业级安全保障
- **易维护**: 清晰的代码结构和完善的文档

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
├─────────────────────────────────────────────────────────────┤
│  Web Browser  │  Mobile App  │  Desktop App  │  API Client  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      负载均衡层                              │
├─────────────────────────────────────────────────────────────┤
│              Nginx / HAProxy / AWS ALB                     │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      应用服务层                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ FastAPI App │  │ FastAPI App │  │ FastAPI App │          │
│  │  Instance 1 │  │  Instance 2 │  │  Instance N │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务层                                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ OCR Service │  │Auth Service │  │File Service │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │Cache Service│  │ Log Service │  │Alert Service│          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ PostgreSQL  │  │    Redis    │  │File Storage │          │
│  │  (主数据库)  │  │   (缓存)    │  │  (文件存储)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    监控和日志层                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Prometheus  │  │   Grafana   │  │ ELK Stack   │          │
│  │  (指标收集)  │  │  (可视化)   │  │  (日志聚合)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 分层架构

#### 1. 表现层 (Presentation Layer)
- **Web 界面**: 基于现代前端框架的响应式界面
- **API 接口**: RESTful API，支持 OpenAPI/Swagger 文档
- **移动端**: 支持移动设备访问

#### 2. 业务逻辑层 (Business Logic Layer)
- **用户管理**: 认证、授权、用户信息管理
- **项目管理**: 项目创建、更新、删除、查询
- **文档管理**: 文档上传、存储、检索、分析
- **OCR 处理**: 文档内容提取和识别
- **审查流程**: 标准化的审查工作流

#### 3. 数据访问层 (Data Access Layer)
- **ORM 映射**: SQLAlchemy 异步 ORM
- **缓存管理**: Redis 缓存策略
- **文件存储**: 本地/云存储管理

#### 4. 基础设施层 (Infrastructure Layer)
- **数据库**: PostgreSQL 主数据库
- **缓存**: Redis 内存缓存
- **消息队列**: Celery + Redis (可选)
- **监控**: Prometheus + Grafana

## 技术栈

### 后端技术

```python
# 核心框架
FastAPI = "0.104+"          # Web 框架
Uvicorn = "0.24+"           # ASGI 服务器
Gunicorn = "21.2+"          # WSGI 服务器

# 数据库和 ORM
SQLAlchemy = "2.0+"         # 异步 ORM
Asyncpg = "0.29+"           # PostgreSQL 异步驱动
Alembic = "1.12+"           # 数据库迁移

# 缓存和会话
Redis = "5.0+"              # 缓存和会话存储
Aioredis = "2.0+"           # Redis 异步客户端

# 认证和安全
PyJWT = "2.8+"              # JWT 处理
Passlib = "1.7+"            # 密码哈希
Bcrypt = "4.0+"             # 密码加密

# OCR 和文档处理
PaddleOCR = "3.1.0"         # OCR 引擎
Pillow = "10.0+"            # 图像处理
PyPDF2 = "3.0+"             # PDF 处理
Python_docx = "0.8+"        # Word 文档处理

# 监控和日志
Prometheus_client = "0.19+" # Prometheus 指标
Structlog = "23.2+"         # 结构化日志

# 开发和测试
Pytest = "7.4+"             # 测试框架
Pytest_asyncio = "0.21+"    # 异步测试
Black = "23.9+"             # 代码格式化
Mypy = "1.6+"               # 类型检查
```

### 基础设施

```yaml
# 数据库
PostgreSQL: "15+"
Redis: "7+"

# 容器化
Docker: "20.10+"
Docker_Compose: "2.0+"

# 反向代理
Nginx: "1.20+"

# 监控
Prometheus: "2.40+"
Grafana: "10.0+"

# CI/CD
GitHub_Actions: "latest"
```

## 数据模型

### 核心实体关系图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────▶│   Project   │────▶│  Document   │
│             │     │             │     │             │
│ - id        │     │ - id        │     │ - id        │
│ - username  │     │ - name      │     │ - filename  │
│ - email     │     │ - owner_id  │     │ - project_id│
│ - role      │     │ - status    │     │ - file_path │
│ - is_active │     │ - created_at│     │ - file_size │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ OCR_Result  │
                                        │             │
                                        │ - id        │
                                        │ - doc_id    │
                                        │ - text      │
                                        │ - confidence│
                                        │ - bbox_data │
                                        └─────────────┘
```

### 数据模型详细设计

#### 用户模型 (User)

```python
class User(Base):
    __tablename__ = "users"
    
    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(50), unique=True, index=True, nullable=False)
    email: str = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    full_name: str = Column(String(100))
    role: str = Column(String(20), default="user")  # admin, user, viewer
    is_active: bool = Column(Boolean, default=True)
    is_superuser: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: datetime = Column(DateTime)
    
    # 关系
    projects = relationship("Project", back_populates="owner")
    documents = relationship("Document", back_populates="uploader")
```

#### 项目模型 (Project)

```python
class Project(Base):
    __tablename__ = "projects"
    
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(200), nullable=False, index=True)
    description: str = Column(Text)
    project_type: str = Column(String(50), default="government_procurement")
    status: str = Column(String(20), default="active")  # active, completed, archived
    owner_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
```

#### 文档模型 (Document)

```python
class Document(Base):
    __tablename__ = "documents"
    
    id: int = Column(Integer, primary_key=True, index=True)
    filename: str = Column(String(255), nullable=False)
    original_filename: str = Column(String(255), nullable=False)
    file_path: str = Column(String(500), nullable=False)
    file_size: int = Column(BigInteger)
    file_type: str = Column(String(50))
    document_category: str = Column(String(100), index=True)
    document_type: str = Column(String(50))
    summary: str = Column(Text)
    extracted_text: str = Column(Text)
    project_id: int = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    uploader_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_time: datetime = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User", back_populates="documents")
    ocr_results = relationship("OCRResult", back_populates="document", cascade="all, delete-orphan")
```

#### OCR 结果模型 (OCRResult)

```python
class OCRResult(Base):
    __tablename__ = "ocr_results"
    
    id: int = Column(Integer, primary_key=True, index=True)
    document_id: int = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    extracted_text: str = Column(Text)
    confidence_score: float = Column(Float)
    processing_time: float = Column(Float)
    status: str = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message: str = Column(Text)
    bounding_boxes: str = Column(JSON)  # 存储边界框数据
    created_at: datetime = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    document = relationship("Document", back_populates="ocr_results")
```

### 数据库索引策略

```sql
-- 用户表索引
CREATE INDEX CONCURRENTLY idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_role ON users(role);
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);

-- 项目表索引
CREATE INDEX CONCURRENTLY idx_projects_owner_id ON projects(owner_id);
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);
CREATE INDEX CONCURRENTLY idx_projects_created_at ON projects(created_at);
CREATE INDEX CONCURRENTLY idx_projects_name_gin ON projects USING gin(to_tsvector('english', name));

-- 文档表索引
CREATE INDEX CONCURRENTLY idx_documents_project_id ON documents(project_id);
CREATE INDEX CONCURRENTLY idx_documents_uploader_id ON documents(uploader_id);
CREATE INDEX CONCURRENTLY idx_documents_category ON documents(document_category);
CREATE INDEX CONCURRENTLY idx_documents_upload_time ON documents(upload_time);
CREATE INDEX CONCURRENTLY idx_documents_filename_gin ON documents USING gin(to_tsvector('english', filename));
CREATE INDEX CONCURRENTLY idx_documents_text_gin ON documents USING gin(to_tsvector('english', extracted_text));

-- OCR 结果表索引
CREATE INDEX CONCURRENTLY idx_ocr_results_document_id ON ocr_results(document_id);
CREATE INDEX CONCURRENTLY idx_ocr_results_status ON ocr_results(status);
CREATE INDEX CONCURRENTLY idx_ocr_results_created_at ON ocr_results(created_at);
```

## API 设计

### RESTful API 设计原则

1. **资源导向**: 使用名词表示资源，动词表示操作
2. **HTTP 方法**: 正确使用 GET、POST、PUT、DELETE
3. **状态码**: 使用标准 HTTP 状态码
4. **版本控制**: 使用 URL 路径版本控制 (/api/v1/)
5. **统一响应**: 所有 API 使用统一的响应格式

### API 路由设计

```python
# 认证相关
POST   /api/v1/auth/login          # 用户登录
POST   /api/v1/auth/logout         # 用户登出
POST   /api/v1/auth/refresh        # 刷新 Token

# 用户管理
GET    /api/v1/users/              # 获取用户列表 (管理员)
POST   /api/v1/users/              # 创建用户 (管理员)
GET    /api/v1/users/me            # 获取当前用户信息
PUT    /api/v1/users/me            # 更新当前用户信息
PUT    /api/v1/users/me/password   # 修改密码
GET    /api/v1/users/{user_id}     # 获取用户详情 (管理员)
PUT    /api/v1/users/{user_id}     # 更新用户信息 (管理员)
DELETE /api/v1/users/{user_id}     # 删除用户 (管理员)

# 项目管理
GET    /api/v1/projects/           # 获取项目列表
POST   /api/v1/projects/           # 创建项目
GET    /api/v1/projects/{id}       # 获取项目详情
PUT    /api/v1/projects/{id}       # 更新项目
DELETE /api/v1/projects/{id}       # 删除项目

# 文档管理
POST   /api/v1/documents/upload/{project_id}        # 上传文档
POST   /api/v1/documents/batch-upload/{project_id}  # 批量上传
GET    /api/v1/documents/project/{project_id}       # 获取项目文档
GET    /api/v1/documents/search                     # 搜索文档
GET    /api/v1/documents/{id}                       # 获取文档详情
GET    /api/v1/documents/{id}/download              # 下载文档
PUT    /api/v1/documents/{id}                       # 更新文档信息
DELETE /api/v1/documents/{id}                       # 删除文档

# OCR 服务
POST   /api/v1/ocr/process/{document_id}           # 处理文档 OCR
GET    /api/v1/ocr/results/{document_id}           # 获取 OCR 结果
GET    /api/v1/ocr/results/detail/{ocr_id}         # 获取 OCR 详情

# 系统管理
GET    /health                                     # 健康检查
GET    /metrics                                    # Prometheus 指标
GET    /api/v1/system/info                         # 系统信息
```

### 响应格式标准化

```python
class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = 200
    message: str = "Success"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int
    message: str
    error: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## 安全架构

### 认证和授权

#### JWT 认证流程

```
1. 用户登录 → 验证用户名密码
2. 生成 JWT Token (包含用户ID、角色、过期时间)
3. 客户端存储 Token
4. 后续请求携带 Token
5. 服务端验证 Token 有效性
6. 提取用户信息进行授权检查
```

#### RBAC 权限模型

```python
class Role(Enum):
    ADMIN = "admin"        # 系统管理员
    USER = "user"          # 普通用户
    VIEWER = "viewer"      # 只读用户

class Permission(Enum):
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 项目管理
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    
    # 文档管理
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"

# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],  # 管理员拥有所有权限
    Role.USER: [
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, 
        Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE, Permission.DOCUMENT_DELETE,
    ],
    Role.VIEWER: [
        Permission.PROJECT_READ, Permission.DOCUMENT_READ,
    ],
}
```

### 数据安全

#### 密码安全

```python
# 使用 bcrypt 进行密码哈希
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

#### 数据加密

```python
# 敏感数据加密存储
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### 网络安全

#### HTTPS 配置

```nginx
# SSL/TLS 配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# 安全头
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

#### CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## 性能设计

### 缓存策略

#### 多级缓存架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Application │───▶│    Redis    │───▶│ PostgreSQL  │
│   Cache     │    │   Cache     │    │  Database   │
│ (内存缓存)   │    │ (分布式缓存) │    │ (持久化存储) │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### 缓存策略实现

```python
class CacheStrategy:
    # 缓存时间配置
    TTL_SHORT = 300      # 5 分钟 - 频繁变化的数据
    TTL_MEDIUM = 1800    # 30 分钟 - 中等变化的数据
    TTL_LONG = 7200      # 2 小时 - 相对稳定的数据
    
    # 缓存键前缀
    USER_PREFIX = "user:"
    PROJECT_PREFIX = "project:"
    DOCUMENT_PREFIX = "document:"
    SEARCH_PREFIX = "search:"

@cache_decorator(ttl=CacheStrategy.TTL_MEDIUM)
async def get_user_by_id(user_id: int) -> User:
    """获取用户信息 - 中等缓存时间"""
    pass

@cache_decorator(ttl=CacheStrategy.TTL_SHORT)
async def search_documents(query: str, filters: dict) -> List[Document]:
    """搜索文档 - 短缓存时间"""
    pass
```

### 数据库优化

#### 连接池配置

```python
# SQLAlchemy 异步连接池
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # 连接池大小
    max_overflow=30,        # 最大溢出连接数
    pool_timeout=30,        # 连接超时时间
    pool_recycle=3600,      # 连接回收时间
    pool_pre_ping=True,     # 连接预检查
    echo=False,             # 生产环境关闭 SQL 日志
)
```

#### 查询优化

```python
# 使用索引优化查询
class DocumentCRUD:
    async def search_documents(
        self, 
        db: AsyncSession,
        query: str,
        project_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Document]:
        # 使用全文搜索索引
        stmt = select(Document).where(
            or_(
                Document.filename.contains(query),
                func.to_tsvector('english', Document.extracted_text).match(query)
            )
        )
        
        if project_id:
            stmt = stmt.where(Document.project_id == project_id)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
```

### 异步处理

#### OCR 异步处理

```python
from celery import Celery

# Celery 配置
celery_app = Celery(
    "sys_rev_tec",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/2"
)

@celery_app.task
def process_ocr_task(document_id: int) -> dict:
    """异步 OCR 处理任务"""
    try:
        # OCR 处理逻辑
        result = ocr_service.process_document(document_id)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# API 端点
@router.post("/ocr/process/{document_id}")
async def process_document_ocr(document_id: int):
    # 提交异步任务
    task = process_ocr_task.delay(document_id)
    return {"task_id": task.id, "status": "processing"}
```

## 监控和日志

### 监控架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Application │───▶│ Prometheus  │───▶│   Grafana   │
│  Metrics    │    │  (指标收集)  │    │  (可视化)   │
└─────────────┘    └─────────────┘    └─────────────┘
        │
        ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Logs      │───▶│ Elasticsearch│───▶│   Kibana    │
│ (应用日志)   │    │  (日志存储)  │    │ (日志分析)  │
└─────────────┘    └─────────────┘    └─────────────┘
        │
        ▼
┌─────────────┐    ┌─────────────┐
│   Alerts    │───▶│ AlertManager│
│ (告警规则)   │    │  (告警管理)  │
└─────────────┘    └─────────────┘
```

### 指标收集

```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users_total',
    'Number of active users'
)

database_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

# 中间件收集指标
class MetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # 记录请求指标
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        http_request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
```

### 结构化日志

```python
import structlog

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# 使用示例
logger.info(
    "User login",
    user_id=user.id,
    username=user.username,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

## 部署架构

### 容器化部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dbname
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=sys_rev_tec
      - POSTGRES_USER=app_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass redis_password
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 生产环境架构

```
                    ┌─────────────┐
                    │ Load Balancer│
                    │   (AWS ALB)  │
                    └─────────────┘
                           │
                           ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   App-1     │ │   App-2     │ │   App-N     │
    │ (Container) │ │ (Container) │ │ (Container) │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ PostgreSQL  │ │    Redis    │ │File Storage │
    │   (RDS)     │ │ (ElastiCache│ │   (S3)      │
    └─────────────┘ └─────────────┘ └─────────────┘
```

## 扩展性设计

### 水平扩展

#### 应用层扩展

```python
# 无状态应用设计
class StatelessApp:
    def __init__(self):
        # 所有状态存储在外部系统
        self.db = get_database_session()
        self.cache = get_redis_client()
        self.storage = get_file_storage()
    
    async def handle_request(self, request):
        # 请求处理逻辑
        # 不依赖本地状态
        pass
```

#### 数据库扩展

```python
# 读写分离
class DatabaseRouter:
    def __init__(self):
        self.write_db = create_engine(WRITE_DATABASE_URL)
        self.read_db = create_engine(READ_DATABASE_URL)
    
    def get_session(self, read_only: bool = False):
        if read_only:
            return sessionmaker(bind=self.read_db)()
        return sessionmaker(bind=self.write_db)()

# 分库分表
class ShardingStrategy:
    def get_shard_key(self, user_id: int) -> str:
        return f"shard_{user_id % 4}"
    
    def get_database_url(self, shard_key: str) -> str:
        return DATABASE_URLS[shard_key]
```

### 微服务架构演进

```
当前单体架构 → 模块化单体 → 微服务架构

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monolithic    │    │   Modular       │    │  Microservices  │
│   Application   │───▶│   Monolith      │───▶│   Architecture  │
│                 │    │                 │    │                 │
│ - All in one    │    │ - Clear modules │    │ - User Service  │
│ - Single DB     │    │ - Shared DB     │    │ - Doc Service   │
│ - Single deploy │    │ - Single deploy │    │ - OCR Service   │
└─────────────────┘    └─────────────────┘    │ - Auth Service  │
                                              └─────────────────┘
```

### 插件化架构

```python
# 插件接口定义
class PluginInterface:
    def initialize(self) -> None:
        pass
    
    def process(self, data: Any) -> Any:
        pass
    
    def cleanup(self) -> None:
        pass

# OCR 插件示例
class PaddleOCRPlugin(PluginInterface):
    def initialize(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    
    def process(self, image_path: str) -> dict:
        result = self.ocr.ocr(image_path, cls=True)
        return self.format_result(result)

# 插件管理器
class PluginManager:
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, name: str, plugin: PluginInterface):
        self.plugins[name] = plugin
        plugin.initialize()
    
    def execute_plugin(self, name: str, data: Any) -> Any:
        if name in self.plugins:
            return self.plugins[name].process(data)
        raise ValueError(f"Plugin {name} not found")
```

---

**最后更新**: 2025-01-25  
**文档版本**: v1.0.0  
**架构版本**: v1.0.0