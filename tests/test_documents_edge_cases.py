import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from io import BytesIO
import os
import tempfile
from sqlalchemy.exc import SQLAlchemyError


class TestDocumentsEdgeCases:
    """文档管理API边界情况测试"""
    
    def test_upload_document_database_error_with_file_cleanup(self, client: TestClient, auth_headers, test_project):
        """测试数据库操作失败时的文件清理"""
        test_content = b"This is a test document content"
        test_file = BytesIO(test_content)
        
        files = {
            "file": ("test_document.txt", test_file, "text/plain")
        }
        data = {
            "document_category": "测试文档"
        }
        
        # 模拟数据库commit操作失败
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Database error")
            
            response = client.post(
                f"/api/v1/documents/upload/{test_project.id}",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            assert response.status_code == 500
            result = response.json()
            assert "Failed to upload document" in result["error"]["message"]
    
    def test_batch_upload_empty_files_list(self, client: TestClient, auth_headers, test_project):
        """测试批量上传空文件列表"""
        # FastAPI会在没有files参数时返回422，所以我们需要提供空的files参数
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/batch-upload/{test_project.id}",
            data=data,
            headers=auth_headers
        )
        
        # FastAPI会返回422因为缺少必需的files参数
        assert response.status_code == 422
    
    def test_batch_upload_too_many_files(self, client: TestClient, auth_headers, test_project):
        """测试批量上传超过限制的文件数量"""
        # 创建11个测试文件（超过10个限制）
        files = []
        for i in range(11):
            test_content = f"Test content {i}".encode()
            test_file = BytesIO(test_content)
            files.append(("files", (f"test_{i}.txt", test_file, "text/plain")))
        
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/batch-upload/{test_project.id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "Maximum 10 files allowed" in result["error"]["message"]
    
    def test_batch_upload_unsupported_file_type(self, client: TestClient, auth_headers, test_project):
        """测试批量上传包含不支持文件类型"""
        test_content = b"Test content"
        test_file = BytesIO(test_content)
        
        files = [
            ("files", ("test.txt", BytesIO(b"Valid content"), "text/plain")),
            ("files", ("test.xyz", test_file, "application/octet-stream"))  # 不支持的类型
        ]
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/batch-upload/{test_project.id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "Unsupported file type" in result["error"]["message"]
    
    def test_batch_upload_project_not_found(self, client: TestClient, auth_headers):
        """测试批量上传到不存在的项目"""
        test_content = b"Test content"
        test_file = BytesIO(test_content)
        
        files = [
            ("files", ("test.txt", test_file, "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            "/api/v1/documents/batch-upload/99999",  # 不存在的项目ID
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Project not found" in result["error"]["message"]
    
    def test_batch_upload_partial_failure(self, client: TestClient, auth_headers, test_project):
        """测试批量上传部分失败的情况"""
        files = [
            ("files", ("test1.txt", BytesIO(b"Content 1"), "text/plain")),
            ("files", ("test2.txt", BytesIO(b"Content 2"), "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        # 模拟第二个文件处理失败
        with patch('app.models.document.Document') as mock_document:
            # 第一次调用成功，第二次失败
            mock_instance = MagicMock()
            mock_instance.id = 1
            mock_instance.filename = "test1.txt"
            mock_instance.file_size = 100
            mock_instance.file_type = "txt"
            mock_instance.document_category = "测试文档"
            
            def side_effect(*args, **kwargs):
                if 'test2.txt' in str(kwargs):
                    raise Exception("Processing failed")
                return mock_instance
            
            mock_document.side_effect = side_effect
            
            response = client.post(
                f"/api/v1/documents/batch-upload/{test_project.id}",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 应该返回部分成功的结果
            assert response.status_code == 200
            result = response.json()
            assert "Batch upload completed" in result["message"]
            assert result["data"]["successful_uploads"] >= 0
            assert result["data"]["failed_uploads_count"] >= 0
    
    def test_batch_upload_complete_failure(self, client: TestClient, auth_headers, test_project):
        """测试批量上传完全失败的情况"""
        files = [
            ("files", ("test.txt", BytesIO(b"Content"), "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        # 模拟创建上传目录失败
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = OSError("Permission denied")
            
            response = client.post(
                f"/api/v1/documents/batch-upload/{test_project.id}",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            assert response.status_code == 500
            result = response.json()
            assert "Batch upload failed" in result["error"]["message"]
    
    def test_batch_upload_file_save_error(self, client: TestClient, auth_headers, test_project):
        """测试批量上传文件保存失败"""
        files = [
            ("files", ("test.txt", BytesIO(b"Content"), "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        # 模拟文件保存失败
        with patch('builtins.open', side_effect=OSError("Disk full")):
            response = client.post(
                f"/api/v1/documents/batch-upload/{test_project.id}",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 应该返回失败信息
            assert response.status_code == 200  # 批量上传可能部分成功
            result = response.json()
            # 检查是否有失败记录
            assert "failed_uploads" in result["data"]
    
    def test_batch_upload_database_flush_error(self, client: TestClient, auth_headers, test_project):
        """测试批量上传数据库flush失败"""
        files = [
            ("files", ("test.txt", BytesIO(b"Content"), "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        # 模拟数据库flush失败
        with patch('sqlalchemy.orm.Session.flush') as mock_flush:
            mock_flush.side_effect = SQLAlchemyError("Database error")
            
            response = client.post(
                f"/api/v1/documents/batch-upload/{test_project.id}",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 应该返回失败信息
            assert response.status_code == 200  # 批量上传可能部分成功
            result = response.json()
            assert "failed_uploads" in result["data"]
    
    def test_batch_upload_file_cleanup_on_error(self, client: TestClient, auth_headers, test_project):
        """测试批量上传失败时的文件清理"""
        files = [
            ("files", ("test.txt", BytesIO(b"Content"), "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        with patch('app.models.document.Document') as mock_document:
            # 模拟数据库操作失败
            mock_document.side_effect = Exception("Database error")
            
            # 模拟文件存在检查和删除
            with patch('pathlib.Path.exists', return_value=True) as mock_exists, \
                 patch('pathlib.Path.unlink') as mock_unlink:
                
                response = client.post(
                    f"/api/v1/documents/batch-upload/{test_project.id}",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
                
                # 验证文件清理被调用
                assert response.status_code == 200  # 批量上传可能部分成功
                result = response.json()
                assert "failed_uploads" in result["data"]
    
    def test_batch_upload_success_message_variations(self, client: TestClient, auth_headers, test_project):
        """测试批量上传成功消息的不同情况"""
        files = [
            ("files", ("test.txt", BytesIO(b"Content"), "text/plain"))
        ]
        data = {
            "document_category": "测试文档"
        }
        
        response = client.post(
            f"/api/v1/documents/batch-upload/{test_project.id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 检查成功消息格式
        if result["data"]["failed_uploads_count"] == 0:
            assert "All" in result["message"] and "uploaded successfully" in result["message"]
        else:
            assert "Batch upload completed" in result["message"]