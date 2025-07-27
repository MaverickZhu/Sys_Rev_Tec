# 智能搜索API接口设计

## 1. 概述

本文档设计了基于向量数据库和大语言模型的智能搜索API接口，提供语义搜索、混合搜索、智能问答等功能。

## 2. API架构设计

### 2.1 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │    │  Search Gateway │    │  Search Engine  │
│                 │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 搜索界面      │───▶│ • 请求路由      │───▶│ • 向量搜索      │
│ • 结果展示      │    │ • 参数验证      │    │ • 关键词搜索    │
│ • 交互反馈      │◀───│ • 结果聚合      │◀───│ • 混合排序      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Cache Layer   │    │   LLM Service   │
                       │                 │    │                 │
                       │ • Redis缓存     │    │ • deepseek-r1   │
                       │ • 结果缓存      │    │ • 智能问答      │
                       └─────────────────┘    └─────────────────┘
```

### 2.2 搜索类型分类

1. **向量语义搜索**: 基于文档内容的语义相似度
2. **关键词搜索**: 传统的全文检索
3. **混合搜索**: 结合向量和关键词的综合搜索
4. **智能问答**: 基于LLM的问答式搜索
5. **多模态搜索**: 支持图文混合搜索

## 3. API接口定义

### 3.1 基础搜索接口

#### 3.1.1 语义搜索

```python
# POST /api/v1/search/semantic
{
    "query": "政府采购相关法规",
    "limit": 20,
    "similarity_threshold": 0.7,
    "filters": {
        "document_type": ["法规", "政策"],
        "date_range": {
            "start": "2023-01-01",
            "end": "2024-12-31"
        },
        "department": ["财政部", "发改委"]
    },
    "highlight": true,
    "include_metadata": true
}
```

**响应格式**:
```python
{
    "success": true,
    "query": "政府采购相关法规",
    "search_type": "semantic",
    "total_count": 156,
    "search_time_ms": 245,
    "results": [
        {
            "document_id": 1001,
            "title": "政府采购法实施条例",
            "content_snippet": "第一条 为了规范政府采购行为...",
            "similarity_score": 0.89,
            "metadata": {
                "document_type": "法规",
                "department": "财政部",
                "publish_date": "2023-03-15",
                "file_size": "2.3MB",
                "page_count": 45
            },
            "highlights": [
                "政府<em>采购</em>行为规范",
                "<em>法规</em>实施细则"
            ],
            "chunk_info": {
                "chunk_index": 2,
                "total_chunks": 15
            }
        }
    ],
    "facets": {
        "document_type": {
            "法规": 89,
            "政策": 67
        },
        "department": {
            "财政部": 123,
            "发改委": 33
        }
    },
    "suggestions": [
        "政府采购法",
        "采购管理办法",
        "招标投标法"
    ]
}
```

#### 3.1.2 关键词搜索

```python
# POST /api/v1/search/keyword
{
    "query": "政府采购 AND 法规",
    "limit": 20,
    "offset": 0,
    "sort_by": "relevance",  # relevance, date, title
    "sort_order": "desc",
    "filters": {
        "document_type": ["法规"],
        "content_length": {
            "min": 1000,
            "max": 50000
        }
    },
    "search_fields": ["title", "content", "summary"],
    "fuzzy_search": true,
    "boost_fields": {
        "title": 2.0,
        "summary": 1.5
    }
}
```

#### 3.1.3 混合搜索

```python
# POST /api/v1/search/hybrid
{
    "query": "如何规范政府采购流程",
    "search_config": {
        "semantic_weight": 0.7,
        "keyword_weight": 0.3,
        "enable_reranking": true,
        "rerank_model": "deepseek-r1:8b"
    },
    "limit": 15,
    "min_score": 0.5,
    "diversify_results": true,
    "filters": {
        "language": "zh",
        "quality_score": {
            "min": 0.8
        }
    }
}
```

### 3.2 智能问答接口

#### 3.2.1 问答搜索

```python
# POST /api/v1/search/qa
{
    "question": "政府采购中如何处理供应商投诉？",
    "context_limit": 5,
    "answer_style": "detailed",  # brief, detailed, step_by_step
    "include_sources": true,
    "language": "zh",
    "domain_context": "government_procurement",
    "conversation_id": "conv_123456",  # 可选，用于多轮对话
    "previous_context": []  # 可选，上下文历史
}
```

**响应格式**:
```python
{
    "success": true,
    "question": "政府采购中如何处理供应商投诉？",
    "answer": {
        "content": "根据《政府采购法》相关规定，供应商投诉处理流程如下：\n\n1. **投诉受理**：供应商应在知道或应当知道其权益受到损害之日起7个工作日内，以书面形式向采购人或采购代理机构提出质疑...\n\n2. **调查处理**：采购人应当在收到质疑后7个工作日内作出答复...\n\n3. **投诉处理**：供应商对质疑答复不满意的，可以在答复期满后15个工作日内向同级财政部门投诉...",
        "confidence_score": 0.92,
        "answer_type": "procedural",
        "key_points": [
            "7个工作日内提出质疑",
            "书面形式提交",
            "15个工作日内可投诉",
            "向同级财政部门投诉"
        ]
    },
    "sources": [
        {
            "document_id": 1001,
            "title": "政府采购法",
            "relevance_score": 0.95,
            "excerpt": "第五十二条 供应商认为采购文件、采购过程和中标、成交结果使自己的权益受到损害的...",
            "page_number": 23,
            "section": "第六章 质疑与投诉"
        },
        {
            "document_id": 1002,
            "title": "政府采购法实施条例",
            "relevance_score": 0.88,
            "excerpt": "第五十四条 采购人、采购代理机构应当在收到质疑后7个工作日内作出答复...",
            "page_number": 31,
            "section": "质疑处理程序"
        }
    ],
    "related_questions": [
        "政府采购质疑的时效性要求是什么？",
        "供应商投诉需要提供哪些材料？",
        "财政部门如何处理政府采购投诉？"
    ],
    "conversation_id": "conv_123456",
    "response_time_ms": 1250
}
```

#### 3.2.2 多轮对话

```python
# POST /api/v1/search/conversation
{
    "conversation_id": "conv_123456",
    "message": "那投诉的具体材料要求是什么？",
    "context_window": 10,  # 保留的对话轮数
    "maintain_context": true
}
```

### 3.3 高级搜索接口

#### 3.3.1 多模态搜索

```python
# POST /api/v1/search/multimodal
{
    "query": {
        "text": "组织架构图",
        "image_url": "https://example.com/org_chart.png",  # 可选
        "image_base64": "data:image/png;base64,..."  # 可选
    },
    "search_modes": ["text_to_text", "image_to_text", "text_to_image"],
    "limit": 10,
    "include_visual_similarity": true
}
```

#### 3.3.2 批量搜索

```python
# POST /api/v1/search/batch
{
    "queries": [
        {
            "id": "query_1",
            "query": "政府采购法规",
            "type": "semantic",
            "limit": 5
        },
        {
            "id": "query_2",
            "query": "招标投标流程",
            "type": "hybrid",
            "limit": 3
        }
    ],
    "parallel_execution": true,
    "timeout_ms": 5000
}
```

### 3.4 搜索管理接口

#### 3.4.1 搜索历史

```python
# GET /api/v1/search/history
{
    "user_id": 123,
    "limit": 50,
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-01-31"
    },
    "search_types": ["semantic", "qa"]
}
```

#### 3.4.2 搜索统计

```python
# GET /api/v1/search/analytics
{
    "metrics": ["query_count", "avg_response_time", "popular_queries"],
    "time_range": "last_7_days",
    "group_by": "search_type"
}
```

## 4. 数据模型设计

### 4.1 搜索请求模型

```python
# app/schemas/search.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    QA = "qa"
    MULTIMODAL = "multimodal"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class AnswerStyle(str, Enum):
    BRIEF = "brief"
    DETAILED = "detailed"
    STEP_BY_STEP = "step_by_step"

class DateRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class NumericRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None

class SearchFilters(BaseModel):
    document_type: Optional[List[str]] = None
    department: Optional[List[str]] = None
    date_range: Optional[DateRange] = None
    content_length: Optional[NumericRange] = None
    language: Optional[str] = None
    quality_score: Optional[NumericRange] = None

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=20, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: Optional[SearchFilters] = None
    highlight: bool = True
    include_metadata: bool = True
    offset: int = Field(default=0, ge=0)

class KeywordSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="relevance")
    sort_order: SortOrder = SortOrder.DESC
    filters: Optional[SearchFilters] = None
    search_fields: List[str] = ["title", "content"]
    fuzzy_search: bool = False
    boost_fields: Optional[Dict[str, float]] = None

class HybridSearchConfig(BaseModel):
    semantic_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    enable_reranking: bool = True
    rerank_model: str = "deepseek-r1:8b"

class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    search_config: HybridSearchConfig = HybridSearchConfig()
    limit: int = Field(default=15, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)
    diversify_results: bool = True
    filters: Optional[SearchFilters] = None

class QASearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context_limit: int = Field(default=5, ge=1, le=10)
    answer_style: AnswerStyle = AnswerStyle.DETAILED
    include_sources: bool = True
    language: str = "zh"
    domain_context: Optional[str] = None
    conversation_id: Optional[str] = None
    previous_context: List[Dict[str, Any]] = []
```

### 4.2 搜索响应模型

```python
class SearchResult(BaseModel):
    document_id: int
    title: str
    content_snippet: str
    similarity_score: Optional[float] = None
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = {}
    highlights: List[str] = []
    chunk_info: Optional[Dict[str, Any]] = None

class SearchFacets(BaseModel):
    document_type: Optional[Dict[str, int]] = None
    department: Optional[Dict[str, int]] = None
    date_distribution: Optional[Dict[str, int]] = None

class SearchResponse(BaseModel):
    success: bool = True
    query: str
    search_type: SearchType
    total_count: int
    search_time_ms: int
    results: List[SearchResult]
    facets: Optional[SearchFacets] = None
    suggestions: List[str] = []
    next_page_token: Optional[str] = None

class QAAnswer(BaseModel):
    content: str
    confidence_score: float
    answer_type: str
    key_points: List[str] = []

class QASource(BaseModel):
    document_id: int
    title: str
    relevance_score: float
    excerpt: str
    page_number: Optional[int] = None
    section: Optional[str] = None

class QAResponse(BaseModel):
    success: bool = True
    question: str
    answer: QAAnswer
    sources: List[QASource]
    related_questions: List[str] = []
    conversation_id: Optional[str] = None
    response_time_ms: int
```

## 5. 服务实现

### 5.1 智能搜索服务

```python
# app/services/intelligent_search_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import asyncio
import time
from app.services.vector_service import VectorService
from app.services.cache_service import CacheService
from app.core.config import settings
import requests
import json

class IntelligentSearchService:
    def __init__(self):
        self.vector_service = VectorService()
        self.cache_service = CacheService()
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.chat_model = settings.OLLAMA_CHAT_MODEL
    
    async def semantic_search(
        self, 
        db: Session, 
        request: SemanticSearchRequest
    ) -> SearchResponse:
        """语义搜索"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = f"semantic:{hash(str(request.dict()))}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return SearchResponse.parse_raw(cached_result)
            
            # 执行向量搜索
            results = await self.vector_service.search_similar_documents(
                db=db,
                query=request.query,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold
            )
            
            # 应用过滤器
            if request.filters:
                results = await self._apply_filters(db, results, request.filters)
            
            # 生成高亮和摘要
            search_results = []
            for doc_id, content, similarity in results:
                highlights = self._generate_highlights(content, request.query) if request.highlight else []
                
                search_results.append(SearchResult(
                    document_id=doc_id,
                    title=await self._get_document_title(db, doc_id),
                    content_snippet=content[:300] + "..." if len(content) > 300 else content,
                    similarity_score=similarity,
                    highlights=highlights,
                    metadata=await self._get_document_metadata(db, doc_id) if request.include_metadata else {}
                ))
            
            # 生成搜索建议
            suggestions = await self._generate_suggestions(request.query)
            
            # 构建响应
            response = SearchResponse(
                query=request.query,
                search_type=SearchType.SEMANTIC,
                total_count=len(search_results),
                search_time_ms=int((time.time() - start_time) * 1000),
                results=search_results,
                suggestions=suggestions
            )
            
            # 缓存结果
            await self.cache_service.set(
                cache_key, 
                response.json(), 
                expire=300  # 5分钟缓存
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"语义搜索失败: {str(e)}")
    
    async def hybrid_search(
        self, 
        db: Session, 
        request: HybridSearchRequest
    ) -> SearchResponse:
        """混合搜索"""
        start_time = time.time()
        
        try:
            # 并行执行语义搜索和关键词搜索
            semantic_task = self._semantic_search_internal(db, request)
            keyword_task = self._keyword_search_internal(db, request)
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task
            )
            
            # 结果融合和重排序
            merged_results = await self._merge_and_rerank(
                semantic_results, 
                keyword_results, 
                request.search_config
            )
            
            # 结果多样化
            if request.diversify_results:
                merged_results = await self._diversify_results(merged_results)
            
            # 过滤低分结果
            filtered_results = [
                result for result in merged_results 
                if result.relevance_score >= request.min_score
            ]
            
            response = SearchResponse(
                query=request.query,
                search_type=SearchType.HYBRID,
                total_count=len(filtered_results),
                search_time_ms=int((time.time() - start_time) * 1000),
                results=filtered_results[:request.limit]
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"混合搜索失败: {str(e)}")
    
    async def qa_search(
        self, 
        db: Session, 
        request: QASearchRequest
    ) -> QAResponse:
        """问答搜索"""
        start_time = time.time()
        
        try:
            # 1. 检索相关文档
            relevant_docs = await self.vector_service.search_similar_documents(
                db=db,
                query=request.question,
                limit=request.context_limit,
                similarity_threshold=0.6
            )
            
            # 2. 构建上下文
            context = await self._build_qa_context(db, relevant_docs, request)
            
            # 3. 生成答案
            answer = await self._generate_answer(
                question=request.question,
                context=context,
                style=request.answer_style,
                language=request.language
            )
            
            # 4. 构建源文档信息
            sources = []
            if request.include_sources:
                for doc_id, content, similarity in relevant_docs:
                    sources.append(QASource(
                        document_id=doc_id,
                        title=await self._get_document_title(db, doc_id),
                        relevance_score=similarity,
                        excerpt=content[:200] + "..." if len(content) > 200 else content
                    ))
            
            # 5. 生成相关问题
            related_questions = await self._generate_related_questions(
                request.question, context
            )
            
            response = QAResponse(
                question=request.question,
                answer=answer,
                sources=sources,
                related_questions=related_questions,
                conversation_id=request.conversation_id,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"问答搜索失败: {str(e)}")
    
    async def _generate_answer(
        self, 
        question: str, 
        context: str, 
        style: AnswerStyle,
        language: str
    ) -> QAAnswer:
        """使用LLM生成答案"""
        try:
            # 构建提示词
            prompt = self._build_qa_prompt(question, context, style, language)
            
            # 调用Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.chat_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 1000
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            answer_content = result["response"]
            
            # 提取关键点
            key_points = self._extract_key_points(answer_content)
            
            # 计算置信度
            confidence_score = self._calculate_confidence(answer_content, context)
            
            return QAAnswer(
                content=answer_content,
                confidence_score=confidence_score,
                answer_type="informational",
                key_points=key_points
            )
            
        except Exception as e:
            raise Exception(f"答案生成失败: {str(e)}")
    
    def _build_qa_prompt(
        self, 
        question: str, 
        context: str, 
        style: AnswerStyle,
        language: str
    ) -> str:
        """构建问答提示词"""
        style_instructions = {
            AnswerStyle.BRIEF: "请提供简洁明了的答案，控制在100字以内。",
            AnswerStyle.DETAILED: "请提供详细全面的答案，包含相关背景和具体说明。",
            AnswerStyle.STEP_BY_STEP: "请按步骤详细说明，使用编号列表格式。"
        }
        
        prompt = f"""
你是一个专业的政府文档分析助手。请基于以下上下文信息回答用户问题。

上下文信息：
{context}

用户问题：{question}

回答要求：
1. {style_instructions.get(style, style_instructions[AnswerStyle.DETAILED])}
2. 答案必须基于提供的上下文信息
3. 如果上下文信息不足以回答问题，请明确说明
4. 使用{language}语言回答
5. 保持客观、准确、专业的语调

请提供答案：
"""
        
        return prompt
    
    async def _apply_filters(
        self, 
        db: Session, 
        results: List[Tuple[int, str, float]], 
        filters: SearchFilters
    ) -> List[Tuple[int, str, float]]:
        """应用搜索过滤器"""
        if not filters:
            return results
        
        # 构建过滤条件
        filter_conditions = []
        
        if filters.document_type:
            filter_conditions.append(
                text("documents.document_type = ANY(:doc_types)")
            )
        
        if filters.department:
            filter_conditions.append(
                text("documents.department = ANY(:departments)")
            )
        
        if filters.date_range:
            if filters.date_range.start:
                filter_conditions.append(
                    text("documents.created_at >= :start_date")
                )
            if filters.date_range.end:
                filter_conditions.append(
                    text("documents.created_at <= :end_date")
                )
        
        # 执行过滤查询
        if filter_conditions:
            doc_ids = [result[0] for result in results]
            
            query = text(f"""
                SELECT id FROM documents 
                WHERE id = ANY(:doc_ids) 
                AND {' AND '.join([str(cond) for cond in filter_conditions])}
            """)
            
            params = {
                "doc_ids": doc_ids,
                "doc_types": filters.document_type,
                "departments": filters.department,
                "start_date": filters.date_range.start if filters.date_range else None,
                "end_date": filters.date_range.end if filters.date_range else None
            }
            
            filtered_ids = set(
                row[0] for row in db.execute(query, params).fetchall()
            )
            
            # 过滤结果
            results = [
                result for result in results 
                if result[0] in filtered_ids
            ]
        
        return results
    
    def _generate_highlights(self, content: str, query: str) -> List[str]:
        """生成搜索高亮"""
        import re
        
        highlights = []
        query_terms = query.split()
        
        for term in query_terms:
            pattern = re.compile(f'(.{{0,20}}){re.escape(term)}(.{{0,20}})', re.IGNORECASE)
            matches = pattern.findall(content)
            
            for before, after in matches[:3]:  # 最多3个高亮
                highlight = f"{before}<em>{term}</em>{after}"
                highlights.append(highlight)
        
        return highlights
    
    async def _get_document_title(self, db: Session, doc_id: int) -> str:
        """获取文档标题"""
        result = db.execute(
            text("SELECT title FROM documents WHERE id = :doc_id"),
            {"doc_id": doc_id}
        ).fetchone()
        
        return result[0] if result else f"文档 {doc_id}"
    
    async def _get_document_metadata(self, db: Session, doc_id: int) -> Dict[str, Any]:
        """获取文档元数据"""
        result = db.execute(
            text("""
                SELECT document_type, department, created_at, file_size 
                FROM documents WHERE id = :doc_id
            """),
            {"doc_id": doc_id}
        ).fetchone()
        
        if result:
            return {
                "document_type": result[0],
                "department": result[1],
                "created_at": result[2].isoformat() if result[2] else None,
                "file_size": result[3]
            }
        
        return {}
```

## 6. API路由实现

### 6.1 搜索路由

```python
# app/api/v1/endpoints/intelligent_search.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.services.intelligent_search_service import IntelligentSearchService
from app.schemas.search import *
from app.models.user import User
from app.core.logging import logger

router = APIRouter()
search_service = IntelligentSearchService()

@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """语义搜索"""
    try:
        # 记录搜索日志
        background_tasks.add_task(
            log_search_activity,
            user_id=current_user.id,
            search_type="semantic",
            query=request.query
        )
        
        result = await search_service.semantic_search(db, request)
        return result
        
    except Exception as e:
        logger.error(f"语义搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """混合搜索"""
    try:
        background_tasks.add_task(
            log_search_activity,
            user_id=current_user.id,
            search_type="hybrid",
            query=request.query
        )
        
        result = await search_service.hybrid_search(db, request)
        return result
        
    except Exception as e:
        logger.error(f"混合搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/qa", response_model=QAResponse)
async def qa_search(
    request: QASearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """问答搜索"""
    try:
        background_tasks.add_task(
            log_search_activity,
            user_id=current_user.id,
            search_type="qa",
            query=request.question
        )
        
        result = await search_service.qa_search(db, request)
        return result
        
    except Exception as e:
        logger.error(f"问答搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_search_suggestions(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """获取搜索建议"""
    try:
        suggestions = await search_service.get_search_suggestions(db, query, limit)
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def log_search_activity(
    user_id: int, 
    search_type: str, 
    query: str
):
    """记录搜索活动"""
    try:
        # 记录到数据库或日志系统
        logger.info(f"搜索活动: 用户{user_id}, 类型{search_type}, 查询'{query}'")
    except Exception as e:
        logger.error(f"记录搜索活动失败: {str(e)}")
```

## 7. 性能优化

### 7.1 缓存策略

```python
# 多层缓存策略
class SearchCacheManager:
    def __init__(self):
        self.redis_cache = CacheService()  # Redis缓存
        self.memory_cache = {}  # 内存缓存
        self.cache_ttl = {
            "semantic": 300,    # 5分钟
            "keyword": 600,     # 10分钟
            "qa": 1800,         # 30分钟
            "suggestions": 3600  # 1小时
        }
    
    async def get_cached_result(self, cache_key: str, search_type: str):
        # 1. 检查内存缓存
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # 2. 检查Redis缓存
        cached_result = await self.redis_cache.get(cache_key)
        if cached_result:
            # 回填内存缓存
            self.memory_cache[cache_key] = cached_result
            return cached_result
        
        return None
    
    async def cache_result(self, cache_key: str, result: Any, search_type: str):
        ttl = self.cache_ttl.get(search_type, 300)
        
        # 缓存到Redis
        await self.redis_cache.set(cache_key, result, expire=ttl)
        
        # 缓存到内存（限制大小）
        if len(self.memory_cache) < 1000:
            self.memory_cache[cache_key] = result
```

### 7.2 并发优化

```python
# 并发搜索处理
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ConcurrentSearchService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.semaphore = asyncio.Semaphore(50)  # 限制并发数
    
    async def batch_search(self, requests: List[SearchRequest]):
        async with self.semaphore:
            tasks = [
                self._process_single_search(req) 
                for req in requests
            ]
            
            results = await asyncio.gather(
                *tasks, 
                return_exceptions=True
            )
            
            return results
    
    async def _process_single_search(self, request: SearchRequest):
        try:
            # 异步处理单个搜索请求
            return await self.search_service.process_search(request)
        except Exception as e:
            return {"error": str(e), "request_id": request.id}
```

## 8. 监控和分析

### 8.1 搜索指标

```python
# 搜索性能指标收集
class SearchMetrics:
    def __init__(self):
        self.metrics = {
            "total_searches": 0,
            "avg_response_time": 0,
            "search_types": {},
            "popular_queries": {},
            "error_rate": 0
        }
    
    def record_search(
        self, 
        search_type: str, 
        query: str, 
        response_time: float,
        success: bool
    ):
        self.metrics["total_searches"] += 1
        
        # 更新平均响应时间
        current_avg = self.metrics["avg_response_time"]
        total = self.metrics["total_searches"]
        self.metrics["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
        
        # 记录搜索类型分布
        if search_type not in self.metrics["search_types"]:
            self.metrics["search_types"][search_type] = 0
        self.metrics["search_types"][search_type] += 1
        
        # 记录热门查询
        if query not in self.metrics["popular_queries"]:
            self.metrics["popular_queries"][query] = 0
        self.metrics["popular_queries"][query] += 1
        
        # 更新错误率
        if not success:
            error_count = self.metrics.get("error_count", 0) + 1
            self.metrics["error_count"] = error_count
            self.metrics["error_rate"] = error_count / total
```

## 9. 安全和权限

### 9.1 搜索权限控制

```python
# 搜索权限验证
class SearchPermissionService:
    def __init__(self):
        self.permission_cache = {}
    
    async def check_search_permission(
        self, 
        user: User, 
        search_type: str,
        filters: Optional[SearchFilters] = None
    ) -> bool:
        # 检查基础搜索权限
        if not user.has_permission(f"search_{search_type}"):
            return False
        
        # 检查部门访问权限
        if filters and filters.department:
            user_departments = user.accessible_departments
            requested_departments = set(filters.department)
            
            if not requested_departments.issubset(user_departments):
                return False
        
        return True
    
    def filter_results_by_permission(
        self, 
        user: User, 
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """根据用户权限过滤搜索结果"""
        filtered_results = []
        
        for result in results:
            if self._can_access_document(user, result.document_id):
                filtered_results.append(result)
        
        return filtered_results
    
    def _can_access_document(self, user: User, document_id: int) -> bool:
        # 实现文档访问权限检查逻辑
        return True  # 简化实现
```

## 10. 总结

本智能搜索API设计提供了：

1. **多种搜索模式**: 语义搜索、关键词搜索、混合搜索、智能问答
2. **高性能架构**: 并发处理、多层缓存、异步操作
3. **灵活的过滤**: 多维度过滤器、权限控制
4. **智能功能**: 自动建议、结果重排序、多轮对话
5. **完善的监控**: 性能指标、搜索分析、错误追踪

该API设计能够满足政府文档系统的复杂搜索需求，提供准确、快速、安全的智能搜索服务。