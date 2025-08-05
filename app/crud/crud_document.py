from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    def create_with_uploader(
        self, db: Session, *, obj_in: DocumentCreate, owner_id: int
    ) -> Document:
        """创建文档并关联上传者"""
        obj_in_data = (
            obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        )
        db_obj = self.model(**obj_in_data, uploader_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_uploader(
        self, db: Session, *, uploader_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """根据上传者获取文档列表"""
        return (
            db.query(self.model)
            .filter(Document.uploader_id == uploader_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """根据项目获取文档列表"""
        return (
            db.query(self.model)
            .filter(Document.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self, db: Session, *, document_type: str, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """根据文档类型获取文档列表"""
        return (
            db.query(self.model)
            .filter(Document.document_type == document_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_filters(
        self, db: Session, *, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """根据多个条件筛选文档"""
        query = db.query(self.model)

        for key, value in filters.items():
            if hasattr(Document, key) and value is not None:
                query = query.filter(getattr(Document, key) == value)

        return query.offset(skip).limit(limit).all()

    def search_documents(
        self,
        db: Session,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
    ) -> List[Document]:
        """搜索文档（按文件名、摘要、提取的文本内容和OCR文本）"""
        search_filter = or_(
            Document.filename.contains(query),
            Document.original_filename.contains(query),
            Document.summary.contains(query),
            Document.extracted_text.contains(query),
            Document.ocr_text.contains(query),
            Document.keywords.contains(query),
        )

        query_obj = db.query(self.model).filter(search_filter)

        # 如果指定了项目ID，则只在该项目中搜索
        if project_id is not None:
            query_obj = query_obj.filter(Document.project_id == project_id)

        return query_obj.offset(skip).limit(limit).all()

    def search_documents_count(
        self, db: Session, *, query: str, project_id: Optional[int] = None
    ) -> int:
        """获取搜索结果总数"""
        search_filter = or_(
            Document.filename.contains(query),
            Document.original_filename.contains(query),
            Document.summary.contains(query),
            Document.extracted_text.contains(query),
            Document.ocr_text.contains(query),
            Document.keywords.contains(query),
        )

        query_obj = db.query(self.model).filter(search_filter)

        if project_id is not None:
            query_obj = query_obj.filter(Document.project_id == project_id)

        return query_obj.count()

    def get_unprocessed_documents(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """获取未处理的文档"""
        return (
            db.query(self.model)
            .filter(Document.is_processed == False)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def mark_as_processed(
        self, db: Session, *, document_id: int, processing_status: str = "processed"
    ) -> Optional[Document]:
        """标记文档为已处理"""
        document = self.get(db, id=document_id)
        if document:
            document.is_processed = True
            document.status = processing_status
            db.commit()
            return document
        return None

    def update_access_info(
        self, db: Session, *, document_id: int
    ) -> Optional[Document]:
        """更新文档访问信息"""
        document = self.get(db, id=document_id)
        if document:
            # 由于Document模型没有access_count和last_accessed字段
            # 这里只是更新updated_at时间戳
            if hasattr(document, "updated_at"):
                document.updated_at = datetime.utcnow()
                db.commit()
            return document
        return None

    def get_statistics(
        self, db: Session, *, uploader_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取文档统计信息"""
        query = db.query(self.model)

        if uploader_id:
            query = query.filter(Document.uploader_id == uploader_id)

        total_documents = query.count()
        processed_documents = query.filter(Document.is_processed).count()
        unprocessed_documents = total_documents - processed_documents

        # 按类型统计
        type_stats = {}
        for doc_type, count in (
            db.query(Document.document_type, func.count(Document.id))
            .group_by(Document.document_type)
            .all()
        ):
            type_stats[doc_type] = count

        # 按处理状态统计
        status_stats = {}
        for status, count in (
            db.query(Document.status, func.count(Document.id))
            .group_by(Document.status)
            .all()
        ):
            if status:
                status_stats[status] = count

        return {
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "unprocessed_documents": unprocessed_documents,
            "processing_rate": (
                round(processed_documents / total_documents * 100, 2)
                if total_documents > 0
                else 0
            ),
            "by_type": [{"type": k, "count": v} for k, v in type_stats.items()],
            "by_status": [{"status": k, "count": v} for k, v in status_stats.items()],
            "total_size": db.query(func.sum(Document.file_size)).scalar() or 0,
        }


crud_document = CRUDDocument(Document)
