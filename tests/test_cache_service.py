import pytest
import json
import pickle
from unittest.mock import Mock, patch, MagicMock
from app.services.cache_service import (
    CacheService, 
    cache_service,
    cache_set, 
    cache_get, 
    cache_delete, 
    cache_exists, 
    cache_clear_pattern
)


class TestCacheService:
    """缓存服务测试"""
    
    def test_init_disabled(self):
        """测试缓存禁用时的初始化"""
        with patch('app.services.cache_service.settings.CACHE_ENABLED', False):
            service = CacheService()
            assert service.is_enabled is False
            assert service.redis_client is None
    
    @patch('app.services.cache_service.redis.from_url')
    def test_init_enabled_success(self, mock_redis):
        """测试缓存启用且连接成功"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        with patch('app.services.cache_service.settings.CACHE_ENABLED', True):
            service = CacheService()
            assert service.is_enabled is True
            assert service.redis_client == mock_client
            mock_client.ping.assert_called_once()
    
    @patch('app.services.cache_service.redis.from_url')
    def test_init_enabled_connection_failed(self, mock_redis):
        """测试缓存启用但连接失败"""
        mock_redis.side_effect = Exception("Connection failed")
        
        with patch('app.services.cache_service.settings.CACHE_ENABLED', True):
            service = CacheService()
            assert service.is_enabled is False
            assert service.redis_client is None
    
    def test_get_key(self):
        """测试缓存键生成"""
        service = CacheService()
        assert service._get_key("test", "app") == "app:test"
        assert service._get_key("user:123", "session") == "session:user:123"
    
    def test_set_disabled(self):
        """测试缓存禁用时的设置操作"""
        service = CacheService()
        service.is_enabled = False
        service.redis_client = None
        
        result = service.set("test", "value")
        assert result is False
    
    def test_set_no_client(self):
        """测试没有Redis客户端时的设置操作"""
        service = CacheService()
        service.is_enabled = True
        service.redis_client = None
        
        result = service.set("test", "value")
        assert result is False
    
    def test_set_string_value(self):
        """测试设置字符串值"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.setex.return_value = True
        service.redis_client = mock_client
        
        with patch('app.services.cache_service.settings.CACHE_EXPIRE_TIME', 3600):
            result = service.set("test", "value")
            assert result is True
            mock_client.setex.assert_called_once_with("app:test", 3600, "value")
    
    def test_set_dict_value(self):
        """测试设置字典值"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.setex.return_value = True
        service.redis_client = mock_client
        
        test_dict = {"key": "value", "number": 123}
        with patch('app.services.cache_service.settings.CACHE_EXPIRE_TIME', 3600):
            result = service.set("test", test_dict)
            assert result is True
            expected_json = json.dumps(test_dict, ensure_ascii=False, default=str)
            mock_client.setex.assert_called_once_with("app:test", 3600, expected_json)
    
    def test_set_complex_object(self):
        """测试设置复杂对象（使用pickle）"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.setex.return_value = True
        service.redis_client = mock_client
        
        # 使用一个可以pickle的对象
        from datetime import datetime
        test_obj = datetime.now()
        
        with patch('app.services.cache_service.settings.CACHE_EXPIRE_TIME', 3600):
            result = service.set("test", test_obj)
            assert result is True
            # 验证使用了pickle键
            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args
            assert call_args[0][0] == "app:test:pickle"
    
    def test_set_with_custom_expire(self):
        """测试设置自定义过期时间"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.setex.return_value = True
        service.redis_client = mock_client
        
        result = service.set("test", "value", expire=1800)
        assert result is True
        mock_client.setex.assert_called_once_with("app:test", 1800, "value")
    
    def test_set_exception(self):
        """测试设置时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.setex.side_effect = Exception("Redis error")
        service.redis_client = mock_client
        
        result = service.set("test", "value")
        assert result is False
    
    def test_get_disabled(self):
        """测试缓存禁用时的获取操作"""
        service = CacheService()
        service.is_enabled = False
        service.redis_client = None
        
        result = service.get("test")
        assert result is None
    
    def test_get_no_client(self):
        """测试没有Redis客户端时的获取操作"""
        service = CacheService()
        service.is_enabled = True
        service.redis_client = None
        
        result = service.get("test")
        assert result is None
    
    def test_get_json_value(self):
        """测试获取JSON值"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        test_dict = {"key": "value", "number": 123}
        mock_client.get.return_value = json.dumps(test_dict)
        service.redis_client = mock_client
        
        result = service.get("test")
        assert result == test_dict
        mock_client.get.assert_called_with("app:test")
    
    def test_get_string_value(self):
        """测试获取字符串值"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.get.side_effect = ["simple string", None]  # 第一次返回字符串，第二次返回None（pickle键）
        service.redis_client = mock_client
        
        result = service.get("test")
        assert result == "simple string"
    
    def test_get_pickle_value(self):
        """测试获取pickle值"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        
        # 使用一个可以pickle的对象
        from datetime import datetime
        test_obj = datetime(2023, 1, 1, 12, 0, 0)
        pickled_data = pickle.dumps(test_obj).hex()
        
        # 第一次调用返回None（普通键），第二次调用返回pickle数据
        mock_client.get.side_effect = [None, pickled_data]
        service.redis_client = mock_client
        
        result = service.get("test")
        assert isinstance(result, datetime)
        assert result == test_obj
    
    def test_get_cache_miss(self):
        """测试缓存未命中"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.get.return_value = None
        service.redis_client = mock_client
        
        result = service.get("test")
        assert result is None
    
    def test_get_exception(self):
        """测试获取时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Redis error")
        service.redis_client = mock_client
        
        result = service.get("test")
        assert result is None
    
    def test_get_pickle_deserialization_error(self):
        """测试pickle反序列化失败的异常处理（第115-117行）"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        
        # 模拟普通缓存键不存在，但pickle缓存键存在且包含无效数据
        mock_client.get.side_effect = lambda key: {
            "app:test": None,  # 普通缓存键不存在
            "app:test:pickle": "invalid_hex_data"  # pickle缓存键存在但数据无效
        }.get(key)
        
        service.redis_client = mock_client
        
        # 这将触发pickle反序列化异常处理
        result = service.get("test")
        assert result is None
        
        # 验证两次get调用：一次普通键，一次pickle键
        assert mock_client.get.call_count == 2
        mock_client.get.assert_any_call("app:test")
        mock_client.get.assert_any_call("app:test:pickle")
    
    def test_delete_disabled(self):
        """测试缓存禁用时的删除操作"""
        service = CacheService()
        service.is_enabled = False
        service.redis_client = None
        
        result = service.delete("test")
        assert result is False
    
    def test_delete_success(self):
        """测试删除成功"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.delete.side_effect = [1, 0]  # 第一个键删除成功，第二个键不存在
        service.redis_client = mock_client
        
        result = service.delete("test")
        assert result is True
        assert mock_client.delete.call_count == 2
    
    def test_delete_not_found(self):
        """测试删除不存在的键"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.delete.return_value = 0
        service.redis_client = mock_client
        
        result = service.delete("test")
        assert result is False
    
    def test_delete_exception(self):
        """测试删除时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.delete.side_effect = Exception("Redis error")
        service.redis_client = mock_client
        
        result = service.delete("test")
        assert result is False
    
    def test_exists_disabled(self):
        """测试缓存禁用时的存在检查"""
        service = CacheService()
        service.is_enabled = False
        service.redis_client = None
        
        result = service.exists("test")
        assert result is False
    
    def test_exists_true(self):
        """测试键存在"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.exists.side_effect = [1, 0]  # 第一个键存在
        service.redis_client = mock_client
        
        result = service.exists("test")
        assert result is True
    
    def test_exists_false(self):
        """测试键不存在"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.exists.return_value = 0
        service.redis_client = mock_client
        
        result = service.exists("test")
        assert result is False
    
    def test_exists_exception(self):
        """测试存在检查时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.exists.side_effect = Exception("Redis error")
        service.redis_client = mock_client
        
        result = service.exists("test")
        assert result is False
    
    def test_clear_pattern_disabled(self):
        """测试缓存禁用时的模式清除"""
        service = CacheService()
        service.is_enabled = False
        service.redis_client = None
        
        result = service.clear_pattern("test:*")
        assert result == 0
    
    def test_clear_pattern_success(self):
        """测试模式清除成功"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.keys.return_value = ["app:test:1", "app:test:2"]
        mock_client.delete.return_value = 2
        service.redis_client = mock_client
        
        result = service.clear_pattern("test:*")
        assert result == 2
        mock_client.keys.assert_called_once_with("app:test:*")
        mock_client.delete.assert_called_once_with("app:test:1", "app:test:2")
    
    def test_clear_pattern_no_keys(self):
        """测试模式清除无匹配键"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.keys.return_value = []
        service.redis_client = mock_client
        
        result = service.clear_pattern("test:*")
        assert result == 0
        mock_client.delete.assert_not_called()
    
    def test_clear_pattern_exception(self):
        """测试模式清除时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.keys.side_effect = Exception("Redis error")
        service.redis_client = mock_client
        
        result = service.clear_pattern("test:*")
        assert result == 0
    
    def test_get_stats_disabled(self):
        """测试缓存禁用时的统计信息"""
        service = CacheService()
        service.is_enabled = False
        service.redis_client = None
        
        result = service.get_stats()
        assert result == {"enabled": False, "connected": False}
    
    def test_get_stats_no_client(self):
        """测试没有Redis客户端时的统计信息"""
        service = CacheService()
        service.is_enabled = True
        service.redis_client = None
        
        result = service.get_stats()
        assert result == {"enabled": False, "connected": False}
    
    def test_get_stats_success(self):
        """测试获取统计信息成功"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_info = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }
        mock_client.info.return_value = mock_info
        service.redis_client = mock_client
        
        result = service.get_stats()
        assert result["enabled"] is True
        assert result["connected"] is True
        assert result["used_memory"] == "1.5M"
        assert result["connected_clients"] == 5
        assert result["hit_rate"] == "80.00%"
    
    def test_get_stats_exception(self):
        """测试获取统计信息时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.info.side_effect = Exception("Redis error")
        service.redis_client = mock_client
        
        result = service.get_stats()
        assert result["enabled"] is True
        assert result["connected"] is False
        assert "error" in result
    
    def test_calculate_hit_rate(self):
        """测试命中率计算"""
        service = CacheService()
        
        # 测试正常情况
        info = {"keyspace_hits": 80, "keyspace_misses": 20}
        assert service._calculate_hit_rate(info) == "80.00%"
        
        # 测试零除情况
        info = {"keyspace_hits": 0, "keyspace_misses": 0}
        assert service._calculate_hit_rate(info) == "N/A"
        
        # 测试缺少字段
        info = {}
        assert service._calculate_hit_rate(info) == "N/A"
    
    def test_health_check_disabled(self):
        """测试缓存禁用时的健康检查"""
        service = CacheService()
        service.is_enabled = False
        
        result = service.health_check()
        assert result["status"] == "disabled"
        assert "disabled" in result["message"]
    
    def test_health_check_no_client(self):
        """测试没有Redis客户端时的健康检查"""
        service = CacheService()
        service.is_enabled = True
        service.redis_client = None
        
        result = service.health_check()
        assert result["status"] == "error"
        assert "not initialized" in result["message"]
    
    def test_health_check_success(self):
        """测试健康检查成功"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.ping.return_value = True
        service.redis_client = mock_client
        
        result = service.health_check()
        assert result["status"] == "healthy"
        assert "working properly" in result["message"]
        assert "response_time_ms" in result
        mock_client.ping.assert_called_once()
    
    def test_health_check_exception(self):
        """测试健康检查时发生异常"""
        service = CacheService()
        service.is_enabled = True
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection failed")
        service.redis_client = mock_client
        
        result = service.health_check()
        assert result["status"] == "error"
        assert "failed" in result["message"]


class TestCacheConvenienceFunctions:
    """缓存便捷函数测试"""
    
    @patch('app.services.cache_service.cache_service')
    def test_cache_set(self, mock_service):
        """测试cache_set便捷函数"""
        mock_service.set.return_value = True
        
        result = cache_set("test", "value", 3600, "custom")
        assert result is True
        mock_service.set.assert_called_once_with("test", "value", 3600, "custom")
    
    @patch('app.services.cache_service.cache_service')
    def test_cache_get(self, mock_service):
        """测试cache_get便捷函数"""
        mock_service.get.return_value = "value"
        
        result = cache_get("test", "custom")
        assert result == "value"
        mock_service.get.assert_called_once_with("test", "custom")
    
    @patch('app.services.cache_service.cache_service')
    def test_cache_delete(self, mock_service):
        """测试cache_delete便捷函数"""
        mock_service.delete.return_value = True
        
        result = cache_delete("test", "custom")
        assert result is True
        mock_service.delete.assert_called_once_with("test", "custom")
    
    @patch('app.services.cache_service.cache_service')
    def test_cache_exists(self, mock_service):
        """测试cache_exists便捷函数"""
        mock_service.exists.return_value = True
        
        result = cache_exists("test", "custom")
        assert result is True
        mock_service.exists.assert_called_once_with("test", "custom")
    
    @patch('app.services.cache_service.cache_service')
    def test_cache_clear_pattern(self, mock_service):
        """测试cache_clear_pattern便捷函数"""
        mock_service.clear_pattern.return_value = 5
        
        result = cache_clear_pattern("test:*", "custom")
        assert result == 5
        mock_service.clear_pattern.assert_called_once_with("test:*", "custom")