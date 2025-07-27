import pytest
import tempfile
import os
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, PropertyMock, AsyncMock, mock_open
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO
from PIL import Image

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
    

        

            

        

        
    @patch('os.path.exists')
    @patch('app.services.document_service.DocumentService._process_image_ocr')
    def test_process_document_ocr_image_file(self, mock_process_image, mock_exists, db):
        """测试处理图像文件OCR"""
        service = DocumentService()
        
        mock_exists.return_value = True
        mock_process_image.return_value = {'success': True, 'text': 'test text'}
        
        document = Mock()
        document.file_path = 'test.jpg'
        document.filename = 'test.jpg'
        document.id = 1
        
        result = service.process_document_ocr(document, db)
        
        assert result['success'] == True
        mock_process_image.assert_called_once_with(document, db)
        
    @patch('os.path.exists')
    @patch('app.services.document_service.DocumentService._process_pdf_ocr')
    def test_process_document_ocr_pdf_file(self, mock_process_pdf, mock_exists, db):
        """测试处理PDF文件OCR"""
        service = DocumentService()
        
        mock_exists.return_value = True
        mock_process_pdf.return_value = {'success': True, 'text': 'test text'}
        
        document = Mock()
        document.file_path = 'test.pdf'
        document.filename = 'test.pdf'
        document.id = 1
        
        result = service.process_document_ocr(document, db)
        
        assert result['success'] == True
        mock_process_pdf.assert_called_once_with(document, db)
        
    @patch('os.path.exists')
    @patch('app.services.document_service.DocumentService._process_text_file')
    def test_process_document_ocr_text_file(self, mock_process_text, mock_exists, db):
        """测试处理文本文件OCR"""
        service = DocumentService()
        
        mock_exists.return_value = True
        mock_process_text.return_value = {'success': True, 'text': 'test text'}
        
        document = Mock()
        document.file_path = 'test.txt'
        document.filename = 'test.txt'
        document.id = 1
        
        result = service.process_document_ocr(document, db)
        
        assert result['success'] == True
        mock_process_text.assert_called_once_with(document, db)
        
    @patch('app.services.document_service.ocr_service')
    @patch('app.services.document_service.cache_service')
    def test_process_image_file_success(self, mock_cache_service, mock_ocr_service, db):
        """测试图像文件处理成功"""
        service = DocumentService()
        
        # 模拟OCR服务返回
        mock_ocr_service.extract_text.return_value = {
            'text': 'extracted text',
            'engine': 'tesseract',
            'confidence': 0.95,
            'details': {'processing_time': 1.5, 'method': 'tesseract'}
        }
        mock_ocr_service.detect_handwriting.return_value = False
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.jpg'
        document.extracted_text = None
        document.ocr_text = None
        document.ocr_engine = None
        document.ocr_confidence = None
        document.is_ocr_processed = None
        document.is_handwritten = None
        document.ocr_details = None
        document.processed_at = None
        
        result = service._process_image_ocr(document, db)
        
        assert result['success'] == True
        assert result['text'] == 'extracted text'
        assert result['engine'] == 'tesseract'
        assert result['confidence'] == 0.95
        assert result['is_handwritten'] == False
        
        # 验证文档更新
        assert document.ocr_text == 'extracted text'
        assert document.ocr_engine == 'tesseract'
        assert document.ocr_confidence == 95  # 0.95 * 100 = 95
        assert document.is_ocr_processed == True
        assert document.is_handwritten == False
        assert document.extracted_text == 'extracted text'
        
        # 验证缓存清除
        mock_cache_service.clear_pattern.assert_called_once_with("get_ocr_statistics:*", "app")
        
    @patch('app.services.document_service.ocr_service')
    def test_process_image_file_ocr_failure(self, mock_ocr_service, db):
        """测试图像OCR处理失败"""
        service = DocumentService()
        
        # 模拟OCR服务抛出异常
        mock_ocr_service.extract_text.side_effect = Exception('OCR failed')
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.jpg'
        
        # 测试应该抛出异常
        try:
            result = service._process_image_ocr(document, db)
            assert False, "Expected exception was not raised"
        except Exception as e:
            assert 'OCR failed' in str(e)
        
    @patch('os.unlink')
    @patch('tempfile.NamedTemporaryFile')
    @patch('pdf2image.convert_from_path')
    @patch('app.services.document_service.ocr_service')
    @patch('app.services.document_service.cache_service')
    def test_process_pdf_file_success(self, mock_cache_service, mock_ocr_service, mock_convert_from_path, mock_tempfile, mock_unlink, db):
        """测试PDF文件处理成功"""
        service = DocumentService()
        
        # 模拟PDF转图像
        mock_image = Mock()
        mock_image.save = Mock()
        mock_convert_from_path.return_value = [mock_image, mock_image]
        
        # 模拟临时文件
        mock_temp_file = Mock()
        mock_temp_file.name = '/tmp/test_page.png'
        mock_temp_file.__enter__ = Mock(return_value=mock_temp_file)
        mock_temp_file.__exit__ = Mock(return_value=None)
        mock_tempfile.return_value = mock_temp_file
        
        # 模拟OCR服务返回
        mock_ocr_service.extract_text.side_effect = [
            {
                'text': 'page 1 text',
                'engine': 'tesseract',
                'confidence': 0.9,
                'details': {'processing_time': 1.2, 'method': 'tesseract'}
            },
            {
                'text': 'page 2 text',
                'engine': 'tesseract',
                'confidence': 0.8,
                'details': {'processing_time': 1.3, 'method': 'tesseract'}
            }
        ]
        mock_ocr_service.detect_handwriting.return_value = False
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.pdf'
        document.extracted_text = None
        document.ocr_text = None
        document.ocr_engine = None
        document.ocr_confidence = None
        document.is_ocr_processed = None
        document.is_handwritten = None
        document.ocr_details = None
        document.processed_at = None
        
        result = service._process_pdf_ocr(document, db)
        
        assert result['success'] == True
        assert 'page 1 text' in result['text']
        assert 'page 2 text' in result['text']
        assert result['engine'] == 'tesseract'
        assert abs(result['confidence'] - 0.85) < 0.01  # 平均置信度，允许浮点数误差
        assert result['pages_processed'] == 2
        assert result['is_handwritten'] == False
        
        # 验证缓存清除
        mock_cache_service.clear_pattern.assert_called_once_with("get_ocr_statistics:*", "app")
        
    def test_process_pdf_file_no_pdf2image(self):
        """测试没有pdf2image库的情况"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.pdf'
        document.extracted_text = None
        
        # 模拟pdf2image不可用
        with patch('pdf2image.convert_from_path', side_effect=ImportError("No module named 'pdf2image'")):
            mock_db = Mock()
            result = service._process_pdf_ocr(document, mock_db)
            
            assert result['success'] == False
            assert 'pdf2image' in result['message']
        
    @patch('app.services.document_service.cache_service')
    @patch('builtins.open', new_callable=mock_open, read_data='test content')
    def test_process_text_file_utf8_success(self, mock_file, mock_cache_service):
        """测试文本文件UTF-8编码处理成功"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        document.extracted_text = None
        document.ocr_text = None
        document.ocr_engine = None
        document.ocr_confidence = None
        document.is_ocr_processed = None
        document.is_handwritten = None
        document.ocr_details = None
        document.processed_at = None
        
        mock_db = Mock()
        result = service._process_text_file(document, mock_db)
        
        assert result['success'] == True
        assert result['text'] == 'test content'
        assert result['engine'] == 'text_reader'
        assert result['confidence'] == 1.0
        assert result['is_handwritten'] == False
        
        # 验证文档更新
        assert document.ocr_text == 'test content'
        assert document.ocr_engine == 'text_reader'
        assert document.ocr_confidence == 100
        assert document.is_ocr_processed == True
        assert document.is_handwritten == False
        assert document.extracted_text == 'test content'
        
        # 验证缓存清除
        mock_cache_service.clear_pattern.assert_called_once_with("get_ocr_statistics:*", "app")
        
    @patch('app.services.document_service.cache_service')
    def test_process_text_file_gbk_fallback(self, mock_cache_service):
        """测试文本文件GBK编码回退"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        document.extracted_text = None
        
        # 模拟UTF-8失败，GBK成功
        with patch('builtins.open') as mock_open_func:
            # 第一次调用抛出UnicodeDecodeError，第二次成功
            mock_file_utf8 = Mock()
            mock_file_utf8.read.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
            mock_file_utf8.__enter__ = Mock(return_value=mock_file_utf8)
            mock_file_utf8.__exit__ = Mock(return_value=None)
            
            mock_file_gbk = Mock()
            mock_file_gbk.read.return_value = 'gbk content'
            mock_file_gbk.__enter__ = Mock(return_value=mock_file_gbk)
            mock_file_gbk.__exit__ = Mock(return_value=None)
            
            mock_open_func.side_effect = [mock_file_utf8, mock_file_gbk]
            
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            assert result['success'] == True
            assert result['text'] == 'gbk content'
            assert result['engine'] == 'text_reader'
            
            # 验证缓存清除
            mock_cache_service.clear_pattern.assert_called_once_with("get_ocr_statistics:*", "app")
        
    def test_process_text_file_all_encodings_fail(self):
        """测试所有编码都失败的情况"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        
        with patch('builtins.open') as mock_open_func:
            # 第一次调用抛出UnicodeDecodeError
            mock_file_utf8 = Mock()
            mock_file_utf8.read.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
            mock_file_utf8.__enter__ = Mock(return_value=mock_file_utf8)
            mock_file_utf8.__exit__ = Mock(return_value=None)
            
            # 第二次调用抛出其他异常
            mock_file_gbk = Mock()
            mock_file_gbk.read.side_effect = Exception('File read error')
            mock_file_gbk.__enter__ = Mock(return_value=mock_file_gbk)
            mock_file_gbk.__exit__ = Mock(return_value=None)
            
            mock_open_func.side_effect = [mock_file_utf8, mock_file_gbk]
            
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            assert result['success'] == False
            assert 'Text file processing failed' in result['message']
        
    def test_batch_process_ocr_with_processing_success(self):
        """测试批量OCR处理成功"""
        service = DocumentService()
        
        # 创建mock数据库和文档
        mock_db = Mock()
        mock_document = Mock()
        mock_document.id = 1
        mock_document.filename = "test.jpg"
        mock_document.is_ocr_processed = False
        
        mock_db.query().filter().first.return_value = mock_document
        
        # 模拟OCR处理
        with patch.object(service, 'process_document_ocr') as mock_process:
            mock_process.return_value = {
                'success': True,
                'engine': 'tesseract',
                'confidence': 0.9
            }
            
            result = service.batch_process_ocr([1], mock_db)
            
            assert result['processed'] == 1
            assert result['failed'] == 0
            assert result['skipped'] == 0
            assert len(result['details']) == 1
            assert result['details'][0]['status'] == 'success'
            
    def test_batch_process_ocr_with_failures(self):
        """测试批量OCR处理包含失败"""
        service = DocumentService()
        
        # 创建mock数据库和文档
        mock_db = Mock()
        mock_document = Mock()
        mock_document.id = 1
        mock_document.filename = "test.jpg"
        mock_document.is_ocr_processed = False
        
        mock_db.query().filter().first.return_value = mock_document
        
        # 模拟OCR处理失败
        with patch.object(service, 'process_document_ocr') as mock_process:
            mock_process.return_value = {
                'success': False,
                'message': 'OCR failed'
            }
            
            result = service.batch_process_ocr([1], mock_db)
            
            assert result['processed'] == 0
            assert result['failed'] == 1
            assert result['skipped'] == 0
            assert result['details'][0]['status'] == 'failed'
            
    def test_batch_process_ocr_with_exception(self):
        """测试批量OCR处理异常"""
        service = DocumentService()
        
        # 创建mock数据库和文档
        mock_db = Mock()
        mock_document = Mock()
        mock_document.id = 1
        mock_document.filename = "test.jpg"
        mock_document.is_ocr_processed = False
        
        mock_db.query().filter().first.return_value = mock_document
        
        # 模拟OCR处理抛出异常
        with patch.object(service, 'process_document_ocr') as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            result = service.batch_process_ocr([1], mock_db)
            
            assert result['processed'] == 0
            assert result['failed'] == 1
            assert result['skipped'] == 0
            assert 'Processing error' in result['details'][0]['message']