import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO

from app.services.document_service import DocumentService, document_service
from app.models.document import Document
from app.models.project import Project


class TestDocumentService:
    """文档服务测试"""
    
    def test_init(self):
        """测试文档服务初始化"""
        service = DocumentService()
        assert service.upload_dir.exists()
        assert '.jpg' in service.supported_image_types
        assert '.pdf' in service.supported_pdf_types
        assert '.doc' in service.supported_doc_types
    
    def test_is_image_file(self):
        """测试图像文件检测"""
        service = DocumentService()
        
        # 测试支持的图像格式
        assert service.is_image_file('test.jpg') == True
        assert service.is_image_file('test.jpeg') == True
        assert service.is_image_file('test.png') == True
        assert service.is_image_file('test.bmp') == True
        assert service.is_image_file('test.tiff') == True
        assert service.is_image_file('test.tif') == True
        
        # 测试大小写不敏感
        assert service.is_image_file('test.JPG') == True
        assert service.is_image_file('test.PNG') == True
        
        # 测试不支持的格式
        assert service.is_image_file('test.pdf') == False
        assert service.is_image_file('test.doc') == False
        assert service.is_image_file('test.txt') == False
    
    def test_is_pdf_file(self):
        """测试PDF文件检测"""
        service = DocumentService()
        
        assert service.is_pdf_file('test.pdf') == True
        assert service.is_pdf_file('test.PDF') == True
        assert service.is_pdf_file('test.jpg') == False
        assert service.is_pdf_file('test.doc') == False
    
    def test_is_document_file(self):
        """测试文档文件检测"""
        service = DocumentService()
        
        assert service.is_document_file('test.doc') == True
        assert service.is_document_file('test.docx') == True
        assert service.is_document_file('test.txt') == True
        assert service.is_document_file('test.rtf') == True
        assert service.is_document_file('test.DOC') == True
        
        assert service.is_document_file('test.pdf') == False
        assert service.is_document_file('test.jpg') == False
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file(self):
        """测试保存上传文件"""
        service = DocumentService()
        
        # 创建模拟上传文件
        file_content = b"test file content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = AsyncMock(return_value=file_content)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            service.upload_dir = Path(temp_dir)
            
            # 保存文件
            file_path = await service.save_uploaded_file(mock_file, project_id=1)
            
            # 验证文件保存
            assert os.path.exists(file_path)
            assert "project_1" in file_path
            assert "test.txt" in file_path
            
            # 验证文件内容
            with open(file_path, 'rb') as f:
                saved_content = f.read()
            assert saved_content == file_content
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_error(self):
        """测试保存上传文件错误处理"""
        service = DocumentService()
        
        # 创建会抛出异常的模拟文件
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = AsyncMock(side_effect=Exception("Read error"))
        
        with pytest.raises(Exception):
            await service.save_uploaded_file(mock_file, project_id=1)
    
    def test_process_document_ocr_file_not_found(self, db):
        """测试OCR处理文件不存在"""
        service = DocumentService()
        
        document = Document(
            id=1,
            filename="nonexistent.jpg",
            file_path="/nonexistent/path/nonexistent.jpg",
            project_id=1
        )
        
        result = service.process_document_ocr(document, db)
        assert result['success'] == False
        assert "File not found" in result['message']
    
    def test_process_document_ocr_unsupported_type(self, db):
        """测试OCR处理不支持的文件类型"""
        service = DocumentService()
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=True) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            document = Document(
                id=1,
                filename="test.xyz",
                file_path=temp_file.name,
                project_id=1
            )
            
            result = service.process_document_ocr(document, db)
            assert result['success'] == False
            assert "Unsupported file type" in result['message']
    
    @patch('app.services.document_service.ocr_service')
    def test_process_image_ocr_success(self, mock_ocr_service, db):
        """测试图像OCR处理成功"""
        service = DocumentService()
        
        # 模拟OCR服务返回
        mock_ocr_service.extract_text.return_value = {
            'text': '测试文本内容',
            'engine': 'tesseract',
            'confidence': 0.95,
            'details': {'pages': 1}
        }
        mock_ocr_service.detect_handwriting.return_value = False
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_file:
            temp_file.write(b"fake image content")
            temp_file.flush()
            
            document = Document(
                id=1,
                filename="test.jpg",
                original_filename="test.jpg",
                file_path=temp_file.name,
                project_id=1,
                uploader_id=1,
                file_size=1024,
                file_type="image",
                document_category="test"
            )
            db.add(document)
            db.commit()
            
            result = service.process_document_ocr(document, db)
            
            assert result['success'] == True
            assert result['text'] == '测试文本内容'
            assert result['engine'] == 'tesseract'
            assert result['confidence'] == 0.95
            assert result['is_handwritten'] == False
            
            # 验证数据库更新
            db.refresh(document)
            assert document.ocr_text == '测试文本内容'
            assert document.ocr_engine == 'tesseract'
            assert document.ocr_confidence == 95
            assert document.is_ocr_processed == True
            assert document.is_handwritten == False
    
    @patch('app.services.document_service.ocr_service')
    def test_process_image_ocr_failure(self, mock_ocr_service, db):
        """测试图像OCR处理失败"""
        service = DocumentService()
        
        # 模拟OCR服务抛出异常
        mock_ocr_service.extract_text.side_effect = Exception("OCR failed")
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_file:
            temp_file.write(b"fake image content")
            temp_file.flush()
            
            document = Document(
                id=1,
                filename="test.jpg",
                original_filename="test.jpg",
                file_path=temp_file.name,
                project_id=1,
                uploader_id=1,
                file_size=1024,
                file_type="image",
                document_category="test"
            )
            
            result = service.process_document_ocr(document, db)
            assert result['success'] == False
            assert "OCR processing failed" in result['message']
    
    def test_batch_process_ocr_empty_list(self, db):
        """测试批量处理空列表"""
        service = DocumentService()
        
        result = service.batch_process_ocr([], db)
        
        assert result['processed'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 0
        assert result['details'] == []
    
    def test_batch_process_ocr_nonexistent_documents(self, db):
        """测试批量处理不存在的文档"""
        service = DocumentService()
        
        result = service.batch_process_ocr([999, 1000], db)
        
        assert result['processed'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 2
        assert len(result['details']) == 2
        assert all(detail['status'] == 'skipped' for detail in result['details'])
        assert all('not found' in detail['message'] for detail in result['details'])
    
    def test_batch_process_ocr_already_processed(self, db):
        """测试批量处理已处理的文档"""
        service = DocumentService()
        
        # 创建已处理的文档
        document = Document(
            id=1,
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/test/test.jpg",
            project_id=1,
            uploader_id=1,
            file_size=1024,
            file_type="image",
            document_category="test",
            is_ocr_processed=True
        )
        db.add(document)
        db.commit()
        
        result = service.batch_process_ocr([1], db)
        
        assert result['processed'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 1
        assert result['details'][0]['status'] == 'skipped'
        assert 'Already processed' in result['details'][0]['message']
    
    def test_get_ocr_statistics_empty_db(self, db):
        """测试获取OCR统计信息（空数据库）"""
        service = DocumentService()
        
        stats = service.get_ocr_statistics(db)
        
        assert stats['total_documents'] == 0
        assert stats['ocr_processed'] == 0
        assert stats['ocr_pending'] == 0
        assert stats['handwritten_documents'] == 0
        assert stats['engine_usage'] == {}
        assert stats['average_confidence'] == 0
        assert stats['processing_rate'] == 0
    
    def test_get_ocr_statistics_with_data(self, db):
        """测试获取OCR统计信息（有数据）"""
        service = DocumentService()
        
        # 创建测试文档
        documents = [
            Document(
                id=1, filename="test1.jpg", original_filename="test1.jpg", file_path="/test1.jpg", 
                project_id=1, uploader_id=1, file_size=1024, file_type="image", document_category="test",
                is_ocr_processed=True, ocr_engine="tesseract", ocr_confidence=90,
                is_handwritten=False
            ),
            Document(
                id=2, filename="test2.jpg", original_filename="test2.jpg", file_path="/test2.jpg", 
                project_id=1, uploader_id=1, file_size=1024, file_type="image", document_category="test",
                is_ocr_processed=True, ocr_engine="paddleocr", ocr_confidence=85,
                is_handwritten=True
            ),
            Document(
                id=3, filename="test3.jpg", original_filename="test3.jpg", file_path="/test3.jpg", 
                project_id=1, uploader_id=1, file_size=1024, file_type="image", document_category="test",
                is_ocr_processed=False
            )
        ]
        
        for doc in documents:
            db.add(doc)
        db.commit()
        
        stats = service.get_ocr_statistics(db)
        
        assert stats['total_documents'] == 3
        assert stats['ocr_processed'] == 2
        assert stats['ocr_pending'] == 1
        assert stats['handwritten_documents'] == 1
        assert stats['engine_usage']['tesseract'] == 1
        assert stats['engine_usage']['paddleocr'] == 1
        assert stats['average_confidence'] == 87.5
        assert stats['processing_rate'] == 66.67
    
    def test_get_ocr_statistics_with_project_filter(self, db):
        """测试按项目筛选OCR统计信息"""
        service = DocumentService()
        
        # 创建不同项目的文档
        documents = [
            Document(
                id=1, filename="test1.jpg", original_filename="test1.jpg", file_path="/test1.jpg", 
                project_id=1, uploader_id=1, file_size=1024, file_type="image", document_category="test",
                is_ocr_processed=True, ocr_engine="tesseract", ocr_confidence=90
            ),
            Document(
                id=2, filename="test2.jpg", original_filename="test2.jpg", file_path="/test2.jpg", 
                project_id=2, uploader_id=1, file_size=1024, file_type="image", document_category="test",
                is_ocr_processed=True, ocr_engine="paddleocr", ocr_confidence=85
            )
        ]
        
        for doc in documents:
            db.add(doc)
        db.commit()
        
        # 测试项目1的统计
        stats = service.get_ocr_statistics(db, project_id=1)
        
        assert stats['total_documents'] == 1
        assert stats['ocr_processed'] == 1
        assert stats['engine_usage']['tesseract'] == 1
        assert 'paddleocr' not in stats['engine_usage']
        assert stats['average_confidence'] == 90.0
    
    def test_global_document_service_instance(self):
        """测试全局文档服务实例"""
        assert document_service is not None
        assert isinstance(document_service, DocumentService)