from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.base_class import Base


class DocumentVector(Base):
    """文档向量化模型"""
    __tablename__ = "document_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # 分块信息
    chunk_index = Column(Integer, nullable=False, comment="分块索引")
    chunk_text = Column(Text, nullable=False, comment="分块文本内容")
    chunk_size = Column(Integer, nullable=False, comment="分块大小（字符数）")
    chunk_position = Column(Text, comment="分块在原文档中的位置信息(JSON格式)")
    
    # 向量信息
    embedding_vector = Column(ARRAY(Float), comment="向量嵌入")
    vector_model = Column(String(100), nullable=False, comment="使用的向量化模型")
    embedding_dimension = Column(Integer, nullable=False, comment="向量维度")
    
    # 元数据
    chunk_type = Column(String(50), default="text", comment="分块类型：text/title/table/list")
    language = Column(String(10), comment="文本语言")
    confidence_score = Column(Float, comment="向量化置信度")
    
    # 语义信息
    semantic_keywords = Column(Text, comment="语义关键词(JSON格式)")
    topic_category = Column(String(100), comment="主题分类")
    importance_score = Column(Float, comment="重要性评分(0-1)")
    
    # 处理信息
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    processing_time = Column(Float, comment="处理时间（秒）")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    document = relationship("Document")
    processor = relationship("User")


class VectorSearchIndex(Base):
    """向量搜索索引模型"""
    __tablename__ = "vector_search_indexes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 索引信息
    index_name = Column(String(100), unique=True, nullable=False, comment="索引名称")
    index_type = Column(String(50), nullable=False, comment="索引类型：ivfflat/hnsw")
    vector_dimension = Column(Integer, nullable=False, comment="向量维度")
    distance_metric = Column(String(20), default="cosine", comment="距离度量：cosine/euclidean/inner_product")
    
    # 索引配置
    index_config = Column(Text, comment="索引配置参数(JSON格式)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 统计信息
    total_vectors = Column(Integer, default=0, comment="总向量数量")
    index_size = Column(Integer, comment="索引大小（字节）")
    last_rebuild_at = Column(DateTime(timezone=True), comment="最后重建时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SearchQuery(Base):
    """搜索查询记录模型"""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 查询信息
    query_text = Column(Text, nullable=False, comment="查询文本")
    query_type = Column(String(50), nullable=False, comment="查询类型：semantic/keyword/hybrid")
    query_vector = Column(ARRAY(Float), comment="查询向量")
    
    # 搜索参数
    search_filters = Column(Text, comment="搜索过滤条件(JSON格式)")
    similarity_threshold = Column(Float, comment="相似度阈值")
    max_results = Column(Integer, comment="最大结果数量")
    
    # 搜索结果
    result_count = Column(Integer, comment="结果数量")
    search_results = Column(Text, comment="搜索结果(JSON格式)")
    response_time = Column(Float, comment="响应时间（毫秒）")
    
    # 用户反馈
    user_rating = Column(Integer, comment="用户评分(1-5)")
    feedback = Column(Text, comment="用户反馈")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    user = relationship("User")


class KnowledgeGraph(Base):
    """知识图谱节点模型"""
    __tablename__ = "knowledge_graph_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 节点信息
    node_id = Column(String(100), unique=True, nullable=False, comment="节点唯一标识")
    node_type = Column(String(50), nullable=False, comment="节点类型：entity/concept/document")
    node_name = Column(String(200), nullable=False, comment="节点名称")
    node_description = Column(Text, comment="节点描述")
    
    # 实体信息
    entity_type = Column(String(50), comment="实体类型：person/organization/location/date")
    entity_properties = Column(Text, comment="实体属性(JSON格式)")
    
    # 关联信息
    source_document_id = Column(Integer, ForeignKey("documents.id"), comment="来源文档ID")
    confidence_score = Column(Float, comment="置信度评分")
    
    # 向量表示
    node_vector = Column(ARRAY(Float), comment="节点向量表示")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    source_document = relationship("Document")


class KnowledgeGraphRelation(Base):
    """知识图谱关系模型"""
    __tablename__ = "knowledge_graph_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关系信息
    relation_id = Column(String(100), unique=True, nullable=False, comment="关系唯一标识")
    source_node_id = Column(String(100), ForeignKey("knowledge_graph_nodes.node_id"), nullable=False)
    target_node_id = Column(String(100), ForeignKey("knowledge_graph_nodes.node_id"), nullable=False)
    relation_type = Column(String(50), nullable=False, comment="关系类型")
    relation_name = Column(String(200), nullable=False, comment="关系名称")
    
    # 关系属性
    relation_properties = Column(Text, comment="关系属性(JSON格式)")
    confidence_score = Column(Float, comment="置信度评分")
    weight = Column(Float, default=1.0, comment="关系权重")
    
    # 来源信息
    source_document_id = Column(Integer, ForeignKey("documents.id"), comment="来源文档ID")
    extraction_method = Column(String(50), comment="抽取方法：rule_based/ml/llm")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    source_node = relationship("KnowledgeGraph", foreign_keys=[source_node_id])
    target_node = relationship("KnowledgeGraph", foreign_keys=[target_node_id])
    source_document = relationship("Document")