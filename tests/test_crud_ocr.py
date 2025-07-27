import pytest
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core.config import settings
from tests.utils.utils import random_lower_string
from tests.utils.user import create_random_user
from tests.utils.project import create_random_project
from tests.utils.document import create_random_document
from tests.utils.ocr import create_random_ocr_result


class TestCRUDOCR:
    def test_create_ocr_result(self, db: Session) -> None:
        """测试创建OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        extracted_text = "This is extracted text from OCR"
        confidence_score = 0.95
        
        ocr_in = schemas.OCRResultCreate(
            filename="test_document.pdf",
            engine="tesseract",
            language="en",
            text_content=extracted_text,
            confidence_score=confidence_score,
            processing_time=1.5,
            word_count=len(extracted_text.split()),
            metadata="{}",
            document_id=document.id
        )
        
        ocr_result = crud.ocr_result.create_with_processor(db=db, obj_in=ocr_in, processor_id=user.id)
        
        assert ocr_result.document_id == document.id
        assert ocr_result.extracted_text == extracted_text
        assert ocr_result.confidence == confidence_score
        assert ocr_result.processing_time == 1.5
        assert ocr_result.ocr_engine == "tesseract"

    def test_get_ocr_result(self, db: Session) -> None:
        """测试获取OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        ocr_result = create_random_ocr_result(db, document_id=document.id, processed_by=user.id)
        
        stored_ocr = crud.ocr_result.get(db=db, id=ocr_result.id)
        assert stored_ocr
        assert stored_ocr.id == ocr_result.id
        assert stored_ocr.document_id == document.id
        assert stored_ocr.extracted_text == ocr_result.extracted_text

    def test_update_ocr_result(self, db: Session) -> None:
        """测试更新OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        ocr_result = create_random_ocr_result(db, document_id=document.id, processed_by=user.id)
        
        new_text = "Updated extracted text"
        new_confidence = 0.98
        
        ocr_update = schemas.OCRResultUpdate(
            text_content=new_text,
            confidence_score=new_confidence
        )
        
        updated_ocr = crud.ocr_result.update(
            db=db, db_obj=ocr_result, obj_in=ocr_update
        )
        
        assert updated_ocr.id == ocr_result.id
        assert updated_ocr.extracted_text == new_text
        assert updated_ocr.confidence == new_confidence
        assert updated_ocr.document_id == document.id

    def test_delete_ocr_result(self, db: Session) -> None:
        """测试删除OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        ocr_result = create_random_ocr_result(db, document_id=document.id, processed_by=user.id)
        
        ocr_id = ocr_result.id
        crud.ocr_result.remove(db=db, id=ocr_id)
        
        deleted_ocr = crud.ocr_result.get(db=db, id=ocr_id)
        assert deleted_ocr is None

    def test_get_by_document(self, db: Session) -> None:
        """测试按文档获取OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document1 = create_random_document(db, owner_id=user.id, project_id=project.id)
        document2 = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 为document1创建OCR结果
        ocr1 = create_random_ocr_result(db, document_id=document1.id, processed_by=user.id)
        ocr2 = create_random_ocr_result(db, document_id=document1.id, processed_by=user.id)
        
        # 为document2创建OCR结果
        create_random_ocr_result(db, document_id=document2.id, processed_by=user.id)
        
        ocr_results = crud.ocr_result.get_by_document(db=db, document_id=document1.id)
        
        assert len(ocr_results) == 2
        for ocr in ocr_results:
            assert ocr.document_id == document1.id
        
        ocr_ids = [ocr.id for ocr in ocr_results]
        assert ocr1.id in ocr_ids
        assert ocr2.id in ocr_ids

    def test_get_by_status(self, db: Session) -> None:
        """测试按状态获取OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 创建不同状态的OCR结果
        completed_ocr_in = schemas.OCRResultCreate(
            filename="completed_doc.pdf",
            engine="tesseract",
            language="chi_sim+eng",
            text_content="Completed OCR text",
            confidence_score=0.95,
            processing_time=2.5,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        completed_ocr = crud.ocr_result.create_with_processor(db=db, obj_in=completed_ocr_in, processor_id=user.id)
        
        # 创建处理中的OCR结果
        processing_ocr_in = schemas.OCRResultCreate(
            filename="processing_document.pdf",
            engine="tesseract",
            language="en",
            text_content="",
            confidence_score=0.0,
            processing_time=0.0,
            word_count=0,
            metadata="{}",
            document_id=document.id,
            status="processing"
        )
        processing_ocr = crud.ocr_result.create_with_processor(db=db, obj_in=processing_ocr_in, processor_id=user.id)
        
        # 获取completed状态的OCR结果
        completed_results = crud.ocr_result.get_by_status(db=db, status="completed")
        
        # 获取processing状态的OCR结果
        processing_results = crud.ocr_result.get_by_status(db=db, status="processing")
        
        # 验证结果
        completed_ids = [ocr.id for ocr in completed_results]
        processing_ids = [ocr.id for ocr in processing_results]
        
        assert completed_ocr.id in completed_ids
        assert processing_ocr.id in processing_ids
        assert processing_ocr.id not in completed_ids
        assert completed_ocr.id not in processing_ids

    def test_update_status(self, db: Session) -> None:
        """测试更新OCR状态"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 创建处理中的OCR结果
        ocr_in = schemas.OCRResultCreate(
            filename="status_test_document.pdf",
            engine="tesseract",
            language="en",
            text_content="",
            confidence_score=0.0,
            processing_time=0.0,
            word_count=0,
            metadata="{}",
            document_id=document.id,
            status="processing"
        )
        ocr_result = crud.ocr_result.create_with_processor(db=db, obj_in=ocr_in, processor_id=user.id)
        
        # 更新状态为completed
        updated_ocr = crud.ocr_result.update_status(
            db=db, ocr_id=ocr_result.id, status="completed"
        )
        
        assert updated_ocr.status == "completed"
        assert updated_ocr.id == ocr_result.id
        
        # 验证数据库中的状态也已更新
        stored_ocr = crud.ocr_result.get(db=db, id=ocr_result.id)
        assert stored_ocr.status == "completed"

    def test_get_latest_by_document(self, db: Session) -> None:
        """测试获取文档的最新OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 创建多个OCR结果
        ocr1_in = schemas.OCRResultCreate(
            filename="first_doc.pdf",
            engine="tesseract",
            language="chi_sim+eng",
            text_content="First OCR text",
            confidence_score=0.85,
            processing_time=1.5,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        ocr1 = crud.ocr_result.create_with_processor(db=db, obj_in=ocr1_in, processor_id=user.id)
        
        # 手动设置不同的时间戳
        from datetime import datetime, timedelta
        import time
        time.sleep(0.1)  # 确保时间差异
        
        ocr2_in = schemas.OCRResultCreate(
            filename="second_doc.pdf",
            engine="tesseract",
            language="chi_sim+eng",
            text_content="Second OCR text",
            confidence_score=0.90,
            processing_time=2.0,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        ocr2 = crud.ocr_result.create_with_processor(db=db, obj_in=ocr2_in, processor_id=user.id)
        
        # 手动更新第二个OCR的时间戳以确保它更新
        from datetime import timezone
        ocr2.created_at = datetime.now(timezone.utc) + timedelta(seconds=1)
        db.add(ocr2)
        db.commit()
        db.refresh(ocr2)
        
        latest_ocr = crud.ocr_result.get_latest_by_document(db=db, document_id=document.id)
        
        assert latest_ocr is not None
        assert latest_ocr.id == ocr2.id  # 应该是最新的
        assert latest_ocr.document_id == document.id

    def test_get_by_confidence_range(self, db: Session) -> None:
        """测试按置信度范围获取OCR结果"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 创建不同置信度的OCR结果
        high_confidence_ocr = schemas.OCRResultCreate(
            filename="high_confidence_document.pdf",
            engine="tesseract",
            language="en",
            text_content="High confidence text",
            confidence_score=0.95,
            processing_time=1.0,
            word_count=3,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        high_ocr = crud.ocr_result.create_with_processor(db=db, obj_in=high_confidence_ocr, processor_id=user.id)
        
        low_confidence_ocr = schemas.OCRResultCreate(
            filename="low_confidence_document.pdf",
            engine="tesseract",
            language="en",
            text_content="Low confidence text",
            confidence_score=0.30,
            processing_time=1.5,
            word_count=3,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        low_ocr = crud.ocr_result.create_with_processor(db=db, obj_in=low_confidence_ocr, processor_id=user.id)
        
        # 获取高置信度结果 (>= 0.9)
        high_confidence_results = crud.ocr_result.get_by_confidence_range(
            db=db, min_confidence=0.9, max_confidence=1.0
        )
        
        # 获取低置信度结果 (0.2 - 0.4)
        low_confidence_results = crud.ocr_result.get_by_confidence_range(
            db=db, min_confidence=0.2, max_confidence=0.4
        )
        
        # 验证结果
        high_ids = [ocr.id for ocr in high_confidence_results]
        low_ids = [ocr.id for ocr in low_confidence_results]
        
        assert high_ocr.id in high_ids
        assert low_ocr.id in low_ids
        assert low_ocr.id not in high_ids
        assert high_ocr.id not in low_ids

    def test_search_text(self, db: Session) -> None:
        """测试搜索OCR文本"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 创建包含特定文本的OCR结果
        search_term = "specific_search_term"
        ocr_in = schemas.OCRResultCreate(
            filename="search_test_document.pdf",
            engine="tesseract",
            language="en",
            text_content=f"This text contains {search_term} for testing",
            confidence_score=0.9,
            processing_time=1.0,
            word_count=7,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        ocr_result = crud.ocr_result.create_with_processor(db=db, obj_in=ocr_in, processor_id=user.id)
        
        # 创建不包含搜索词的OCR结果
        other_ocr_in = schemas.OCRResultCreate(
            filename="other_test_document.pdf",
            engine="tesseract",
            language="en",
            text_content="This is different text without the term",
            confidence_score=0.9,
            processing_time=1.0,
            word_count=8,
            metadata="{}",
            document_id=document.id,
            status="completed"
        )
        crud.ocr_result.create_with_processor(db=db, obj_in=other_ocr_in, processor_id=user.id)
        
        # 搜索文本
        search_results = crud.ocr_result.search_text(db=db, query=search_term)
        
        # 验证搜索结果
        found_ocr = None
        for ocr in search_results:
            if ocr.id == ocr_result.id:
                found_ocr = ocr
                break
        
        assert found_ocr is not None
        assert search_term in found_ocr.extracted_text

    def test_get_statistics(self, db: Session) -> None:
        """测试获取OCR统计信息"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 创建多个OCR结果
        for i in range(3):
            ocr_in = schemas.OCRResultCreate(
                filename=f"stats_test_doc_{i}.pdf",
                engine="tesseract",
                language="chi_sim+eng",
                text_content=f"Statistics test text {i}",
                confidence_score=0.8 + (i * 0.05),
                processing_time=1.0 + (i * 0.5),
                metadata="{}",
                document_id=document.id,
                status="completed"
            )
            crud.ocr_result.create_with_processor(db=db, obj_in=ocr_in, processor_id=user.id)
        
        stats = crud.ocr_result.get_statistics(db=db)
        
        assert "total_results" in stats
        assert "average_confidence" in stats
        assert "average_processing_time" in stats
        assert stats["total_results"] >= 3
        assert 0 <= stats["average_confidence"] <= 1
        assert stats["average_processing_time"] >= 0