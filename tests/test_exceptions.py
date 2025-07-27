# -*- coding: utf-8 -*-
"""
异常处理模块测试
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import json

from app.core.exceptions import (
    BaseAPIException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    BusinessLogicException,
    ExternalServiceException,
    DatabaseException,
    FileOperationException,
    OCRProcessingException,
    create_error_response,
    base_api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)


class TestBaseAPIException:
    """测试基础API异常类"""
    
    def test_base_api_exception_default(self):
        """测试基础异常默认参数"""
        exc = BaseAPIException()
        assert exc.message == "Internal server error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.details == {}
    
    def test_base_api_exception_custom(self):
        """测试基础异常自定义参数"""
        details = {"key": "value"}
        exc = BaseAPIException(
            message="Custom error",
            status_code=400,
            error_code="CUSTOM_ERROR",
            details=details
        )
        assert exc.message == "Custom error"
        assert exc.status_code == 400
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details == details


class TestValidationException:
    """测试验证异常类"""
    
    def test_validation_exception_default(self):
        """测试验证异常默认参数"""
        exc = ValidationException()
        assert exc.message == "Validation error"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details == {}
    
    def test_validation_exception_custom(self):
        """测试验证异常自定义参数"""
        details = {"field": "username", "issue": "required"}
        exc = ValidationException(message="Username is required", details=details)
        assert exc.message == "Username is required"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details == details


class TestAuthenticationException:
    """测试认证异常类"""
    
    def test_authentication_exception_default(self):
        """测试认证异常默认参数"""
        exc = AuthenticationException()
        assert exc.message == "Authentication failed"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.error_code == "AUTHENTICATION_ERROR"
    
    def test_authentication_exception_custom(self):
        """测试认证异常自定义参数"""
        exc = AuthenticationException(message="Invalid token")
        assert exc.message == "Invalid token"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.error_code == "AUTHENTICATION_ERROR"


class TestAuthorizationException:
    """测试授权异常类"""
    
    def test_authorization_exception_default(self):
        """测试授权异常默认参数"""
        exc = AuthorizationException()
        assert exc.message == "Access denied"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.error_code == "AUTHORIZATION_ERROR"
    
    def test_authorization_exception_custom(self):
        """测试授权异常自定义参数"""
        exc = AuthorizationException(message="Insufficient permissions")
        assert exc.message == "Insufficient permissions"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.error_code == "AUTHORIZATION_ERROR"


class TestResourceNotFoundException:
    """测试资源未找到异常类"""
    
    def test_resource_not_found_exception_default(self):
        """测试资源未找到异常默认参数"""
        exc = ResourceNotFoundException()
        assert exc.message == "Resource not found"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "RESOURCE_NOT_FOUND"
        assert exc.details == {"resource_type": "Resource"}
    
    def test_resource_not_found_exception_custom(self):
        """测试资源未找到异常自定义参数"""
        exc = ResourceNotFoundException(message="User not found", resource_type="User")
        assert exc.message == "User not found"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "RESOURCE_NOT_FOUND"
        assert exc.details == {"resource_type": "User"}


class TestBusinessLogicException:
    """测试业务逻辑异常类"""
    
    def test_business_logic_exception_default(self):
        """测试业务逻辑异常默认参数"""
        exc = BusinessLogicException()
        assert exc.message == "Business logic error"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.error_code == "BUSINESS_LOGIC_ERROR"
        assert exc.details == {}
    
    def test_business_logic_exception_custom(self):
        """测试业务逻辑异常自定义参数"""
        details = {"rule": "max_upload_size", "limit": "10MB"}
        exc = BusinessLogicException(message="File too large", details=details)
        assert exc.message == "File too large"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.error_code == "BUSINESS_LOGIC_ERROR"
        assert exc.details == details


class TestExternalServiceException:
    """测试外部服务异常类"""
    
    def test_external_service_exception_default(self):
        """测试外部服务异常默认参数"""
        exc = ExternalServiceException()
        assert exc.message == "External service error"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.details == {"service_name": "Unknown"}
    
    def test_external_service_exception_custom(self):
        """测试外部服务异常自定义参数"""
        exc = ExternalServiceException(message="OCR service unavailable", service_name="Tesseract")
        assert exc.message == "OCR service unavailable"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.details == {"service_name": "Tesseract"}


class TestDatabaseException:
    """测试数据库异常类"""
    
    def test_database_exception_default(self):
        """测试数据库异常默认参数"""
        exc = DatabaseException()
        assert exc.message == "Database error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details == {"operation": "Unknown"}
    
    def test_database_exception_custom(self):
        """测试数据库异常自定义参数"""
        exc = DatabaseException(message="Connection timeout", operation="SELECT")
        assert exc.message == "Connection timeout"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details == {"operation": "SELECT"}


class TestFileOperationException:
    """测试文件操作异常类"""
    
    def test_file_operation_exception_default(self):
        """测试文件操作异常默认参数"""
        exc = FileOperationException()
        assert exc.message == "File operation error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "FILE_OPERATION_ERROR"
        assert exc.details == {"operation": "Unknown"}
    
    def test_file_operation_exception_custom(self):
        """测试文件操作异常自定义参数"""
        exc = FileOperationException(message="File not found", operation="READ")
        assert exc.message == "File not found"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "FILE_OPERATION_ERROR"
        assert exc.details == {"operation": "READ"}


class TestOCRProcessingException:
    """测试OCR处理异常类"""
    
    def test_ocr_processing_exception_default(self):
        """测试OCR处理异常默认参数"""
        exc = OCRProcessingException()
        assert exc.message == "OCR processing error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "OCR_PROCESSING_ERROR"
        assert exc.details == {"engine": "Unknown"}
    
    def test_ocr_processing_exception_custom(self):
        """测试OCR处理异常自定义参数"""
        exc = OCRProcessingException(message="Image format not supported", engine="Tesseract")
        assert exc.message == "Image format not supported"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "OCR_PROCESSING_ERROR"
        assert exc.details == {"engine": "Tesseract"}


class TestCreateErrorResponse:
    """测试错误响应创建函数"""
    
    def test_create_error_response_minimal(self):
        """测试最小参数错误响应"""
        response = create_error_response(400, "Bad request")
        
        assert "error" in response
        error = response["error"]
        assert error["code"] == "UNKNOWN_ERROR"
        assert error["message"] == "Bad request"
        assert error["status_code"] == 400
        assert "timestamp" in error
        assert "details" not in error
        assert "request_id" not in error
    
    def test_create_error_response_full(self):
        """测试完整参数错误响应"""
        details = {"field": "username"}
        request_id = "req-123"
        
        response = create_error_response(
            status_code=422,
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details=details,
            request_id=request_id
        )
        
        assert "error" in response
        error = response["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["message"] == "Validation failed"
        assert error["status_code"] == 422
        assert error["details"] == details
        assert error["request_id"] == request_id
        assert "timestamp" in error


class TestExceptionHandlers:
    """测试异常处理器"""
    
    def create_mock_request(self, path="/test", method="GET", client_host="127.0.0.1", request_id=None):
        """创建模拟请求对象"""
        request = Mock(spec=Request)
        request.url.path = path
        request.method = method
        request.client.host = client_host
        
        # 模拟request.state
        request.state = Mock()
        if request_id:
            request.state.request_id = request_id
        else:
            # 模拟没有request_id的情况
            def getattr_side_effect(obj, name, default=None):
                if name == "request_id":
                    return default
                return getattr(obj, name, default)
            
            with patch('builtins.getattr', side_effect=getattr_side_effect):
                pass
        
        return request
    
    @pytest.mark.asyncio
    async def test_base_api_exception_handler(self):
        """测试基础API异常处理器"""
        request = self.create_mock_request(request_id="req-123")
        exc = ValidationException(message="Test validation error")
        
        with patch('app.core.exceptions.logger') as mock_logger:
            response = await base_api_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        # 检查日志记录
        mock_logger.error.assert_called_once()
        
        # 检查响应内容
        content = json.loads(response.body)
        assert "error" in content
        error = content["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["message"] == "Test validation error"
        assert error["request_id"] == "req-123"
    
    @pytest.mark.asyncio
    async def test_base_api_exception_handler_no_request_id(self):
        """测试基础API异常处理器（无请求ID）"""
        request = self.create_mock_request()
        # 确保没有request_id属性
        if hasattr(request.state, 'request_id'):
            delattr(request.state, 'request_id')
        
        exc = AuthenticationException()
        
        with patch('app.core.exceptions.logger') as mock_logger:
            response = await base_api_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        
        content = json.loads(response.body)
        assert "request_id" not in content["error"]
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """测试HTTP异常处理器"""
        request = self.create_mock_request(request_id="req-456")
        exc = HTTPException(status_code=404, detail="Not found")
        
        with patch('app.core.exceptions.logger') as mock_logger:
            response = await http_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # 检查日志记录
        mock_logger.warning.assert_called_once()
        
        # 检查响应内容
        content = json.loads(response.body)
        error = content["error"]
        assert error["code"] == "HTTP_ERROR"
        assert error["message"] == "Not found"
        assert error["request_id"] == "req-456"
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """测试验证异常处理器"""
        request = self.create_mock_request(request_id="req-validation")
        
        # 创建模拟的验证错误
        validation_errors = [
            {
                "loc": ("body", "username"),
                "msg": "field required",
                "type": "value_error.missing"
            },
            {
                "loc": ("body", "email"),
                "msg": "invalid email format",
                "type": "value_error.email"
            }
        ]
        
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = validation_errors
        
        with patch('app.core.exceptions.logger') as mock_logger:
            response = await validation_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        # 检查日志记录
        mock_logger.warning.assert_called_once()
        
        # 检查响应内容
        content = json.loads(response.body)
        error = content["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["message"] == "Validation failed"
        assert "validation_errors" in error["details"]
        assert len(error["details"]["validation_errors"]) == 2
        assert error["request_id"] == "req-validation"
    
    @pytest.mark.asyncio
    async def test_general_exception_handler_development(self):
        """测试通用异常处理器（开发环境）"""
        request = self.create_mock_request(request_id="req-dev")
        exc = ValueError("Test error")
        
        with patch('app.core.exceptions.logger') as mock_logger, \
             patch('app.core.config.settings') as mock_settings:
            mock_settings.is_production = False
            response = await general_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # 检查日志记录
        mock_logger.error.assert_called_once()
        
        # 检查响应内容
        content = json.loads(response.body)
        error = content["error"]
        assert error["code"] == "INTERNAL_SERVER_ERROR"
        assert "ValueError: Test error" in error["message"]
        assert "traceback" in error["details"]
        assert error["request_id"] == "req-dev"
    
    @pytest.mark.asyncio
    async def test_general_exception_handler_production(self):
        """测试通用异常处理器（生产环境）"""
        request = self.create_mock_request(request_id="req-prod")
        exc = ValueError("Test error")
        
        with patch('app.core.exceptions.logger') as mock_logger, \
             patch('app.core.config.settings') as mock_settings:
            mock_settings.is_production = True
            response = await general_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # 检查响应内容
        content = json.loads(response.body)
        error = content["error"]
        assert error["code"] == "INTERNAL_SERVER_ERROR"
        assert error["message"] == "Internal server error"
        assert "details" not in error or error["details"] is None
        assert error["request_id"] == "req-prod"
    
    @pytest.mark.asyncio
    async def test_exception_handler_no_client(self):
        """测试异常处理器（无客户端信息）"""
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.client = None
        request.state = Mock()
        request.state.request_id = "req-no-client"
        
        exc = AuthenticationException()
        
        with patch('app.core.exceptions.logger') as mock_logger:
            response = await base_api_exception_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        
        # 检查日志调用参数中包含"unknown"作为客户端IP
        call_args = mock_logger.error.call_args
        assert "unknown" in str(call_args)
        
        # 检查响应内容
        content = json.loads(response.body)
        error = content["error"]
        assert error["request_id"] == "req-no-client"