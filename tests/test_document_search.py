import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from tests.utils.user import create_random_user
from tests.utils.project import create_random_project
from tests.utils.document import create_random_document


class TestDocumentSearch:
    """文档搜索API测试"""
    
    def test_search_documents_success(self, client: TestClient, db: Session, auth_user, auth_headers):
        """测试文档搜索成功"""
        # 使用认证用户创建测试数据
        project = create_random_project(db, owner_id=auth_user.id)
        
        # 创建测试文档
        doc1 = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
        doc1.filename = "test_search_document.pdf"
        doc1.summary = "This is a test document for searching"
        doc1.extracted_text = "Important content about testing and validation"
        db.commit()
        
        doc2 = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
        doc2.filename = "another_file.docx"
        doc2.summary = "Different content"
        doc2.extracted_text = "Some other content without the keyword"
        db.commit()
        
        # 执行搜索
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "documents" in data["data"]
        assert data["data"]["total_results"] >= 1
        assert data["data"]["query"] == "test"
        
        # 验证搜索结果包含匹配的文档
        documents = data["data"]["documents"]
        found_doc = next((doc for doc in documents if doc["id"] == doc1.id), None)
        assert found_doc is not None
    
    def test_search_documents_with_project_filter(self, client: TestClient, db: Session, auth_user, auth_headers):
        """测试在指定项目中搜索文档"""
        project1 = create_random_project(db, owner_id=auth_user.id)
        project2 = create_random_project(db, owner_id=auth_user.id)
        
        # 在不同项目中创建文档
        doc1 = create_random_document(db, project_id=project1.id, owner_id=auth_user.id)
        doc1.filename = "project1_test.pdf"
        doc1.summary = "Test document in project 1"
        db.commit()
        
        doc2 = create_random_document(db, project_id=project2.id, owner_id=auth_user.id)
        doc2.filename = "project2_test.pdf"
        doc2.summary = "Test document in project 2"
        db.commit()
        
        # 在project1中搜索
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=test&project_id={project1.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        documents = data["data"]["documents"]
        
        # 验证只返回project1中的文档
        for doc in documents:
            assert doc["project_id"] == project1.id
    
    def test_search_documents_pagination(self, client: TestClient, db: Session, auth_user, auth_headers):
        """测试搜索结果分页"""
        project = create_random_project(db, owner_id=auth_user.id)
        
        # 创建多个测试文档
        for i in range(5):
            doc = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
            doc.filename = f"search_test_{i}.pdf"
            doc.summary = f"Search test document {i}"
            db.commit()
        
        # 测试分页
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=search&skip=0&limit=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["documents"]) <= 3
        assert data["data"]["skip"] == 0
        assert data["data"]["limit"] == 3
        assert data["data"]["total_results"] >= 5
    
    def test_search_documents_empty_query(self, client: TestClient, auth_headers):
        """测试空搜索查询"""
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Search query must be at least 2 characters long" in data["error"]["message"]
    
    def test_search_documents_short_query(self, client: TestClient, auth_headers):
        """测试过短的搜索查询"""
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=a",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Search query must be at least 2 characters long" in data["error"]["message"]
    
    def test_search_documents_nonexistent_project(self, client: TestClient, auth_headers):
        """测试在不存在的项目中搜索"""
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=test&project_id=99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Project not found" in data["error"]["message"]
    
    def test_search_documents_no_results(self, client: TestClient, db: Session, auth_user, auth_headers):
        """测试搜索无结果"""
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=nonexistent_keyword_xyz",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total_results"] == 0
        assert len(data["data"]["documents"]) == 0
    
    def test_search_documents_match_score(self, client: TestClient, db: Session, auth_user, auth_headers):
        """测试搜索结果匹配度评分"""
        project = create_random_project(db, owner_id=auth_user.id)
        
        # 创建不同匹配度的文档
        # 高匹配度：文件名匹配
        doc1 = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
        doc1.filename = "important_test_file.pdf"
        doc1.summary = "Some content"
        db.commit()
        
        # 中匹配度：摘要匹配
        doc2 = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
        doc2.filename = "document.pdf"
        doc2.summary = "This is an important test document"
        db.commit()
        
        # 低匹配度：文本内容匹配
        doc3 = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
        doc3.filename = "document2.pdf"
        doc3.summary = "Regular document"
        doc3.extracted_text = "Some text with important keyword"
        db.commit()
        
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=important",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        documents = data["data"]["documents"]
        
        # 验证返回了文档结果
        assert len(documents) > 0
    
    def test_search_documents_text_preview(self, client: TestClient, db: Session, auth_user, auth_headers):
        """测试搜索结果文本预览"""
        project = create_random_project(db, owner_id=auth_user.id)
        
        # 创建包含长文本的文档
        doc = create_random_document(db, project_id=project.id, owner_id=auth_user.id)
        doc.filename = "test_preview.pdf"
        doc.extracted_text = "This is a test document. " * 50  # 创建长文本
        db.commit()
        
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        documents = data["data"]["documents"]
        
        found_doc = next((d for d in documents if d["id"] == doc.id), None)
        assert found_doc is not None
        assert "filename" in found_doc
        assert "file_size" in found_doc
        assert "file_type" in found_doc
    
    def test_search_documents_unauthorized(self, client: TestClient):
        """测试未授权访问搜索API"""
        response = client.get(
            f"{settings.API_V1_STR}/documents/search?q=test"
        )
        
        assert response.status_code == 401