from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== 向量化相关Schema ====================


class VectorizeRequest(BaseModel):
    """向量化请求"""

    document_id: int = Field(..., description="文档ID")
    force_reprocess: bool = Field(default=False, description="是否强制重新处理")
    chunk_strategy: str = Field(default="semantic", description="分块策略")
    chunk_size: int = Field(default=1000, description="分块大小")
    chunk_overlap: int = Field(default=200, description="分块重叠")
    vector_model: str = Field(
        default="text-embedding-ada-002", description="向量化模型"
    )


class VectorizeResponse(BaseModel):
    """向量化响应"""

    document_id: int = Field(..., description="文档ID")
    status: str = Field(..., description="处理状态")
    chunk_count: int = Field(..., description="分块数量")
    vector_dimension: int = Field(..., description="向量维度")
    processing_time: float = Field(..., description="处理时间(秒)")
    message: str = Field(..., description="处理消息")


class BatchVectorizeRequest(BaseModel):
    """批量向量化请求"""

    document_ids: List[int] = Field(..., description="文档ID列表")
    force_reprocess: bool = Field(default=False, description="是否强制重新处理")
    chunk_strategy: str = Field(default="semantic", description="分块策略")
    chunk_size: int = Field(default=1000, description="分块大小")
    chunk_overlap: int = Field(default=200, description="分块重叠")
    vector_model: str = Field(
        default="text-embedding-ada-002", description="向量化模型"
    )


class BatchVectorizeResponse(BaseModel):
    """批量向量化响应"""

    total_documents: int = Field(..., description="总文档数")
    processed: int = Field(..., description="已处理数")
    failed: int = Field(..., description="失败数")
    skipped: int = Field(..., description="跳过数")
    processing_time: float = Field(..., description="处理时间(秒)")
    results: List[Dict[str, Any]] = Field(..., description="处理结果")


class VectorizationStatusResponse(BaseModel):
    """向量化状态响应"""

    document_id: int = Field(..., description="文档ID")
    status: str = Field(..., description="处理状态")
    chunk_count: int = Field(..., description="分块数量")
    vector_dimension: int = Field(..., description="向量维度")
    processing_time: float = Field(..., description="处理时间(秒)")
    error_message: Optional[str] = Field(None, description="错误消息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


# ==================== 语义搜索相关Schema ====================


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""

    query: str = Field(..., description="搜索查询")
    document_ids: Optional[List[int]] = Field(None, description="限制搜索的文档ID")
    project_id: Optional[int] = Field(None, description="限制搜索的项目ID")
    top_k: int = Field(default=10, description="返回结果数量")
    similarity_threshold: float = Field(default=0.7, description="相似度阈值")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    search_type: str = Field(default="hybrid", description="搜索类型")


class SearchResult(BaseModel):
    """搜索结果项"""

    document_id: int = Field(..., description="文档ID")
    chunk_id: str = Field(..., description="分块ID")
    content: str = Field(..., description="内容")
    similarity_score: float = Field(..., description="相似度分数")
    metadata: Dict[str, Any] = Field(..., description="元数据")
    document_title: str = Field(..., description="文档标题")
    page_number: Optional[int] = Field(None, description="页码")


class SemanticSearchResponse(BaseModel):
    """语义搜索响应"""

    query: str = Field(..., description="搜索查询")
    total_results: int = Field(..., description="总结果数")
    search_time: float = Field(..., description="搜索时间(秒)")
    results: List[SearchResult] = Field(..., description="搜索结果")
    suggestions: List[str] = Field(default=[], description="搜索建议")


class SearchHistoryResponse(BaseModel):
    """搜索历史响应"""

    searches: List[Dict[str, Any]] = Field(..., description="搜索历史")
    total_count: int = Field(..., description="总搜索次数")
    popular_terms: List[str] = Field(..., description="热门搜索词")


# ==================== 文档分析相关Schema ====================


class DocumentAnalysisRequest(BaseModel):
    """文档分析请求"""

    document_id: int = Field(..., description="文档ID")
    analysis_types: List[str] = Field(..., description="分析类型列表")
    include_summary: bool = Field(default=True, description="是否包含摘要")
    include_keywords: bool = Field(default=True, description="是否包含关键词")
    include_entities: bool = Field(default=True, description="是否包含实体识别")
    include_sentiment: bool = Field(default=False, description="是否包含情感分析")
    include_compliance: bool = Field(default=False, description="是否包含合规检查")


class EnhancedDocumentAnalysisResponse(BaseModel):
    """增强文档分析响应"""

    document_id: int = Field(..., description="文档ID")
    status: str = Field(..., description="分析状态")
    analysis_types: List[str] = Field(..., description="分析类型")
    processing_time: float = Field(..., description="处理时间(秒)")
    task_id: Optional[str] = Field(None, description="任务ID")
    results: Optional[Dict[str, Any]] = Field(None, description="分析结果")


class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""

    document_id: int = Field(..., description="文档ID")
    status: str = Field(..., description="分析状态")
    analysis_types: List[str] = Field(..., description="分析类型")
    processing_time: float = Field(..., description="处理时间(秒)")
    results: Dict[str, Any] = Field(..., description="分析结果")
    error_message: Optional[str] = Field(None, description="错误消息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


# ==================== 统计和监控相关Schema ====================


class AIStatisticsResponse(BaseModel):
    """AI统计响应"""

    total_vectorized_documents: int = Field(..., description="总向量化文档数")
    total_searches: int = Field(..., description="总搜索次数")
    total_analyses: int = Field(..., description="总分析次数")
    average_search_time: float = Field(..., description="平均搜索时间")
    average_analysis_time: float = Field(..., description="平均分析时间")
    popular_search_terms: List[str] = Field(..., description="热门搜索词")
    usage_by_day: List[Dict[str, Any]] = Field(..., description="按日使用统计")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""

    ai_enabled: bool = Field(..., description="AI功能是否启用")
    vector_service_status: str = Field(..., description="向量服务状态")
    ai_service_status: str = Field(..., description="AI服务状态")
    knowledge_graph_status: str = Field(..., description="知识图谱状态")
    vector_store_connected: bool = Field(..., description="向量存储是否连接")
    ai_model_loaded: bool = Field(..., description="AI模型是否加载")
    last_check_time: Optional[datetime] = Field(None, description="最后检查时间")
