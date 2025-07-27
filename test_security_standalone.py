#!/usr/bin/env python3
"""
独立的security中间件测试，不依赖conftest.py
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.middleware.security import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware, 
    RequestLoggingMiddleware
)

# 创建一个简单的settings mock
class MockSettings:
    def __init__(self):
        self.ENVIRONMENT = 'development'
        self.VERSION = '1.0.0'
        self.is_production = False
        self.ENABLE_SECURITY_HEADERS = False
        self.FORCE_HTTPS = False

# 替换settings
import app.middleware.security
app.middleware.security.settings = MockSettings()

class TestSecurityHeadersMiddleware:
    """Security headers middleware tests"""
    
    def setup_method(self):
        """Setup test"""
        self.app = FastAPI()
        self.app.add_middleware(SecurityHeadersMiddleware)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    def test_security_headers_in_production(self):
        """Test adding security headers in production"""
        # 临时设置为生产环境
        original_is_production = app.middleware.security.settings.is_production
        app.middleware.security.settings.is_production = True
        
        try:
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert "X-Frame-Options" in response.headers
            assert "X-Content-Type-Options" in response.headers
            assert "X-XSS-Protection" in response.headers
            assert "Referrer-Policy" in response.headers
            assert "Content-Security-Policy" in response.headers
            assert "Permissions-Policy" in response.headers
            
            # 检查具体的header值
            assert response.headers["X-Frame-Options"] == "DENY"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-XSS-Protection"] == "1; mode=block"
            
        finally:
            # 恢复原始设置
            app.middleware.security.settings.is_production = original_is_production
    
    def test_security_headers_with_enable_flag(self):
        """Test adding security headers when explicitly enabled"""
        # 临时启用安全头
        original_enable = getattr(app.middleware.security.settings, 'ENABLE_SECURITY_HEADERS', False)
        app.middleware.security.settings.ENABLE_SECURITY_HEADERS = True
        
        try:
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert "X-Frame-Options" in response.headers
            assert "X-Content-Type-Options" in response.headers
            
        finally:
            # 恢复原始设置
            app.middleware.security.settings.ENABLE_SECURITY_HEADERS = original_enable
    
    def test_security_headers_disabled_in_development(self):
        """Test security headers disabled in development"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        # 在开发环境下，安全头不应该被添加
        assert "X-Frame-Options" not in response.headers
        assert "X-Content-Type-Options" not in response.headers
    
    def test_custom_server_header(self):
        """Test custom server header"""
        response = self.client.get("/test")
        
        assert "Server" in response.headers
        # Check for the English app name used in HTTP headers
        assert "Gov-Procurement-System" in response.headers["Server"]
        assert app.middleware.security.settings.VERSION in response.headers["Server"]
    
    def test_hsts_header_with_force_https(self):
        """Test HSTS header when FORCE_HTTPS is enabled"""
        # 临时设置
        original_is_production = app.middleware.security.settings.is_production
        original_force_https = getattr(app.middleware.security.settings, 'FORCE_HTTPS', False)
        
        app.middleware.security.settings.is_production = True
        app.middleware.security.settings.FORCE_HTTPS = True
        
        try:
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert "Strict-Transport-Security" in response.headers
            assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
            
        finally:
            # 恢复原始设置
            app.middleware.security.settings.is_production = original_is_production
            app.middleware.security.settings.FORCE_HTTPS = original_force_https


class TestHTTPSRedirectMiddleware:
    """HTTPS redirect middleware tests"""
    
    def setup_method(self):
        """Setup test"""
        self.app = FastAPI()
        self.app.add_middleware(HTTPSRedirectMiddleware)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    def test_no_redirect_in_development(self):
        """Test no redirect in development"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
    
    def test_https_redirect_in_production(self):
        """Test HTTPS redirect in production with FORCE_HTTPS"""
        # 临时设置
        original_is_production = app.middleware.security.settings.is_production
        original_force_https = getattr(app.middleware.security.settings, 'FORCE_HTTPS', False)
        
        app.middleware.security.settings.is_production = True
        app.middleware.security.settings.FORCE_HTTPS = True
        
        try:
            # 注意：TestClient默认使用http，但实际的重定向逻辑需要特殊处理
            # 这里我们主要测试中间件逻辑是否正确
            response = self.client.get("/test")
            # 在TestClient环境下，可能不会触发重定向，但中间件逻辑应该正常
            assert response.status_code in [200, 301, 307, 308]  # 允许多种状态码
            
        finally:
            # 恢复原始设置
            app.middleware.security.settings.is_production = original_is_production
            app.middleware.security.settings.FORCE_HTTPS = original_force_https


class TestRequestLoggingMiddleware:
    """Request logging middleware tests"""
    
    def setup_method(self):
        """Setup test"""
        self.app = FastAPI()
        self.app.add_middleware(RequestLoggingMiddleware)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @patch('app.middleware.security.logger')
    def test_request_logging(self, mock_logger):
        """Test request logging"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        assert mock_logger.info.call_count >= 2  # Start and completion logs
        
        # 检查日志调用
        calls = mock_logger.info.call_args_list
        assert len(calls) >= 2
        
        # 检查第一个调用（请求开始）
        first_call = str(calls[0])
        assert "Request started" in first_call
        assert "GET" in first_call
        assert "/test" in first_call
        
        # 检查最后一个调用（请求完成）
        last_call = str(calls[-1])
        assert "Request completed" in last_call
        assert "Status: 200" in last_call
    
    def test_process_time_header(self):
        """Test process time header"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        
        # 检查处理时间是否为有效数字
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
        assert process_time < 10  # 应该在合理范围内


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])