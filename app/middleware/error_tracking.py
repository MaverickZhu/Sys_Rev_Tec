# -*- coding: utf-8 -*-
"""
错误追踪中间件
"""

import traceback
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.error_tracking import track_error, ErrorSeverity
from app.core.exceptions import BaseAPIException
from app.core.logging import get_structured_logger

logger = get_structured_logger(__name__)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """错误追踪中间件"""
    
    def __init__(self, app, track_all_errors: bool = True, track_4xx_errors: bool = False):
        super().__init__(app)
        self.track_all_errors = track_all_errors
        self.track_4xx_errors = track_4xx_errors
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        try:
            response = await call_next(request)
            
            # 检查是否需要追踪4xx错误
            if self.track_4xx_errors and 400 <= response.status_code < 500:
                await self._track_http_error(request, response, client_ip, request_id)
            
            return response
            
        except BaseAPIException as e:
            # 追踪自定义API异常
            await self._track_api_exception(request, e, client_ip, request_id)
            
            # 重新抛出异常，让异常处理器处理
            raise e
            
        except Exception as e:
            # 追踪未处理的异常
            await self._track_unhandled_exception(request, e, client_ip, request_id)
            
            # 重新抛出异常，让异常处理器处理
            raise e
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 回退到直接连接IP
        return request.client.host if request.client else "unknown"
    
    async def _track_http_error(self, request: Request, response: Response, client_ip: str, request_id: str):
        """追踪HTTP错误"""
        severity = ErrorSeverity.LOW if response.status_code < 500 else ErrorSeverity.HIGH
        
        track_error(
            error_type="HTTP_ERROR",
            error_code=str(response.status_code),
            message=f"HTTP {response.status_code} error on {request.method} {request.url.path}",
            severity=severity,
            path=str(request.url.path),
            method=request.method,
            user_id=getattr(request.state, 'user_id', None),
            request_id=request_id,
            client_ip=client_ip,
            details={
                "status_code": response.status_code,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            }
        )
    
    async def _track_api_exception(self, request: Request, exception: BaseAPIException, client_ip: str, request_id: str):
        """追踪API异常"""
        # 根据异常类型确定严重程度
        severity_map = {
            "ValidationException": ErrorSeverity.LOW,
            "AuthenticationException": ErrorSeverity.MEDIUM,
            "AuthorizationException": ErrorSeverity.MEDIUM,
            "ResourceNotFoundException": ErrorSeverity.LOW,
            "DatabaseException": ErrorSeverity.HIGH,
            "FileOperationException": ErrorSeverity.MEDIUM,
            "OCRProcessingException": ErrorSeverity.MEDIUM,
            "ExternalServiceException": ErrorSeverity.MEDIUM,
            "RateLimitException": ErrorSeverity.LOW,
            "ConfigurationException": ErrorSeverity.HIGH
        }
        
        severity = severity_map.get(exception.__class__.__name__, ErrorSeverity.MEDIUM)
        
        track_error(
            error_type="API_EXCEPTION",
            error_code=exception.error_code,
            message=exception.message,
            severity=severity,
            path=str(request.url.path),
            method=request.method,
            user_id=getattr(request.state, 'user_id', None),
            request_id=request_id,
            client_ip=client_ip,
            traceback=traceback.format_exc(),
            details={
                "exception_type": exception.__class__.__name__,
                "status_code": exception.status_code,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "exception_details": exception.details if hasattr(exception, 'details') else None
            }
        )
    
    async def _track_unhandled_exception(self, request: Request, exception: Exception, client_ip: str, request_id: str):
        """追踪未处理的异常"""
        track_error(
            error_type="UNHANDLED_EXCEPTION",
            error_code="INTERNAL_ERROR",
            message=str(exception),
            severity=ErrorSeverity.CRITICAL,
            path=str(request.url.path),
            method=request.method,
            user_id=getattr(request.state, 'user_id', None),
            request_id=request_id,
            client_ip=client_ip,
            traceback=traceback.format_exc(),
            details={
                "exception_type": exception.__class__.__name__,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            }
        )


def create_error_tracking_middleware(track_all_errors: bool = True, track_4xx_errors: bool = False):
    """创建错误追踪中间件的工厂函数"""
    def middleware_factory(app):
        return ErrorTrackingMiddleware(app, track_all_errors, track_4xx_errors)
    return middleware_factory