# AI服务 (AI Service)

智能向量化和搜索服务，为系统评审技术平台提供AI增强功能。

## 🚀 功能特性

### 核心功能
- **智能向量化**: 支持文本和文档的向量化处理
- **多模态搜索**: 向量搜索、文本搜索、混合搜索、语义搜索
- **问答系统**: 基于检索增强生成(RAG)的智能问答
- **文本处理**: 智能分块、关键词提取、语言检测
- **缓存优化**: Redis缓存提升性能
- **监控指标**: Prometheus集成，实时性能监控

### AI模型支持
- **Ollama**: 本地部署的开源模型
- **Azure OpenAI**: 云端GPT模型
- **自定义模型**: 支持扩展其他AI服务

## 📋 系统要求

### 最低配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 20GB可用空间
- **Python**: 3.11+

### 推荐配置
- **CPU**: 8核心
- **内存**: 16GB RAM
- **存储**: 50GB SSD
- **GPU**: 支持CUDA的显卡(可选)

## 🛠️ 快速开始

### 方式一：Docker Compose (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd ai_service
```

2. **启动服务栈**
```bash
docker-compose up -d
```

3. **等待服务启动**
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f ai-service
```

4. **验证服务**
```bash
# 健康检查
curl http://localhost:8001/health

# API文档
open http://localhost:8001/docs
```

### 方式二：本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库和AI服务
```

3. **启动依赖服务**
```bash
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=sys_rev_tec \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 postgres:15

# Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Ollama
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest
```

4. **启动AI服务**
```bash
python start_ai_service.py
```

## 🔧 配置说明

### 环境变量

```bash
# 服务配置
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=8001

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/sys_rev_tec

# 缓存配置
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# AI模型配置
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_EMBEDDING_MODEL=nomic-embed-text
VECTOR_DIMENSION=768

# Azure OpenAI (可选)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/ai_service.log
```

### Ollama模型安装

```bash
# 安装嵌入模型
docker exec ollama ollama pull nomic-embed-text

# 安装对话模型
docker exec ollama ollama pull llama3.1:8b
docker exec ollama ollama pull qwen2.5:7b

# 查看已安装模型
docker exec ollama ollama list
```

## 📚 API文档

### 向量化API

#### 生成文本嵌入
```bash
POST /api/v1/vectorization/embed
{
  "text": "要向量化的文本",
  "provider": "ollama",
  "model": "nomic-embed-text"
}
```

#### 批量向量化
```bash
POST /api/v1/vectorization/batch-embed
{
  "texts": ["文本1", "文本2", "文本3"],
  "provider": "ollama"
}
```

#### 文档向量化
```bash
POST /api/v1/vectorization/vectorize-document
{
  "content": "文档内容",
  "document_id": "doc_001",
  "chunk_strategy": "fixed_size",
  "chunk_size": 512
}
```

### 搜索API

#### 智能搜索
```bash
POST /api/v1/search/intelligent
{
  "query": "搜索查询",
  "search_type": "hybrid",
  "limit": 10,
  "filters": {
    "document_type": "pdf",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

#### 问答搜索
```bash
POST /api/v1/search/qa
{
  "question": "什么是人工智能？",
  "context_limit": 5,
  "generate_answer": true
}
```

### 健康检查API

```bash
# 基础健康检查
GET /health

# 详细健康检查
GET /health/detailed

# Prometheus指标
GET /health/metrics
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest tests/test_ai_service.py -v

# 运行特定测试
pytest tests/test_ai_service.py::TestVectorizationService -v

# 生成覆盖率报告
pytest tests/test_ai_service.py --cov=ai_service --cov-report=html
```

### 性能测试
```bash
# 向量化性能测试
python -m ai_service.benchmarks.vectorization_benchmark

# 搜索性能测试
python -m ai_service.benchmarks.search_benchmark
```

## 📊 监控和日志

### Prometheus指标
- 访问 http://localhost:9090 查看Prometheus
- 关键指标：
  - `ai_service_requests_total`: 请求总数
  - `ai_service_request_duration_seconds`: 请求耗时
  - `ai_service_vectorization_operations_total`: 向量化操作数
  - `ai_service_search_operations_total`: 搜索操作数

### Grafana仪表板
- 访问 http://localhost:3000 (admin/admin)
- 预配置仪表板显示服务性能指标

### 日志查看
```bash
# Docker日志
docker-compose logs -f ai-service

# 本地日志
tail -f logs/ai_service.log
```

## 🔍 故障排除

### 常见问题

1. **Ollama连接失败**
```bash
# 检查Ollama状态
curl http://localhost:11434/api/tags

# 重启Ollama
docker restart ollama
```

2. **数据库连接错误**
```bash
# 检查PostgreSQL状态
docker exec postgres pg_isready -U postgres

# 查看数据库日志
docker logs postgres
```

3. **Redis连接问题**
```bash
# 检查Redis状态
docker exec redis redis-cli ping

# 查看Redis日志
docker logs redis
```

4. **内存不足**
```bash
# 检查系统资源
docker stats

# 调整Docker内存限制
# 在docker-compose.yml中添加:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

### 性能优化

1. **向量化优化**
- 使用批量向量化减少API调用
- 启用缓存避免重复计算
- 选择合适的分块大小

2. **搜索优化**
- 使用适当的搜索类型
- 设置合理的结果限制
- 利用过滤器减少搜索范围

3. **缓存优化**
- 调整缓存TTL
- 监控缓存命中率
- 定期清理过期缓存

## 🚀 部署指南

### 生产环境部署

1. **环境准备**
```bash
# 创建生产环境配置
cp docker-compose.yml docker-compose.prod.yml

# 编辑生产配置
# - 移除端口暴露
# - 添加SSL证书
# - 配置环境变量
# - 设置资源限制
```

2. **SSL配置**
```bash
# 生成SSL证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key -out ssl/certificate.crt

# 或使用Let's Encrypt
certbot certonly --standalone -d your-domain.com
```

3. **启动生产服务**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes部署

```yaml
# k8s/ai-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-service
  template:
    metadata:
      labels:
        app: ai-service
    spec:
      containers:
      - name: ai-service
        image: ai-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-service-secrets
              key: database-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

### 开发规范
- 遵循PEP 8代码风格
- 添加类型注解
- 编写单元测试
- 更新文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

- 📧 邮箱: support@example.com
- 💬 讨论: [GitHub Discussions](https://github.com/your-repo/discussions)
- 🐛 问题: [GitHub Issues](https://github.com/your-repo/issues)

## 🗺️ 路线图

### v1.1 (计划中)
- [ ] 多语言支持
- [ ] 图像向量化
- [ ] 实时搜索
- [ ] 搜索结果排序优化

### v1.2 (计划中)
- [ ] 知识图谱集成
- [ ] 对话式搜索
- [ ] 自动摘要生成
- [ ] 搜索分析仪表板

---

**AI服务** - 让智能搜索触手可及 🚀