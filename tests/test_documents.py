import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os
from io import BytesIO


class TestDocuments:
    """文档管理API测试"""
    
    def test_upload_document_success(self, client: TestClient, auth_headers, test_project):
        """测试成功上传文档"""
        # 创建测试文件
        test_content = b"This is a test document content"
        test_file = BytesIO(test_content)
        
        files = {
            "file": ("test_document.txt", test_file, "text/plain")
        }
        data = {
            "document_category": "测试文档",
            "document_type": "文本文件",
            "summary": "这是一个测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/upload/{test_project.id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["message"] == "Document uploaded successfully"
        assert "data" in result
        assert "document_id" in result["data"]
        assert result["data"]["filename"] == "test_document.txt"
        assert result["data"]["document_category"] == "测试文档"
    
    def test_upload_document_without_auth(self, client: TestClient, test_project):
        """测试无认证上传文档"""
        test_content = b"This is a test document content"
        test_file = BytesIO(test_content)
        
        files = {
            "file": ("test_document.txt", test_file, "text/plain")
        }
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/upload/{test_project.id}",
            files=files,
            data=data
        )
        
        assert response.status_code == 401
    
    def test_upload_document_invalid_project(self, client: TestClient, auth_headers):
        """测试上传文档到不存在的项目"""
        test_content = b"This is a test document content"
        test_file = BytesIO(test_content)
        
        files = {
            "file": ("test_document.txt", test_file, "text/plain")
        }
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            "/api/v1/documents/upload/99999",  # 不存在的项目ID
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Project not found" in result["error"]["message"]
    
    def test_upload_unsupported_file_type(self, client: TestClient, auth_headers, test_project):
        """测试上传不支持的文件类型"""
        test_content = b"This is a test file with unsupported extension"
        test_file = BytesIO(test_content)
        
        files = {
            "file": ("test_document.xyz", test_file, "application/octet-stream")
        }
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/upload/{test_project.id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "Unsupported file type" in result["error"]["message"]
    
    def test_get_project_documents(self, client: TestClient, auth_headers, test_project, test_document):
        """测试获取项目文档列表"""
        response = client.get(
            f"/api/v1/documents/project/{test_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        assert "documents" in result["data"]
        assert "total" in result["data"]
        assert len(result["data"]["documents"]) >= 1
        
        # 检查文档信息
        document = result["data"]["documents"][0]
        assert "id" in document
        assert "filename" in document
        assert "document_category" in document
    
    def test_get_project_documents_with_pagination(self, client: TestClient, auth_headers, test_project):
        """测试分页获取项目文档"""
        response = client.get(
            f"/api/v1/documents/project/{test_project.id}?skip=0&limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["skip"] == 0
        assert result["data"]["limit"] == 5
    
    def test_get_project_documents_with_category_filter(self, client: TestClient, auth_headers, test_project):
        """测试按类别筛选项目文档"""
        response = client.get(
            f"/api/v1/documents/project/{test_project.id}?document_category=测试文档",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
    
    def test_get_project_documents_invalid_project(self, client: TestClient, auth_headers):
        """测试获取不存在项目的文档列表"""
        response = client.get(
            "/api/v1/documents/project/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Project not found" in result["error"]["message"]
    
    def test_get_document_detail(self, client: TestClient, auth_headers, test_document):
        """测试获取文档详细信息"""
        response = client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        assert result["data"]["id"] == test_document.id
        assert result["data"]["filename"] == test_document.filename
    
    def test_get_document_detail_not_found(self, client: TestClient, auth_headers):
        """测试获取不存在文档的详细信息"""
        response = client.get(
            "/api/v1/documents/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Document not found" in result["error"]["message"]
    
    def test_update_document(self, client: TestClient, auth_headers, test_document):
        """测试更新文档信息"""
        update_data = {
            "document_category": "更新后的类别",
            "document_type": "更新后的类型",
            "summary": "更新后的描述"
        }
        
        response = client.put(
            f"/api/v1/documents/{test_document.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["document_category"] == "更新后的类别"
        assert result["data"]["document_type"] == "更新后的类型"
        assert result["data"]["summary"] == "更新后的描述"
    
    def test_update_document_not_found(self, client: TestClient, auth_headers):
        """测试更新不存在的文档"""
        update_data = {
            "document_category": "新类别"
        }
        
        response = client.put(
            "/api/v1/documents/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Document not found" in result["error"]["message"]
    
    def test_delete_document(self, client: TestClient, auth_headers, test_document):
        """测试删除文档"""
        response = client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["document_id"] == test_document.id
        
        # 验证文档已被删除
        get_response = client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_delete_document_not_found(self, client: TestClient, auth_headers):
        """测试删除不存在的文档"""
        response = client.delete(
            "/api/v1/documents/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Document not found" in result["error"]["message"]
    
    def test_get_project_documents_without_auth(self, client: TestClient, test_project):
        """测试无认证获取项目文档列表"""
        response = client.get(f"/api/v1/documents/project/{test_project.id}")
        assert response.status_code == 401
    
    def test_get_document_detail_without_auth(self, client: TestClient, test_document):
        """测试无认证获取文档详细信息"""
        response = client.get(f"/api/v1/documents/{test_document.id}")
        assert response.status_code == 401
    
    def test_update_document_without_auth(self, client: TestClient, test_document):
        """测试无认证更新文档"""
        update_data = {"document_category": "新类别"}
        response = client.put(f"/api/v1/documents/{test_document.id}", json=update_data)
        assert response.status_code == 401
    
    def test_delete_document_without_auth(self, client: TestClient, test_document):
        """测试无认证删除文档"""
        response = client.delete(f"/api/v1/documents/{test_document.id}")
        assert response.status_code == 401