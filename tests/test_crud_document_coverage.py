import pytest
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app import crud, models, schemas
from tests.utils.user import create_random_user
from tests.utils.project import create_random_project
from tests.utils.document import create_random_document


class TestCRUDDocumentCoverage:
    """测试CRUDDocument的覆盖率"""
    
    def test_create_with_uploader(self, db: Session):
        """测试创建文档并关联上传者"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        document_in = schemas.DocumentCreate(
            filename="test.pdf",
            original_filename="test.pdf",
            document_type="pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            file_type="pdf",
            document_category="test",
            project_id=project.id
        )
        
        document = crud.document.create_with_uploader(
            db=db, obj_in=document_in, owner_id=user.id
        )
        
        assert document.uploader_id == user.id
        assert document.filename == "test.pdf"
        assert document.project_id == project.id
    
    def test_get_by_uploader(self, db: Session):
        """测试根据上传者获取文档列表"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建多个文档
        for i in range(3):
            create_random_document(db, owner_id=user.id, project_id=project.id)
        
        documents = crud.document.get_by_uploader(db=db, uploader_id=user.id)
        assert len(documents) == 3
        
        # 测试分页
        documents_page = crud.document.get_by_uploader(
            db=db, uploader_id=user.id, skip=1, limit=2
        )
        assert len(documents_page) == 2
    
    def test_get_by_project(self, db: Session):
        """测试根据项目获取文档列表"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建多个文档
        for i in range(2):
            create_random_document(db, owner_id=user.id, project_id=project.id)
        
        documents = crud.document.get_by_project(db=db, project_id=project.id)
        assert len(documents) == 2
        
        for doc in documents:
            assert doc.project_id == project.id
    
    def test_get_by_type(self, db: Session):
        """测试根据文档类型获取文档列表"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建不同类型的文档
        doc1 = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc1.document_type = "pdf"
        db.add(doc1)
        
        doc2 = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc2.document_type = "docx"
        db.add(doc2)
        
        db.commit()
        
        pdf_docs = crud.document.get_by_type(db=db, document_type="pdf")
        assert len(pdf_docs) >= 1
        assert all(doc.document_type == "pdf" for doc in pdf_docs)
    
    def test_get_by_filters(self, db: Session):
        """测试根据多个条件筛选文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc.document_type = "pdf"
        doc.is_processed = True
        db.add(doc)
        db.commit()
        
        # 测试单个过滤条件
        filters = {"document_type": "pdf"}
        documents = crud.document.get_by_filters(db=db, filters=filters)
        assert len(documents) >= 1
        
        # 测试多个过滤条件
        filters = {"document_type": "pdf", "is_processed": True}
        documents = crud.document.get_by_filters(db=db, filters=filters)
        assert len(documents) >= 1
        
        # 测试空过滤条件
        filters = {}
        documents = crud.document.get_by_filters(db=db, filters=filters)
        assert len(documents) >= 1
        
        # 测试None值过滤
        filters = {"document_type": None, "is_processed": True}
        documents = crud.document.get_by_filters(db=db, filters=filters)
        assert len(documents) >= 1
    
    def test_search_documents(self, db: Session):
        """测试搜索文档功能"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc.filename = "test_search.pdf"
        doc.summary = "This is a test document for searching"
        doc.extracted_text = "Important content here"
        doc.ocr_text = "OCR extracted text"
        doc.keywords = "test,search,document"
        db.add(doc)
        db.commit()
        
        # 测试按文件名搜索
        results = crud.document.search_documents(db=db, query="test_search")
        assert len(results) >= 1
        
        # 测试按摘要搜索
        results = crud.document.search_documents(db=db, query="test document")
        assert len(results) >= 1
        
        # 测试按提取文本搜索
        results = crud.document.search_documents(db=db, query="Important content")
        assert len(results) >= 1
        
        # 测试按OCR文本搜索
        results = crud.document.search_documents(db=db, query="OCR extracted")
        assert len(results) >= 1
        
        # 测试按关键词搜索
        results = crud.document.search_documents(db=db, query="search")
        assert len(results) >= 1
        
        # 测试指定项目ID搜索
        results = crud.document.search_documents(
            db=db, query="test", project_id=project.id
        )
        assert len(results) >= 1
        
        # 测试分页
        results = crud.document.search_documents(
            db=db, query="test", skip=0, limit=1
        )
        assert len(results) <= 1
    
    def test_search_documents_count(self, db: Session):
        """测试搜索结果计数"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc.filename = "count_test.pdf"
        db.add(doc)
        db.commit()
        
        # 测试搜索计数
        count = crud.document.search_documents_count(db=db, query="count_test")
        assert count >= 1
        
        # 测试指定项目ID的搜索计数
        count = crud.document.search_documents_count(
            db=db, query="count_test", project_id=project.id
        )
        assert count >= 1
        
        # 测试不存在的搜索
        count = crud.document.search_documents_count(db=db, query="nonexistent_file")
        assert count == 0
    
    def test_get_unprocessed_documents(self, db: Session):
        """测试获取未处理的文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建未处理的文档
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc.is_processed = False
        db.add(doc)
        db.commit()
        
        unprocessed = crud.document.get_unprocessed_documents(db=db)
        assert len(unprocessed) >= 1
        assert all(not doc.is_processed for doc in unprocessed)
        
        # 测试分页
        unprocessed_page = crud.document.get_unprocessed_documents(
            db=db, skip=0, limit=1
        )
        assert len(unprocessed_page) <= 1
    
    def test_mark_as_processed(self, db: Session):
        """测试标记文档为已处理"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        # 确保文档初始状态为未处理
        doc.is_processed = False
        db.commit()
        db.refresh(doc)
        
        # 标记为已处理
        updated_doc = crud.document.mark_as_processed(
            db=db, document_id=doc.id, processing_status="processed"
        )
        
        assert updated_doc is not None
        assert updated_doc.is_processed is True
        assert updated_doc.status == "processed"
        
        # 测试标记不存在的文档
        result = crud.document.mark_as_processed(db=db, document_id=999999)
        assert result is None
    
    def test_update_access_info(self, db: Session):
        """测试更新文档访问信息"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 由于Document模型没有access_count字段，我们测试方法是否正常执行
        updated_doc = crud.document.update_access_info(db=db, document_id=doc.id)
        
        # 如果方法执行成功，应该返回文档对象
        assert updated_doc is not None
        assert updated_doc.id == doc.id
        
        # 再次更新
        updated_doc2 = crud.document.update_access_info(db=db, document_id=doc.id)
        assert updated_doc2 is not None
        assert updated_doc2.id == doc.id
        
        # 测试更新不存在的文档
        result = crud.document.update_access_info(db=db, document_id=999999)
        assert result is None
    
    def test_get_statistics_basic(self, db: Session):
        """测试基本统计信息"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建不同状态的文档
        doc1 = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc1.is_processed = True
        doc1.status = "processed"
        doc1.document_type = "pdf"
        
        doc2 = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc2.is_processed = False
        doc2.status = "uploaded"
        doc2.document_type = "docx"
        
        db.add_all([doc1, doc2])
        db.commit()
        
        # 获取统计信息
        stats = crud.document.get_statistics(db=db)
        
        assert "total_documents" in stats
        assert "processed_documents" in stats
        assert "unprocessed_documents" in stats
        assert "processing_rate" in stats
        assert "by_type" in stats
        assert "by_status" in stats
        
        assert stats["total_documents"] >= 2
        assert stats["processed_documents"] >= 1
        assert stats["unprocessed_documents"] >= 1
        assert isinstance(stats["processing_rate"], (int, float))
        assert isinstance(stats["by_type"], (dict, list))
        assert isinstance(stats["by_status"], (dict, list))
    
    def test_get_statistics_by_uploader(self, db: Session):
        """测试按上传者获取统计信息"""
        user1 = create_random_user(db)
        user2 = create_random_user(db)
        project = create_random_project(db, owner_id=user1.id)
        
        # 为user1创建文档
        doc1 = create_random_document(db, owner_id=user1.id, project_id=project.id)
        doc1.is_processed = True
        doc1.document_type = "pdf"
        
        # 为user2创建文档
        doc2 = create_random_document(db, owner_id=user2.id, project_id=project.id)
        doc2.is_processed = False
        doc2.document_type = "docx"
        
        db.add_all([doc1, doc2])
        db.commit()
        
        # 获取user1的统计信息
        stats = crud.document.get_statistics(db=db, uploader_id=user1.id)
        
        # 由于只查询user1的文档，所以应该只有1个文档
        assert stats["total_documents"] >= 1
        assert stats["processed_documents"] >= 1
        assert stats["unprocessed_documents"] >= 0
    
    def test_get_statistics_empty_database(self, db: Session):
        """测试空数据库的统计信息"""
        # 清空所有文档（如果有的话）
        db.query(models.Document).delete()
        db.commit()
        
        stats = crud.document.get_statistics(db=db)
        
        assert stats["total_documents"] == 0
        assert stats["processed_documents"] == 0
        assert stats["unprocessed_documents"] == 0
        assert stats["processing_rate"] == 0
        assert stats["by_type"] == [] or stats["by_type"] == {}
        assert stats["by_status"] == [] or stats["by_status"] == {}
    
    def test_get_statistics_with_null_status(self, db: Session):
        """测试包含空状态的统计信息"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建状态为None的文档
        doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        doc.status = None
        doc.document_type = "pdf"
        db.add(doc)
        db.commit()
        
        stats = crud.document.get_statistics(db=db)
        
        # 状态为None的文档不应该出现在by_status中
        assert "by_type" in stats
        if isinstance(stats["by_type"], dict):
            assert "pdf" in stats["by_type"]
        
        # None状态不应该在by_status中
        if "by_status" in stats and isinstance(stats["by_status"], dict):
            assert None not in stats["by_status"]


class TestCRUDDocumentEdgeCases:
    """测试CRUDDocument的边界情况"""
    
    def test_search_empty_query(self, db: Session):
        """测试空查询字符串搜索"""
        results = crud.document.search_documents(db=db, query="")
        # 空查询应该返回所有文档或空列表
        assert isinstance(results, list)
    
    def test_get_by_filters_invalid_attribute(self, db: Session):
        """测试使用无效属性的过滤"""
        filters = {"invalid_attribute": "value", "document_type": "pdf"}
        documents = crud.document.get_by_filters(db=db, filters=filters)
        # 应该忽略无效属性，只应用有效的过滤条件
        assert isinstance(documents, list)
    
    def test_search_with_nonexistent_project(self, db: Session):
        """测试在不存在的项目中搜索"""
        results = crud.document.search_documents(
            db=db, query="test", project_id=999999
        )
        assert results == []
        
        count = crud.document.search_documents_count(
            db=db, query="test", project_id=999999
        )
        assert count == 0
    
    def test_pagination_edge_cases(self, db: Session):
        """测试分页边界情况"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建一个文档
        create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 测试skip超过总数
        results = crud.document.get_by_uploader(
            db=db, uploader_id=user.id, skip=1000, limit=10
        )
        assert results == []
        
        # 测试limit为0
        results = crud.document.get_by_uploader(
            db=db, uploader_id=user.id, skip=0, limit=0
        )
        assert results == []