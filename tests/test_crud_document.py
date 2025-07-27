import pytest
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core.config import settings
from tests.utils.utils import random_lower_string
from tests.utils.user import create_random_user
from tests.utils.project import create_random_project
from tests.utils.document import create_random_document


class TestCRUDDocument:
    def test_create_document(self, db: Session) -> None:
        """测试创建文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        filename = f"{random_lower_string()}.pdf"
        original_filename = f"original_{filename}"
        file_path = f"/uploads/{filename}"
        
        document_in = schemas.DocumentCreate(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=1024,
            file_type="pdf",
            document_type="contract",
            document_category="procurement",
            project_id=project.id
        )
        
        document = crud.document.create_with_uploader(
            db=db, obj_in=document_in, owner_id=user.id
        )
        
        assert document.filename == filename
        assert document.original_filename == original_filename
        assert document.file_path == file_path
        assert document.project_id == project.id
        assert document.uploader_id == user.id
        assert document.status == "uploaded"

    def test_get_document(self, db: Session) -> None:
        """测试获取文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        stored_document = crud.document.get(db=db, id=document.id)
        assert stored_document
        assert stored_document.id == document.id
        assert stored_document.filename == document.filename
        assert stored_document.uploader_id == user.id

    def test_update_document(self, db: Session) -> None:
        """测试更新文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        new_filename = f"{random_lower_string()}.pdf"
        new_document_type = "specification"
        
        document_update = schemas.DocumentUpdate(
            filename=new_filename,
            document_type=new_document_type
        )
        
        updated_document = crud.document.update(
            db=db, db_obj=document, obj_in=document_update
        )
        
        assert updated_document.id == document.id
        assert updated_document.filename == new_filename
        assert updated_document.document_type == new_document_type
        assert updated_document.uploader_id == user.id

    def test_delete_document(self, db: Session) -> None:
        """测试删除文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        document_id = document.id
        crud.document.remove(db=db, id=document_id)
        
        deleted_document = crud.document.get(db=db, id=document_id)
        assert deleted_document is None

    def test_get_multi_by_owner(self, db: Session) -> None:
        """测试按上传者获取多个文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建多个文档
        documents = []
        for _ in range(3):
            document = create_random_document(db, owner_id=user.id, project_id=project.id)
            documents.append(document)
        
        # 创建其他用户的文档
        other_user = create_random_user(db)
        other_project = create_random_project(db, owner_id=other_user.id)
        create_random_document(db, owner_id=other_user.id, project_id=other_project.id)
        
        stored_documents = crud.document.get_by_uploader(
            db=db, uploader_id=user.id
        )
        
        assert len(stored_documents) >= 3
        for document in stored_documents:
            assert document.uploader_id == user.id

    def test_get_by_project(self, db: Session) -> None:
        """测试按项目获取文档"""
        user = create_random_user(db)
        project1 = create_random_project(db, owner_id=user.id)
        project2 = create_random_project(db, owner_id=user.id)
        
        # 为project1创建文档
        documents_p1 = []
        for _ in range(2):
            document = create_random_document(db, owner_id=user.id, project_id=project1.id)
            documents_p1.append(document)
        
        # 为project2创建文档
        create_random_document(db, owner_id=user.id, project_id=project2.id)
        
        stored_documents = crud.document.get_by_project(
            db=db, project_id=project1.id
        )
        
        assert len(stored_documents) == 2
        for document in stored_documents:
            assert document.project_id == project1.id

    def test_get_by_status(self, db: Session) -> None:
        """测试按状态获取文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建不同状态的文档
        uploaded_doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 更新一个文档状态为processing
        processing_doc = create_random_document(db, owner_id=user.id, project_id=project.id)
        crud.document.update(
            db=db, 
            db_obj=processing_doc, 
            obj_in=schemas.DocumentUpdate()
        )
        # 手动设置状态
        processing_doc.status = "processing"
        db.commit()
        db.refresh(processing_doc)
        
        # 获取uploaded状态的文档
        uploaded_documents = crud.document.get_by_filters(
            db=db, filters={"status": "uploaded"}
        )
        
        # 获取processing状态的文档
        processing_documents = crud.document.get_by_filters(
            db=db, filters={"status": "processing"}
        )
        
        # 验证结果
        uploaded_ids = [doc.id for doc in uploaded_documents]
        processing_ids = [doc.id for doc in processing_documents]
        
        assert uploaded_doc.id in uploaded_ids
        assert processing_doc.id in processing_ids
        assert processing_doc.id not in uploaded_ids
        assert uploaded_doc.id not in processing_ids

    def test_update_status(self, db: Session) -> None:
        """测试更新文档状态"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        document = create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 初始状态应该是uploaded
        assert document.status == "uploaded"
        
        # 使用mark_as_processed方法更新状态
        updated_document = crud.document.mark_as_processed(
            db=db, document_id=document.id, processing_status="processed"
        )
        
        assert updated_document.is_processed == True
        assert updated_document.status == "processed"
        assert updated_document.id == document.id
        
        # 验证数据库中的状态也已更新
        stored_document = crud.document.get(db=db, id=document.id)
        assert stored_document.is_processed == True
        assert stored_document.status == "processed"

    def test_get_documents_with_pagination(self, db: Session) -> None:
        """测试分页获取文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建5个文档
        documents = []
        for i in range(5):
            document = create_random_document(db, owner_id=user.id, project_id=project.id)
            documents.append(document)
        
        # 测试分页
        page1 = crud.document.get_multi(db=db, skip=0, limit=3)
        page2 = crud.document.get_multi(db=db, skip=3, limit=3)
        
        assert len(page1) == 3
        assert len(page2) >= 2  # 可能包含其他测试创建的文档
        
        # 确保没有重复
        page1_ids = [doc.id for doc in page1]
        page2_ids = [doc.id for doc in page2]
        
        # 检查前3个文档不在第二页
        for doc_id in page1_ids:
            assert doc_id not in page2_ids

    def test_search_documents(self, db: Session) -> None:
        """测试搜索文档"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 创建具有特定文件名的文档
        search_term = "test_search_document"
        document_in = schemas.DocumentCreate(
            filename=f"{search_term}_file.pdf",
            original_filename=f"{search_term}_original.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            file_type="application/pdf",
            document_type="contract",
            document_category="technical",
            project_id=project.id
        )
        
        document = crud.document.create_with_uploader(
            db=db, obj_in=document_in, owner_id=user.id
        )
        
        # 创建其他文档
        create_random_document(db, owner_id=user.id, project_id=project.id)
        
        # 搜索文档
        search_results = crud.document.search_documents(
            db=db, query=search_term
        )
        
        # 验证搜索结果
        found_document = None
        for doc in search_results:
            if doc.id == document.id:
                found_document = doc
                break
        
        assert found_document is not None
        assert search_term in found_document.filename