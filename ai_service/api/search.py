"""
AI服务搜索API路由
提供智能搜索、语义搜索、问答等功能的REST API接口
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ai_service.search import (
    RerankMethod,
    SearchFilter,
    SearchType,
    get_search_service,
)
from ai_service.search import SearchResponse as ServiceSearchResponse
from ai_service.search import SearchResult as ServiceSearchResult
from ai_service.utils.logging import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("api.search")

# 创建路由器
router = APIRouter(prefix="/search", tags=["search"])


# 请求模型
class SearchRequest(BaseModel):
    """搜索请求"""

    query: str = Field(..., description="搜索查询", min_length=1, max_length=1000)
    search_type: SearchType = Field(default=SearchType.HYBRID, description="搜索类型")
    max_results: int = Field(default=10, description="最大结果数", ge=1, le=100)
    similarity_threshold: float = Field(
        default=0.5, description="相似度阈值", ge=0.0, le=1.0
    )
    rerank_method: RerankMethod = Field(
        default=RerankMethod.SIMILARITY, description="重排序方法"
    )
    enable_highlights: bool = Field(default=True, description="是否启用高亮")
    enable_explanations: bool = Field(default=False, description="是否启用解释")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    # 过滤器
    document_types: Optional[List[str]] = Field(
        default=None, description="文档类型过滤"
    )
    date_range: Optional[Tuple[str, str]] = Field(
        default=None, description="日期范围过滤 (start_date, end_date)"
    )
    metadata_filters: Optional[Dict[str, Any]] = Field(
        default=None, description="元数据过滤器"
    )
    min_score: Optional[float] = Field(
        default=None, description="最小分数过滤", ge=0.0, le=1.0
    )
    # 搜索配置
    vector_weight: float = Field(
        default=0.7, description="向量搜索权重（混合搜索）", ge=0.0, le=1.0
    )
    text_weight: float = Field(
        default=0.3, description="文本搜索权重（混合搜索）", ge=0.0, le=1.0
    )

    @validator("vector_weight", "text_weight")
    def validate_weights(cls, v, values):
        if "vector_weight" in values and "text_weight" in values:
            if abs(values["vector_weight"] + values["text_weight"] - 1.0) > 0.01:
                raise ValueError("向量权重和文本权重之和必须等于1.0")
        return v


class QuickSearchRequest(BaseModel):
    """快速搜索请求"""

    query: str = Field(..., description="搜索查询", min_length=1, max_length=500)
    limit: int = Field(default=5, description="结果限制", ge=1, le=20)
    search_type: SearchType = Field(default=SearchType.VECTOR, description="搜索类型")


class SuggestionsRequest(BaseModel):
    """搜索建议请求"""

    partial_query: str = Field(
        ..., description="部分查询", min_length=1, max_length=100
    )
    limit: int = Field(default=5, description="建议数量", ge=1, le=10)


# 响应模型
class SearchResult(BaseModel):
    """搜索结果项"""

    document_id: str = Field(..., description="文档ID")
    chunk_id: int = Field(..., description="分块ID")
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相关性分数")
    metadata: Dict[str, Any] = Field(..., description="元数据")
    highlights: Optional[List[str]] = Field(default=None, description="高亮片段")
    explanation: Optional[str] = Field(default=None, description="相关性解释")


class SearchResponse(BaseModel):
    """搜索响应"""

    query: str = Field(..., description="搜索查询")
    search_type: str = Field(..., description="搜索类型")
    results: List[SearchResult] = Field(..., description="搜索结果")
    total_results: int = Field(..., description="结果总数")
    processing_time: float = Field(..., description="处理时间（秒）")
    metadata: Dict[str, Any] = Field(..., description="搜索元数据")
    suggestions: Optional[List[str]] = Field(default=None, description="搜索建议")
    answer: Optional[str] = Field(default=None, description="生成的答案（问答搜索）")


class QuickSearchResponse(BaseModel):
    """快速搜索响应"""

    query: str = Field(..., description="搜索查询")
    results: List[SearchResult] = Field(..., description="搜索结果")
    processing_time: float = Field(..., description="处理时间（秒）")


class SuggestionsResponse(BaseModel):
    """搜索建议响应"""

    partial_query: str = Field(..., description="部分查询")
    suggestions: List[str] = Field(..., description="搜索建议")
    processing_time: float = Field(..., description="处理时间（秒）")


class SearchStatsResponse(BaseModel):
    """搜索统计响应"""

    total_searches: int = Field(..., description="总搜索次数")
    cache_hits: int = Field(..., description="缓存命中次数")
    cache_misses: int = Field(..., description="缓存未命中次数")
    cache_hit_rate: float = Field(..., description="缓存命中率")
    total_processing_time: float = Field(..., description="总处理时间")
    average_processing_time: float = Field(..., description="平均处理时间")
    search_type_stats: Dict[str, Dict[str, Any]] = Field(
        ..., description="搜索类型统计"
    )
    service_status: Dict[str, Any] = Field(..., description="服务状态")


# 辅助函数
def _convert_service_result_to_api(service_result: ServiceSearchResult) -> SearchResult:
    """转换服务层搜索结果到API响应格式"""
    return SearchResult(
        document_id=service_result.document_id,
        chunk_id=service_result.chunk_id,
        content=service_result.content,
        score=service_result.score,
        metadata=service_result.metadata,
        highlights=service_result.highlights,
        explanation=service_result.explanation,
    )


def _convert_service_response_to_api(
    service_response: ServiceSearchResponse,
) -> SearchResponse:
    """转换服务层搜索响应到API响应格式"""
    return SearchResponse(
        query=service_response.query,
        search_type=service_response.search_type,
        results=[
            _convert_service_result_to_api(result)
            for result in service_response.results
        ],
        total_results=service_response.total_results,
        processing_time=service_response.processing_time,
        metadata=service_response.metadata,
        suggestions=service_response.suggestions,
        answer=service_response.answer,
    )


# API端点
@router.post(
    "/",
    response_model=SearchResponse,
    summary="智能搜索",
    description="执行智能搜索，支持向量搜索、文本搜索、混合搜索、语义搜索和问答搜索",
)
async def search(request: SearchRequest, search_service=Depends(get_search_service)):
    """智能搜索"""
    start_time = time.time()

    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/search",
            method="POST",
            request_data={
                "query_length": len(request.query),
                "search_type": request.search_type.value,
                "max_results": request.max_results,
                "rerank_method": request.rerank_method.value,
                "use_cache": request.use_cache,
            },
        )

        # 构建搜索过滤器
        filters = None
        if any(
            [
                request.document_types,
                request.date_range,
                request.metadata_filters,
                request.min_score,
            ]
        ):
            filters = SearchFilter(
                document_types=request.document_types,
                date_range=request.date_range,
                metadata_filters=request.metadata_filters,
                min_score=request.min_score,
                max_results=request.max_results,
            )

        # 执行搜索
        service_response = await search_service.search(
            query=request.query,
            search_type=request.search_type,
            filters=filters,
            rerank_method=request.rerank_method,
            use_cache=request.use_cache,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold,
            enable_highlights=request.enable_highlights,
            enable_explanations=request.enable_explanations,
            vector_weight=request.vector_weight,
            text_weight=request.text_weight,
        )

        # 转换响应格式
        api_response = _convert_service_response_to_api(service_response)

        processing_time = time.time() - start_time

        # 记录搜索日志
        structured_logger.log_search(
            query=request.query,
            search_type=request.search_type.value,
            result_count=len(api_response.results),
            processing_time=processing_time,
            cache_hit=api_response.metadata.get("cache_hit", False),
            extra_data={
                "rerank_method": request.rerank_method.value,
                "filters_applied": filters is not None,
            },
        )

        return api_response

    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            error_type="search_error",
            error_message=str(e),
            context={
                "query": request.query,
                "search_type": request.search_type.value,
                "processing_time": processing_time,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}",
        )


@router.get(
    "/quick",
    response_model=QuickSearchResponse,
    summary="快速搜索",
    description="执行快速搜索，返回少量结果",
)
async def quick_search(
    q: str = Query(..., description="搜索查询", min_length=1, max_length=500),
    limit: int = Query(default=5, description="结果限制", ge=1, le=20),
    search_type: SearchType = Query(default=SearchType.VECTOR, description="搜索类型"),
    search_service=Depends(get_search_service),
):
    """快速搜索"""
    start_time = time.time()

    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/search/quick",
            method="GET",
            request_data={"query": q, "limit": limit, "search_type": search_type.value},
        )

        # 执行快速搜索
        service_response = await search_service.search(
            query=q,
            search_type=search_type,
            filters=None,
            rerank_method=RerankMethod.NONE,
            use_cache=True,
            max_results=limit,
            enable_highlights=False,
            enable_explanations=False,
        )

        processing_time = time.time() - start_time

        # 构建响应
        response = QuickSearchResponse(
            query=q,
            results=[
                _convert_service_result_to_api(result)
                for result in service_response.results
            ],
            processing_time=processing_time,
        )

        # 记录搜索日志
        structured_logger.log_search(
            query=q,
            search_type=search_type.value,
            result_count=len(response.results),
            processing_time=processing_time,
            cache_hit=service_response.metadata.get("cache_hit", False),
            extra_data={"quick_search": True},
        )

        return response

    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            error_type="quick_search_error",
            error_message=str(e),
            context={
                "query": q,
                "search_type": search_type.value,
                "processing_time": processing_time,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速搜索失败: {str(e)}",
        )


@router.post(
    "/vector",
    response_model=SearchResponse,
    summary="向量搜索",
    description="执行纯向量搜索",
)
async def vector_search(
    request: QuickSearchRequest, search_service=Depends(get_search_service)
):
    """向量搜索"""
    try:
        # 强制使用向量搜索
        service_response = await search_service.search(
            query=request.query,
            search_type=SearchType.VECTOR,
            filters=None,
            rerank_method=RerankMethod.SIMILARITY,
            use_cache=True,
            max_results=request.limit,
        )

        return _convert_service_response_to_api(service_response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"向量搜索失败: {str(e)}",
        )


@router.post(
    "/semantic",
    response_model=SearchResponse,
    summary="语义搜索",
    description="执行语义搜索，使用LLM进行语义理解",
)
async def semantic_search(
    request: QuickSearchRequest, search_service=Depends(get_search_service)
):
    """语义搜索"""
    try:
        # 强制使用语义搜索
        service_response = await search_service.search(
            query=request.query,
            search_type=SearchType.SEMANTIC,
            filters=None,
            rerank_method=RerankMethod.LLM_RERANK,
            use_cache=True,
            max_results=request.limit,
            enable_explanations=True,
        )

        return _convert_service_response_to_api(service_response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语义搜索失败: {str(e)}",
        )


@router.post(
    "/qa",
    response_model=SearchResponse,
    summary="问答搜索",
    description="执行问答搜索，生成基于文档的答案",
)
async def question_answer_search(
    request: QuickSearchRequest, search_service=Depends(get_search_service)
):
    """问答搜索"""
    try:
        # 强制使用问答搜索
        service_response = await search_service.search(
            query=request.query,
            search_type=SearchType.QUESTION_ANSWER,
            filters=None,
            rerank_method=RerankMethod.RELEVANCE,
            use_cache=True,
            max_results=request.limit,
            enable_highlights=True,
            enable_explanations=True,
        )

        return _convert_service_response_to_api(service_response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"问答搜索失败: {str(e)}",
        )


@router.get(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="获取搜索建议",
    description="根据部分查询获取搜索建议",
)
async def get_search_suggestions(
    q: str = Query(..., description="部分查询", min_length=1, max_length=100),
    limit: int = Query(default=5, description="建议数量", ge=1, le=10),
    search_service=Depends(get_search_service),
):
    """获取搜索建议"""
    start_time = time.time()

    try:
        # 获取搜索建议
        suggestions = await search_service.get_search_suggestions(q, limit)

        processing_time = time.time() - start_time

        return SuggestionsResponse(
            partial_query=q, suggestions=suggestions, processing_time=processing_time
        )

    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            error_type="suggestions_error",
            error_message=str(e),
            context={"partial_query": q, "processing_time": processing_time},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索建议获取失败: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=SearchStatsResponse,
    summary="获取搜索统计",
    description="获取搜索服务的统计信息",
)
async def get_search_stats(search_service=Depends(get_search_service)):
    """获取搜索统计"""
    try:
        stats = await search_service.get_service_stats()

        search_stats = stats.get("search_stats", {})
        total_searches = search_stats.get("total_searches", 0)
        cache_hits = search_stats.get("cache_hits", 0)
        cache_misses = search_stats.get("cache_misses", 0)

        # 计算缓存命中率
        cache_hit_rate = 0.0
        if total_searches > 0:
            cache_hit_rate = (
                cache_hits / (cache_hits + cache_misses)
                if (cache_hits + cache_misses) > 0
                else 0.0
            )

        return SearchStatsResponse(
            total_searches=total_searches,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hit_rate,
            total_processing_time=search_stats.get("total_processing_time", 0.0),
            average_processing_time=search_stats.get("average_processing_time", 0.0),
            search_type_stats=search_stats.get("search_type_stats", {}),
            service_status=stats.get("service_status", {}),
        )

    except Exception as e:
        structured_logger.log_error(
            error_type="search_stats_error",
            error_message=str(e),
            context={"endpoint": "/search/stats"},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索统计获取失败: {str(e)}",
        )


@router.get("/health", summary="搜索服务健康检查", description="检查搜索服务的健康状态")
async def health_check(search_service=Depends(get_search_service)):
    """搜索服务健康检查"""
    try:
        health_status = await search_service.health_check()

        if health_status["status"] == "healthy":
            return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e), "timestamp": time.time()},
        )


# 高级搜索端点
@router.post(
    "/advanced",
    response_model=SearchResponse,
    summary="高级搜索",
    description="执行高级搜索，支持复杂过滤和配置",
)
async def advanced_search(
    query: str = Query(..., description="搜索查询"),
    search_type: SearchType = Query(default=SearchType.HYBRID, description="搜索类型"),
    max_results: int = Query(default=20, ge=1, le=100, description="最大结果数"),
    similarity_threshold: float = Query(
        default=0.5, ge=0.0, le=1.0, description="相似度阈值"
    ),
    rerank_method: RerankMethod = Query(
        default=RerankMethod.RELEVANCE, description="重排序方法"
    ),
    document_types: Optional[str] = Query(
        default=None, description="文档类型过滤（逗号分隔）"
    ),
    date_from: Optional[str] = Query(default=None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="结束日期 (YYYY-MM-DD)"),
    min_score: Optional[float] = Query(
        default=None, ge=0.0, le=1.0, description="最小分数"
    ),
    enable_highlights: bool = Query(default=True, description="启用高亮"),
    enable_explanations: bool = Query(default=True, description="启用解释"),
    use_cache: bool = Query(default=True, description="使用缓存"),
    search_service=Depends(get_search_service),
):
    """高级搜索"""
    try:
        # 构建过滤器
        filters = SearchFilter()

        if document_types:
            filters.document_types = [
                t.strip() for t in document_types.split(",") if t.strip()
            ]

        if date_from and date_to:
            filters.date_range = (date_from, date_to)

        if min_score is not None:
            filters.min_score = min_score

        filters.max_results = max_results

        # 执行搜索
        service_response = await search_service.search(
            query=query,
            search_type=search_type,
            filters=filters,
            rerank_method=rerank_method,
            use_cache=use_cache,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            enable_highlights=enable_highlights,
            enable_explanations=enable_explanations,
        )

        return _convert_service_response_to_api(service_response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"高级搜索失败: {str(e)}",
        )


# 搜索历史端点
@router.get("/history", summary="获取搜索历史", description="获取最近的搜索历史记录")
async def get_search_history(
    limit: int = Query(default=10, ge=1, le=50, description="历史记录数量"),
    search_type: Optional[SearchType] = Query(default=None, description="搜索类型过滤"),
):
    """获取搜索历史"""
    try:
        # 这里可以从数据库或缓存中获取搜索历史
        # 简化版：返回空列表
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "history": [],
                "total": 0,
                "limit": limit,
                "message": "搜索历史功能待实现",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索历史获取失败: {str(e)}",
        )


# 热门搜索端点
@router.get("/trending", summary="获取热门搜索", description="获取热门搜索查询")
async def get_trending_searches(
    limit: int = Query(default=10, ge=1, le=20, description="热门搜索数量"),
    time_range: str = Query(default="24h", description="时间范围 (1h, 24h, 7d, 30d)"),
):
    """获取热门搜索"""
    try:
        # 这里可以从统计数据中获取热门搜索
        # 简化版：返回示例数据
        trending_searches = [
            {"query": "人工智能", "count": 156, "trend": "up"},
            {"query": "机器学习", "count": 134, "trend": "up"},
            {"query": "深度学习", "count": 98, "trend": "stable"},
            {"query": "自然语言处理", "count": 87, "trend": "up"},
            {"query": "计算机视觉", "count": 76, "trend": "down"},
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "trending": trending_searches[:limit],
                "time_range": time_range,
                "generated_at": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"热门搜索获取失败: {str(e)}",
        )
