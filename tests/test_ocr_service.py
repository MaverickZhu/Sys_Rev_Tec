import pytest
from unittest.mock import patch, MagicMock
from app.services.ocr_service import EnhancedOCRService, ocr_service
import logging


class TestEnhancedOCRService:
    """增强OCR服务测试"""
    
    def setup_method(self):
        """设置测试"""
        self.ocr_service = EnhancedOCRService()
    
    @patch('app.services.ocr_service.logger')
    def test_init_logging(self, mock_logger):
        """测试初始化日志记录"""
        service = EnhancedOCRService()
        mock_logger.info.assert_called_with("OCR Service initialized (mock mode)")
    
    def test_detect_handwriting(self):
        """测试手写检测"""
        result = self.ocr_service.detect_handwriting("test_image.jpg")
        assert result is False
    
    @patch('app.services.ocr_service.logger')
    def test_get_available_engines(self, mock_logger):
        """测试获取可用引擎"""
        engines = self.ocr_service.get_available_engines()
        
        assert engines == ['mock_ocr']
        mock_logger.info.assert_called_with("Getting available OCR engines (mock)")
    
    def test_extract_text(self):
        """测试文本提取"""
        result = self.ocr_service.extract_text("test_image.jpg")
        
        assert isinstance(result, dict)
        assert 'text' in result
        assert 'confidence' in result
        assert 'engine' in result
        assert 'details' in result
        
        assert result['text'] == '这是模拟的OCR文本内容'
        assert result['confidence'] == 0.95
        assert result['engine'] == 'mock_ocr'
        assert isinstance(result['details'], dict)
    
    def test_ocr_with_tesseract(self):
        """测试Tesseract OCR"""
        result = self.ocr_service.ocr_with_tesseract("test_image.jpg")
        
        # 应该返回与extract_text相同的结果
        expected = self.ocr_service.extract_text("test_image.jpg")
        assert result == expected
    
    def test_ocr_with_paddle(self):
        """测试PaddleOCR"""
        result = self.ocr_service.ocr_with_paddle("test_image.jpg")
        
        # 应该返回与extract_text相同的结果
        expected = self.ocr_service.extract_text("test_image.jpg")
        assert result == expected
    
    def test_ocr_with_trocr(self):
        """测试TrOCR手写识别"""
        result = self.ocr_service.ocr_with_trocr("test_image.jpg")
        
        # 应该返回与extract_text相同的结果
        expected = self.ocr_service.extract_text("test_image.jpg")
        assert result == expected
    
    def test_auto_select_engine(self):
        """测试自动选择引擎"""
        engine = self.ocr_service.auto_select_engine("test_image.jpg")
        assert engine == 'mock_ocr'
    
    def test_extract_text_with_auto_engine(self):
        """测试使用自动选择引擎提取文本"""
        result = self.ocr_service.extract_text_with_auto_engine("test_image.jpg")
        
        # 应该返回与extract_text相同的结果
        expected = self.ocr_service.extract_text("test_image.jpg")
        assert result == expected
    
    def test_different_image_paths(self):
        """测试不同的图像路径"""
        paths = [
            "image1.jpg",
            "path/to/image2.png",
            "/absolute/path/image3.gif",
            "image with spaces.jpg"
        ]
        
        for path in paths:
            # 所有方法都应该正常工作，不管路径如何
            assert self.ocr_service.detect_handwriting(path) is False
            assert self.ocr_service.auto_select_engine(path) == 'mock_ocr'
            
            result = self.ocr_service.extract_text(path)
            assert result['engine'] == 'mock_ocr'
            assert result['confidence'] == 0.95
    
    def test_consistency_across_methods(self):
        """测试不同方法之间的一致性"""
        image_path = "test_image.jpg"
        
        # 所有OCR方法应该返回相同的结果
        base_result = self.ocr_service.extract_text(image_path)
        tesseract_result = self.ocr_service.ocr_with_tesseract(image_path)
        paddle_result = self.ocr_service.ocr_with_paddle(image_path)
        trocr_result = self.ocr_service.ocr_with_trocr(image_path)
        auto_result = self.ocr_service.extract_text_with_auto_engine(image_path)
        
        assert base_result == tesseract_result
        assert base_result == paddle_result
        assert base_result == trocr_result
        assert base_result == auto_result


class TestOCRServiceGlobalInstance:
    """测试全局OCR服务实例"""
    
    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert ocr_service is not None
        assert isinstance(ocr_service, EnhancedOCRService)
    
    def test_global_instance_functionality(self):
        """测试全局实例功能"""
        # 测试全局实例的基本功能
        engines = ocr_service.get_available_engines()
        assert engines == ['mock_ocr']
        
        result = ocr_service.extract_text("test.jpg")
        assert result['engine'] == 'mock_ocr'
        
        handwriting = ocr_service.detect_handwriting("test.jpg")
        assert handwriting is False
    
    def test_global_instance_is_singleton(self):
        """测试全局实例是单例（在模块级别）"""
        # 导入应该返回相同的实例
        from app.services.ocr_service import ocr_service as imported_service
        assert ocr_service is imported_service