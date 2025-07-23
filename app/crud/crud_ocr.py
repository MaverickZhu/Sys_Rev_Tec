from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.crud.base import CRUDBase
from app.models.ocr import OCRResult
from app.schemas.ocr import OCRResultCreate, OCRResultUpdate


class CRUDOCRResult(CRUDBase[OCRResult, OCRResultCreate, OCRResultUpdate]):
    def create_with_processor(
        self, db: Session, *, obj_in: OCRResultCreate, processor_id: int
    ) -> OCRResult:
        """创建OCR结果并关联处理者"""
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        db_obj = self.model(**obj_in_data, processed_by=processor_id)
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
                if key == 'confidence_min':
                    query = query.filter(OCRResult.confidence >= value)
                elif key == 'confidence_max':
                    query = query.filter(OCRResult.confidence <= value)
                else:
                    query = query.filter(getattr(OCRResult, key) == value)
        
        return query.order_by(desc(OCRResult.created_at)).offset(skip).limit(limit).all()
    
    def search_text(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """在OCR识别文本中搜索"""
        search_filter = or_(
            OCRResult.extracted_text.contains(query),
            OCRResult.filename.contains(query)
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
        self, db: Session, *, min_confidence: float = 0.8, skip: int = 0, limit: int = 100
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
    
    def update_processing_time(
        self, db: Session, *, ocr_id: int, processing_time: float
    ) -> Optional[OCRResult]:
        """更新OCR处理时间"""
        ocr_result = self.get(db, id=ocr_id)
        if ocr_result:
            ocr_result.processing_time = processing_time
            db.add(ocr_result)
            db.commit()
            db.refresh(ocr_result)
        return ocr_result
    
    def mark_as_completed(
        self, db: Session, *, ocr_id: int, extracted_text: str, confidence: float
    ) -> Optional[OCRResult]:
        """标记OCR处理完成"""
        ocr_result = self.get(db, id=ocr_id)
        if ocr_result:
            ocr_result.status = "completed"
            ocr_result.extracted_text = extracted_text
            ocr_result.confidence = confidence
            db.add(ocr_result)
            db.commit()
            db.refresh(ocr_result)
        return ocr_result
    
    def mark_as_failed(
        self, db: Session, *, ocr_id: int, error_message: str
    ) -> Optional[OCRResult]:
        """标记OCR处理失败"""
        ocr_result = self.get(db, id=ocr_id)
        if ocr_result:
            ocr_result.status = "failed"
            ocr_result.error_message = error_message
            db.add(ocr_result)
            db.commit()
            db.refresh(ocr_result)
        return ocr_result
    
    def get_statistics(
        self, db: Session, *, processor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取OCR处理统计信息"""
        query = db.query(self.model)
        
        if processor_id:
            query = query.filter(OCRResult.processed_by == processor_id)
        
        total_results = query.count()
        completed_results = query.filter(OCRResult.status == "completed").count()
        failed_results = query.filter(OCRResult.status == "failed").count()
        processing_results = query.filter(OCRResult.status == "processing").count()
        
        # 平均置信度
        avg_confidence = db.query(db.func.avg(OCRResult.confidence)).filter(
            OCRResult.status == "completed"
        ).scalar() or 0
        
        # 平均处理时间
        avg_processing_time = db.query(db.func.avg(OCRResult.processing_time)).filter(
            OCRResult.processing_time.isnot(None)
        ).scalar() or 0
        
        # 按引擎统计
        engine_stats = {}
        for engine, count in db.query(OCRResult.ocr_engine, db.func.count(OCRResult.id)).group_by(OCRResult.ocr_engine).all():
            engine_stats[engine] = count
        
        # 按语言统计
        language_stats = {}
        for language, count in db.query(OCRResult.language, db.func.count(OCRResult.id)).group_by(OCRResult.language).all():
            if language:
                language_stats[language] = count
        
        return {
            "total_results": total_results,
            "completed_results": completed_results,
            "failed_results": failed_results,
            "processing_results": processing_results,
            "success_rate": round(completed_results / total_results * 100, 2) if total_results > 0 else 0,
            "average_confidence": round(float(avg_confidence), 4),
            "average_processing_time": round(float(avg_processing_time), 2),
            "engine_distribution": engine_stats,
            "language_distribution": language_stats
        }
    
    def get_recent_results(
        self, db: Session, *, days: int = 7, skip: int = 0, limit: int = 100
    ) -> List[OCRResult]:
        """获取最近几天的OCR结果"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (
            db.query(self.model)
            .filter(OCRResult.created_at >= cutoff_date)
            .order_by(desc(OCRResult.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )


ocr_result = CRUDOCRResult(OCRResult)