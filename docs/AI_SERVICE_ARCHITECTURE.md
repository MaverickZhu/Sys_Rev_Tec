# AI服务模块架构设计

## 概述

本文档详细描述了政府采购项目审查分析系统AI服务模块的架构设计，基于技术调研结果，采用pgvector + Azure OpenAI的技术栈实现智能化功能。

**设计日期**: 2025-07-27  
**架构版本**: v1.0  
**技术栈**: FastAPI + pgvector + Azure OpenAI + Redis

## 1. 整体架构设计

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           前端应用层 (Frontend)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                           API网关层 (API Gateway)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                          业务服务层 (Business Services)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   用户服务   │  │   项目服务   │  │   文档服务   │  │   AI服务     │        │
│  │ User Service │  │Project Svc  │  │Document Svc │  │ AI Service  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                          AI服务层 (AI Service Layer)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 文档处理服务  │  │ 智能搜索服务  │  │ 分析引擎服务  │  │ 知识图谱服务  │        │
│  │ Document    │  │ Search      │  │ Analysis    │  │ Knowledge   │        │
│  │ Processor   │  │ Service     │  │ Engine      │  │ Graph       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                         数据存储层 (Data Storage Layer)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │ pgvector    │  │ Redis       │  │ File        │        │
│  │ (主数据库)   │  │ (向量存储)   │  │ (缓存)      │  │ Storage     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                        外部服务层 (External Services)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 本地Ollama   │  │ Azure       │  │ Azure Doc   │  │ 监控告警     │        │
│  │ Models      │  │ OpenAI      │  │ Intelligence│  │ Services    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 AI服务模块详细架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AI服务模块 (AI Service Module)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                              API接口层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 文档处理API  │  │ 智能搜索API  │  │ 分析引擎API  │  │ 知识图谱API  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                              业务逻辑层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 文档解析器   │  │ 向量搜索器   │  │ 智能分析器   │  │ 图谱构建器   │        │
│  │ Parser      │  │ Vector      │  │ Analyzer    │  │ Graph       │        │
│  │ Engine      │  │ Searcher    │  │ Engine      │  │ Builder     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                              数据访问层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 向量数据库   │  │ 缓存管理器   │  │ 文件管理器   │  │ 外部API     │        │
│  │ Vector DB   │  │ Cache       │  │ File        │  │ Client      │        │
│  │ Access      │  │ Manager     │  │ Manager     │  │ Manager     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 核心组件设计

### 2.1 文档处理服务 (Document Processor)

#### 2.1.1 功能职责
- OCR文本提取和优化
- 文档结构化解析
- 文本分块和预处理
- 向量化处理
- 元数据提取

#### 2.1.2 技术实现

```python
# app/ai/services/document_processor.py
from typing import List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class DocumentChunk:
    """文档分块数据结构"""
    content: str
    chunk_id: str
    document_id: int
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: List[float] = None

class DocumentProcessor:
    """文档处理服务主类"""
    
    def __init__(self, 
                 ocr_client,
                 embedding_client,
                 vector_store,
                 cache_manager):
        self.ocr_client = ocr_client
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.cache_manager = cache_manager
    
    async def process_document(self, 
                             document_path: str, 
                             document_id: int) -> Dict[str, Any]:
        """处理单个文档的完整流程"""
        try:
            # 1. OCR文本提取
            extracted_text = await self._extract_text(document_path)
            
            # 2. 文档结构化解析
            structured_content = await self._parse_structure(extracted_text)
            
            # 3. 智能分块
            chunks = await self._create_chunks(structured_content, document_id)
            
            # 4. 向量化处理
            embeddings = await self._generate_embeddings(chunks)
            
            # 5. 存储向量数据
            await self._store_embeddings(chunks, embeddings)
            
            # 6. 缓存处理结果
            await self._cache_results(document_id, chunks)
            
            return {
                'document_id': document_id,
                'total_chunks': len(chunks),
                'processing_status': 'completed',
                'extracted_text_length': len(extracted_text),
                'metadata': structured_content.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise DocumentProcessingError(f"Failed to process document {document_id}: {e}")
    
    async def _extract_text(self, document_path: str) -> str:
        """使用Azure Document Intelligence提取文本"""
        return await self.ocr_client.extract_text(document_path)
    
    async def _parse_structure(self, text: str) -> Dict[str, Any]:
        """解析文档结构"""
        # 实现文档结构解析逻辑
        pass
    
    async def _create_chunks(self, content: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """智能分块处理"""
        # 实现智能分块逻辑
        pass
    
    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[List[float]]:
        """生成文本向量"""
        texts = [chunk.content for chunk in chunks]
        return await self.embedding_client.embed_documents(texts)
    
    async def _store_embeddings(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """存储向量数据到pgvector"""
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            await self.vector_store.store_chunk(chunk)
```

### 2.2 智能搜索服务 (Search Service)

#### 2.2.1 功能职责
- 语义搜索查询
- 混合搜索(向量+关键词)
- 搜索结果排序和过滤
- 搜索结果聚合

#### 2.2.2 技术实现

```python
# app/ai/services/search_service.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    """搜索结果数据结构"""
    chunk_id: str
    document_id: int
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    highlights: List[str] = None

class SearchService:
    """智能搜索服务"""
    
    def __init__(self, 
                 embedding_client,
                 vector_store,
                 cache_manager):
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.cache_manager = cache_manager
    
    async def semantic_search(self, 
                            query: str, 
                            limit: int = 10,
                            filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """语义搜索"""
        try:
            # 1. 查询向量化
            query_embedding = await self._embed_query(query)
            
            # 2. 向量相似度搜索
            similar_chunks = await self.vector_store.similarity_search(
                query_embedding, 
                limit=limit,
                filters=filters
            )
            
            # 3. 结果后处理
            results = await self._post_process_results(similar_chunks, query)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise SearchError(f"Search failed for query '{query}': {e}")
    
    async def hybrid_search(self, 
                          query: str, 
                          limit: int = 10,
                          semantic_weight: float = 0.7) -> List[SearchResult]:
        """混合搜索(语义+关键词)"""
        # 1. 语义搜索
        semantic_results = await self.semantic_search(query, limit * 2)
        
        # 2. 关键词搜索
        keyword_results = await self._keyword_search(query, limit * 2)
        
        # 3. 结果融合和重排序
        merged_results = await self._merge_and_rerank(
            semantic_results, 
            keyword_results, 
            semantic_weight
        )
        
        return merged_results[:limit]
    
    async def _embed_query(self, query: str) -> List[float]:
        """查询向量化"""
        return await self.embedding_client.embed_query(query)
    
    async def _keyword_search(self, query: str, limit: int) -> List[SearchResult]:
        """关键词搜索"""
        # 实现基于PostgreSQL全文搜索的关键词搜索
        pass
    
    async def _merge_and_rerank(self, 
                              semantic_results: List[SearchResult],
                              keyword_results: List[SearchResult],
                              semantic_weight: float) -> List[SearchResult]:
        """结果融合和重排序"""
        # 实现结果融合算法
        pass
```

### 2.3 分析引擎服务 (Analysis Engine)

#### 2.3.1 功能职责
- 文档内容智能分析
- 风险评估和合规检查
- 关键信息提取
- 分析报告生成

#### 2.3.2 技术实现

```python
# app/ai/services/analysis_engine.py
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class AnalysisType(Enum):
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_CHECK = "compliance_check"
    KEY_EXTRACTION = "key_extraction"
    SUMMARY_GENERATION = "summary_generation"

@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    analysis_id: str
    document_id: int
    analysis_type: AnalysisType
    results: Dict[str, Any]
    confidence_score: float
    created_at: str

class AnalysisEngine:
    """智能分析引擎"""
    
    def __init__(self, 
                 llm_client,
                 search_service,
                 cache_manager):
        self.llm_client = llm_client
        self.search_service = search_service
        self.cache_manager = cache_manager
    
    async def analyze_document(self, 
                             document_id: int, 
                             analysis_types: List[AnalysisType]) -> List[AnalysisResult]:
        """文档智能分析"""
        results = []
        
        for analysis_type in analysis_types:
            try:
                result = await self._perform_analysis(document_id, analysis_type)
                results.append(result)
            except Exception as e:
                logger.error(f"Analysis failed for {analysis_type}: {e}")
        
        return results
    
    async def _perform_analysis(self, 
                              document_id: int, 
                              analysis_type: AnalysisType) -> AnalysisResult:
        """执行具体分析任务"""
        # 根据分析类型调用相应的分析方法
        if analysis_type == AnalysisType.RISK_ASSESSMENT:
            return await self._risk_assessment(document_id)
        elif analysis_type == AnalysisType.COMPLIANCE_CHECK:
            return await self._compliance_check(document_id)
        elif analysis_type == AnalysisType.KEY_EXTRACTION:
            return await self._key_extraction(document_id)
        elif analysis_type == AnalysisType.SUMMARY_GENERATION:
            return await self._summary_generation(document_id)
    
    async def _risk_assessment(self, document_id: int) -> AnalysisResult:
        """风险评估分析"""
        # 实现风险评估逻辑
        pass
    
    async def _compliance_check(self, document_id: int) -> AnalysisResult:
        """合规性检查"""
        # 实现合规性检查逻辑
        pass
```

## 3. 数据模型设计

### 3.1 向量数据表结构

```sql
-- 文档向量表
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_vector vector(1536),
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建向量索引
CREATE INDEX idx_document_embeddings_vector 
ON document_embeddings 
USING hnsw (content_vector vector_cosine_ops);

-- 创建复合索引
CREATE INDEX idx_document_embeddings_doc_id 
ON document_embeddings (document_id);

CREATE INDEX idx_document_embeddings_metadata 
ON document_embeddings USING gin (metadata);

-- 分析结果表
CREATE TABLE ai_analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(255) UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    results JSONB NOT NULL,
    confidence_score FLOAT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 搜索历史表
CREATE TABLE ai_search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query_text TEXT NOT NULL,
    query_vector vector(1536),
    search_type VARCHAR(50),
    results_count INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.3 配置管理

```python
# app/ai/config.py
from pydantic import BaseSettings
from typing import Optional
from enum import Enum

class LLMProvider(Enum):
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    AUTO = "auto"

class AIServiceConfig(BaseSettings):
    """AI服务配置"""
    
    # 模型提供商选择
    primary_llm_provider: LLMProvider = LLMProvider.OLLAMA
    fallback_llm_provider: LLMProvider = LLMProvider.AZURE_OPENAI
    
    # 本地Ollama配置
     ollama_base_url: str = "http://localhost:11434"
     ollama_chat_model: str = "deepseek-r1:8b"
     ollama_embedding_model: str = "bge-m3:latest"
     ollama_chinese_model: str = "deepseek-r1:8b"
     ollama_code_model: str = "deepseek-coder:latest"
     ollama_multimodal_model: str = "qwen2.5vl:7b"
     ollama_reasoning_model: str = "qwq:latest"
     ollama_timeout: int = 60
    
    # Azure OpenAI配置
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_embedding_model: str = "text-embedding-3-small"
    azure_chat_model: str = "gpt-4o-mini"
    
    # pgvector配置
    vector_dimension: int = 1536
    similarity_threshold: float = 0.7
    max_search_results: int = 50
    
    # 文档处理配置
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 100
    
    # 缓存配置
    cache_ttl_seconds: int = 3600
    enable_result_cache: bool = True
    
    # 性能配置
    batch_size: int = 10
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30
    
    # 智能路由配置
    sensitivity_threshold: str = "high"  # high, medium, low
    auto_fallback_enabled: bool = True
    max_retry_attempts: int = 3
    
    # 模型性能配置
    ollama_max_tokens: int = 4096
    azure_max_tokens: int = 8192
    
    class Config:
        env_prefix = "AI_"
        case_sensitive = False

# 混合LLM客户端配置
class HybridLLMConfig:
    """混合LLM服务配置"""
    
    # 敏感度路由规则
    SENSITIVITY_ROUTING = {
        "high": "ollama",      # 高敏感度使用本地模型
        "medium": "auto",     # 中等敏感度自动选择
        "low": "azure_openai" # 低敏感度可使用云端
    }
    
    # 任务类型路由规则
     TASK_ROUTING = {
         "document_analysis": "ollama",      # 使用deepseek-r1:8b
         "code_analysis": "ollama",          # 使用deepseek-coder:latest
         "embedding": "ollama",              # 使用bge-m3:latest
         "chinese_processing": "ollama",     # 使用deepseek-r1:8b
         "multimodal": "ollama",             # 使用qwen2.5vl:7b
         "complex_reasoning": "ollama",      # 使用qwq:latest或deepseek-r1:32b
         "multilingual": "azure_openai"      # 备用云端处理
     }
     
     # 模型选择策略
     MODEL_SELECTION = {
         "document_analysis": "deepseek-r1:8b",
         "code_analysis": "deepseek-coder:latest",
         "embedding": "bge-m3:latest",
         "chinese_processing": "deepseek-r1:8b",
         "multimodal": "qwen2.5vl:7b",
         "complex_reasoning": "qwq:latest",
         "large_context": "deepseek-r1:32b"
     }
```

## 4. API接口设计

### 4.1 文档处理API

```python
# app/ai/routers/document_processing.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import List

router = APIRouter(prefix="/ai/documents", tags=["AI Document Processing"])

@router.post("/process")
async def process_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    force_reprocess: bool = False
):
    """处理文档并生成向量"""
    pass

@router.get("/processing-status/{document_id}")
async def get_processing_status(document_id: int):
    """获取文档处理状态"""
    pass

@router.post("/batch-process")
async def batch_process_documents(
    document_ids: List[int],
    background_tasks: BackgroundTasks
):
    """批量处理文档"""
    pass
```

### 4.2 智能搜索API

```python
# app/ai/routers/search.py
from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter(prefix="/ai/search", tags=["AI Search"])

@router.post("/semantic")
async def semantic_search(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    document_types: Optional[List[str]] = None,
    date_range: Optional[dict] = None
):
    """语义搜索"""
    pass

@router.post("/hybrid")
async def hybrid_search(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0)
):
    """混合搜索"""
    pass

@router.get("/suggestions")
async def get_search_suggestions(query: str):
    """搜索建议"""
    pass
```

### 4.3 智能分析API

```python
# app/ai/routers/analysis.py
from fastapi import APIRouter
from typing import List
from ..services.analysis_engine import AnalysisType

router = APIRouter(prefix="/ai/analysis", tags=["AI Analysis"])

@router.post("/analyze/{document_id}")
async def analyze_document(
    document_id: int,
    analysis_types: List[AnalysisType]
):
    """文档智能分析"""
    pass

@router.get("/results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """获取分析结果"""
    pass

@router.post("/batch-analyze")
async def batch_analyze_documents(
    document_ids: List[int],
    analysis_types: List[AnalysisType]
):
    """批量文档分析"""
    pass
```

## 5. 部署和运维

### 5.1 Docker配置更新

```yaml
# docker-compose.ai.yml
version: '3.8'

services:
  ai-service:
    build:
      context: .
      dockerfile: Dockerfile.ai
    environment:
      - AI_AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AI_AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads
    networks:
      - app-network

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-pgvector.sql:/docker-entrypoint-initdb.d/init-pgvector.sql
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

### 5.2 监控指标

```python
# app/ai/monitoring.py
from prometheus_client import Counter, Histogram, Gauge

# 业务指标
document_processing_total = Counter(
    'ai_document_processing_total',
    'Total number of documents processed',
    ['status']
)

search_requests_total = Counter(
    'ai_search_requests_total',
    'Total number of search requests',
    ['search_type']
)

analysis_requests_total = Counter(
    'ai_analysis_requests_total',
    'Total number of analysis requests',
    ['analysis_type']
)

# 性能指标
processing_duration = Histogram(
    'ai_processing_duration_seconds',
    'Time spent processing documents',
    ['operation_type']
)

search_duration = Histogram(
    'ai_search_duration_seconds',
    'Time spent on search operations',
    ['search_type']
)

# 资源指标
vector_store_size = Gauge(
    'ai_vector_store_size_bytes',
    'Size of vector store in bytes'
)

active_embeddings = Gauge(
    'ai_active_embeddings_total',
    'Total number of active embeddings'
)
```

## 6. 测试策略

### 6.1 单元测试

```python
# tests/ai/test_document_processor.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.ai.services.document_processor import DocumentProcessor

@pytest.fixture
def document_processor():
    ocr_client = AsyncMock()
    embedding_client = AsyncMock()
    vector_store = AsyncMock()
    cache_manager = AsyncMock()
    
    return DocumentProcessor(
        ocr_client=ocr_client,
        embedding_client=embedding_client,
        vector_store=vector_store,
        cache_manager=cache_manager
    )

@pytest.mark.asyncio
async def test_process_document_success(document_processor):
    # 测试文档处理成功场景
    document_processor.ocr_client.extract_text.return_value = "Sample text"
    document_processor.embedding_client.embed_documents.return_value = [[0.1, 0.2, 0.3]]
    
    result = await document_processor.process_document("/path/to/doc.pdf", 1)
    
    assert result['processing_status'] == 'completed'
    assert result['document_id'] == 1
```

### 6.2 集成测试

```python
# tests/ai/test_integration.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_end_to_end_document_processing():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 上传文档
        response = await client.post("/api/documents/upload", files={"file": ("test.pdf", b"test content")})
        document_id = response.json()["id"]
        
        # 2. 处理文档
        response = await client.post(f"/ai/documents/process", json={"document_id": document_id})
        assert response.status_code == 200
        
        # 3. 搜索文档
        response = await client.post("/ai/search/semantic", json={"query": "test query"})
        assert response.status_code == 200
        assert len(response.json()["results"]) > 0
```

## 7. 性能优化

### 7.1 向量搜索优化

- **索引优化**: 调整HNSW参数(m, ef_construction)
- **批量操作**: 批量插入和查询向量
- **缓存策略**: 缓存常用查询结果
- **分页查询**: 实现高效的分页机制

### 7.2 内存管理

- **连接池**: 数据库和Redis连接池优化
- **对象池**: 重用昂贵的对象实例
- **垃圾回收**: 及时清理临时数据

### 7.3 并发控制

- **异步处理**: 使用asyncio提高并发性能
- **限流机制**: 防止API过载
- **队列管理**: 后台任务队列优化

## 8. 安全考虑

### 8.1 数据安全

- **加密存储**: 敏感向量数据加密
- **访问控制**: 基于角色的访问控制
- **审计日志**: 记录所有AI操作

### 8.2 API安全

- **认证授权**: JWT token验证
- **输入验证**: 严格的输入参数验证
- **速率限制**: API调用频率限制

---

**文档版本**: v1.0  
**最后更新**: 2025-07-27  
**下次审核**: 2025-08-10