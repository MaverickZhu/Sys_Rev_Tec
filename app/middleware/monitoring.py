#!/usr/bin/env python3
"""
监控中间件

自动收集HTTP请求指标和性能数据
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.monitoring import monitor

logger = logging.getLogger(__name__)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    监控中间件
    
    自动记录HTTP请求指标：
    - 请求计数
    - 响应时间
    - 状态码分布
    - 端点访问统计
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = {
            "/metrics",
            "/health", 
            "/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录监控指标
        """
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        
        # 简化路径用于指标标签（避免高基数）
        endpoint = self._normalize_endpoint(path)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            duration = time.time() - start_time
            
            # 记录指标（排除某些路径以减少噪音）
            if not self._should_exclude_path(path):
                monitor.record_http_request(
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration=duration
                )
                
                # 记录慢请求
                if duration > 1.0:  # 超过1秒的请求
                    logger.warning(
                        f"Slow request: {method} {path} - {duration:.2f}s - {response.status_code}"
                    )
            
            return response
            
        except Exception as e:
            # 记录错误请求
            duration = time.time() - start_time
            
            if not self._should_exclude_path(path):
                monitor.record_http_request(
                    method=method,
                    endpoint=endpoint,
                    status_code=500,
                    duration=duration
                )
            
            logger.error(f"Request error: {method} {path} - {str(e)}")
            raise
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        标准化端点路径，避免高基数标签
        
        将动态路径参数替换为占位符
        例如: /api/v1/users/123 -> /api/v1/users/{id}
        """
        # 静态文件
        if path.startswith("/static"):
            return "/static/*"
        
        # API路径
        if path.startswith("/api/v1"):
            parts = path.split("/")
            normalized_parts = []
            
            for i, part in enumerate(parts):
                if not part:
                    continue
                    
                # 检查是否为数字ID
                if part.isdigit():
                    normalized_parts.append("{id}")
                # 检查是否为UUID格式
                elif self._is_uuid_like(part):
                    normalized_parts.append("{uuid}")
                else:
                    normalized_parts.append(part)
            
            return "/" + "/".join(normalized_parts)
        
        # 其他路径
        return path
    
    def _is_uuid_like(self, value: str) -> bool:
        """
        检查字符串是否类似UUID格式
        """
        import re
        # 匹配标准UUID格式：8-4-4-4-12个十六进制字符
        uuid_pattern = re.compile(
            r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        )
        # 匹配类似abc-123-def这样的格式，要求正好3个部分，每部分至少3个字符，且包含数字
        simple_pattern = re.compile(
            r'^[a-zA-Z0-9]{3,}-[a-zA-Z0-9]{3,}-[a-zA-Z0-9]{3,}$'
        )
        # 检查是否为标准UUID
        if uuid_pattern.match(value):
            return True
        # 检查是否为简单格式且包含数字
        if simple_pattern.match(value):
            # 确保至少有一个部分包含数字
            parts = value.split('-')
            return len(parts) == 3 and any(any(c.isdigit() for c in part) for part in parts)
        return False
    
    def _should_exclude_path(self, path: str) -> bool:
        """
        检查是否应该排除此路径的监控
        """
        return any(path.startswith(excluded) for excluded in self.excluded_paths)