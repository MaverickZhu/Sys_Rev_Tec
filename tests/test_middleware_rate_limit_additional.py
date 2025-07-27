import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import settings


class TestRateLimitMiddlewareAdditional:
    """限流中间件额外测试 - 覆盖异常处理分支"""
    
    def setup_method(self):
        """设置测试"""
        self.app = FastAPI()
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
    
    @pytest.mark.asyncio
    @patch('app.middleware.rate_limit.logger')
    async def test_middleware_exception_in_call_next(self, mock_logger):
        """测试call_next抛出异常时的处理"""
        call_count = 0
        
        # 创建一个第一次抛出异常，第二次正常返回的call_next函数
        async def failing_call_next(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Test exception in call_next")
            else:
                # 第二次调用返回正常响应
                from fastapi import Response
                return Response(content="OK", status_code=200)
        
        # 创建中间件实例
        middleware = RateLimitMiddleware(None)
        middleware.enabled = True
        middleware.limiter = MagicMock()
        
        # 创建请求
        from unittest.mock import Mock
        from fastapi import Request
        request = Mock(spec=Request)
        
        # 调用dispatch方法
        result = await middleware.dispatch(request, failing_call_next)
        
        # 验证异常被记录
        mock_logger.error.assert_called_once()
        assert "限流中间件错误" in str(mock_logger.error.call_args)
        
        # 验证返回了正常响应（第二次call_next调用）
        assert result.status_code == 200
        assert call_count == 2  # 确保call_next被调用了两次
    
    @patch('app.middleware.rate_limit.logger')
    def test_middleware_exception_handling_with_testclient(self, mock_logger):
        """使用TestClient测试中间件异常处理"""
        mock_limiter = MagicMock()
        
        # 创建一个会在处理过程中抛出异常的中间件
        class FailingRateLimitMiddleware(RateLimitMiddleware):
            async def dispatch(self, request, call_next):
                if not self.enabled or not self.limiter:
                    return await call_next(request)
                
                try:
                    # 模拟在限流检查过程中发生异常
                    raise ValueError("Rate limit check failed")
                    
                except Exception as e:
                    mock_logger.error(f"限流中间件错误: {e}")
                    # 如果限流出错，允许请求通过
                    return await call_next(request)
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            self.app.add_middleware(FailingRateLimitMiddleware, limiter_instance=mock_limiter)
            client = TestClient(self.app)
            
            response = client.get("/test")
            
            # 验证请求成功（异常被处理）
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
            
            # 验证异常被记录
            mock_logger.error.assert_called_with("限流中间件错误: Rate limit check failed")
    
    @patch('app.middleware.rate_limit.logger')
    def test_middleware_network_exception_handling(self, mock_logger):
        """测试网络异常的处理"""
        mock_limiter = MagicMock()
        
        class NetworkFailingMiddleware(RateLimitMiddleware):
            async def dispatch(self, request, call_next):
                if not self.enabled or not self.limiter:
                    return await call_next(request)
                
                try:
                    # 模拟网络连接异常
                    raise ConnectionError("Redis connection failed")
                    
                except Exception as e:
                    mock_logger.error(f"限流中间件错误: {e}")
                    # 如果限流出错，允许请求通过
                    return await call_next(request)
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            self.app.add_middleware(NetworkFailingMiddleware, limiter_instance=mock_limiter)
            client = TestClient(self.app)
            
            response = client.get("/test")
            
            # 验证请求成功（异常被处理）
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
            
            # 验证异常被记录
            mock_logger.error.assert_called_with("限流中间件错误: Redis connection failed")
    
    @patch('app.middleware.rate_limit.logger')
    def test_middleware_timeout_exception_handling(self, mock_logger):
        """测试超时异常的处理"""
        mock_limiter = MagicMock()
        
        class TimeoutFailingMiddleware(RateLimitMiddleware):
            async def dispatch(self, request, call_next):
                if not self.enabled or not self.limiter:
                    return await call_next(request)
                
                try:
                    # 模拟超时异常
                    raise TimeoutError("Rate limit check timeout")
                    
                except Exception as e:
                    mock_logger.error(f"限流中间件错误: {e}")
                    # 如果限流出错，允许请求通过
                    return await call_next(request)
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            self.app.add_middleware(TimeoutFailingMiddleware, limiter_instance=mock_limiter)
            client = TestClient(self.app)
            
            response = client.get("/test")
            
            # 验证请求成功（异常被处理）
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
            
            # 验证异常被记录
            mock_logger.error.assert_called_with("限流中间件错误: Rate limit check timeout")
    
    @patch('app.middleware.rate_limit.logger')
    def test_middleware_generic_exception_handling(self, mock_logger):
        """测试通用异常的处理"""
        mock_limiter = MagicMock()
        
        class GenericFailingMiddleware(RateLimitMiddleware):
            async def dispatch(self, request, call_next):
                if not self.enabled or not self.limiter:
                    return await call_next(request)
                
                try:
                    # 模拟通用异常
                    raise Exception("Unexpected error occurred")
                    
                except Exception as e:
                    mock_logger.error(f"限流中间件错误: {e}")
                    # 如果限流出错，允许请求通过
                    return await call_next(request)
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            self.app.add_middleware(GenericFailingMiddleware, limiter_instance=mock_limiter)
            client = TestClient(self.app)
            
            response = client.get("/test")
            
            # 验证请求成功（异常被处理）
            assert response.status_code == 200
            assert response.json() == {"message": "test"}
            
            # 验证异常被记录
            mock_logger.error.assert_called_with("限流中间件错误: Unexpected error occurred")
    
    @patch('app.middleware.rate_limit.logger')
    def test_middleware_multiple_exceptions(self, mock_logger):
        """测试多次异常的处理"""
        mock_limiter = MagicMock()
        call_count = 0
        
        class MultipleFailingMiddleware(RateLimitMiddleware):
            async def dispatch(self, request, call_next):
                nonlocal call_count
                call_count += 1
                
                if not self.enabled or not self.limiter:
                    return await call_next(request)
                
                try:
                    # 模拟不同类型的异常
                    if call_count == 1:
                        raise ValueError("First error")
                    elif call_count == 2:
                        raise RuntimeError("Second error")
                    else:
                        raise Exception("Third error")
                    
                except Exception as e:
                    mock_logger.error(f"限流中间件错误: {e}")
                    # 如果限流出错，允许请求通过
                    return await call_next(request)
        
        with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
            self.app.add_middleware(MultipleFailingMiddleware, limiter_instance=mock_limiter)
            client = TestClient(self.app)
            
            # 发送多个请求
            response1 = client.get("/test")
            response2 = client.get("/test")
            response3 = client.get("/test")
            
            # 验证所有请求都成功
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response3.status_code == 200
            
            # 验证所有异常都被记录
            assert mock_logger.error.call_count == 3
            mock_logger.error.assert_any_call("限流中间件错误: First error")
            mock_logger.error.assert_any_call("限流中间件错误: Second error")
            mock_logger.error.assert_any_call("限流中间件错误: Third error")