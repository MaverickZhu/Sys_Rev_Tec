from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.vector import (
    DocumentVector,
    SearchQuery,
    VectorSearchIndex,
)
from app.schemas.vector import (
    DocumentVectorCreate,
    DocumentVectorUpdate,
    SearchQueryCreate,
    SearchQueryUpdate,
    VectorSearchIndexCreate,
    VectorSearchIndexUpdate,
)


class CRUDDocumentVector(
    CRUDBase[DocumentVector, DocumentVectorCreate, DocumentVectorUpdate]
):
    """文档向量CRUD操作"""

    def get_by_document(self, db: Session, *, document_id: int) -> List[DocumentVector]:
        """获取文档的所有向量分块"""
        return (
            db.query(self.model)
            .filter(DocumentVector.document_id == document_id)
            .order_by(DocumentVector.chunk_index)
            .all()
        )

    def get_by_document_and_chunk(
        self, db: Session, *, document_id: int, chunk_index: int
    ) -> Optional[DocumentVector]:
        """获取文档的特定分块向量"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    DocumentVector.document_id == document_id,
                    DocumentVector.chunk_index == chunk_index,
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
        document_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索"""
        # 构建基础查询
        query = db.query(
            self.model,
            func.cosine_distance(DocumentVector.embedding_vector, query_vector).label(
                "similarity"
            ),
        )

        # 添加文档过滤
        if document_ids:
            query = query.filter(DocumentVector.document_id.in_(document_ids))

        # 添加相似度过滤和排序
        results = (
            query.filter(
                func.cosine_distance(DocumentVector.embedding_vector, query_vector)
                >= similarity_threshold
            )
            .order_by(desc("similarity"))
            .limit(max_results)
            .all()
        )

        return [
            {"vector": result[0], "similarity": float(result[1])} for result in results
        ]

    def get_by_topic_category(
        self, db: Session, *, topic_category: str, limit: int = 100
    ) -> List[DocumentVector]:
        """根据主题分类获取向量"""
        return (
            db.query(self.model)
            .filter(DocumentVector.topic_category == topic_category)
            .order_by(desc(DocumentVector.importance_score))
            .limit(limit)
            .all()
        )

    def get_high_importance_vectors(
        self, db: Session, *, min_importance: float = 0.8, limit: int = 100
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
        total_documents = db.query(
            func.count(func.distinct(self.model.document_id))
        ).scalar()

        avg_chunks_per_doc = (
            db.query(func.avg(func.count(self.model.id)))
            .group_by(self.model.document_id)
            .scalar()
        ) or 0

        model_distribution = (
            db.query(self.model.vector_model, func.count(self.model.id).label("count"))
            .group_by(self.model.vector_model)
            .all()
        )

        return {
            "total_vectors": total_vectors,
            "total_documents": total_documents,
            "avg_chunks_per_document": float(avg_chunks_per_doc),
            "model_distribution": dict(model_distribution),
        }


class CRUDVectorSearchIndex(
    CRUDBase[VectorSearchIndex, VectorSearchIndexCreate, VectorSearchIndexUpdate]
):
    """向量搜索索引CRUD操作"""

    def get_by_name(
        self, db: Session, *, index_name: str
    ) -> Optional[VectorSearchIndex]:
        """根据索引名称获取索引"""
        return (
            db.query(self.model)
            .filter(VectorSearchIndex.index_name == index_name)
            .first()
        )

    def get_active_indexes(self, db: Session) -> List[VectorSearchIndex]:
        """获取所有活跃的索引"""
        return (
            db.query(self.model)
            .filter(VectorSearchIndex.is_active)
            .order_by(VectorSearchIndex.created_at)
            .all()
        )


class CRUDSearchQuery(CRUDBase[SearchQuery, SearchQueryCreate, SearchQueryUpdate]):
    """搜索查询CRUD操作"""

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[SearchQuery]:
        """获取用户的搜索历史"""
        return (
            db.query(self.model)
            .filter(SearchQuery.user_id == user_id)
            .order_by(desc(SearchQuery.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_popular_queries(
        self, db: Session, *, days: int = 30, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取热门搜索查询"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(SearchQuery.query_text, func.count(SearchQuery.id).label("count"))
            .filter(SearchQuery.created_at >= cutoff_date)
            .group_by(SearchQuery.query_text)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )


# 创建CRUD实例
document_vector = CRUDDocumentVector(DocumentVector)
vector_search_index = CRUDVectorSearchIndex(VectorSearchIndex)
search_query = CRUDSearchQuery(SearchQuery)
