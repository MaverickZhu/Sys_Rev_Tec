# 向量数据库集成方案设计

## 1. 概述

本文档详细设计了pgvector与现有PostgreSQL数据库的集成方案，实现文档向量化存储和智能搜索功能。

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Vector Service │    │   PostgreSQL    │
│                 │    │                 │    │   + pgvector    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 文档上传      │───▶│ • 文档向量化    │───▶│ • 向量存储      │
│ • 搜索请求      │    │ • 相似度计算    │    │ • 元数据存储    │
│ • 结果展示      │◀───│ • 结果排序      │◀───│ • 索引优化      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │                 │
                       │ • bge-m3:latest │
                       │ • 向量生成      │
                       └─────────────────┘
```

### 2.2 数据库扩展安装

```sql
-- 安装pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证安装
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## 3. 数据模型设计

### 3.1 向量存储表结构

```sql
-- 文档向量表
CREATE TABLE document_vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content_text TEXT NOT NULL,
    content_vector vector(1024),  -- bge-m3模型输出1024维向量
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 复合索引
    UNIQUE(document_id, chunk_index)
);

-- 创建向量相似度索引 (HNSW)
CREATE INDEX idx_document_vectors_hnsw 
ON document_vectors 
USING hnsw (content_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 创建文档ID索引
CREATE INDEX idx_document_vectors_doc_id ON document_vectors(document_id);

-- 创建元数据索引
CREATE INDEX idx_document_vectors_metadata ON document_vectors USING GIN(metadata);
```

### 3.2 搜索历史表

```sql
-- 搜索历史表
CREATE TABLE vector_search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query_text TEXT NOT NULL,
    query_vector vector(1024),
    search_results JSONB,
    search_time_ms INTEGER,
    result_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 搜索历史索引
CREATE INDEX idx_search_history_user ON vector_search_history(user_id);
CREATE INDEX idx_search_history_created ON vector_search_history(created_at);
```

### 3.3 向量索引统计表

```sql
-- 向量索引性能统计
CREATE TABLE vector_index_stats (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100) NOT NULL,
    total_vectors INTEGER,
    index_size_mb DECIMAL(10,2),
    avg_search_time_ms DECIMAL(10,2),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 4. 向量化服务实现

### 4.1 向量化服务类

```python
# app/services/vector_service.py
from typing import List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
import requests
import json
from app.core.config import settings
from app.models.document import DocumentVector
from app.schemas.vector import VectorSearchRequest, VectorSearchResponse

class VectorService:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.chunk_size = 512  # 文档分块大小
        self.chunk_overlap = 50  # 分块重叠
    
    async def generate_embedding(self, text: str) -> List[float]:
        """使用Ollama生成文本向量"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
        except Exception as e:
            raise Exception(f"向量生成失败: {str(e)}")
    
    def chunk_text(self, text: str) -> List[str]:
        """文档分块处理"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    async def vectorize_document(self, db: Session, document_id: int, content: str) -> bool:
        """文档向量化处理"""
        try:
            # 删除已存在的向量
            db.query(DocumentVector).filter(
                DocumentVector.document_id == document_id
            ).delete()
            
            # 文档分块
            chunks = self.chunk_text(content)
            
            # 批量向量化
            for idx, chunk in enumerate(chunks):
                vector = await self.generate_embedding(chunk)
                
                doc_vector = DocumentVector(
                    document_id=document_id,
                    chunk_index=idx,
                    content_text=chunk,
                    content_vector=vector,
                    metadata={
                        "chunk_length": len(chunk),
                        "word_count": len(chunk.split())
                    }
                )
                db.add(doc_vector)
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"文档向量化失败: {str(e)}")
    
    async def search_similar_documents(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[int, str, float]]:
        """向量相似度搜索"""
        try:
            # 生成查询向量
            query_vector = await self.generate_embedding(query)
            
            # 执行相似度搜索
            sql = text("""
                SELECT 
                    dv.document_id,
                    dv.content_text,
                    1 - (dv.content_vector <=> :query_vector) as similarity
                FROM document_vectors dv
                WHERE 1 - (dv.content_vector <=> :query_vector) > :threshold
                ORDER BY dv.content_vector <=> :query_vector
                LIMIT :limit
            """)
            
            result = db.execute(sql, {
                "query_vector": str(query_vector),
                "threshold": similarity_threshold,
                "limit": limit
            })
            
            return [(row.document_id, row.content_text, row.similarity) 
                   for row in result.fetchall()]
            
        except Exception as e:
            raise Exception(f"向量搜索失败: {str(e)}")
```

### 4.2 向量搜索API

```python
# app/api/v1/endpoints/vector_search.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.services.vector_service import VectorService
from app.schemas.vector import VectorSearchRequest, VectorSearchResponse
from app.models.user import User

router = APIRouter()
vector_service = VectorService()

@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """向量相似度搜索"""
    try:
        results = await vector_service.search_similar_documents(
            db=db,
            query=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        return VectorSearchResponse(
            query=request.query,
            results=[
                {
                    "document_id": doc_id,
                    "content": content,
                    "similarity": similarity
                }
                for doc_id, content, similarity in results
            ],
            total_count=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vectorize/{document_id}")
async def vectorize_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """文档向量化"""
    try:
        # 获取文档内容
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 执行向量化
        success = await vector_service.vectorize_document(
            db=db,
            document_id=document_id,
            content=document.content
        )
        
        if success:
            return {"message": "文档向量化成功", "document_id": document_id}
        else:
            raise HTTPException(status_code=500, detail="向量化失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 5. 性能优化策略

### 5.1 索引优化

```sql
-- HNSW索引参数调优
-- m: 每个节点的最大连接数 (16-64)
-- ef_construction: 构建时的搜索范围 (64-200)
CREATE INDEX idx_vectors_hnsw_optimized 
ON document_vectors 
USING hnsw (content_vector vector_cosine_ops)
WITH (m = 32, ef_construction = 128);

-- 设置查询时的ef参数
SET hnsw.ef_search = 100;
```

### 5.2 批量处理优化

```python
class BatchVectorService:
    async def batch_vectorize_documents(
        self, 
        db: Session, 
        document_ids: List[int],
        batch_size: int = 10
    ):
        """批量文档向量化"""
        for i in range(0, len(document_ids), batch_size):
            batch = document_ids[i:i + batch_size]
            
            # 并发处理批次
            tasks = [
                self.vectorize_document(db, doc_id, content)
                for doc_id in batch
            ]
            
            await asyncio.gather(*tasks)
            
            # 批次间延迟，避免过载
            await asyncio.sleep(0.1)
```

### 5.3 缓存策略

```python
# 向量缓存
from app.services.cache_service import CacheService

class CachedVectorService(VectorService):
    def __init__(self):
        super().__init__()
        self.cache = CacheService()
    
    async def generate_embedding(self, text: str) -> List[float]:
        # 检查缓存
        cache_key = f"embedding:{hash(text)}"
        cached_vector = await self.cache.get(cache_key)
        
        if cached_vector:
            return json.loads(cached_vector)
        
        # 生成新向量
        vector = await super().generate_embedding(text)
        
        # 缓存结果
        await self.cache.set(
            cache_key, 
            json.dumps(vector), 
            expire=3600  # 1小时过期
        )
        
        return vector
```

## 6. 监控和维护

### 6.1 性能监控

```sql
-- 向量搜索性能统计
CREATE OR REPLACE FUNCTION update_vector_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO vector_index_stats (
        table_name, 
        index_name, 
        total_vectors,
        index_size_mb
    )
    SELECT 
        'document_vectors',
        'idx_document_vectors_hnsw',
        COUNT(*),
        pg_size_pretty(pg_total_relation_size('document_vectors'))::DECIMAL
    FROM document_vectors
    ON CONFLICT (table_name, index_name) 
    DO UPDATE SET 
        total_vectors = EXCLUDED.total_vectors,
        index_size_mb = EXCLUDED.index_size_mb,
        last_updated = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER vector_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON document_vectors
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_vector_stats();
```

### 6.2 维护脚本

```python
# scripts/vector_maintenance.py
class VectorMaintenance:
    def __init__(self, db: Session):
        self.db = db
    
    def cleanup_orphaned_vectors(self):
        """清理孤立向量"""
        sql = text("""
            DELETE FROM document_vectors 
            WHERE document_id NOT IN (
                SELECT id FROM documents
            )
        """)
        result = self.db.execute(sql)
        return result.rowcount
    
    def reindex_vectors(self):
        """重建向量索引"""
        self.db.execute(text("DROP INDEX IF EXISTS idx_document_vectors_hnsw"))
        self.db.execute(text("""
            CREATE INDEX idx_document_vectors_hnsw 
            ON document_vectors 
            USING hnsw (content_vector vector_cosine_ops)
            WITH (m = 32, ef_construction = 128)
        """))
        self.db.commit()
    
    def analyze_vector_distribution(self):
        """分析向量分布"""
        sql = text("""
            SELECT 
                document_id,
                COUNT(*) as chunk_count,
                AVG(array_length(content_vector, 1)) as avg_dimension
            FROM document_vectors 
            GROUP BY document_id
            ORDER BY chunk_count DESC
            LIMIT 10
        """)
        return self.db.execute(sql).fetchall()
```

## 7. 部署配置

### 7.1 Docker Compose更新

```yaml
# docker-compose.yml 添加pgvector支持
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init-vector.sql:/docker-entrypoint-initdb.d/02-init-vector.sql
    ports:
      - "5432:5432"
```

### 7.2 初始化脚本

```sql
-- docker/postgres/init-vector.sql
-- 安装pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 设置向量相关参数
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';

-- 重启配置
SELECT pg_reload_conf();
```

## 8. 测试策略

### 8.1 单元测试

```python
# tests/test_vector_service.py
import pytest
from app.services.vector_service import VectorService

@pytest.mark.asyncio
async def test_generate_embedding():
    service = VectorService()
    text = "这是一个测试文档"
    vector = await service.generate_embedding(text)
    
    assert isinstance(vector, list)
    assert len(vector) == 1024  # bge-m3维度
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.asyncio
async def test_vector_search():
    # 测试向量搜索功能
    pass
```

### 8.2 性能测试

```python
# tests/test_vector_performance.py
import time
import pytest

@pytest.mark.performance
async def test_search_performance():
    """测试搜索性能"""
    service = VectorService()
    
    start_time = time.time()
    results = await service.search_similar_documents(
        db=test_db,
        query="测试查询",
        limit=100
    )
    end_time = time.time()
    
    search_time = (end_time - start_time) * 1000  # 毫秒
    assert search_time < 500  # 搜索时间应小于500ms
```

## 9. 安全考虑

### 9.1 访问控制

```python
# 向量搜索权限控制
@router.post("/search")
async def vector_search(
    request: VectorSearchRequest,
    current_user: User = Depends(get_current_user)
):
    # 检查用户权限
    if not current_user.has_permission("vector_search"):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 限制搜索范围
    if current_user.role != "admin":
        # 普通用户只能搜索自己的文档
        request.filter_user_id = current_user.id
```

### 9.2 数据脱敏

```python
# 敏感信息过滤
def sanitize_content(content: str) -> str:
    """清理敏感信息"""
    import re
    
    # 移除身份证号
    content = re.sub(r'\d{17}[\dXx]', '[身份证号]', content)
    
    # 移除手机号
    content = re.sub(r'1[3-9]\d{9}', '[手机号]', content)
    
    # 移除邮箱
    content = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[邮箱]', content)
    
    return content
```

## 10. 总结

本向量数据库集成方案提供了：

1. **完整的技术架构**: pgvector + PostgreSQL + Ollama
2. **高性能搜索**: HNSW索引 + 优化配置
3. **灵活的API设计**: RESTful接口 + 异步处理
4. **全面的监控**: 性能统计 + 维护工具
5. **安全保障**: 权限控制 + 数据脱敏

该方案能够支持大规模文档向量化和高效的语义搜索，为AI集成奠定坚实基础。