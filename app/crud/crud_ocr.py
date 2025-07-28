from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.ocr import OCRResult
from app.schemas.ocr import OCRResultCreate, OCRResultUpdate


class CRUDOCRResult(CRUDBase[OCRResult, OCRResultCreate, OCRResultUpdate]):
    def create_with_processor(
        self, db: Session, *, obj_in: OCRResultCreate, processor_id: int
    ) -> OCRResult:
        """创建OCR结果记录，关联处理者"""
        obj_in_data = obj_in.model_dump()

        # 字段映射（处理schema和model之间的差异）
        field_mapping = {
            "document_id": "document_id",
            "filename": "filename",
            "file_path": "file_path",
            "extracted_text": "extracted_text",
            "confidence": "confidence",
            "ocr_engine": "ocr_engine",
            "processing_time": "processing_time",
            "status": "status",
            "error_message": "error_message",
        }

        # 忽略的字段（模型中不存在）
        ignored_fields = {"word_count"}

        # 转换字段名
        mapped_data = {}
        for key, value in obj_in_data.items():
            if key in ignored_fields:
                continue
            mapped_key = field_mapping.get(key, key)
            mapped_data[mapped_key] = value

        # 设置默认状态（如果没有明确指定）
        if "status" not in mapped_data:
            mapped_data["status"] = "completed"

        db_obj = self.model(**mapped_data, processed_by=processor_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_processor(
        self, db: Session, *, processor_id: int, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """根据处理者获取OCR结果列表"""
        return (
            db.query(self.model)
            .filter(OCRResult.processed_by == processor_id)
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_document(
        self, db: Session, *, document_id: int, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """根据文档获取OCR结果列表"""
        return (
            db.query(self.model)
            .filter(OCRResult.document_id == document_id)
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_engine(
        self, db: Session, *, engine: str, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """根据OCR引擎获取结果列表"""
        return (
            db.query(self.model)
            .filter(OCRResult.ocr_engine == engine)
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self, db: Session, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """根据处理状态获取OCR结果列表"""
        return (
            db.query(self.model)
            .filter(OCRResult.status == status)
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_filters(
        self, db: Session, *, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """根据多个条件筛选OCR结果"""
        query = db.query(self.model)

        for key, value in filters.items():
            if hasattr(OCRResult, key) and value is not None:
                if key == "confidence_min":
                    query = query.filter(OCRResult.confidence >= value)
                elif key == "confidence_max":
                    query = query.filter(OCRResult.confidence <= value)
                else:
                    query = query.filter(getattr(OCRResult, key) == value)

        return (
            query.order_by(desc(OCRResult.created_at)).offset(skip).limit(limit).all()
        )

    def get_by_filters_with_dates(
        self,
        db: Session,
        *,
        filters: Dict[str, Any] = None,
        date_filters: Dict[str, datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OCRResult]:
        """根据多个条件和日期范围筛选OCR结果"""
        query = db.query(self.model)

        # 应用普通过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(OCRResult, key) and value is not None:
                    if key == "confidence_min":
                        query = query.filter(OCRResult.confidence >= value)
                    elif key == "confidence_max":
                        query = query.filter(OCRResult.confidence <= value)
                    else:
                        query = query.filter(getattr(OCRResult, key) == value)

        # 应用日期过滤条件
        if date_filters:
            if "start_date" in date_filters:
                query = query.filter(OCRResult.created_at >= date_filters["start_date"])
            if "end_date" in date_filters:
                query = query.filter(OCRResult.created_at <= date_filters["end_date"])

        return (
            query.order_by(desc(OCRResult.created_at)).offset(skip).limit(limit).all()
        )

    def search_text(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """在OCR识别文本中搜索"""
        search_filter = or_(
            OCRResult.extracted_text.contains(query), OCRResult.filename.contains(query)
        )

        return (
            db.query(self.model)
            .filter(search_filter)
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_high_confidence_results(
        self,
        db: Session,
        *,
        min_confidence: float = 0.8,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OCRResult]:
        """获取高置信度的OCR结果"""
        return (
            db.query(self.model)
            .filter(OCRResult.confidence >= min_confidence)
            .order_by(desc(OCRResult.confidence))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_failed_results(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """获取处理失败的OCR结果"""
        return (
            db.query(self.model)
            .filter(OCRResult.status == "failed")
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """获取OCR处理统计信息"""
        total_count = db.query(self.model).count()
        completed_count = (
            db.query(self.model).filter(OCRResult.status == "completed").count()
        )
        failed_count = db.query(self.model).filter(OCRResult.status == "failed").count()
        processing_count = (
            db.query(self.model).filter(OCRResult.status == "processing").count()
        )

        # 计算平均置信度
        avg_confidence = (
            db.query(db.func.avg(OCRResult.confidence))
            .filter(OCRResult.status == "completed")
            .scalar()
        ) or 0.0

        return {
            "total_count": total_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "processing_count": processing_count,
            "success_rate": (
                (completed_count / total_count * 100) if total_count > 0 else 0
            ),
            "average_confidence": float(avg_confidence),
        }


ocr_result = CRUDOCRResult(OCRResult)
