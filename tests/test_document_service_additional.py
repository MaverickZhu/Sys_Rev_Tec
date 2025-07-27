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


class TestDocumentServiceAdditional:
    """文档服务额外测试 - 覆盖未测试的异常处理分支"""
    
    @patch('app.services.document_service.cache_service')
    def test_process_pdf_ocr_import_error_return(self, mock_cache_service, db):
        """测试PDF OCR处理中ImportError的return语句（第217-219行）"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.pdf'
        document.extracted_text = None
        
        # 模拟pdf2image导入错误，但不抛出异常，而是被捕获并返回错误信息
        with patch('pdf2image.convert_from_path', side_effect=ImportError("No module named 'pdf2image'")):
            result = service._process_pdf_ocr(document, db)
            
            # 验证返回的错误信息（覆盖第217-219行）
            assert result['success'] == False
            assert 'pdf2image library' in result['message']
            assert 'pip install pdf2image' in result['message']
    
    def test_process_text_file_general_exception_return(self):
        """测试文本文件处理中通用Exception的return语句（第303-305行）"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        
        # 模拟文件打开时抛出通用异常（不是UnicodeDecodeError）
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            # 验证返回的错误信息（覆盖第303-305行）
            assert result['success'] == False
            assert 'Text file processing failed' in result['message']
            assert 'Permission denied' in result['message']
    
    def test_process_text_file_file_not_found_exception(self):
        """测试文本文件处理中FileNotFoundError异常"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = '/nonexistent/path/test.txt'
        
        # 模拟文件不存在异常
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            # 验证返回的错误信息
            assert result['success'] == False
            assert 'Text file processing failed' in result['message']
            assert 'File not found' in result['message']
    
    def test_process_text_file_io_error_exception(self):
        """测试文本文件处理中IOError异常"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        
        # 模拟IO错误
        with patch('builtins.open', side_effect=IOError("I/O operation failed")):
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            # 验证返回的错误信息
            assert result['success'] == False
            assert 'Text file processing failed' in result['message']
            assert 'I/O operation failed' in result['message']
    
    @patch('app.services.document_service.logger')
    def test_process_pdf_ocr_import_error_logging(self, mock_logger, db):
        """测试PDF OCR处理ImportError时的日志记录"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.pdf'
        document.extracted_text = None
        
        # 模拟pdf2image导入错误
        with patch('pdf2image.convert_from_path', side_effect=ImportError("No module named 'pdf2image'")):
            result = service._process_pdf_ocr(document, db)
            
            # 验证日志记录
            mock_logger.warning.assert_called_once_with("pdf2image not available, cannot process PDF files")
            assert result['success'] == False
    
    @patch('app.services.document_service.logger')
    def test_process_text_file_general_exception_logging(self, mock_logger):
        """测试文本文件处理通用异常时的日志记录"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        
        # 模拟通用异常
        with patch('builtins.open', side_effect=OSError("Operating system error")):
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            # 验证日志记录
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert f"Text file processing failed for document {document.id}" in error_call_args
            assert result['success'] == False
    
    def test_process_text_file_unicode_decode_error_then_general_exception(self):
        """测试文本文件处理：先UnicodeDecodeError，然后GBK编码也失败"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.txt'
        document.extracted_text = None
        
        # 模拟UTF-8失败，GBK也失败
        with patch('builtins.open') as mock_open_func:
            # 第一次调用抛出UnicodeDecodeError
            mock_file_utf8 = Mock()
            mock_file_utf8.read.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
            mock_file_utf8.__enter__ = Mock(return_value=mock_file_utf8)
            mock_file_utf8.__exit__ = Mock(return_value=None)
            
            # 第二次调用抛出通用异常
            mock_file_gbk = Mock()
            mock_file_gbk.read.side_effect = OSError('Disk full')
            mock_file_gbk.__enter__ = Mock(return_value=mock_file_gbk)
            mock_file_gbk.__exit__ = Mock(return_value=None)
            
            mock_open_func.side_effect = [mock_file_utf8, mock_file_gbk]
            
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            # 验证返回的错误信息（这会触发第303-305行的return语句）
            assert result['success'] == False
            assert 'Text file processing failed' in result['message']
            assert 'Disk full' in result['message']
    
    def test_process_text_file_memory_error_exception(self):
        """测试文本文件处理中MemoryError异常"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'huge_file.txt'
        
        # 模拟内存不足错误
        with patch('builtins.open', side_effect=MemoryError("Not enough memory")):
            mock_db = Mock()
            result = service._process_text_file(document, mock_db)
            
            # 验证返回的错误信息
            assert result['success'] == False
            assert 'Text file processing failed' in result['message']
            assert 'Not enough memory' in result['message']
    
    @patch('app.services.document_service.logger')
    def test_pdf_ocr_exception_handling_and_raise(self, mock_logger, db):
        """测试PDF OCR处理中的异常处理和重新抛出"""
        service = DocumentService()
        
        document = Mock()
        document.id = 1
        document.file_path = 'test.pdf'
        
        # 模拟pdf2image可用但处理过程中出现其他异常
        with patch('pdf2image.convert_from_path', side_effect=RuntimeError("PDF processing error")):
            with pytest.raises(RuntimeError, match="PDF processing error"):
                service._process_pdf_ocr(document, db)
            
            # 验证错误日志记录
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert f"PDF OCR failed for document {document.id}" in error_call_args