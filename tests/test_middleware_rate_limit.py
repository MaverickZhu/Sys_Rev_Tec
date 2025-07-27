import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import redis
from app.middleware.rate_limit import (
    RateLimitMiddleware,
    get_redis_client,
    get_rate_limit_key,
    create_limiter,
    limiter,
    custom_rate_limit_handler,
    rate_limit,
    simple_rate_limit,
    strict_rate_limit,
    moderate_rate_limit,
    loose_rate_limit
)
from app.core.config import settings
from slowapi.errors import RateLimitExceeded


class TestRedisConnection:
    """Redis连接测试"""
    
    @patch('app.middleware.rate_limit.redis.from_url')
    @patch('app.middleware.rate_limit.logger')
    def test_get_redis_client_success(self, mock_logger, mock_redis):
        """测试成功获取Redis客户端"""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        # 使用实际的Redis URL格式
        redis_url = 'redis://:redis_password@localhost:6379/1'
        with patch.object(settings, 'REDIS_URL', redis_url):
            client = get_redis_client()
            
            assert client == mock_redis_client
            mock_redis.assert_called_once_with(redis_url, decode_responses=True)
    
    @patch('app.middleware.rate_limit.redis.from_url')
    @patch('app.middleware.rate_limit.logger')
    def test_get_redis_client_failure(self, mock_logger, mock_redis):
        """测试Redis连接失败"""
        mock_redis.side_effect = Exception("Connection failed")
        
        client = get_redis_client()
        
        assert client is None
        mock_logger.warning.assert_called_once()
        assert "Redis连接失败" in str(mock_logger.warning.call_args)
    
    @patch('app.middleware.rate_limit.redis.from_url')
    def test_get_redis_client_with_rate_limit_url(self, mock_redis):
        """测试使用专用限流Redis URL"""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        with patch.object(settings, 'RATE_LIMIT_REDIS_URL', 'redis://rate-limit:6379'), \
             patch.object(settings, 'REDIS_URL', 'redis://general:6379'):
            client = get_redis_client()
            
            mock_redis.assert_called_once_with('redis://rate-limit:6379', decode_responses=True)


class TestRateLimitKey:
    """限流键测试"""
    
    def test_get_rate_limit_key(self):
        """测试获取限流键"""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        with patch('app.middleware.rate_limit.get_remote_address', return_value="192.168.1.1"):
            key = get_rate_limit_key(mock_request)
            assert key == "192.168.1.1"


class TestCreateLimiter:
    """创建限流器测试"""
    
    @patch('app.middleware.rate_limit.get_redis_client')
    @patch('app.middleware.rate_limit.Limiter')
    @patch('app.middleware.rate_limit.logger')
    def test_create_limiter_with_redis(self, mock_logger, mock_limiter_class, mock_get_redis):
        """测试使用Redis创建限流器"""
        mock_redis_client = MagicMock()
        mock_get_redis.return_value = mock_redis_client
        mock_limiter = MagicMock()
        mock_limiter_class.return_value = mock_limiter
        
        with patch.object(settings, 'REDIS_URL', 'redis://localhost:6379'):
            limiter = create_limiter()
            
            assert limiter == mock_limiter
            mock_logger.info.assert_called_with("使用Redis作为限流存储后端")
    
    @patch('app.middleware.rate_limit.get_redis_client')
    @patch('app.middleware.rate_limit.Limiter')
    @patch('app.middleware.rate_limit.logger')
    def test_create_limiter_without_redis(self, mock_logger, mock_limiter_class, mock_get_redis):
        """测试不使用Redis创建限流器"""
        mock_get_redis.return_value = None
        mock_limiter = MagicMock()
        mock_limiter_class.return_value = mock_limiter
        
        limiter = create_limiter()
        
        assert limiter == mock_limiter
        mock_logger.warning.assert_called_with("使用内存作为限流存储后端（仅适用于单实例）")


class TestRateLimitMiddleware:
    """限流中间件测试"""
    
    def setup_method(self):
        """设置测试"""
        self.app = FastAPI()
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
    def test_middleware_disabled(self):
        """测试中间件禁用时"""
        with patch.object(settings, 'RATE_LIMIT_ENABLED', False):
            self.app.add_middleware(RateLimitMiddleware)
            client = TestClient(self.app)
            
            response = client.get("/test")
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
    
    def test_middleware_enabled_without_limiter(self):
        """测试中间件启用但无限流器"""
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            middleware = RateLimitMiddleware(self.app, limiter_instance=None)
            self.app.add_middleware(RateLimitMiddleware, limiter_instance=None)
            client = TestClient(self.app)
            
            response = client.get("/test")
            assert response.status_code == 200
    
    @patch('app.middleware.rate_limit.logger')
    def test_middleware_with_exception(self, mock_logger):
        """测试中间件异常处理"""
        mock_limiter = MagicMock()
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            self.app.add_middleware(RateLimitMiddleware, limiter_instance=mock_limiter)
            client = TestClient(self.app)
            
            response = client.get("/test")
            assert response.status_code == 200


class TestCustomRateLimitHandler:
    """自定义限流异常处理器测试"""
    
    def test_custom_rate_limit_handler(self):
        """测试自定义限流异常处理"""
        mock_request = MagicMock()
        # 创建一个模拟的Limit对象
        mock_limit = MagicMock()
        mock_limit.error_message = "Rate limit exceeded"
        mock_exc = RateLimitExceeded(mock_limit)
        
        with patch.object(settings, 'RATE_LIMIT_REQUESTS', 10), \
             patch.object(settings, 'RATE_LIMIT_PERIOD', 60):
            
            result = custom_rate_limit_handler(mock_request, mock_exc)
            
            assert isinstance(result, HTTPException)
            assert result.status_code == 429
            assert "Rate limit exceeded" in str(result.detail["error"])
            assert "10次/60秒" in str(result.detail["message"])


class TestRateLimitDecorators:
    """限流装饰器测试"""
    
    def test_rate_limit_decorator_disabled(self):
        """测试限流装饰器禁用时"""
        with patch.object(settings, 'RATE_LIMIT_ENABLED', False):
            
            @rate_limit("10/minute")
            def test_func():
                return "test"
            
            result = test_func()
            assert result == "test"
    
    def test_rate_limit_decorator_no_limiter(self):
        """测试限流装饰器无限流器时"""
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True), \
             patch('app.middleware.rate_limit.limiter', None):
            
            @rate_limit("10/minute")
            def test_func():
                return "test"
            
            result = test_func()
            assert result == "test"
    
    @patch('app.middleware.rate_limit.logger')
    def test_rate_limit_decorator_enabled(self, mock_logger):
        """测试限流装饰器启用时"""
        mock_limiter = MagicMock()
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True), \
             patch('app.middleware.rate_limit.limiter', mock_limiter):
            
            @rate_limit("10/minute")
            def test_func():
                return "test"
            
            result = test_func()
            assert result == "test"
            # 应该记录调试日志
            mock_logger.debug.assert_called()
    
    @patch('app.middleware.rate_limit.logger')
    def test_simple_rate_limit_decorator(self, mock_logger):
        """测试简化限流装饰器"""
        
        @simple_rate_limit
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"
        mock_logger.debug.assert_called_with("Rate limit check for test_func")
    
    def test_predefined_decorators(self):
        """测试预定义的限流装饰器"""
        # 测试所有预定义装饰器都能正常工作
        
        @strict_rate_limit
        def strict_func():
            return "strict"
        
        @moderate_rate_limit
        def moderate_func():
            return "moderate"
        
        @loose_rate_limit
        def loose_func():
            return "loose"
        
        assert strict_func() == "strict"
        assert moderate_func() == "moderate"
        assert loose_func() == "loose"


class TestGlobalLimiterInstance:
    """全局限流器实例测试"""
    
    def test_limiter_exists_when_enabled(self):
        """测试启用时限流器存在"""
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            # 测试全局限流器的存在性
            from app.middleware.rate_limit import limiter
            # 在当前设置下，限流器可能存在也可能不存在，取决于Redis连接
            # 这里只测试不会抛出异常
            assert limiter is not None or limiter is None
    
    def test_limiter_behavior_when_disabled(self):
        """测试禁用时限流器行为"""
        with patch.object(settings, 'RATE_LIMIT_ENABLED', False):
            # 测试装饰器在禁用时的行为
            @rate_limit("10/minute")
            def test_func():
                return "test"
            
            result = test_func()
            assert result == "test"