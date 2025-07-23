from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import CRUDBase
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    def create_with_uploader(
        self, db: Session, *, obj_in: DocumentCreate, uploader_id: int
    ) -> Document:
        """创建文档并关联上传者"""
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        db_obj = self.model(**obj_in_data, uploaded_by=uploader_id)
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
            .filter(Document.uploaded_by == uploader_id)
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
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """搜索文档（按文件名和描述）"""
        search_filter = or_(
            Document.filename.contains(query),
            Document.description.contains(query)
        )
        
        return (
            db.query(self.model)
            .filter(search_filter)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
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
        self, db: Session, *, document_id: int, processing_status: str = "completed"
    ) -> Optional[Document]:
        """标记文档为已处理"""
        document = self.get(db, id=document_id)
        if document:
            document.is_processed = True
            document.processing_status = processing_status
            db.add(document)
            db.commit()
            db.refresh(document)
        return document
    
    def update_access_info(
        self, db: Session, *, document_id: int
    ) -> Optional[Document]:
        """更新文档访问信息"""
        from datetime import datetime
        
        document = self.get(db, id=document_id)
        if document:
            document.access_count = (document.access_count or 0) + 1
            document.last_accessed = datetime.utcnow()
            db.add(document)
            db.commit()
            db.refresh(document)
        return document
    
    def get_statistics(
        self, db: Session, *, uploader_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取文档统计信息"""
        query = db.query(self.model)
        
        if uploader_id:
            query = query.filter(Document.uploaded_by == uploader_id)
        
        total_documents = query.count()
        processed_documents = query.filter(Document.is_processed == True).count()
        unprocessed_documents = total_documents - processed_documents
        
        # 按类型统计
        type_stats = {}
        for doc_type, count in db.query(Document.document_type, db.func.count(Document.id)).group_by(Document.document_type).all():
            type_stats[doc_type] = count
        
        # 按处理状态统计
        status_stats = {}
        for status, count in db.query(Document.processing_status, db.func.count(Document.id)).group_by(Document.processing_status).all():
            if status:
                status_stats[status] = count
        
        return {
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "unprocessed_documents": unprocessed_documents,
            "processing_rate": round(processed_documents / total_documents * 100, 2) if total_documents > 0 else 0,
            "type_distribution": type_stats,
            "status_distribution": status_stats
        }


document = CRUDDocument(Document)