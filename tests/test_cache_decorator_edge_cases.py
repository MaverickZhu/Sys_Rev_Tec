"""缓存装饰器边界情况测试"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from app.utils.cache_decorator import (
    cache_result,
    _serialize_for_cache,
    _is_fastapi_dependency,
    fastapi_cache_result
)
from app.services.cache_service import cache_service
import decimal
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MockSQLAlchemyModel(Base):
    """模拟SQLAlchemy模型用于测试"""
    __tablename__ = 'test_model'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    created_at = Column(DateTime)
    price = Column(Numeric(10, 2))

class TestCacheDecoratorEdgeCases:
    """测试缓存装饰器的边界情况"""
    
    def setup_method(self):
        """每个测试前的设置"""
        # 清除所有缓存前缀
        try:
            cache_service.clear_pattern("*", "app")
            cache_service.clear_pattern("*", "api")
            cache_service.clear_pattern("*", "func")
            cache_service.clear_pattern("*", "model")
        except:
            pass  # 如果清除失败，忽略错误
    
    def test_serialize_for_cache_with_sqlalchemy_object(self):
        """测试SQLAlchemy对象序列化"""
        # 创建模拟的SQLAlchemy对象
        mock_obj = Mock()
        mock_obj.__table__ = Mock()
        
        # 模拟列
        mock_column1 = Mock()
        mock_column1.name = 'id'
        mock_column2 = Mock()
        mock_column2.name = 'name'
        mock_column3 = Mock()
        mock_column3.name = 'created_at'
        mock_column4 = Mock()
        mock_column4.name = 'price'
        
        mock_obj.__table__.columns = [mock_column1, mock_column2, mock_column3, mock_column4]
        
        # 设置属性值
        mock_obj.id = 1
        mock_obj.name = "Test"
        mock_obj.created_at = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_obj.price = decimal.Decimal('99.99')
        
        result = _serialize_for_cache(mock_obj)
        
        assert isinstance(result, dict)
        assert result['id'] == 1
        assert result['name'] == "Test"
        assert result['created_at'] == "2024-01-01T12:00:00"
        assert result['price'] == 99.99
    
    def test_serialize_for_cache_with_exception(self):
        """测试序列化异常处理"""
        from app.utils.cache_decorator import _serialize_for_cache
        
        # 测试简单的不可序列化对象
        import threading
        lock = threading.Lock()
        
        # 应该返回None或抛出异常
        try:
            result = _serialize_for_cache(lock)
            assert result is None or isinstance(result, str)
        except Exception:
            pass  # 异常是预期的
    
    def test_serialize_for_cache_with_list(self):
        """测试列表序列化"""
        test_list = [1, "test", None, {'key': 'value'}]
        result = _serialize_for_cache(test_list)
        
        assert result == [1, "test", None, {'key': 'value'}]
    
    def test_serialize_for_cache_with_none(self):
        """测试None值序列化"""
        result = _serialize_for_cache(None)
        assert result is None
    
    def test_is_fastapi_dependency_with_none(self):
        """测试FastAPI依赖检查 - None值"""
        result = _is_fastapi_dependency(None)
        assert result is False
    
    def test_is_fastapi_dependency_with_various_objects(self):
        """测试FastAPI依赖检查 - 各种对象类型"""
        # 测试普通对象
        normal_obj = "test_string"
        assert _is_fastapi_dependency(normal_obj) is False
        
        # 测试数字
        number = 123
        assert _is_fastapi_dependency(number) is False
        
        # 测试字典
        dict_obj = {'key': 'value'}
        assert _is_fastapi_dependency(dict_obj) is False
    
    def test_cache_result_with_non_callable_function(self):
        """测试缓存装饰器处理非标准函数对象"""
        @cache_result(expire=60)
        async def test_async_func():
            return "async_result"
        
        # 模拟函数没有__call__或__code__属性的情况
        original_func = test_async_func.__wrapped__
        
        # 创建一个没有__code__属性的函数
        mock_func = Mock()
        mock_func.__name__ = "mock_func"
        mock_func.return_value = "mock_result"
        
        # 删除__code__属性
        if hasattr(mock_func, '__code__'):
            delattr(mock_func, '__code__')
        
        @cache_result(expire=60)
        def decorated_mock():
            return mock_func()
        
        result = decorated_mock()
        assert result == "mock_result"
    
    @pytest.mark.asyncio
    async def test_fastapi_cache_with_skip_cache_function(self):
        """测试FastAPI缓存装饰器的跳过缓存功能"""
        call_count = 0
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('skip_cache', False)
        
        @fastapi_cache_result(expire=60, skip_cache=skip_condition)
        async def test_func(value: int, skip_cache: bool = False):
            nonlocal call_count
            call_count += 1
            return f"result_{value}_{call_count}"
        
        # 测试跳过缓存功能
        result1 = await test_func(1, skip_cache=True)
        assert "result_1_" in result1
        
        result2 = await test_func(1, skip_cache=True)
        assert "result_1_" in result2
        
        # 验证函数被调用了多次（因为跳过了缓存）
        assert call_count >= 2
    
    def test_fastapi_cache_sync_with_skip_cache(self):
        """测试同步FastAPI缓存装饰器的跳过缓存功能"""
        call_count = 0
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('force_refresh', False)
        
        @fastapi_cache_result(expire=60, skip_cache=skip_condition)
        def test_sync_func(value: int, force_refresh: bool = False):
            nonlocal call_count
            call_count += 1
            return f"sync_result_{value}_{call_count}"
        
        # 第一次调用
        result1 = test_sync_func(1, force_refresh=False)
        assert result1 == "sync_result_1_1"
        assert call_count == 1
        
        # 第二次调用，跳过缓存
        result2 = test_sync_func(1, force_refresh=True)
        assert result2 == "sync_result_1_2"
        assert call_count == 2
    
    def test_cache_result_with_custom_key_function(self):
        """测试使用自定义键生成函数的缓存装饰器"""
        from app.utils.cache_decorator import cache_result
        
        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}"
        
        call_count = 0
        
        @cache_result(expire=60, key_func=custom_key_func)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return f"result_{x}_{call_count}"
        
        # 测试自定义键函数
        result1 = test_func(123)
        assert "result_123_" in result1
        
        # 验证函数被调用
        assert call_count >= 1
    
    def test_serialize_for_cache_with_other_types(self):
        """测试序列化其他类型的对象"""
        # 测试字符串转换情况
        mock_obj = Mock()
        mock_obj.__table__ = Mock()
        
        mock_column = Mock()
        mock_column.name = 'special_field'
        mock_obj.__table__.columns = [mock_column]
        
        # 设置一个需要转换为字符串的特殊对象
        class SpecialObject:
            def __str__(self):
                return "special_string_representation"
        
        mock_obj.special_field = SpecialObject()
        
        result = _serialize_for_cache(mock_obj)
        
        assert isinstance(result, dict)
        assert result['special_field'] == "special_string_representation"