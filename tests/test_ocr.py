import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.document import Document
from app.models.project import Project


class TestOCR:
    """OCR功能测试"""
    
    def test_get_ocr_statistics_without_auth(self, client: TestClient):
        """测试无认证获取OCR统计"""
        response = client.get("/api/v1/ocr/statistics")
        assert response.status_code == 401
    
    def test_get_ocr_statistics_with_auth(self, client: TestClient, auth_headers):
        """测试有认证获取OCR统计"""
        response = client.get("/api/v1/ocr/statistics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "data" in data
        assert data["code"] == 200
    
    def test_get_ocr_statistics_with_project_filter(self, client: TestClient, auth_headers, test_project):
        """测试按项目筛选OCR统计"""
        response = client.get(
            f"/api/v1/ocr/statistics?project_id={test_project.id}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["code"] == 200
    
    def test_get_ocr_status_nonexistent_document(self, client: TestClient, auth_headers):
        """测试获取不存在文档的OCR状态"""
        response = client.get("/api/v1/ocr/status/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()
    
    def test_get_ocr_text_nonexistent_document(self, client: TestClient, auth_headers):
        """测试获取不存在文档的OCR文本"""
        response = client.get("/api/v1/ocr/text/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()
    
    def test_process_ocr_nonexistent_document(self, client: TestClient, auth_headers):
        """测试处理不存在文档的OCR"""
        response = client.post("/api/v1/ocr/process/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()
    
    def test_batch_process_empty_list(self, client: TestClient, auth_headers):
        """测试批量处理空文档列表"""
        response = client.post(
            "/api/v1/ocr/batch-process", 
            json=[], 
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "empty" in response.json()["message"].lower()
    
    def test_batch_process_too_many_documents(self, client: TestClient, auth_headers):
        """测试批量处理过多文档"""
        document_ids = list(range(1, 52))  # 51个文档ID
        response = client.post(
            "/api/v1/ocr/batch-process", 
            json=document_ids, 
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "50" in response.json()["message"]
    
    @patch('app.services.document_service.document_service.process_document_ocr')
    def test_process_ocr_success_mock(self, mock_process, client: TestClient, auth_headers, db, test_project):
        """测试OCR处理成功（使用模拟）"""
        # 创建一个模拟文档
        from app.models.document import Document
        document = Document(
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/test/test.pdf",
            file_size=1024,
            file_type="pdf",
            document_category="技术文档",
            project_id=test_project.id,
            uploader_id=1,
            is_ocr_processed=False
        )
        db.add(document)
        db.commit()
        
        # 模拟OCR处理结果
        mock_process.return_value = {
            'success': True,
            'text': '测试文本内容',
            'engine': 'PaddleOCR',
            'confidence': 0.95,
            'is_handwritten': False,
            'pages_processed': 1
        }
        
        response = client.post("/api/v1/ocr/process/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "OCR processing completed" in data["message"]
        assert data["data"]["text"] == "测试文本内容"
    
    @patch('app.services.document_service.document_service.batch_process_ocr')
    def test_batch_process_success_mock(self, mock_batch, client: TestClient, auth_headers):
        """测试批量OCR处理成功（使用模拟）"""
        # 模拟批量处理结果
        mock_batch.return_value = {
            'processed': 3,
            'failed': 1,
            'skipped': 1,
            'total': 5,
            'results': []
        }
        
        document_ids = [1, 2, 3, 4, 5]
        response = client.post(
            "/api/v1/ocr/batch-process", 
            json=document_ids, 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "Batch processing completed" in data["message"]
        assert data["data"]["processed"] == 3
        assert data["data"]["failed"] == 1
    
    def test_ocr_endpoints_require_auth(self, client: TestClient):
        """测试所有OCR端点都需要认证"""
        endpoints = [
            "/api/v1/ocr/process/1",
            "/api/v1/ocr/status/1",
            "/api/v1/ocr/text/1",
            "/api/v1/ocr/statistics"
        ]
        
        for endpoint in endpoints:
            if "process" in endpoint:
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
    
    def test_get_ocr_status_success(self, client: TestClient, auth_headers, db, test_project):
        """测试获取OCR状态成功"""
        # 创建已处理的文档
        document = Document(
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            file_type="image",
            document_category="test",
            project_id=test_project.id,
            uploader_id=1,
            is_ocr_processed=True,
            ocr_engine="tesseract",
            ocr_confidence=95,
            is_handwritten=False,
            ocr_text="测试文本",
            processed_at=datetime.now()
        )
        db.add(document)
        db.commit()
        
        response = client.get(
            f"/api/v1/ocr/status/{document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["document_id"] == document.id
        assert data["data"]["filename"] == "test.jpg"
        assert data["data"]["is_ocr_processed"] == True
        assert data["data"]["ocr_engine"] == "tesseract"
        assert data["data"]["ocr_confidence"] == 95
        assert data["data"]["is_handwritten"] == False
        assert data["data"]["ocr_text_length"] == 4
        assert data["data"]["processed_at"] is not None
    
    def test_get_ocr_text_success(self, client: TestClient, auth_headers, db, test_project):
        """测试获取OCR文本成功"""
        # 创建已处理的文档
        document = Document(
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            file_type="image",
            document_category="test",
            project_id=test_project.id,
            uploader_id=1,
            is_ocr_processed=True,
            ocr_engine="tesseract",
            ocr_confidence=95,
            is_handwritten=False,
            ocr_text="这是测试文本内容",
            processed_at=datetime.now()
        )
        db.add(document)
        db.commit()
        
        response = client.get(
            f"/api/v1/ocr/text/{document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["document_id"] == document.id
        assert data["data"]["filename"] == "test.jpg"
        assert data["data"]["ocr_text"] == "这是测试文本内容"
        assert data["data"]["ocr_engine"] == "tesseract"
        assert data["data"]["ocr_confidence"] == 95
        assert data["data"]["is_handwritten"] == False
        assert data["data"]["processed_at"] is not None
    
    def test_get_ocr_text_not_processed(self, client: TestClient, auth_headers, db, test_project):
        """测试获取未处理文档的OCR文本"""
        # 创建未处理的文档
        document = Document(
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            file_type="image",
            document_category="test",
            project_id=test_project.id,
            uploader_id=1,
            is_ocr_processed=False
        )
        db.add(document)
        db.commit()
        
        response = client.get(
            f"/api/v1/ocr/text/{document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        response_data = response.json()
        # 检查错误信息是否在message或detail字段中
        error_message = response_data.get("message", response_data.get("detail", ""))
        assert "Document has not been processed with OCR yet" in error_message
    
    @patch('app.services.document_service.document_service.get_ocr_statistics')
    def test_get_ocr_statistics_error(self, mock_get_stats, client: TestClient, auth_headers):
        """测试获取OCR统计信息错误"""
        mock_get_stats.side_effect = Exception("Database error")
        
        response = client.get(
            "/api/v1/ocr/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 500
        response_data = response.json()
        error_message = response_data.get("message", response_data.get("detail", ""))
        assert "Failed to retrieve OCR statistics" in error_message
    
    @patch('app.services.document_service.document_service.process_document_ocr')
    def test_process_document_ocr_exception(self, mock_process, client: TestClient, auth_headers, db, test_project):
        """测试处理文档OCR异常"""
        # 创建未处理的文档
        document = Document(
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            file_type="image",
            document_category="test",
            project_id=test_project.id,
            uploader_id=1,
            is_ocr_processed=False
        )
        db.add(document)
        db.commit()
        
        mock_process.side_effect = Exception("OCR service error")
        
        response = client.post(
            f"/api/v1/ocr/process/{document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 500
        response_data = response.json()
        error_message = response_data.get("message", response_data.get("detail", ""))
        assert "OCR processing failed: OCR service error" in error_message
    
    @patch('app.services.document_service.document_service.batch_process_ocr')
    def test_batch_process_ocr_exception(self, mock_batch_process, client: TestClient, auth_headers):
        """测试批量处理OCR异常"""
        mock_batch_process.side_effect = Exception("Batch processing error")
        
        response = client.post(
            "/api/v1/ocr/batch-process",
            json=[1, 2],
            headers=auth_headers
        )
        
        assert response.status_code == 500
        response_data = response.json()
        error_message = response_data.get("message", response_data.get("detail", ""))
        assert "Batch OCR processing failed: Batch processing error" in error_message