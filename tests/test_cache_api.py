"""缓存API端点测试"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.config import settings
from app.models.user import User
from app.services.cache_service import cache_service
from app.api.deps import get_current_user

# Mock用户数据
mock_user = User(
    id=1,
    username="testuser",
    email="test@example.com",
    is_active=True,
    is_superuser=True
)

@pytest.fixture
def client_with_auth():
    """带认证的测试客户端"""
    def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client
    # 清理
    app.dependency_overrides.clear()

@pytest.fixture
def client_no_auth():
    """无认证的测试客户端"""
    return TestClient(app)


class TestCacheStats:
    """测试缓存统计信息API"""
    
    def test_get_cache_stats_success(self, client_with_auth):
        """测试成功获取缓存统计信息"""
        mock_stats = {
            "total_keys": 100,
            "memory_usage": "10MB",
            "hit_rate": 0.85
        }
        mock_health = {
            "status": "healthy",
            "message": "Cache is working properly"
        }
        
        async def mock_get_stats():
            return mock_stats
        async def mock_health_check():
            return mock_health
        
        with patch.object(cache_service, 'get_stats', side_effect=mock_get_stats), \
             patch.object(cache_service, 'health_check', side_effect=mock_health_check), \
             patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_with_auth.get("/api/v1/cache/stats")
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Cache statistics retrieved successfully"
        assert data["data"]["cache_enabled"] is True
        assert data["data"]["statistics"] == mock_stats
        assert data["data"]["health"] == mock_health
    
    def test_get_cache_stats_cache_disabled(self, client_with_auth):
        """测试缓存禁用时获取统计信息"""
        with patch('app.core.config.settings.CACHE_ENABLED', False):
            response = client_with_auth.get("/api/v1/cache/stats")
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Cache is disabled"
        assert data["data"]["cache_enabled"] is False
    
    def test_get_cache_stats_error(self, client_with_auth):
        """测试获取缓存统计信息时发生错误"""
        async def mock_get_stats():
            raise Exception("Redis连接失败")
        
        with patch.object(cache_service, 'get_stats', side_effect=mock_get_stats), \
             patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_with_auth.get("/api/v1/cache/stats")
            
        assert response.status_code == 500
        response_data = response.json()
        assert "Failed to get cache statistics" in response_data["error"]["message"]
    
    def test_get_cache_stats_unauthorized(self, client_no_auth):
        """测试未授权访问缓存统计信息"""
        response = client_no_auth.get("/api/v1/cache/stats")
        assert response.status_code == 401


class TestClearCache:
    """测试清除缓存API"""
    
    @patch.object(cache_service, 'clear_pattern')
    def test_clear_cache_success(self, mock_clear, client_with_auth):
        """测试成功清除缓存"""
        async def mock_clear_pattern(pattern, prefix):
            return 5
        mock_clear.side_effect = mock_clear_pattern
        
        with patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_with_auth.post("/api/v1/cache/clear", json={
                "pattern": "*",
                "prefix": "app"
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Successfully cleared 5 cache entries"
        assert data["data"]["cleared_count"] == 5
    
    @patch.object(cache_service, 'clear_pattern')
    def test_clear_cache_with_pattern(self, mock_clear, client_with_auth):
        """测试使用特定模式清除缓存"""
        async def mock_clear_pattern(pattern, prefix):
            return 3
        mock_clear.side_effect = mock_clear_pattern
        
        with patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_with_auth.post("/api/v1/cache/clear", json={
                "pattern": "user:*",
                "prefix": "app"
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Successfully cleared 3 cache entries"
    
    def test_clear_cache_disabled(self, client_with_auth):
        """测试缓存禁用时清除缓存"""
        with patch('app.core.config.settings.CACHE_ENABLED', False):
            response = client_with_auth.post("/api/v1/cache/clear", json={
                "pattern": "*",
                "prefix": "app"
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Cache is disabled"
        assert data["data"]["cache_enabled"] is False
    
    @patch.object(cache_service, 'clear_pattern')
    def test_clear_cache_error(self, mock_clear, client_with_auth):
        """测试清除缓存时发生错误"""
        async def mock_clear_pattern(pattern, prefix):
            raise Exception("清除失败")
        mock_clear.side_effect = mock_clear_pattern
        
        with patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_with_auth.post("/api/v1/cache/clear", json={
                "pattern": "*",
                "prefix": "app"
            })
            
        assert response.status_code == 500
        response_data = response.json()
        assert "Failed to clear cache" in response_data["error"]["message"]
    
    def test_clear_cache_unauthorized(self, client_no_auth):
        """测试未授权清除缓存"""
        response = client_no_auth.post("/api/v1/cache/clear", json={
            "pattern": "*",
            "prefix": "app"
        })
        assert response.status_code == 401


class TestCacheHealth:
    """测试缓存健康检查API"""
    
    @patch.object(cache_service, 'health_check')
    def test_cache_health_check_success(self, mock_health, client_no_auth):
        """测试缓存健康检查成功（无需认证）"""
        async def mock_health_check():
            return {"status": "healthy", "message": "Cache is working properly"}
        mock_health.side_effect = mock_health_check
        
        with patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_no_auth.get("/api/v1/cache/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Cache health check completed"
        assert data["data"]["healthy"] is True
        assert data["data"]["status"] == "healthy"
    
    @patch.object(cache_service, 'health_check')
    def test_cache_health_check_failed(self, mock_health, client_no_auth):
        """测试缓存健康检查失败"""
        async def mock_health_check():
            return {"status": "error", "message": "Redis connection failed"}
        mock_health.side_effect = mock_health_check
        
        with patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_no_auth.get("/api/v1/cache/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 503
        assert data["message"] == "Cache health check completed"
        assert data["data"]["healthy"] is False
        assert data["data"]["status"] == "error"
    
    def test_cache_health_check_disabled(self, client_no_auth):
        """测试缓存禁用时的健康检查"""
        with patch('app.core.config.settings.CACHE_ENABLED', False):
            response = client_no_auth.get("/api/v1/cache/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Cache is disabled"
        assert data["data"]["cache_enabled"] is False
        assert data["data"]["healthy"] is True
    
    @patch.object(cache_service, 'health_check')
    def test_cache_health_check_error(self, mock_health, client_no_auth):
        """测试缓存健康检查异常"""
        async def mock_health_check():
            raise Exception("Connection error")
        mock_health.side_effect = mock_health_check
        
        with patch('app.core.config.settings.CACHE_ENABLED', True):
            response = client_no_auth.get("/api/v1/cache/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 503
        assert data["message"] == "Cache health check failed"
        assert data["data"]["healthy"] is False
        assert "Connection error" in data["data"]["error"]
    
    def test_cache_health_check_unauthorized(self, client_no_auth):
        """测试未授权访问健康检查（实际上health端点无需认证，此测试仅为完整性）"""
        response = client_no_auth.get("/api/v1/cache/health")
        assert response.status_code == 200  # health端点是公开的，不需要认证