from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# 注释掉不存在的导入
# from app.models.document import Document
# from app.models.vector import Vector
class VectorizationStatus(str, Enum):
    """向量化状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """分析状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """风险等级枚举"""

    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    CRITICAL = "极高风险"


class DocumentCategory(str, Enum):
    """文档分类枚举"""

    TECHNICAL = "技术文档"
    BUSINESS = "商务文档"
    LEGAL = "法律文档"
    FINANCIAL = "财务文档"
    MANAGEMENT = "管理文档"
    CONTRACT = "合同文档"
    REPORT = "报告文档"
    OTHER = "其他"


# DocumentVector Schemas


class DocumentVectorBase(BaseModel):
    """文档向量基础模型"""

    chunk_index: int = Field(..., description="分块索引")
    chunk_text: str = Field(..., description="分块文本内容")
    chunk_size: int = Field(..., description="分块大小(字符数)")
    chunk_position: Optional[str] = Field(None, description="分块位置信息")
    vector_model: str = Field(..., description="向量化模型")
    embedding_dimension: int = Field(..., description="向量维度")
    chunk_type: str = Field("text", description="分块类型")
    language: Optional[str] = Field(None, description="文本语言")
    confidence_score: Optional[float] = Field(None, description="向量化置信度")
    semantic_keywords: Optional[str] = Field(None, description="语义关键词")
    topic_category: Optional[str] = Field(None, description="主题分类")
    importance_score: Optional[float] = Field(None, description="重要性评分")


class DocumentVectorCreate(DocumentVectorBase):
    """创建文档向量"""

    document_id: int = Field(..., description="文档ID")
    embedding_vector: List[float] = Field(..., description="向量嵌入")
    processing_time: Optional[float] = Field(None, description="处理时间")


class DocumentVectorUpdate(BaseModel):
    """更新文档向量"""

    chunk_text: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    confidence_score: Optional[float] = None
    semantic_keywords: Optional[str] = None
    topic_category: Optional[str] = None
    importance_score: Optional[float] = None


class DocumentVectorInDB(DocumentVectorBase):
    """数据库中的文档向量"""

    id: int
    document_id: int
    embedding_vector: List[float]
    processed_by: int
    processing_time: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentVector(DocumentVectorInDB):
    """文档向量响应模型"""


# VectorSearchIndex Schemas


class VectorSearchIndexBase(BaseModel):
    """向量搜索索引基础模型"""

    index_name: str = Field(..., description="索引名称")
    index_type: str = Field(..., description="索引类型")
    vector_dimension: int = Field(..., description="向量维度")
    distance_metric: str = Field("cosine", description="距离度量")
    index_config: Optional[str] = Field(None, description="索引配置")
    is_active: bool = Field(True, description="是否启用")


class VectorSearchIndexCreate(VectorSearchIndexBase):
    """创建向量搜索索引"""


class VectorSearchIndexUpdate(BaseModel):
    """更新向量搜索索引"""

    index_config: Optional[str] = None
    is_active: Optional[bool] = None
    total_vectors: Optional[int] = None
    index_size: Optional[int] = None


class VectorSearchIndexInDB(VectorSearchIndexBase):
    """数据库中的向量搜索索引"""

    id: int
    total_vectors: int
    index_size: Optional[int]
    last_rebuild_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class VectorSearchIndex(VectorSearchIndexInDB):
    """向量搜索索引响应模型"""


# SearchQuery Schemas


class SearchQueryBase(BaseModel):
    """搜索查询基础模型"""

    query_text: str = Field(..., description="查询文本")
    query_type: str = Field(..., description="查询类型")
    search_filters: Optional[str] = Field(None, description="搜索过滤条件")
    similarity_threshold: Optional[float] = Field(0.7, description="相似度阈值")
    max_results: Optional[int] = Field(10, description="最大结果数量")


class SearchQueryCreate(SearchQueryBase):
    """创建搜索查询"""

    user_id: int = Field(..., description="用户ID")
    query_vector: Optional[List[float]] = Field(None, description="查询向量")


class SearchQueryUpdate(BaseModel):
    """更新搜索查询"""

    result_count: Optional[int] = None
    search_results: Optional[str] = None
    response_time: Optional[float] = None
    user_rating: Optional[int] = None
    feedback: Optional[str] = None


class SearchQueryInDB(SearchQueryBase):
    """数据库中的搜索查询"""

    id: int
    user_id: int
    query_vector: Optional[List[float]]
    result_count: Optional[int]
    search_results: Optional[str]
    response_time: Optional[float]
    user_rating: Optional[int]
    feedback: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchQuery(SearchQueryInDB):
    """搜索查询响应模型"""


# 向量化请求和响应模型


class VectorizeRequest(BaseModel):
    """向量化请求"""

    document_id: int = Field(..., description="文档ID")
    force_reprocess: bool = Field(False, description="是否强制重新处理")
    chunk_strategy: str = Field("semantic", description="分块策略")
    chunk_size: int = Field(1000, description="分块大小")
    chunk_overlap: int = Field(200, description="分块重叠")
    vector_model: str = Field("bge-m3", description="向量化模型")


class VectorizeResponse(BaseModel):
    """向量化响应"""

    document_id: int
    status: str
    chunk_count: int
    vector_dimension: int
    processing_time: float
    message: str


class BatchVectorizeRequest(BaseModel):
    """批量向量化请求"""

    document_ids: List[int] = Field(..., description="文档ID列表")
    force_reprocess: bool = Field(False, description="是否强制重新处理")
    chunk_strategy: str = Field("semantic", description="分块策略")
    chunk_size: int = Field(1000, description="分块大小")
    chunk_overlap: int = Field(200, description="分块重叠")
    vector_model: str = Field("bge-m3", description="向量化模型")


class BatchVectorizeResponse(BaseModel):
    """批量向量化响应"""

    total_documents: int
    processed: int
    failed: int
    skipped: int
    processing_time: float
    results: List[VectorizeResponse]


# 语义搜索请求和响应模型


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""

    query: str = Field(..., description="搜索查询")
    project_id: Optional[int] = Field(None, description="项目ID过滤")
    document_types: Optional[List[str]] = Field(None, description="文档类型过滤")
    similarity_threshold: float = Field(0.7, description="相似度阈值")
    max_results: int = Field(10, description="最大结果数量")
    include_metadata: bool = Field(True, description="是否包含元数据")
    search_type: str = Field("semantic", description="搜索类型:semantic/keyword/hybrid")


class SearchResult(BaseModel):
    """搜索结果项"""

    document_id: int
    chunk_id: int
    chunk_text: str
    similarity_score: float
    document_title: str
    document_type: str
    chunk_position: Optional[str]
    metadata: Optional[Dict[str, Any]]


class SemanticSearchResponse(BaseModel):
    """语义搜索响应"""

    query: str
    total_results: int
    search_time: float
    results: List[SearchResult]
    suggestions: Optional[List[str]] = Field(None, description="搜索建议")


# 知识图谱相关模型


class KnowledgeGraphNodeBase(BaseModel):
    """知识图谱节点基础模型"""

    node_id: str = Field(..., description="节点ID")
    node_type: str = Field(..., description="节点类型")
    node_name: str = Field(..., description="节点名称")
    node_description: Optional[str] = Field(None, description="节点描述")
    entity_type: Optional[str] = Field(None, description="实体类型")
    entity_properties: Optional[str] = Field(None, description="实体属性")
    confidence_score: Optional[float] = Field(None, description="置信度")


class KnowledgeGraphNodeCreate(KnowledgeGraphNodeBase):
    """创建知识图谱节点"""

    source_document_id: Optional[int] = Field(None, description="来源文档ID")
    node_vector: Optional[List[float]] = Field(None, description="节点向量")


class KnowledgeGraphNode(KnowledgeGraphNodeBase):
    """知识图谱节点响应模型"""

    id: int
    source_document_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class KnowledgeGraphRelationBase(BaseModel):
    """知识图谱关系基础模型"""

    relation_id: str = Field(..., description="关系ID")
    source_node_id: str = Field(..., description="源节点ID")
    target_node_id: str = Field(..., description="目标节点ID")
    relation_type: str = Field(..., description="关系类型")
    relation_name: str = Field(..., description="关系名称")
    relation_properties: Optional[str] = Field(None, description="关系属性")
    confidence_score: Optional[float] = Field(None, description="置信度")
    weight: float = Field(1.0, description="关系权重")


class KnowledgeGraphRelationCreate(KnowledgeGraphRelationBase):
    """创建知识图谱关系"""

    source_document_id: Optional[int] = Field(None, description="来源文档ID")
    extraction_method: Optional[str] = Field(None, description="抽取方法")


class KnowledgeGraphRelation(KnowledgeGraphRelationBase):
    """知识图谱关系响应模型"""

    id: int
    source_document_id: Optional[int]
    extraction_method: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# 文档智能分析相关模型


class DocumentAnalysisRequest(BaseModel):
    """文档智能分析请求"""

    document_id: int = Field(..., description="文档ID")
    analysis_types: List[str] = Field(..., description="分析类型列表")
    force_reprocess: bool = Field(False, description="是否强制重新分析")


class DocumentAnalysisResponse(BaseModel):
    """文档智能分析响应"""

    document_id: int
    analysis_results: Dict[str, Any]
    processing_time: float
    status: str
    message: str


class DocumentClassificationResult(BaseModel):
    """文档分类结果"""

    category: str
    confidence: float
    subcategories: Optional[List[Dict[str, Any]]]


class RiskAssessmentResult(BaseModel):
    """风险评估结果"""

    overall_risk_level: str
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float


class ComplianceAnalysisResult(BaseModel):
    """合规性分析结果"""

    compliance_status: str
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float


class EntityExtractionResult(BaseModel):
    """实体抽取结果"""

    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]


# === 新增的AI功能模型 ===


class VectorizationStatusResponse(BaseModel):
    """向量化状态响应"""

    document_id: int = Field(description="文档ID")
    status: VectorizationStatus = Field(description="向量化状态")
    progress: float = Field(ge=0, le=100, description="进度百分比")
    total_chunks: Optional[int] = Field(default=None, description="总分块数")
    processed_chunks: Optional[int] = Field(default=None, description="已处理分块数")
    model: Optional[str] = Field(default=None, description="使用的模型")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""

    document_id: int = Field(description="文档ID")
    status: AnalysisStatus = Field(description="分析状态")
    progress: float = Field(ge=0, le=100, description="进度百分比")
    analysis_types: List[str] = Field(description="分析类型")
    completed_types: List[str] = Field(description="已完成的分析类型")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class DocumentSummary(BaseModel):
    """文档摘要"""

    content: str = Field(description="摘要内容")
    length: int = Field(description="摘要长度")
    confidence: float = Field(ge=0, le=1, description="置信度")


class DocumentKeywords(BaseModel):
    """文档关键词"""

    keywords: List[str] = Field(description="关键词列表")
    scores: List[float] = Field(description="关键词分数")
    total_count: int = Field(description="关键词总数")


class DocumentClassification(BaseModel):
    """文档分类"""

    category: DocumentCategory = Field(description="文档类别")
    confidence: float = Field(ge=0, le=1, description="置信度")
    subcategories: Optional[List[str]] = Field(default=None, description="子类别")


class RiskFactor(BaseModel):
    """风险因素"""

    factor: str = Field(description="风险因素")
    level: RiskLevel = Field(description="风险等级")
    description: str = Field(description="风险描述")
    confidence: float = Field(ge=0, le=1, description="置信度")


class RiskAssessment(BaseModel):
    """风险评估"""

    overall_risk: RiskLevel = Field(description="总体风险等级")
    risk_score: float = Field(ge=0, le=100, description="风险分数")
    risk_factors: List[RiskFactor] = Field(description="风险因素列表")
    recommendations: List[str] = Field(description="建议列表")


class ComplianceCheck(BaseModel):
    """合规性检查"""

    is_compliant: bool = Field(description="是否合规")
    compliance_score: float = Field(ge=0, le=100, description="合规分数")
    violations: List[str] = Field(description="违规项列表")
    recommendations: List[str] = Field(description="合规建议")


class EntityExtraction(BaseModel):
    """实体提取"""

    entities: Dict[str, List[str]] = Field(description="实体字典")
    entity_count: int = Field(description="实体总数")
    confidence_scores: Dict[str, List[float]] = Field(description="置信度分数")


class SentimentAnalysis(BaseModel):
    """情感分析"""

    sentiment: str = Field(description="情感倾向")
    confidence: float = Field(ge=0, le=1, description="置信度")
    scores: Dict[str, float] = Field(description="各情感分数")


class EnhancedDocumentAnalysisResponse(BaseModel):
    """增强的文档分析响应"""

    document_id: int = Field(description="文档ID")
    analysis_types: List[str] = Field(description="分析类型")
    summary: Optional[DocumentSummary] = Field(default=None, description="文档摘要")
    keywords: Optional[DocumentKeywords] = Field(default=None, description="关键词")
    classification: Optional[DocumentClassification] = Field(
        default=None, description="分类"
    )
    risk_assessment: Optional[RiskAssessment] = Field(
        default=None, description="风险评估"
    )
    compliance: Optional[ComplianceCheck] = Field(
        default=None, description="合规性检查"
    )
    entities: Optional[EntityExtraction] = Field(default=None, description="实体提取")
    sentiment: Optional[SentimentAnalysis] = Field(default=None, description="情感分析")
    model: str = Field(description="使用的模型")
    analysis_time: float = Field(description="分析耗时(秒)")
    created_at: datetime = Field(description="创建时间")


class SearchHistoryItem(BaseModel):
    """搜索历史项"""

    search_id: str = Field(description="搜索ID")
    query: str = Field(description="搜索查询")
    results_count: int = Field(description="结果数量")
    search_time: float = Field(description="搜索耗时")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    created_at: datetime = Field(description="搜索时间")


class SearchHistoryResponse(BaseModel):
    """搜索历史响应"""

    total_count: int = Field(description="总搜索次数")
    items: List[SearchHistoryItem] = Field(description="搜索历史列表")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")


class VectorStatistics(BaseModel):
    """向量统计信息"""

    total_documents: int = Field(description="总文档数")
    vectorized_documents: int = Field(description="已向量化文档数")
    total_chunks: int = Field(description="总分块数")
    total_vectors: int = Field(description="总向量数")
    average_chunks_per_document: float = Field(description="平均每文档分块数")
    models_used: List[str] = Field(description="使用的模型列表")
    storage_size_mb: float = Field(description="存储大小(MB)")


class SearchStatistics(BaseModel):
    """搜索统计信息"""

    total_searches: int = Field(description="总搜索次数")
    unique_queries: int = Field(description="唯一查询数")
    average_results_per_search: float = Field(description="平均每次搜索结果数")
    average_search_time: float = Field(description="平均搜索时间")
    popular_queries: List[str] = Field(description="热门查询")
    search_frequency_by_day: Dict[str, int] = Field(description="按日搜索频率")


class AnalysisStatistics(BaseModel):
    """分析统计信息"""

    total_analyses: int = Field(description="总分析次数")
    analysis_types_count: Dict[str, int] = Field(description="分析类型计数")
    average_analysis_time: float = Field(description="平均分析时间")
    success_rate: float = Field(description="成功率")
    models_used: List[str] = Field(description="使用的模型列表")


class KnowledgeGraphStatistics(BaseModel):
    """知识图谱统计信息"""

    total_nodes: int = Field(description="总节点数")
    total_relations: int = Field(description="总关系数")
    node_types_count: Dict[str, int] = Field(description="节点类型计数")
    relation_types_count: Dict[str, int] = Field(description="关系类型计数")
    average_connections_per_node: float = Field(description="平均每节点连接数")
    graph_density: float = Field(description="图密度")


class AIStatisticsResponse(BaseModel):
    """AI统计信息响应"""

    vector_stats: VectorStatistics = Field(description="向量统计")
    search_stats: SearchStatistics = Field(description="搜索统计")
    analysis_stats: AnalysisStatistics = Field(description="分析统计")
    knowledge_graph_stats: KnowledgeGraphStatistics = Field(description="知识图谱统计")
    last_updated: datetime = Field(description="最后更新时间")


class TaskResponse(BaseModel):
    """任务响应"""

    task_id: str = Field(description="任务ID")
    status: str = Field(description="任务状态")
    message: str = Field(description="响应消息")
    estimated_time: Optional[int] = Field(default=None, description="预估完成时间(秒)")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(description="服务状态")
    ai_service: bool = Field(description="AI服务状态")
    vector_service: bool = Field(description="向量服务状态")
    knowledge_graph_service: bool = Field(description="知识图谱服务状态")
    cache_service: bool = Field(description="缓存服务状态")
    timestamp: datetime = Field(description="检查时间")
    version: str = Field(description="服务版本")
