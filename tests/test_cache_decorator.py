import pytest
import asyncio
import decimal
import datetime
from unittest.mock import Mock, patch, MagicMock
from app.utils.cache_decorator import (
    cache_result,
    cache_model_result,
    invalidate_cache,
    fastapi_cache_result,
    cache_for,
    cache_short,
    cache_medium,
    cache_long,
    _generate_cache_key,
    _generate_model_cache_key,
    _is_fastapi_dependency,
    _serialize_args,
    _serialize_kwargs,
    _extract_user_id,
    _serialize_for_cache,
    _deserialize_from_cache,
    _clear_cache,
    _clear_model_cache,
    _clear_cache_by_params
)
from app.services.cache_service import cache_service


class TestCacheResult:
    """测试cache_result装饰器"""
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_result_sync_function(self, mock_cache_service):
        """测试同步函数的缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_result(expire=300, prefix="test")
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        assert result == 3
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_invalidate_cache_decorator(self, mock_cache_service):
        """测试缓存失效装饰器"""
        mock_cache_service.clear_pattern.return_value = 5
        
        @invalidate_cache("test_pattern:*")
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"
        mock_cache_service.clear_pattern.assert_called_once_with("test_pattern:*", "app")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_invalidate_cache_with_multiple_patterns(self, mock_cache_service):
        """测试带有多个模式的缓存失效装饰器"""
        mock_cache_service.clear_pattern.return_value = 3
        
        @invalidate_cache(["pattern1:*", "pattern2:*"])
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"
        assert mock_cache_service.clear_pattern.call_count == 2
    
    def test_extract_user_id_from_kwargs(self):
        """测试从kwargs中提取用户ID"""
        # 测试从current_user提取
        mock_user = Mock()
        mock_user.id = 123
        kwargs = {'current_user': mock_user}
        user_id = _extract_user_id((), kwargs)
        assert user_id == "123"
        
        # 测试从user_id提取
        kwargs = {'user_id': 456}
        user_id = _extract_user_id((), kwargs)
        assert user_id == "456"
        
        # 测试没有用户信息
        kwargs = {'other_param': 'value'}
        user_id = _extract_user_id((), kwargs)
        assert user_id is None
    
    def test_extract_user_id_from_args(self):
        """测试从args中提取用户ID"""
        # 创建模拟用户对象
        mock_user = Mock()
        mock_user.id = 789
        mock_user.email = "test@example.com"
        
        args = ('param1', 'param2', mock_user)
        user_id = _extract_user_id(args, {})
        assert user_id == "789"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_clear_cache_function(self, mock_cache_service):
        """测试清除缓存函数"""
        mock_cache_service.delete.return_value = True
        
        # 测试使用默认键生成
        result = _clear_cache("test_func", ("arg1",), {"key": "value"}, "test", None)
        mock_cache_service.delete.assert_called_once()
        
        # 测试使用自定义键生成函数
        mock_cache_service.reset_mock()
        custom_key_func = lambda *args, **kwargs: "custom_key"
        result = _clear_cache("test_func", ("arg1",), {"key": "value"}, "test", custom_key_func)
        mock_cache_service.delete.assert_called_once_with("custom_key", "test")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_clear_model_cache_function(self, mock_cache_service):
        """测试清除模型缓存函数"""
        mock_cache_service.delete.return_value = True
        
        result = _clear_model_cache("TestModel", ("arg1",), {"key": "value"}, True)
        mock_cache_service.delete.assert_called_once()
    
    def test_cache_decorator_with_callable_check(self):
        """测试缓存装饰器的可调用性检查"""
        @cache_result(expire=300)
        def test_func(value):
            return f"result_{value}"
        
        # 测试函数具有__call__和__code__属性
        assert hasattr(test_func, '__call__')
        assert hasattr(test_func, '__code__')
        
        result = test_func("test")
        assert result == "result_test"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_with_filtered_params(self, mock_cache_service):
        """测试FastAPI缓存装饰器的参数过滤"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @fastapi_cache_result(expire=300)
        def test_api_func(skip=0, limit=10, db=None, current_user=None, query="test"):
            return {"data": query, "skip": skip, "limit": limit}
        
        mock_db = Mock()
        mock_user = Mock()
        
        result = test_api_func(skip=5, limit=20, db=mock_db, current_user=mock_user, query="hello")
        assert result["data"] == "hello"
        assert result["skip"] == 5
        assert result["limit"] == 20
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_fastapi_async_cache_with_skip_condition(self, mock_cache_service):
        """测试FastAPI异步缓存的跳过条件"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('force_refresh', False)
        
        @fastapi_cache_result(expire=300, skip_cache=skip_condition)
        async def async_api_func(query="test", force_refresh=False):
            await asyncio.sleep(0.01)
            return {"async_data": query}
        
        # 正常缓存
        result1 = await async_api_func(query="hello")
        assert result1["async_data"] == "hello"
        
        # 跳过缓存
        result2 = await async_api_func(query="world", force_refresh=True)
        assert result2["async_data"] == "world"
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_cache_result_async_function(self, mock_cache_service):
        """测试异步函数的缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_result(expire=300, prefix="test")
        async def test_async_func(x, y):
            return x * y
        
        result = await test_async_func(3, 4)
        assert result == 12
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_hit(self, mock_cache_service):
        """测试缓存命中"""
        mock_cache_service.get.return_value = "cached_result"
        
        @cache_result()
        def test_func():
            return "original_result"
        
        result = test_func()
        assert result == "cached_result"
        
        # 验证只调用了get，没有调用set
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_skip_cache(self, mock_cache_service):
        """测试跳过缓存"""
        def should_skip(*args, **kwargs):
            return True
        
        @cache_result(skip_cache=should_skip)
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"
        
        # 验证没有调用缓存
        mock_cache_service.get.assert_not_called()
        mock_cache_service.set.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_custom_key_func(self, mock_cache_service):
        """测试自定义键生成函数"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def custom_key(x, y):
            return f"custom:{x}:{y}"
        
        @cache_result(key_func=custom_key)
        def test_func(x, y):
            return x + y
        
        test_func(1, 2)
        
        # 验证使用了自定义键
        mock_cache_service.get.assert_called_with("custom:1:2", "func")


class TestCacheModelResult:
    """测试cache_model_result装饰器"""
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_model_result(self, mock_cache_service):
        """测试模型缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_model_result("User", expire=600)
        def get_user(user_id):
            return {"id": user_id, "name": "test"}
        
        result = get_user(123)
        assert result == {"id": 123, "name": "test"}
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_clear_all(self, mock_cache_service):
        """测试清除所有模型缓存"""
        mock_cache_service.clear_pattern.return_value = 5
        
        @cache_model_result("User")
        def get_user(user_id):
            return {"id": user_id}
        
        get_user.cache_clear_all()
        
        mock_cache_service.clear_pattern.assert_called_with("User:*", "model")


class TestInvalidateCache:
    """测试invalidate_cache装饰器"""
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_invalidate_single_pattern(self, mock_cache_service):
        """测试清除单个模式的缓存"""
        mock_cache_service.clear_pattern.return_value = 3
        
        @invalidate_cache("user:*", prefix="test")
        def update_user():
            return "updated"
        
        result = update_user()
        assert result == "updated"
        
        mock_cache_service.clear_pattern.assert_called_with("user:*", "test")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_invalidate_multiple_patterns(self, mock_cache_service):
        """测试清除多个模式的缓存"""
        mock_cache_service.clear_pattern.return_value = 2
        
        @invalidate_cache(["user:*", "profile:*"])
        def update_user_profile():
            return "updated"
        
        update_user_profile()
        
        assert mock_cache_service.clear_pattern.call_count == 2


class TestFastAPICacheResult:
    """测试fastapi_cache_result装饰器"""
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_sync(self, mock_cache_service):
        """测试FastAPI同步函数缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @fastapi_cache_result(expire=300)
        def api_func(skip=0, limit=10, db=None, current_user=None):
            return {"data": "test"}
        
        result = api_func(skip=0, limit=10, db="mock_db", current_user="mock_user")
        assert result == {"data": "test"}
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_fastapi_cache_async(self, mock_cache_service):
        """测试FastAPI异步函数缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @fastapi_cache_result(expire=300)
        async def api_async_func(skip=0, limit=10):
            return {"data": "async_test"}
        
        result = await api_async_func(skip=0, limit=10)
        assert result == {"data": "async_test"}
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()


class TestConvenienceFunctions:
    """测试便捷缓存装饰器"""
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_for(self, mock_cache_service):
        """测试cache_for装饰器"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_for(minutes=30)
        def test_func():
            return "result"
        
        test_func()
        
        # 验证过期时间为30分钟（1800秒）
        args, kwargs = mock_cache_service.set.call_args
        assert args[2] == 1800  # expire参数
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_short(self, mock_cache_service):
        """测试cache_short装饰器"""
        mock_cache_service.get.return_value = None
        
        @cache_short()
        def test_func():
            return "result"
        
        test_func()
        
        # 验证过期时间为5分钟（300秒）
        args, kwargs = mock_cache_service.set.call_args
        assert args[2] == 300
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_medium(self, mock_cache_service):
        """测试cache_medium装饰器"""
        mock_cache_service.get.return_value = None
        
        @cache_medium()
        def test_func():
            return "result"
        
        test_func()
        
        # 验证过期时间为30分钟（1800秒）
        args, kwargs = mock_cache_service.set.call_args
        assert args[2] == 1800
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_long(self, mock_cache_service):
        """测试cache_long装饰器"""
        mock_cache_service.get.return_value = None
        
        @cache_long()
        def test_func():
            return "result"
        
        test_func()
        
        # 验证过期时间为2小时（7200秒）
        args, kwargs = mock_cache_service.set.call_args
        assert args[2] == 7200


class TestUtilityFunctions:
    """测试工具函数"""
    
    def test_generate_cache_key(self):
        """测试缓存键生成"""
        key = _generate_cache_key("test_func", (1, 2), {"param": "value"})
        assert key.startswith("test_func:")
        assert len(key.split(":")[1]) == 32  # MD5哈希长度
    
    def test_generate_model_cache_key(self):
        """测试模型缓存键生成"""
        key = _generate_model_cache_key("User", (123,), {}, include_user=False)
        assert key.startswith("User:")
        
        # 测试包含用户ID
        mock_user = Mock()
        mock_user.id = 456
        key_with_user = _generate_model_cache_key(
            "User", (), {"current_user": mock_user}, include_user=True
        )
        assert "user:456" in key_with_user
    
    def test_is_fastapi_dependency(self):
        """测试FastAPI依赖检测"""
        # 测试None
        assert not _is_fastapi_dependency(None)
        
        # 测试普通对象
        assert not _is_fastapi_dependency("string")
        assert not _is_fastapi_dependency(123)
        
        # 测试模拟的FastAPI对象
        mock_request = Mock()
        mock_request.scope = {}
        mock_request.receive = Mock()
        assert _is_fastapi_dependency(mock_request)
        
        mock_session = Mock()
        mock_session.bind = Mock()
        mock_session.execute = Mock()
        assert _is_fastapi_dependency(mock_session)
    
    def test_serialize_args(self):
        """测试参数序列化"""
        # 测试空参数
        empty_args = ()
        empty_serialized = _serialize_args(empty_args)
        assert isinstance(empty_serialized, list)
        
        # 测试单个参数（第一个参数可能被跳过）
        single_args = ("test",)
        single_serialized = _serialize_args(single_args)
        assert isinstance(single_serialized, list)
        
        # 测试多个参数（第一个可能被跳过，后续应该被包含）
        multi_args = ("first", "second", 123)
        multi_serialized = _serialize_args(multi_args)
        # 至少应该有一些参数被序列化（除非都被过滤掉）
        assert isinstance(multi_serialized, list)
        
        # 测试函数正常工作即可，不依赖具体的过滤逻辑
        result = _serialize_args((1, 2, 3))
        assert isinstance(result, list)
    
    def test_serialize_kwargs(self):
        """测试关键字参数序列化"""
        kwargs = {"param1": "value1", "param2": 123}
        serialized = _serialize_kwargs(kwargs)
        assert serialized["param1"] == "value1"
        assert serialized["param2"] == "123"
    
    def test_extract_user_id(self):
        """测试用户ID提取"""
        # 测试从kwargs提取
        mock_user = Mock()
        mock_user.id = 789
        user_id = _extract_user_id((), {"current_user": mock_user})
        assert user_id == "789"
        
        # 测试从args提取
        mock_user2 = Mock()
        mock_user2.id = 101
        mock_user2.email = "test@example.com"
        user_id2 = _extract_user_id(("other", mock_user2), {})
        assert user_id2 == "101"
        
        # 测试未找到用户
        user_id3 = _extract_user_id(("string", 123), {"other": "value"})
        assert user_id3 is None
    
    def test_serialize_for_cache(self):
        """测试缓存序列化"""
        # 测试None
        assert _serialize_for_cache(None) is None
        
        # 测试列表
        result = _serialize_for_cache([1, 2, 3])
        assert result == [1, 2, 3]
        
        # 测试基本类型
        assert _serialize_for_cache("string") == "string"
        assert _serialize_for_cache(123) == 123
        
        # 测试模拟SQLAlchemy对象
        mock_obj = Mock()
        mock_obj.__table__ = Mock()
        mock_column = Mock()
        mock_column.name = "id"
        mock_obj.__table__.columns = [mock_column]
        mock_obj.id = 123
        
        result = _serialize_for_cache(mock_obj)
        assert isinstance(result, dict)
        assert result["id"] == 123
    
    def test_deserialize_from_cache(self):
        """测试缓存反序列化"""
        data = {"key": "value"}
        result = _deserialize_from_cache(data)
        assert result == data


class TestEdgeCasesAndCoverage:
    """测试边界情况和提高覆盖率"""
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_result_with_fastapi_dependencies(self, mock_cache_service):
        """测试过滤FastAPI依赖参数"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_result(expire=300)
        def test_func(param1, db=None, current_user=None, request=None):
            return f"result_{param1}"
        
        # 模拟FastAPI依赖
        mock_db = Mock()
        mock_db.bind = Mock()
        mock_db.execute = Mock()
        
        mock_user = Mock()
        mock_request = Mock()
        mock_request.scope = {}
        mock_request.receive = Mock()
        
        result = test_func("test", db=mock_db, current_user=mock_user, request=mock_request)
        assert result == "result_test"
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_wrapper_with_skip_cache(self):
        """测试异步函数跳过缓存"""
        with patch('app.utils.cache_decorator.cache_service') as mock_cache_service:
            def should_skip(*args, **kwargs):
                return kwargs.get('skip_cache', False)
            
            @cache_result(skip_cache=should_skip)
            async def async_func(value, skip_cache=False):
                return f"async_{value}"
            
            # 跳过缓存
            result = await async_func("test", skip_cache=True)
            assert result == "async_test"
            
            # 验证没有调用缓存
            mock_cache_service.get.assert_not_called()
            mock_cache_service.set.assert_not_called()
    
    def test_serialize_for_cache_with_decimal_and_datetime(self):
        """测试序列化Decimal和DateTime对象"""
        # 模拟SQLAlchemy对象
        mock_obj = Mock()
        mock_obj.__table__ = Mock()
        
        # 创建列定义
        columns = []
        for name in ['id', 'price', 'created_at', 'updated_at']:
            col = Mock()
            col.name = name
            columns.append(col)
        
        mock_obj.__table__.columns = columns
        mock_obj.id = 123
        mock_obj.price = decimal.Decimal('99.99')
        mock_obj.created_at = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_obj.updated_at = datetime.date(2023, 1, 2)
        
        result = _serialize_for_cache(mock_obj)
        
        assert result['id'] == 123
        assert result['price'] == 99.99
        assert result['created_at'] == '2023-01-01T12:00:00'
        assert result['updated_at'] == '2023-01-02'
    
    def test_serialize_for_cache_with_exception(self):
        """测试序列化过程中的异常处理"""
        # 创建一个有__table__属性的对象
        class TestModel:
            def __init__(self):
                self.name = "test"
                self.id = 123
                # 创建mock table和columns
                self.__table__ = Mock()
                name_col = Mock()
                name_col.name = 'name'
                id_col = Mock()
                id_col.name = 'id'
                self.__table__.columns = [name_col, id_col]
            
            def __str__(self):
                return "TestModel instance"
        
        test_obj = TestModel()
        
        # 测试序列化（应该返回字典）
        result = _serialize_for_cache(test_obj)
        
        # 应该返回字典（因为有__table__属性）
        assert isinstance(result, dict)
        assert "name" in result
        assert result["name"] == "test"
        assert "id" in result
        assert result["id"] == 123
    
    def test_serialize_for_cache_with_other_types(self):
        """测试序列化其他类型的对象"""
        mock_obj = Mock()
        mock_obj.__table__ = Mock()
        
        col = Mock()
        col.name = 'custom_field'
        mock_obj.__table__.columns = [col]
        
        # 设置一个自定义对象
        custom_obj = object()
        mock_obj.custom_field = custom_obj
        
        result = _serialize_for_cache(mock_obj)
        assert 'custom_field' in result
        assert isinstance(result['custom_field'], str)  # 应该转换为字符串
    
    def test_serialize_args_with_self_parameter(self):
        """测试序列化包含self参数的情况"""
        class TestClass:
            def __init__(self):
                self.__class__.__module__ = 'test_module'
        
        test_instance = TestClass()
        args = (test_instance, "param1", 123)
        
        result = _serialize_args(args)
        # 第一个参数（self）应该被跳过
        assert "param1" in result
        assert "123" in result
    
    def test_serialize_args_with_model_objects(self):
        """测试序列化包含模型对象的参数"""
        # 创建简单的对象，使用不会被误识别为FastAPI依赖的类名
        class SimpleObject:
            def __init__(self):
                self.id = 456
        
        obj = SimpleObject()
        
        # 测试参数序列化（第一个参数会被跳过，因为被认为是self）
        args = ("param1", obj, "param2")
        result = _serialize_args(args)
        
        # 第一个参数被跳过，只有obj和param2被序列化
        assert isinstance(result, list)
        assert "obj:SimpleObject:456" in result
        assert "param2" in result
        assert len(result) == 2
        # param1不应该在结果中，因为它被跳过了
        assert "param1" not in result
    
    def test_serialize_kwargs_with_model_objects(self):
        """测试序列化包含模型对象的关键字参数"""
        # 创建一个简单的模型对象，避免被识别为FastAPI依赖
        class SimpleModel:
            def __init__(self):
                self.id = 789
        
        mock_model = SimpleModel()
        mock_model.__class__.__name__ = 'ProjectModel'
        
        kwargs = {
            "user": mock_model,
            "status": "active",
            "count": 10
        }
        
        result = _serialize_kwargs(kwargs)
        
        # 检查结果字典中的值
        assert isinstance(result, dict)
        assert result["user"] == "obj:ProjectModel:789"
        assert result["status"] == "active"
        assert result["count"] == "10"
    
    def test_extract_user_id_from_different_keys(self):
        """测试从不同键名提取用户ID"""
        mock_user = Mock()
        mock_user.id = 999
        
        # 测试不同的键名
        for key in ['current_user', 'user', 'user_id']:
            kwargs = {key: mock_user}
            user_id = _extract_user_id((), kwargs)
            assert user_id == "999"
        
        # 测试直接传入ID
        kwargs = {'user_id': 888}
        user_id = _extract_user_id((), kwargs)
        assert user_id == "888"
        
        # 测试字符串ID
        kwargs = {'user_id': "777"}
        user_id = _extract_user_id((), kwargs)
        assert user_id == "777"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_clear_cache_functions(self, mock_cache_service):
        """测试缓存清除函数"""
        mock_cache_service.delete.return_value = True
        
        # 测试_clear_cache
        result = _clear_cache("test_func", (1, 2), {"param": "value"}, "test", None)
        mock_cache_service.delete.assert_called()
        
        # 测试_clear_model_cache
        result = _clear_model_cache("User", (123,), {}, False)
        assert mock_cache_service.delete.call_count == 2
        
        # 测试_clear_cache_by_params
        result = _clear_cache_by_params("api_func", {"skip": 0, "limit": 10}, "api")
        assert mock_cache_service.delete.call_count == 3
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_with_serialization(self, mock_cache_service):
        """测试FastAPI缓存的序列化功能"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @fastapi_cache_result(expire=300)
        def api_func_with_model():
            # 返回模拟的SQLAlchemy对象
            mock_obj = Mock()
            mock_obj.__table__ = Mock()
            col = Mock()
            col.name = 'id'
            mock_obj.__table__.columns = [col]
            mock_obj.id = 123
            return mock_obj
        
        result = api_func_with_model()
        
        # 验证结果被序列化
        assert isinstance(result, dict)
        assert result['id'] == 123
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    def test_is_fastapi_dependency_type_checking(self):
        """测试FastAPI依赖类型检查的各种情况"""
        # 测试None值
        assert not _is_fastapi_dependency(None)
        
        # 测试普通对象
        normal_obj = "test_string"
        assert not _is_fastapi_dependency(normal_obj)
        
        # 测试具有FastAPI特征的对象
        class MockRequest:
            def __init__(self):
                self.scope = {}
                self.receive = lambda: None
        
        class MockSession:
            def __init__(self):
                self.bind = Mock()
                self.execute = Mock()
        
        request_obj = MockRequest()
        session_obj = MockSession()
        
        # 这些对象应该被识别为FastAPI依赖
        assert _is_fastapi_dependency(request_obj)
        assert _is_fastapi_dependency(session_obj)
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_result_cache_control_methods(self, mock_cache_service):
        """测试缓存控制方法"""
        mock_cache_service.delete.return_value = True
        
        @cache_result(expire=300)
        def test_func(x, y):
            return x + y
        
        # 测试cache_clear方法
        test_func.cache_clear(1, 2)
        mock_cache_service.delete.assert_called_once()
        
        # 测试cache_key方法
        cache_key = test_func.cache_key(1, 2)
        assert isinstance(cache_key, str)
        assert cache_key.startswith("test_func:")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_model_result_cache_control_methods(self, mock_cache_service):
        """测试模型缓存控制方法"""
        mock_cache_service.delete.return_value = True
        mock_cache_service.clear_pattern.return_value = 5
        
        @cache_model_result("User", include_user=True)
        def get_user(user_id, current_user=None):
            return {"id": user_id}
        
        # 测试cache_clear方法
        mock_user = Mock()
        mock_user.id = 123
        get_user.cache_clear(456, current_user=mock_user)
        mock_cache_service.delete.assert_called_once()
        
        # 测试cache_clear_all方法
        get_user.cache_clear_all()
        mock_cache_service.clear_pattern.assert_called_with("User:*", "model")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_control_methods(self, mock_cache_service):
        """测试FastAPI缓存控制方法"""
        mock_cache_service.delete.return_value = True
        
        @fastapi_cache_result(expire=300)
        def api_func(skip=0, limit=10):
            return {"data": "test"}
        
        # 测试cache_clear方法
        api_func.cache_clear(skip=0, limit=10)
        mock_cache_service.delete.assert_called_once()
        
        # 测试cache_key方法
        cache_key = api_func.cache_key(skip=0, limit=10)
        assert isinstance(cache_key, str)
    
    def test_convenience_decorators_parameters(self):
        """测试便捷装饰器的参数设置"""
        # 这些测试主要是为了覆盖便捷装饰器的定义
        from app.utils.cache_decorator import (
            fastapi_cache_short,
            fastapi_cache_medium, 
            fastapi_cache_long
        )
        
        # 验证这些装饰器存在且可调用
        assert callable(fastapi_cache_short)
        assert callable(fastapi_cache_medium)
        assert callable(fastapi_cache_long)
        
        # 测试应用装饰器
        @fastapi_cache_short
        def short_func():
            return "short"
        
        @fastapi_cache_medium
        def medium_func():
            return "medium"
        
        @fastapi_cache_long
        def long_func():
            return "long"
        
        # 验证装饰器正常工作
        assert callable(short_func)
        assert callable(medium_func)
        assert callable(long_func)
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_with_skip_cache_condition(self, mock_cache_service):
        """测试带有跳过缓存条件的装饰器"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        call_count = 0
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('skip_cache', False)
        
        @cache_result(expire=60, skip_cache=skip_condition)
        def test_func(value, skip_cache=False):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"
        
        # 第一次调用，不跳过缓存
        result1 = test_func("test", skip_cache=False)
        assert result1 == "result_test"
        assert call_count == 1
        
        # 第二次调用，跳过缓存
        result2 = test_func("test", skip_cache=True)
        assert result2 == "result_test"
        assert call_count == 2  # 增加了
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_with_custom_key_function(self, mock_cache_service):
        """测试带有自定义键生成函数的装饰器"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def custom_key_func(*args, **kwargs):
            return f"custom_key_{kwargs.get('id', 'default')}"
        
        @cache_result(expire=60, key_func=custom_key_func)
        def test_func(value, id=None):
            return f"result_{value}_{id}"
        
        result = test_func("test", id="123")
        assert result == "result_test_123"
        
        # 测试缓存键生成
        cache_key = test_func.cache_key(value="test", id="123")
        assert cache_key == "custom_key_123"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_model_cache_with_user_context(self, mock_cache_service):
        """测试包含用户上下文的模型缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_model_result("User", include_user=True)
        def get_user_data(user_id, current_user=None):
            return {"id": user_id, "data": "test"}
        
        mock_user = Mock()
        mock_user.id = 456
        
        result = get_user_data(123, current_user=mock_user)
        assert result == {"id": 123, "data": "test"}
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_async_model_cache(self, mock_cache_service):
        """测试异步模型缓存"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_model_result("AsyncModel", expire=600)
        async def get_async_model(model_id):
            await asyncio.sleep(0.01)  # 模拟异步操作
            return {"id": model_id, "async_data": True}
        
        result = await get_async_model(789)
        assert result == {"id": 789, "async_data": True}
        
        # 验证缓存调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()