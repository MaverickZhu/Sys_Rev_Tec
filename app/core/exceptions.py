import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    """API基础异常类"""

    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """验证异常"""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationException(BaseAPIException):
    """认证异常"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationException(BaseAPIException):
    """授权异常"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


class ResourceNotFoundException(BaseAPIException):
    """资源未找到异常"""

    def __init__(
        self, message: str = "Resource not found", resource_type: str = "Resource"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type},
        )


class BusinessLogicException(BaseAPIException):
    """业务逻辑异常"""

    def __init__(
        self,
        message: str = "Business logic error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
        )


class ExternalServiceException(BaseAPIException):
    """外部服务异常"""

    def __init__(
        self, message: str = "External service error", service_name: str = "Unknown"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service_name": service_name},
        )


class DatabaseException(BaseAPIException):
    """数据库异常"""

    def __init__(self, message: str = "Database error", operation: str = "Unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details={"operation": operation},
        )


class FileOperationException(BaseAPIException):
    """文件操作异常"""

    def __init__(
        self, message: str = "File operation error", operation: str = "Unknown"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="FILE_OPERATION_ERROR",
            details={"operation": operation},
        )


class OCRProcessingException(BaseAPIException):
    """OCR处理异常"""

    def __init__(self, message: str = "OCR processing error", engine: str = "Unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="OCR_PROCESSING_ERROR",
            details={"engine": engine},
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """创建标准错误响应"""
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status_code": status_code,
        }
    }

    if details:
        error_response["error"]["details"] = details

    if request_id:
        error_response["error"]["request_id"] = request_id

    return error_response


def handle_database_error(
    error: Exception, operation: str = "Unknown"
) -> DatabaseException:
    """处理数据库错误"""
    logger.error(f"Database error during {operation}: {str(error)}")
    return DatabaseException(
        message=f"Database operation failed: {operation}", operation=operation
    )


def handle_file_error(
    error: Exception, operation: str = "Unknown"
) -> FileOperationException:
    """处理文件操作错误"""
    logger.error(f"File operation error during {operation}: {str(error)}")
    return FileOperationException(
        message=f"File operation failed: {operation}", operation=operation
    )


def handle_ocr_error(
    error: Exception, engine: str = "Unknown"
) -> OCRProcessingException:
    """处理OCR错误"""
    logger.error(f"OCR processing error with {engine}: {str(error)}")
    return OCRProcessingException(
        message=f"OCR processing failed with {engine}", engine=engine
    )


def handle_external_service_error(
    error: Exception, service_name: str = "Unknown"
) -> ExternalServiceException:
    """处理外部服务错误"""
    logger.error(f"External service error with {service_name}: {str(error)}")
    return ExternalServiceException(
        message=f"External service {service_name} is unavailable",
        service_name=service_name,
    )


# ==================== 异常处理器 ====================


async def base_api_exception_handler(
    request: Request, exc: BaseAPIException
) -> JSONResponse:
    """处理自定义API异常"""
    logger.error(f"API Exception: {exc.message} - {exc.details}")

    error_response = create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=exc.status_code, content=error_response)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理HTTP异常"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    error_response = create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code="HTTP_ERROR",
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=exc.status_code, content=error_response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证异常"""
    logger.error(f"Validation Exception: {exc.errors()}")

    error_response = create_error_response(
        status_code=422,
        message="Validation error",
        error_code="VALIDATION_ERROR",
        details={"validation_errors": exc.errors()},
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=422, content=error_response)


async def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    """处理响应验证异常"""
    logger.error(f"Response Validation Exception: {exc.errors()}")

    error_response = create_error_response(
        status_code=500,
        message="Response validation error",
        error_code="RESPONSE_VALIDATION_ERROR",
        details={"validation_errors": exc.errors()},
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=500, content=error_response)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常"""
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}", exc_info=True
    )

    # 在开发环境下显示详细错误信息
    if settings.DEBUG:
        details = {"exception_type": type(exc).__name__, "exception_message": str(exc)}
    else:
        details = None

    error_response = create_error_response(
        status_code=500,
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        details=details,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=500, content=error_response)
