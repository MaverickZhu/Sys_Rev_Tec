# API 文档

本文档详细描述了政府采购项目审查分析系统的 RESTful API 接口。

## 目录

- [基础信息](#基础信息)
- [认证](#认证)
- [用户管理](#用户管理)
- [项目管理](#项目管理)
- [文档管理](#文档管理)
- [OCR 服务](#ocr-服务)
- [监控和健康检查](#监控和健康检查)
- [错误处理](#错误处理)

## 基础信息

### API 基础 URL

- **开发环境**: `http://localhost:8000`
- **生产环境**: `https://your-domain.com`

### API 版本

当前 API 版本: `v1`

所有 API 端点都以 `/api/v1` 为前缀。

### 内容类型

- **请求**: `application/json` (除文件上传外)
- **响应**: `application/json`
- **文件上传**: `multipart/form-data`

### 响应格式

所有 API 响应都遵循统一的格式：

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    // 具体数据
  },
  "timestamp": "2025-01-25T10:30:00Z"
}
```

错误响应格式：

```json
{
  "code": 400,
  "message": "Bad Request",
  "error": {
    "type": "ValidationError",
    "message": "详细错误信息",
    "details": {
      // 错误详情
    }
  },
  "timestamp": "2025-01-25T10:30:00Z"
}
```

## 认证

### JWT 认证

系统使用 JWT (JSON Web Token) 进行用户认证。

#### 登录

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**响应**:

```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true
    }
  }
}
```

#### 使用 Token

在后续请求中，需要在 Header 中包含 Authorization 字段：

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### 刷新 Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <current_token>
```

#### 登出

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

## 用户管理

### 获取当前用户信息

```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

### 更新用户信息

```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "new-email@example.com",
  "full_name": "新的全名"
}
```

### 修改密码

```http
PUT /api/v1/users/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

### 用户列表 (管理员)

```http
GET /api/v1/users/?skip=0&limit=20
Authorization: Bearer <admin_token>
```

### 创建用户 (管理员)

```http
POST /api/v1/users/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "full_name": "新用户",
  "role": "user"
}
```

## 项目管理

### 创建项目

```http
POST /api/v1/projects/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "项目名称",
  "description": "项目描述",
  "project_type": "government_procurement",
  "status": "active"
}
```

### 获取项目列表

```http
GET /api/v1/projects/?skip=0&limit=20&status=active
Authorization: Bearer <token>
```

### 获取项目详情

```http
GET /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

### 更新项目

```http
PUT /api/v1/projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "更新的项目名称",
  "description": "更新的项目描述",
  "status": "completed"
}
```

### 删除项目

```http
DELETE /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

## 文档管理

### 上传文档

```http
POST /api/v1/documents/upload/{project_id}
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <文件>
document_category: "合同文件"
document_type: "PDF"
summary: "文档摘要"
```

**支持的文件格式**:
- 图片: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`
- PDF: `.pdf`
- 文档: `.doc`, `.docx`, `.txt`, `.rtf`

### 批量上传文档

```http
POST /api/v1/documents/batch-upload/{project_id}
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: <文件列表>
document_category: "技术文档"
```

### 获取项目文档列表

```http
GET /api/v1/documents/project/{project_id}?skip=0&limit=20&document_category=合同文件
Authorization: Bearer <token>
```

### 搜索文档

```http
GET /api/v1/documents/search?q=关键词&project_id={project_id}&skip=0&limit=20
Authorization: Bearer <token>
```

### 获取文档详情

```http
GET /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

### 下载文档

```http
GET /api/v1/documents/{document_id}/download
Authorization: Bearer <token>
```

### 更新文档信息

```http
PUT /api/v1/documents/{document_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_category": "新类别",
  "summary": "更新的摘要"
}
```

### 删除文档

```http
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

## OCR 服务

### 处理文档 OCR

```http
POST /api/v1/ocr/process/{document_id}
Authorization: Bearer <token>
```

**响应**:

```json
{
  "code": 200,
  "message": "OCR processing completed",
  "data": {
    "ocr_result_id": 123,
    "document_id": 456,
    "extracted_text": "提取的文本内容...",
    "confidence_score": 0.95,
    "processing_time": 2.34,
    "status": "completed",
    "bounding_boxes": [
      {
        "text": "文本块",
        "confidence": 0.98,
        "bbox": [100, 200, 300, 250]
      }
    ]
  }
}
```

### 获取 OCR 结果

```http
GET /api/v1/ocr/results/{document_id}
Authorization: Bearer <token>
```

### 获取 OCR 结果详情

```http
GET /api/v1/ocr/results/detail/{ocr_result_id}
Authorization: Bearer <token>
```

## 监控和健康检查

### 健康检查

```http
GET /health
```

**响应**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-25T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ocr_service": "healthy"
  }
}
```

### 系统信息

```http
GET /api/v1/system/info
Authorization: Bearer <admin_token>
```

### Prometheus 指标

```http
GET /metrics
```

## 错误处理

### HTTP 状态码

- `200` - 成功
- `201` - 创建成功
- `400` - 请求错误
- `401` - 未认证
- `403` - 权限不足
- `404` - 资源不存在
- `422` - 验证错误
- `429` - 请求过于频繁
- `500` - 服务器内部错误

### 错误类型

#### 验证错误 (422)

```json
{
  "code": 422,
  "message": "Validation Error",
  "error": {
    "type": "ValidationError",
    "message": "输入数据验证失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确",
        "type": "value_error.email"
      }
    ]
  }
}
```

#### 认证错误 (401)

```json
{
  "code": 401,
  "message": "Unauthorized",
  "error": {
    "type": "AuthenticationError",
    "message": "Token 已过期或无效"
  }
}
```

#### 权限错误 (403)

```json
{
  "code": 403,
  "message": "Forbidden",
  "error": {
    "type": "PermissionError",
    "message": "您没有权限访问此资源"
  }
}
```

#### 资源不存在 (404)

```json
{
  "code": 404,
  "message": "Not Found",
  "error": {
    "type": "NotFoundError",
    "message": "请求的资源不存在"
  }
}
```

#### 频率限制 (429)

```json
{
  "code": 429,
  "message": "Too Many Requests",
  "error": {
    "type": "RateLimitError",
    "message": "请求过于频繁，请稍后再试",
    "details": {
      "retry_after": 60
    }
  }
}
```

## 分页

大多数列表 API 都支持分页，使用以下参数：

- `skip`: 跳过的记录数 (默认: 0)
- `limit`: 每页记录数 (默认: 20, 最大: 100)

**响应格式**:

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [...],
    "total": 150,
    "skip": 0,
    "limit": 20,
    "has_next": true
  }
}
```

## 排序和筛选

### 排序

使用 `order_by` 参数进行排序：

```http
GET /api/v1/projects/?order_by=created_at&order=desc
```

- `order_by`: 排序字段
- `order`: 排序方向 (`asc` 或 `desc`)

### 筛选

不同的 API 支持不同的筛选参数，具体请参考各个端点的文档。

## 速率限制

为了保护系统资源，API 实施了速率限制：

- **普通用户**: 每分钟 60 次请求
- **认证用户**: 每分钟 120 次请求
- **管理员**: 每分钟 300 次请求
- **文件上传**: 每分钟 10 次请求

当达到速率限制时，API 会返回 429 状态码。

## 缓存

系统使用 Redis 进行缓存，以提高性能：

- **短期缓存** (5分钟): 搜索结果、列表数据
- **中期缓存** (30分钟): 文档详情、用户信息
- **长期缓存** (2小时): 系统配置、静态数据

## 版本控制

API 使用 URL 路径进行版本控制。当前版本为 `v1`，未来版本将使用 `v2`、`v3` 等。

旧版本将在新版本发布后继续维护 6 个月。

---

**最后更新**: 2025-01-25  
**API 版本**: v1.0.0
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
