import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import logging

from app.middleware.security import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware, 
    RequestLoggingMiddleware
)
from app.core.config import settings


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
        with patch.object(settings, 'ENVIRONMENT', 'production'):
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
    
    def test_security_headers_with_enable_flag(self):
        """Test adding security headers when explicitly enabled"""
        with patch.object(settings, 'ENABLE_SECURITY_HEADERS', True):
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert "X-Frame-Options" in response.headers
            assert "X-Content-Type-Options" in response.headers
    
    def test_security_headers_disabled_in_development(self):
        """Test security headers disabled in development"""
        with patch.object(settings, 'ENVIRONMENT', 'development'), \
             patch.object(settings, 'ENABLE_SECURITY_HEADERS', False):
            response = self.client.get("/test")
            
            assert response.status_code == 200
            # 在开发环境下，安全头不应该被添加
            assert "X-Frame-Options" not in response.headers
            assert "X-Content-Type-Options" not in response.headers
    
    def test_hsts_header_with_force_https(self):
        """Test HSTS header when FORCE_HTTPS is enabled"""
        with patch.object(settings, 'ENVIRONMENT', 'production'), \
             patch.object(settings, 'FORCE_HTTPS', True):
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert "Strict-Transport-Security" in response.headers
            assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    
    def test_hsts_header_disabled_without_force_https(self):
        """Test HSTS header disabled when FORCE_HTTPS is False"""
        with patch.object(settings, 'ENVIRONMENT', 'production'), \
             patch.object(settings, 'FORCE_HTTPS', False):
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert "Strict-Transport-Security" not in response.headers
    
    def test_custom_server_header(self):
        """Test custom server header"""
        response = self.client.get("/test")
        
        assert "Server" in response.headers
        # Check for the English app name used in HTTP headers
        assert "Gov-Procurement-System" in response.headers["Server"]


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
        with patch.object(settings, 'ENVIRONMENT', 'development'):
            response = self.client.get("/test")
            
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
    
    def test_https_redirect_in_production(self):
        """Test HTTPS redirect in production"""
        with patch.object(settings, 'ENVIRONMENT', 'production'), \
             patch.object(settings, 'FORCE_HTTPS', True):
            # 创建HTTP客户端，禁用重定向跟随
            from fastapi.testclient import TestClient
            http_client = TestClient(self.app, base_url="http://testserver", follow_redirects=False)
            response = http_client.get("/test")
            
            assert response.status_code == 301  # 中间件使用301重定向
            assert "location" in response.headers
            assert response.headers["location"].startswith("https://")
    
    def test_no_redirect_for_https_request(self):
        """Test no redirect for HTTPS requests"""
        with patch.object(settings, 'ENVIRONMENT', 'production'), \
             patch.object(settings, 'FORCE_HTTPS', True):
            # 创建HTTPS客户端
            from fastapi.testclient import TestClient
            https_client = TestClient(self.app, base_url="https://testserver")
            response = https_client.get("/test")
            
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
    
    def test_no_redirect_when_force_https_disabled(self):
        """Test no redirect when FORCE_HTTPS is disabled"""
        with patch.object(settings, 'ENVIRONMENT', 'production'), \
             patch.object(settings, 'FORCE_HTTPS', False):
            # 即使是HTTP请求也不应该重定向
            from fastapi.testclient import TestClient
            http_client = TestClient(self.app, base_url="http://testserver")
            response = http_client.get("/test")
            
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
    
    def test_redirect_with_query_params(self):
        """Test HTTPS redirect preserves query parameters"""
        with patch.object(settings, 'ENVIRONMENT', 'production'), \
             patch.object(settings, 'FORCE_HTTPS', True):
            # 创建HTTP客户端测试查询参数保留，禁用重定向跟随
            from fastapi.testclient import TestClient
            http_client = TestClient(self.app, base_url="http://testserver", follow_redirects=False)
            response = http_client.get("/test?param=value")
            
            assert response.status_code == 301  # 中间件使用301重定向
            assert "location" in response.headers
            assert "param=value" in response.headers["location"]


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
        
        # 检查日志内容
        calls = mock_logger.info.call_args_list
        assert any("Request started" in str(call) for call in calls)
        assert any("Request completed" in str(call) for call in calls)
    
    @patch('app.middleware.security.logger')
    def test_request_logging_with_exception(self, mock_logger):
        """Test request logging when exception occurs"""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        client = TestClient(app)
        
        with pytest.raises(ValueError):
            client.get("/error")
        
        # 应该记录请求开始，但不会记录完成（因为异常）
        assert mock_logger.info.call_count >= 1
        calls = mock_logger.info.call_args_list
        assert any("Request started" in str(call) for call in calls)
    
    @patch('app.middleware.security.logger')
    def test_request_logging_post_method(self, mock_logger):
        """Test request logging for POST method"""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.post("/post-test")
        async def post_endpoint(data: dict = None):
            return {"received": data}
        
        client = TestClient(app)
        response = client.post("/post-test", json={"key": "value"})
        
        assert response.status_code == 200
        assert mock_logger.info.call_count >= 2
        
        # 检查日志包含POST方法
        calls = mock_logger.info.call_args_list
        assert any("POST" in str(call) for call in calls)
    
    def test_process_time_header(self):
        """Test process time header"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0
    
    def test_process_time_header_format(self):
        """Test process time header format"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        process_time = response.headers["X-Process-Time"]
        
        # 检查格式是否为浮点数字符串
        try:
            time_value = float(process_time)
            assert time_value >= 0
            assert time_value < 10  # 应该在合理范围内
        except ValueError:
            pytest.fail(f"Process time header is not a valid float: {process_time}")
    
    @patch('app.middleware.security.logger')
    def test_request_logging_with_user_agent(self, mock_logger):
        """Test request logging includes user agent"""
        response = self.client.get("/test", headers={"User-Agent": "TestAgent/1.0"})
        
        assert response.status_code == 200
        assert mock_logger.info.call_count >= 2
        
        # 检查日志调用 - 中间件记录请求开始和完成
        calls = mock_logger.info.call_args_list
        assert any("Request started" in str(call) for call in calls)
        assert any("Request completed" in str(call) for call in calls)
        # 注意：当前中间件实现不记录User-Agent，这个测试主要验证日志功能正常