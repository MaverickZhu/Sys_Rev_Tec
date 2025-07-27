# -*- coding: utf-8 -*-
"""
统一异常处理模块
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime

from app.core.error_tracking import track_error, ErrorSeverity

logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    """API基础异常类"""
    
    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """验证异常"""
    
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationException(BaseAPIException):
    """认证异常"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(BaseAPIException):
    """授权异常"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )


class ResourceNotFoundException(BaseAPIException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "Resource not found", resource_type: str = "Resource"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type}
        )


class BusinessLogicException(BaseAPIException):
    """业务逻辑异常"""
    
    def __init__(self, message: str = "Business logic error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details
        )


class ExternalServiceException(BaseAPIException):
    """外部服务异常"""
    
    def __init__(self, message: str = "External service error", service_name: str = "Unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service_name": service_name}
        )


class DatabaseException(BaseAPIException):
    """数据库异常"""
    
    def __init__(self, message: str = "Database error", operation: str = "Unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details={"operation": operation}
        )


class FileOperationException(BaseAPIException):
    """文件操作异常"""
    
    def __init__(self, message: str = "File operation error", operation: str = "Unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="FILE_OPERATION_ERROR",
            details={"operation": operation}
        )


class OCRProcessingException(BaseAPIException):
    """OCR处理异常"""
    
    def __init__(self, message: str = "OCR processing error", engine: str = "Unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="OCR_PROCESSING_ERROR",
            details={"engine": engine}
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建标准错误响应"""
    
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status_code": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return error_response


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """基础API异常处理器"""
    
    # 记录异常日志
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # 追踪错误
    track_error(
        error_type="API_EXCEPTION",
        error_code=exc.error_code,
        message=exc.message,
        severity=ErrorSeverity.MEDIUM if exc.status_code < 500 else ErrorSeverity.HIGH,
        path=str(request.url.path),
        method=request.method,
        user_id=getattr(request.state, 'user_id', None),
        request_id=getattr(request.state, 'request_id', None),
        client_ip=request.client.host if request.client else None,
        traceback=traceback.format_exc(),
        details={
            "exception_type": exc.__class__.__name__,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )
    
    # 获取请求ID（如果有的话）
    request_id = getattr(request.state, "request_id", None)
    
    error_response = create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # 追踪错误
    track_error(
        error_type="HTTP_EXCEPTION",
        error_code=str(exc.status_code),
        message=exc.detail,
        severity=ErrorSeverity.LOW if exc.status_code < 500 else ErrorSeverity.HIGH,
        path=str(request.url.path),
        method=request.method,
        user_id=getattr(request.state, 'user_id', None),
        request_id=getattr(request.state, 'request_id', None),
        client_ip=request.client.host if request.client else None,
        details={
            "exception_type": exc.__class__.__name__,
            "status_code": exc.status_code
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    error_response = create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code="HTTP_ERROR",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理器"""
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation Error: {len(errors)} validation errors",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # 追踪错误
    track_error(
        error_type="VALIDATION_ERROR",
        error_code="VALIDATION_FAILED",
        message=f"Request validation failed: {len(errors)} errors",
        severity=ErrorSeverity.LOW,
        path=str(request.url.path),
        method=request.method,
        user_id=getattr(request.state, 'user_id', None),
        request_id=getattr(request.state, 'request_id', None),
        client_ip=request.client.host if request.client else None,
        details={
            "exception_type": exc.__class__.__name__,
            "validation_errors": errors
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    error_response = create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    
    # 记录详细的异常信息
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "traceback": traceback.format_exc(),
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # 追踪错误
    track_error(
        error_type="UNHANDLED_EXCEPTION",
        error_code="INTERNAL_ERROR",
        message=str(exc),
        severity=ErrorSeverity.CRITICAL,
        path=str(request.url.path),
        method=request.method,
        user_id=getattr(request.state, 'user_id', None),
        request_id=getattr(request.state, 'request_id', None),
        client_ip=request.client.host if request.client else None,
        traceback=traceback.format_exc(),
        details={
            "exception_type": exc.__class__.__name__
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    # 在生产环境中隐藏详细错误信息
    from app.core.config import settings
    
    if settings.is_production:
        message = "Internal server error"
        details = None
    else:
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {"traceback": traceback.format_exc()}
    
    error_response = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=message,
        error_code="INTERNAL_SERVER_ERROR",
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )