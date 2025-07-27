from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from datetime import datetime, timedelta

from app.crud.base import CRUDBase
from app.models.vector import (
    DocumentVector, VectorSearchIndex, SearchQuery, 
    KnowledgeGraph, KnowledgeGraphRelation
)
from app.schemas.vector import (
    DocumentVectorCreate, DocumentVectorUpdate,
    VectorSearchIndexCreate, VectorSearchIndexUpdate,
    SearchQueryCreate, SearchQueryUpdate,
    KnowledgeGraphNodeCreate, KnowledgeGraphRelationCreate
)


class CRUDDocumentVector(CRUDBase[DocumentVector, DocumentVectorCreate, DocumentVectorUpdate]):
    """文档向量CRUD操作"""
    
    def get_by_document(self, db: Session, *, document_id: int) -> List[DocumentVector]:
        """获取文档的所有向量分块"""
        return (
            db.query(self.model)
            .filter(DocumentVector.document_id == document_id)
            .order_by(DocumentVector.chunk_index)
            .all()
        )
    
    def get_by_document_and_chunk(self, db: Session, *, document_id: int, chunk_index: int) -> Optional[DocumentVector]:
        """获取文档的特定分块向量"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    DocumentVector.document_id == document_id,
                    DocumentVector.chunk_index == chunk_index
                )
            )
            .first()
        )
    
    def search_similar_vectors(
        self, 
        db: Session, 
        *, 
        query_vector: List[float], 
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索"""
        # 构建基础查询
        query = db.query(
            self.model,
            func.cosine_distance(DocumentVector.embedding_vector, query_vector).label('similarity')
        )
        
        # 添加文档过滤
        if document_ids:
            query = query.filter(DocumentVector.document_id.in_(document_ids))
        
        # 添加相似度过滤和排序
        results = (
            query
            .filter(func.cosine_distance(DocumentVector.embedding_vector, query_vector) >= similarity_threshold)
            .order_by(desc('similarity'))
            .limit(max_results)
            .all()
        )
        
        return [
            {
                'vector': result[0],
                'similarity': float(result[1])
            }
            for result in results
        ]
    
    def get_by_topic_category(self, db: Session, *, topic_category: str, limit: int = 100) -> List[DocumentVector]:
        """根据主题分类获取向量"""
        return (
            db.query(self.model)
            .filter(DocumentVector.topic_category == topic_category)
            .order_by(desc(DocumentVector.importance_score))
            .limit(limit)
            .all()
        )
    
    def get_high_importance_vectors(
        self, 
        db: Session, 
        *, 
        min_importance: float = 0.8, 
        limit: int = 100
    ) -> List[DocumentVector]:
        """获取高重要性向量"""
        return (
            db.query(self.model)
            .filter(DocumentVector.importance_score >= min_importance)
            .order_by(desc(DocumentVector.importance_score))
            .limit(limit)
            .all()
        )
    
    def delete_by_document(self, db: Session, *, document_id: int) -> int:
        """删除文档的所有向量"""
        deleted_count = (
            db.query(self.model)
            .filter(DocumentVector.document_id == document_id)
            .delete()
        )
        db.commit()
        return deleted_count
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """获取向量统计信息"""
        total_vectors = db.query(func.count(self.model.id)).scalar()
        total_documents = db.query(func.count(func.distinct(self.model.document_id))).scalar()
        
        avg_chunks_per_doc = (
            db.query(func.avg(func.count(self.model.id)))
            .group_by(self.model.document_id)
            .scalar()
        ) or 0
        
        model_distribution = (
            db.query(
                self.model.vector_model,
                func.count(self.model.id).label('count')
            )
            .group_by(self.model.vector_model)
            .all()
        )
        
        return {
            'total_vectors': total_vectors,
            'total_documents': total_documents,
            'avg_chunks_per_document': float(avg_chunks_per_doc),
            'model_distribution': {model: count for model, count in model_distribution}
        }


class CRUDVectorSearchIndex(CRUDBase[VectorSearchIndex, VectorSearchIndexCreate, VectorSearchIndexUpdate]):
    """向量搜索索引CRUD操作"""
    
    def get_by_name(self, db: Session, *, index_name: str) -> Optional[VectorSearchIndex]:
        """根据索引名称获取索引"""
        return db.query(self.model).filter(VectorSearchIndex.index_name == index_name).first()
    
    def get_active_indexes(self, db: Session) -> List[VectorSearchIndex]:
        """获取所有活跃的索引"""
        return (
            db.query(self.model)
            .filter(VectorSearchIndex.is_active == True)
            .order_by(VectorSearchIndex.created_at)
            .all()
        )
    
    def update_statistics(
        self, 
        db: Session, 
        *, 
        index_id: int, 
        total_vectors: int, 
        index_size: int
    ) -> Optional[VectorSearchIndex]:
        """更新索引统计信息"""
        index = self.get(db, id=index_id)
        if index:
            index.total_vectors = total_vectors
            index.index_size = index_size
            index.last_rebuild_at = datetime.utcnow()
            db.commit()
            db.refresh(index)
        return index


class CRUDSearchQuery(CRUDBase[SearchQuery, SearchQueryCreate, SearchQueryUpdate]):
    """搜索查询CRUD操作"""
    
    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[SearchQuery]:
        """获取用户的搜索历史"""
        return (
            db.query(self.model)
            .filter(SearchQuery.user_id == user_id)
            .order_by(desc(SearchQuery.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent_queries(
        self, 
        db: Session, 
        *, 
        days: int = 7, 
        limit: int = 100
    ) -> List[SearchQuery]:
        """获取最近的搜索查询"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(self.model)
            .filter(SearchQuery.created_at >= cutoff_date)
            .order_by(desc(SearchQuery.created_at))
            .limit(limit)
            .all()
        )
    
    def get_popular_queries(
        self, 
        db: Session, 
        *, 
        days: int = 30, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取热门搜索查询"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(
                SearchQuery.query_text,
                func.count(SearchQuery.id).label('count'),
                func.avg(SearchQuery.user_rating).label('avg_rating')
            )
            .filter(SearchQuery.created_at >= cutoff_date)
            .group_by(SearchQuery.query_text)
            .order_by(desc('count'))
            .limit(limit)
            .all()
        )
    
    def get_search_analytics(
        self, 
        db: Session, 
        *, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取搜索分析数据"""
        query = db.query(self.model).filter(
            and_(
                SearchQuery.created_at >= start_date,
                SearchQuery.created_at <= end_date
            )
        )
        
        total_searches = query.count()
        avg_response_time = query.with_entities(func.avg(SearchQuery.response_time)).scalar() or 0
        avg_results = query.with_entities(func.avg(SearchQuery.result_count)).scalar() or 0
        avg_rating = query.filter(SearchQuery.user_rating.isnot(None)).with_entities(func.avg(SearchQuery.user_rating)).scalar() or 0
        
        query_types = (
            query.with_entities(
                SearchQuery.query_type,
                func.count(SearchQuery.id).label('count')
            )
            .group_by(SearchQuery.query_type)
            .all()
        )
        
        return {
            'total_searches': total_searches,
            'avg_response_time': float(avg_response_time),
            'avg_results_per_search': float(avg_results),
            'avg_user_rating': float(avg_rating),
            'query_type_distribution': {qt: count for qt, count in query_types}
        }


class CRUDKnowledgeGraph(CRUDBase[KnowledgeGraph, KnowledgeGraphNodeCreate, Any]):
    """知识图谱节点CRUD操作"""
    
    def get_by_node_id(self, db: Session, *, node_id: str) -> Optional[KnowledgeGraph]:
        """根据节点ID获取节点"""
        return db.query(self.model).filter(KnowledgeGraph.node_id == node_id).first()
    
    def get_by_type(self, db: Session, *, node_type: str, limit: int = 100) -> List[KnowledgeGraph]:
        """根据节点类型获取节点"""
        return (
            db.query(self.model)
            .filter(KnowledgeGraph.node_type == node_type)
            .order_by(desc(KnowledgeGraph.confidence_score))
            .limit(limit)
            .all()
        )
    
    def get_by_entity_type(self, db: Session, *, entity_type: str, limit: int = 100) -> List[KnowledgeGraph]:
        """根据实体类型获取节点"""
        return (
            db.query(self.model)
            .filter(KnowledgeGraph.entity_type == entity_type)
            .order_by(desc(KnowledgeGraph.confidence_score))
            .limit(limit)
            .all()
        )
    
    def search_nodes(self, db: Session, *, query: str, limit: int = 50) -> List[KnowledgeGraph]:
        """搜索节点"""
        search_filter = or_(
            KnowledgeGraph.node_name.contains(query),
            KnowledgeGraph.node_description.contains(query)
        )
        return (
            db.query(self.model)
            .filter(search_filter)
            .order_by(desc(KnowledgeGraph.confidence_score))
            .limit(limit)
            .all()
        )
    
    def get_by_document(self, db: Session, *, document_id: int) -> List[KnowledgeGraph]:
        """获取文档相关的所有节点"""
        return (
            db.query(self.model)
            .filter(KnowledgeGraph.source_document_id == document_id)
            .order_by(desc(KnowledgeGraph.confidence_score))
            .all()
        )


class CRUDKnowledgeGraphRelation(CRUDBase[KnowledgeGraphRelation, KnowledgeGraphRelationCreate, Any]):
    """知识图谱关系CRUD操作"""
    
    def get_by_relation_id(self, db: Session, *, relation_id: str) -> Optional[KnowledgeGraphRelation]:
        """根据关系ID获取关系"""
        return db.query(self.model).filter(KnowledgeGraphRelation.relation_id == relation_id).first()
    
    def get_by_nodes(
        self, 
        db: Session, 
        *, 
        source_node_id: str, 
        target_node_id: str
    ) -> List[KnowledgeGraphRelation]:
        """获取两个节点之间的所有关系"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    KnowledgeGraphRelation.source_node_id == source_node_id,
                    KnowledgeGraphRelation.target_node_id == target_node_id
                )
            )
            .order_by(desc(KnowledgeGraphRelation.confidence_score))
            .all()
        )
    
    def get_node_relations(
        self, 
        db: Session, 
        *, 
        node_id: str, 
        direction: str = "both"
    ) -> List[KnowledgeGraphRelation]:
        """获取节点的所有关系"""
        if direction == "outgoing":
            filter_condition = KnowledgeGraphRelation.source_node_id == node_id
        elif direction == "incoming":
            filter_condition = KnowledgeGraphRelation.target_node_id == node_id
        else:  # both
            filter_condition = or_(
                KnowledgeGraphRelation.source_node_id == node_id,
                KnowledgeGraphRelation.target_node_id == node_id
            )
        
        return (
            db.query(self.model)
            .filter(filter_condition)
            .order_by(desc(KnowledgeGraphRelation.weight))
            .all()
        )
    
    def get_by_relation_type(self, db: Session, *, relation_type: str, limit: int = 100) -> List[KnowledgeGraphRelation]:
        """根据关系类型获取关系"""
        return (
            db.query(self.model)
            .filter(KnowledgeGraphRelation.relation_type == relation_type)
            .order_by(desc(KnowledgeGraphRelation.confidence_score))
            .limit(limit)
            .all()
        )
    
    def get_by_document(self, db: Session, *, document_id: int) -> List[KnowledgeGraphRelation]:
        """获取文档相关的所有关系"""
        return (
            db.query(self.model)
            .filter(KnowledgeGraphRelation.source_document_id == document_id)
            .order_by(desc(KnowledgeGraphRelation.confidence_score))
            .all()
        )


# 创建CRUD实例
document_vector = CRUDDocumentVector(DocumentVector)
vector_search_index = CRUDVectorSearchIndex(VectorSearchIndex)
search_query = CRUDSearchQuery(SearchQuery)
knowledge_graph = CRUDKnowledgeGraph(KnowledgeGraph)
knowledge_graph_relation = CRUDKnowledgeGraphRelation(KnowledgeGraphRelation)