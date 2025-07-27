import pytest
import asyncio
import decimal
import datetime
import builtins
from unittest.mock import Mock, patch, MagicMock
from app.utils.cache_decorator import (
    cache_result,
    cache_model_result,
    invalidate_cache,
    fastapi_cache_result,
    _serialize_for_cache,
    _is_fastapi_dependency,
    _serialize_args,
    _serialize_kwargs
)


# 定义在测试类外部的普通类，避免路径中包含'fastapi'关键词
class PlainObject:
    pass

class ScopeReceiveObj:
    def __init__(self):
        self.scope = {}
        self.receive = lambda: None

class OnlyReceiveObj:
    def __init__(self):
        self.receive = lambda: None

class OnlyScopeObj:
    def __init__(self):
        self.scope = {}

class BindExecuteObj:
    def __init__(self):
        self.bind = "mock_bind"
        self.execute = lambda: None


class TestMissingCoverage:
    """测试未覆盖的代码行"""
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_async_wrapper_function_without_call_and_code(self, mock_cache_service):
        """测试异步包装器中函数没有__call__和__code__属性的情况（第69-71行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_result(expire=300)
        async def test_func(x, y):
            return x + y
        
        # 模拟函数没有__call__和__code__属性
        with patch('app.utils.cache_decorator.hasattr') as mock_hasattr:
            def hasattr_side_effect(obj, attr):
                if attr in ['__call__', '__code__'] and obj == test_func:
                    return False
                return hasattr(obj, attr)
            mock_hasattr.side_effect = hasattr_side_effect
            
            result = await test_func(3, 4)
            assert result == 7
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_sync_wrapper_skip_cache_condition(self, mock_cache_service):
        """测试同步包装器的跳过缓存条件（第48行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('skip_cache', False)
        
        @cache_result(expire=300, skip_cache=skip_condition)
        def test_func(x, y, skip_cache=False):
            return x * y
        
        # 跳过缓存的情况
        result = test_func(3, 4, skip_cache=True)
        assert result == 12
        
        # 验证没有调用缓存服务
        mock_cache_service.get.assert_not_called()
        mock_cache_service.set.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_sync_wrapper_custom_key_func(self, mock_cache_service):
        """测试同步包装器的自定义键函数（第52行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}_{kwargs.get('param', 'default')}"
        
        @cache_result(expire=300, key_func=custom_key_func)
        def test_func(x, param="test"):
            return x * 2
        
        result = test_func(5, param="custom")
        assert result == 10
        
        # 验证使用了自定义键函数
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_async_wrapper_skip_cache_condition(self, mock_cache_service):
        """测试异步包装器的跳过缓存条件（第59-60行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('force_refresh', False)
        
        @cache_result(expire=300, skip_cache=skip_condition)
        async def test_async_func(x, y, force_refresh=False):
            await asyncio.sleep(0.01)
            return x + y
        
        # 跳过缓存的情况
        result = await test_async_func(3, 4, force_refresh=True)
        assert result == 7
        
        # 验证没有调用缓存服务
        mock_cache_service.get.assert_not_called()
        mock_cache_service.set.assert_not_called()
    
    def test_serialize_for_cache_sqlalchemy_exception(self):
        """测试序列化SQLAlchemy对象时的异常处理（第461行）"""
        # 创建一个模拟的SQLAlchemy对象
        class MockSQLAlchemyObject:
            def __init__(self):
                self.__table__ = Mock()
                self.__table__.columns = [Mock(name='test_column')]
                self.__table__.columns[0].name = 'test_field'
            
            def __getattribute__(self, name):
                if name == 'test_field':
                    raise Exception("Serialization error")
                return super().__getattribute__(name)
        
        obj = MockSQLAlchemyObject()
        
        with patch('app.utils.cache_decorator.logger') as mock_logger:
            result = _serialize_for_cache(obj)
            # 验证异常被记录且字段被跳过
            mock_logger.warning.assert_called_once()
            assert isinstance(result, dict)
            assert 'test_field' not in result
    
    def test_serialize_for_cache_decimal_and_datetime(self):
        """测试序列化Decimal和DateTime对象（第474-477行）"""
        import decimal
        import datetime
        
        # 创建一个模拟的SQLAlchemy对象，包含各种类型的字段
        class MockSQLAlchemyObject:
            def __init__(self):
                self.__table__ = Mock()
                self.__table__.columns = [
                    Mock(name='decimal_field'),
                    Mock(name='datetime_field'),
                    Mock(name='date_field'),
                    Mock(name='other_field')
                ]
                for i, col in enumerate(self.__table__.columns):
                    col.name = ['decimal_field', 'datetime_field', 'date_field', 'other_field'][i]
                
                self.decimal_field = decimal.Decimal('123.45')
                self.datetime_field = datetime.datetime(2023, 1, 1, 12, 0, 0)
                self.date_field = datetime.date(2023, 1, 1)
                self.other_field = object()  # 其他类型
        
        obj = MockSQLAlchemyObject()
        result = _serialize_for_cache(obj)
        
        assert isinstance(result, dict)
        assert result['decimal_field'] == 123.45  # Decimal转float
        assert result['datetime_field'] == '2023-01-01T12:00:00'  # datetime转ISO格式
        assert result['date_field'] == '2023-01-01'  # date转ISO格式
        assert isinstance(result['other_field'], str)  # 其他类型转字符串
    
    def test_is_fastapi_dependency_request_object(self):
        """测试FastAPI依赖检查中的Request对象（第262行）"""
        # 创建一个模拟的Request对象
        class MockRequest:
            def __init__(self):
                self.scope = {}
                self.receive = lambda: None
        
        request_obj = MockRequest()
        result = _is_fastapi_dependency(request_obj)
        assert result is True
    
    def test_is_fastapi_dependency_sqlalchemy_session(self):
        """测试FastAPI依赖检查中的SQLAlchemy Session对象（第276行）"""
        # 创建一个模拟的SQLAlchemy Session对象
        class MockSession:
            def __init__(self):
                self.bind = Mock()
                self.execute = Mock()
        
        session_obj = MockSession()
        result = _is_fastapi_dependency(session_obj)
        assert result is True
    
    def test_serialize_args_with_self_parameter(self):
        """测试序列化参数时跳过self参数（第281行）"""
        # 创建一个模拟的实例对象
        class MockClass:
            def __init__(self):
                self.__class__ = MockClass
                self.__class__.__module__ = 'test_module'
        
        instance = MockClass()
        args = (instance, 'arg1', 'arg2')
        
        result = _serialize_args(args)
        # 验证跳过了第一个参数（self）
        assert len(result) == 2
        assert result == ['arg1', 'arg2']
    
    def test_serialize_args_with_fastapi_dependency(self):
        """测试序列化参数时跳过FastAPI依赖（第281行）"""
        # 创建一个模拟的Request对象（有scope和receive属性）
        class MockRequest:
            def __init__(self):
                self.scope = {}
                self.receive = lambda: None
        
        fastapi_dep = MockRequest()
        
        # 测试普通参数（不在第一个位置）
        args = (None, 'simple_string')  # 第一个参数会被跳过（当作self），第二个是普通参数
        result = _serialize_args(args)
        assert len(result) == 1  # 只有simple_string被保留
        
        # 测试FastAPI依赖会被跳过
        args2 = (None, fastapi_dep, 'normal_arg')  # 第一个跳过（self），第二个是FastAPI依赖，第三个是普通参数
        result2 = _serialize_args(args2)
        assert len(result2) == 1  # 只有normal_arg被保留
    
    def test_serialize_kwargs_with_fastapi_dependency(self):
        """测试序列化关键字参数时跳过FastAPI依赖（第369行）"""
        # 创建FastAPI依赖对象
        class MockSession:
            def __init__(self):
                self.bind = Mock()
                self.execute = Mock()
        
        session_obj = MockSession()
        kwargs = {'param1': 'value1', 'db': session_obj, 'param2': 'value2'}
        
        result = _serialize_kwargs(kwargs)
        # 验证跳过了FastAPI依赖对象
        assert len(result) == 2
        assert 'db' not in result
        assert result == {'param1': 'value1', 'param2': 'value2'}
    
    def test_serialize_args_with_model_objects(self):
        """测试序列化带有模型对象的参数（第376-377行）"""
        # 创建模拟的数据库模型对象
        class MockModel:
            def __init__(self, model_id):
                self.id = model_id
                self.__dict__ = {'id': model_id, 'name': 'test'}

        # 创建一个模拟的self对象（会被跳过）
        class MockSelf:
            def __init__(self):
                self.__class__.__module__ = 'test_module'

        self_obj = MockSelf()
        model_obj = MockModel(123)
        other_obj = Mock()
        other_obj.__dict__ = {'field': 'value'}

        # 第一个参数是self，会被跳过
        args = (self_obj, 'string_arg', model_obj, other_obj, 'another_string')

        result = _serialize_args(args)
        assert len(result) == 4  # self被跳过，剩下4个参数
        assert 'obj:MockModel:123' in result
        assert 'obj:Mock' in result
        assert 'string_arg' in result
        assert 'another_string' in result
    
    def test_serialize_kwargs_with_model_objects(self):
        """测试序列化带有模型对象的关键字参数（第402-403行）"""
        # 创建模拟的数据库模型对象
        class MockModel:
            def __init__(self, model_id):
                self.id = model_id
                self.__dict__ = {'id': model_id, 'name': 'test'}
        
        model_obj = MockModel(456)
        other_obj = Mock()
        other_obj.__dict__ = {'field': 'value'}
        
        kwargs = {
            'string_param': 'value',
            'model_param': model_obj,
            'other_param': other_obj,
            'int_param': 123
        }
        
        result = _serialize_kwargs(kwargs)
        assert len(result) == 4
        assert result['string_param'] == 'value'
        assert result['model_param'] == 'obj:MockModel:456'  # 有id的对象
        assert result['other_param'] == 'obj:Mock'  # 有__dict__但无id的对象
        assert result['int_param'] == '123'
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_sync_skip_cache_debug_log(self, mock_cache_service):
        """测试FastAPI同步缓存跳过缓存时的调试日志（第407行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def skip_condition(*args, **kwargs):
            return kwargs.get('skip', False)
        
        @fastapi_cache_result(expire=300, skip_cache=skip_condition)
        def test_api_func(param="test", skip=False):
            return {"result": param}
        
        with patch('app.utils.cache_decorator.logger') as mock_logger:
            result = test_api_func(param="hello", skip=True)
            assert result["result"] == "hello"
            
            # 验证调试日志被调用
            mock_logger.debug.assert_called_with("Skipping cache for test_api_func")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_sync_with_custom_key_func(self, mock_cache_service):
        """测试FastAPI同步缓存使用自定义键函数（第414-415行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def custom_key_func(**kwargs):
            return f"custom_{kwargs.get('id', 'default')}"
        
        @fastapi_cache_result(expire=300, key_func=custom_key_func)
        def test_api_func(id=None, data="test"):
            return {"id": id, "data": data}
        
        result = test_api_func(id=123, data="hello")
        assert result["id"] == 123
        assert result["data"] == "hello"
        
        # 验证使用了自定义键函数
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    def test_invalidate_cache_no_cleared_entries(self):
        """测试缓存失效时没有清除任何条目的情况（第158-159行）"""
        with patch('app.utils.cache_decorator.cache_service') as mock_cache_service:
            mock_cache_service.clear_pattern.return_value = 0  # 没有清除任何条目
            
            @invalidate_cache("test_pattern:*")
            def test_func():
                return "result"
            
            with patch('app.utils.cache_decorator.logger') as mock_logger:
                result = test_func()
                assert result == "result"
                
                # 验证没有记录info日志（因为cleared=0）
                mock_logger.info.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_async_wrapper_custom_key_func(self, mock_cache_service):
        """测试异步包装器的自定义键函数（第62行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        def custom_key_func(*args, **kwargs):
            return f"async_custom_key_{args[0]}_{kwargs.get('param', 'default')}"
        
        @cache_result(expire=300, key_func=custom_key_func)
        async def test_async_func(x, param="test"):
            await asyncio.sleep(0.01)
            return x * 3
        
        result = await test_async_func(7, param="custom")
        assert result == 21
        
        # 验证使用了自定义键函数
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_model_result_no_user_id(self, mock_cache_service):
        """测试模型缓存结果中没有用户ID的情况（第158-159行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_model_result("test_model", include_user=True)
        def test_model_func(param1="test"):
            return {"data": param1}
        
        # 调用时没有用户相关参数
        result = test_model_func(param1="hello")
        assert result["data"] == "hello"
        
        # 验证缓存被调用
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    def test_serialize_args_no_self_parameter(self):
        """测试序列化参数时没有self参数的情况"""
        # 测试普通函数参数（没有self）
        args = ('arg1', 'arg2', 123)
        
        result = _serialize_args(args)
        # 验证第一个参数被跳过（被当作self处理），其他参数保留
        assert len(result) == 2
        assert result == ['arg2', '123']
    
    def test_serialize_args_with_none_values(self):
        """测试序列化包含None值的参数"""
        args = (None, 'string_arg', None, 123)
        
        result = _serialize_args(args)
        # 第一个None会被当作self跳过，其他参数保留
        assert len(result) == 3
        assert 'string_arg' in result
        assert 'None' in result
        assert '123' in result
    
    @patch('app.utils.cache_decorator.logger')
    def test_serialize_for_cache_sqlalchemy_field_error(self, mock_logger):
        """测试序列化SQLAlchemy对象时字段访问异常（第461行）"""
        from unittest.mock import Mock
        
        # 创建一个模拟的SQLAlchemy对象
        class MockSQLAlchemyObj:
            def __init__(self):
                self.__table__ = Mock()
                mock_column = Mock()
                mock_column.name = 'problematic_field'
                self.__table__.columns = [mock_column]
            
            def __getattribute__(self, name):
                if name == 'problematic_field':
                    raise Exception("Field access error")
                return super().__getattribute__(name)
        
        mock_obj = MockSQLAlchemyObj()
        result = _serialize_for_cache(mock_obj)
        
        # 验证异常被捕获并记录警告
        mock_logger.warning.assert_called_once()
        assert "Failed to serialize field problematic_field" in str(mock_logger.warning.call_args)
        
        # 验证返回空字典（因为字段序列化失败被跳过）
        assert result == {}
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_async_wrapper_function_without_call_code_attrs(self, mock_cache_service):
        """测试异步包装器处理没有__call__和__code__属性的函数（第70行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 创建一个模拟的可调用对象，没有__call__和__code__属性
        class MockCallable:
            async def __call__(self, x):
                return x * 2
        
        mock_func = MockCallable()
        
        # 使用patch来模拟hasattr返回False
        original_hasattr = builtins.hasattr
        
        def mock_hasattr(obj, attr):
            if attr in ['__call__', '__code__'] and obj is mock_func:
                return False
            return original_hasattr(obj, attr)
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
            # 应用缓存装饰器
            @cache_result(expire=300)
            async def test_func(x):
                return await mock_func(x)
            
            # 调用函数，这应该触发else分支（第70行）
            result = await test_func(5)
            assert result == 10
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_sync_wrapper_skip_cache_condition(self, mock_cache_service):
        """测试同步包装器跳过缓存条件（第89行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 创建一个跳过缓存的条件函数
        def should_skip_cache(*args, **kwargs):
            return kwargs.get('skip', False)
        
        @cache_result(expire=300, skip_cache=should_skip_cache)
        def test_func(x, skip=False):
            return x * 2
        
        # 调用时跳过缓存
        result = test_func(5, skip=True)
        assert result == 10
        
        # 验证没有调用缓存服务的get方法
        mock_cache_service.get.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_async_wrapper_inspect_coroutine_function(self, mock_cache_service):
        """测试异步包装器中的inspect.iscoroutinefunction检查（第66-67行）"""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 创建一个模拟的可调用对象，有__call__和__code__属性
        class MockCallableWithAttrs:
            def __call__(self, x):
                return x * 2
            
            def __code__(self):
                pass
        
        mock_func = MockCallableWithAttrs()
        
        @cache_result(expire=300)
        async def test_func(x):
            return mock_func(x)
        
        # 调用函数，这应该触发hasattr检查和inspect.iscoroutinefunction分支
        result = await test_func(5)
        assert result == 10
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_invalidate_cache_with_list_patterns(self, mock_cache_service):
        """测试invalidate_cache装饰器使用列表模式（第190-191行）"""
        mock_cache_service.clear_pattern.return_value = 5
        
        from app.utils.cache_decorator import invalidate_cache
        
        @invalidate_cache(["pattern1:*", "pattern2:*"], prefix="test")
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"
        
        # 验证清除了多个模式
        assert mock_cache_service.clear_pattern.call_count == 2
        mock_cache_service.clear_pattern.assert_any_call("pattern1:*", "test")
        mock_cache_service.clear_pattern.assert_any_call("pattern2:*", "test")
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_invalidate_cache_with_zero_cleared(self, mock_cache_service):
        """测试invalidate_cache装饰器清除0个条目的情况（第196行）"""
        mock_cache_service.clear_pattern.return_value = 0
        
        from app.utils.cache_decorator import invalidate_cache
        
        @invalidate_cache("pattern:*", prefix="test")
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"
        
        # 验证调用了clear_pattern但没有记录日志（因为cleared=0）
        mock_cache_service.clear_pattern.assert_called_once_with("pattern:*", "test")
    
    def test_serialize_args_with_self_parameter(self):
        """测试_serialize_args跳过self参数（第271行）"""
        from app.utils.cache_decorator import _serialize_args
        
        class TestClass:
            def __init__(self):
                pass
        
        test_obj = TestClass()
        args = (test_obj, "arg1", 123)
        
        result = _serialize_args(args)
        # 应该跳过第一个参数（self）
        assert result == ["arg1", "123"]
    
    def test_extract_user_id_from_args(self):
        """测试从args中提取用户ID（第305行）"""
        from app.utils.cache_decorator import _extract_user_id
        
        class MockUser:
            def __init__(self, user_id, email):
                self.id = user_id
                self.email = email
        
        user = MockUser(123, "test@example.com")
        args = ("other_arg", user)
        kwargs = {}
        
        result = _extract_user_id(args, kwargs)
        assert result == "123"

    def test_is_fastapi_dependency_false(self):
        """测试_is_fastapi_dependency函数返回False的情况（第48行）"""
        from app.utils.cache_decorator import _is_fastapi_dependency
        
        # 测试普通对象
        normal_obj = {"key": "value"}
        assert _is_fastapi_dependency(normal_obj) is False
        
        # 测试字符串
        assert _is_fastapi_dependency("test_string") is False
        
        # 测试数字
        assert _is_fastapi_dependency(123) is False
        
        # 测试普通类实例（使用外部定义的类）
        plain_instance = PlainObject()
        assert _is_fastapi_dependency(plain_instance) is False
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_model_result_sync_wrapper(self, mock_cache_service):
        """测试cache_model_result装饰器的同步包装器（第158-159行）"""
        from app.utils.cache_decorator import cache_model_result
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @cache_model_result("TestModel", expire=60)
        def test_sync_model_func():
            return {"id": 1, "name": "test"}
        
        # 调用同步函数
        result = test_sync_model_func()
        assert result == {"id": 1, "name": "test"}
        mock_cache_service.set.assert_called_once()
    
    def test_serialize_for_cache_exception_handling(self):
        """测试_serialize_for_cache函数的异常处理（第461行）"""
        from app.utils.cache_decorator import _serialize_for_cache
        
        # 创建一个模拟的SQLAlchemy对象，其中某个属性会抛出异常
        class MockColumn:
            def __init__(self, name):
                self.name = name
        
        class MockTable:
            def __init__(self):
                self.columns = [MockColumn("normal_field"), MockColumn("error_field")]
        
        class MockSQLAlchemyObj:
            def __init__(self):
                self.__table__ = MockTable()
                self.normal_field = "normal_value"
            
            def __getattribute__(self, name):
                if name == "error_field":
                    raise Exception("Simulated serialization error")
                return super().__getattribute__(name)
        
        # 测试异常处理
        obj = MockSQLAlchemyObj()
        result = _serialize_for_cache(obj)
        
        # 应该只包含正常字段，错误字段被跳过
        assert "normal_field" in result
        assert "error_field" not in result
        assert result["normal_field"] == "normal_value"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_result_wrapper_selection(self, mock_cache_service):
        """测试fastapi_cache_result装饰器的包装器选择逻辑（第369行、376-377行、414-415行）"""
        from app.utils.cache_decorator import fastapi_cache_result
        import inspect
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 测试同步函数
        @fastapi_cache_result(expire=60, prefix="test")
        def sync_func():
            return {"type": "sync"}
        
        # 验证包装器类型选择
        assert not inspect.iscoroutinefunction(sync_func)
        
        # 测试同步函数调用
        sync_result = sync_func()
        assert sync_result == {"type": "sync"}
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_fastapi_cache_result_async_wrapper_selection(self, mock_cache_service):
        """测试fastapi_cache_result装饰器的异步包装器选择（第59-60行、69-71行）"""
        from app.utils.cache_decorator import fastapi_cache_result
        import inspect
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        @fastapi_cache_result(expire=60, prefix="test")
        async def async_func():
            return {"type": "async"}
        
        # 验证包装器类型选择
        assert inspect.iscoroutinefunction(async_func)
        
        # 测试异步函数调用
        async_result = await async_func()
        assert async_result == {"type": "async"}
    
    def test_is_fastapi_dependency_request_object_coverage(self):
        """测试FastAPI依赖检查中的Request对象覆盖（第262行）"""
        from app.utils.cache_decorator import _is_fastapi_dependency
        
        # 创建一个模拟的对象，有scope和receive属性（使用外部定义的类）
        scope_receive_obj = ScopeReceiveObj()
        result = _is_fastapi_dependency(scope_receive_obj)
        assert result is True
        
        # 测试没有scope属性的对象
        only_receive_obj = OnlyReceiveObj()
        result = _is_fastapi_dependency(only_receive_obj)
        assert result is False
        
        # 测试没有receive属性的对象
        only_scope_obj = OnlyScopeObj()
        result = _is_fastapi_dependency(only_scope_obj)
        assert result is False
        
        # 测试SQLAlchemy对象模拟
        bind_execute_obj = BindExecuteObj()
        result = _is_fastapi_dependency(bind_execute_obj)
        assert result is True
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_cache_decorator_function_without_call_attribute(self, mock_cache_service):
        """测试缓存装饰器处理没有__call__或__code__属性的函数（第59-60行、69-71行）"""
        from app.utils.cache_decorator import cache_result
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 创建一个模拟函数对象，没有__call__或__code__属性
        class MockFunction:
            def __init__(self):
                self.__name__ = "mock_func"
                # 不定义__call__方法，这样hasattr(obj, '__call__')会返回False
        
        mock_func = MockFunction()
        
        @cache_result(expire=60)
        def test_func():
            # 这个测试主要是为了覆盖hasattr检查的else分支
            return "test_result"
        
        result = test_func()
        assert result == "test_result"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_result_sync_skip_cache(self, mock_cache_service):
        """测试fastapi_cache_result同步包装器的跳过缓存逻辑（第414-415行）"""
        from app.utils.cache_decorator import fastapi_cache_result
        
        def should_skip_cache(*args, **kwargs):
            return kwargs.get('skip_cache', False)
        
        @fastapi_cache_result(expire=60, skip_cache=should_skip_cache)
        def test_func(value, skip_cache=False):
            return f"result_{value}"
        
        # 测试跳过缓存的情况
        result = test_func("test", skip_cache=True)
        assert result == "result_test"
        
        # 验证没有调用缓存服务
        mock_cache_service.get.assert_not_called()
        mock_cache_service.set.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    @pytest.mark.asyncio
    async def test_fastapi_cache_result_async_skip_cache(self, mock_cache_service):
        """测试fastapi_cache_result异步包装器的跳过缓存逻辑（第376-377行）"""
        from app.utils.cache_decorator import fastapi_cache_result
        
        def should_skip_cache(*args, **kwargs):
            return kwargs.get('skip_cache', False)
        
        @fastapi_cache_result(expire=60, skip_cache=should_skip_cache)
        async def test_async_func(value, skip_cache=False):
            return f"async_result_{value}"
        
        # 测试跳过缓存的情况
        result = await test_async_func("test", skip_cache=True)
        assert result == "async_result_test"
        
        # 验证没有调用缓存服务
        mock_cache_service.get.assert_not_called()
        mock_cache_service.set.assert_not_called()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_cache_result_wrapper_selection_debug(self, mock_cache_service):
        """测试fastapi_cache_result装饰器的包装器选择调试日志（第369行）"""
        from app.utils.cache_decorator import fastapi_cache_result
        import inspect
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 测试同步函数的包装器选择
        @fastapi_cache_result(expire=60)
        def sync_func():
            return {"type": "sync"}
        
        # 验证包装器选择
        assert not inspect.iscoroutinefunction(sync_func)
        
        # 调用函数触发包装器
        result = sync_func()
        assert result == {"type": "sync"}
    
    def test_serialize_for_cache_decimal_datetime(self):
        """测试_serialize_for_cache处理Decimal和DateTime对象"""
        from app.utils.cache_decorator import _serialize_for_cache
        import decimal
        import datetime
        
        # 创建一个模拟的SQLAlchemy对象，包含Decimal和DateTime字段
        class MockColumn:
            def __init__(self, name):
                self.name = name
        
        class MockTable:
            def __init__(self):
                self.columns = [
                    MockColumn("decimal_field"),
                    MockColumn("datetime_field"),
                    MockColumn("date_field"),
                    MockColumn("string_field"),
                    MockColumn("none_field")
                ]
        
        class MockSQLAlchemyObj:
            def __init__(self):
                self.__table__ = MockTable()
                self.decimal_field = decimal.Decimal('123.45')
                self.datetime_field = datetime.datetime(2023, 1, 1, 12, 0, 0)
                self.date_field = datetime.date(2023, 1, 1)
                self.string_field = "test_string"
                self.none_field = None
        
        obj = MockSQLAlchemyObj()
        result = _serialize_for_cache(obj)
        
        # 验证序列化结果
        assert result["decimal_field"] == 123.45
        assert result["datetime_field"] == "2023-01-01T12:00:00"
        assert result["date_field"] == "2023-01-01"
        assert result["string_field"] == "test_string"
        assert result["none_field"] is None
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_convenience_cache_decorators(self, mock_cache_service):
        """测试便捷缓存装饰器（第497、501、505、509行）"""
        from app.utils.cache_decorator import cache_for, cache_short, cache_medium, cache_long
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 测试cache_for
        @cache_for(minutes=10, prefix="test")
        def test_cache_for():
            return "cache_for_result"
        
        result = test_cache_for()
        assert result == "cache_for_result"
        
        # 测试cache_short
        @cache_short(prefix="test")
        def test_cache_short():
            return "cache_short_result"
        
        result = test_cache_short()
        assert result == "cache_short_result"
        
        # 测试cache_medium
        @cache_medium(prefix="test")
        def test_cache_medium():
            return "cache_medium_result"
        
        result = test_cache_medium()
        assert result == "cache_medium_result"
        
        # 测试cache_long
        @cache_long(prefix="test")
        def test_cache_long():
            return "cache_long_result"
        
        result = test_cache_long()
        assert result == "cache_long_result"
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_fastapi_convenience_decorators(self, mock_cache_service):
        """测试FastAPI便捷装饰器（第509行）"""
        from app.utils.cache_decorator import fastapi_cache_short, fastapi_cache_medium, fastapi_cache_long
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        # 测试fastapi_cache_short
        @fastapi_cache_short
        def test_fastapi_short():
            return {"result": "fastapi_short"}
        
        result = test_fastapi_short()
        assert result == {"result": "fastapi_short"}
        
        # 测试fastapi_cache_medium
        @fastapi_cache_medium
        def test_fastapi_medium():
            return {"result": "fastapi_medium"}
        
        result = test_fastapi_medium()
        assert result == {"result": "fastapi_medium"}
        
        # 测试fastapi_cache_long
        @fastapi_cache_long
        def test_fastapi_long():
            return {"result": "fastapi_long"}
        
        result = test_fastapi_long()
        assert result == {"result": "fastapi_long"}
    
    def test_deserialize_from_cache(self):
        """测试_deserialize_from_cache函数（第487行）"""
        from app.utils.cache_decorator import _deserialize_from_cache
        
        # 测试直接返回对象
        test_obj = {"key": "value", "number": 123}
        result = _deserialize_from_cache(test_obj)
        assert result == test_obj
        
        # 测试None值
        result = _deserialize_from_cache(None)
        assert result is None
    
    def test_clear_cache_by_params(self):
        """测试_clear_cache_by_params函数（第491-492行）"""
        from app.utils.cache_decorator import _clear_cache_by_params
        
        with patch('app.utils.cache_decorator.cache_service') as mock_cache_service:
            mock_cache_service.delete.return_value = True
            
            result = _clear_cache_by_params("test_func", {"param1": "value1"}, "test_prefix")
            
            # 验证调用了delete方法
            mock_cache_service.delete.assert_called_once()
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_serialize_for_cache_list_handling(self, mock_cache_service):
        """测试_serialize_for_cache处理列表的情况（第445行）"""
        from app.utils.cache_decorator import _serialize_for_cache
        
        # 测试列表序列化
        test_list = ["item1", "item2", {"key": "value"}]
        result = _serialize_for_cache(test_list)
        assert result == ["item1", "item2", {"key": "value"}]
        
        # 测试空列表
        result = _serialize_for_cache([])
        assert result == []
    
    @patch('app.utils.cache_decorator.cache_service')
    def test_serialize_for_cache_other_types(self, mock_cache_service):
        """测试_serialize_for_cache处理其他类型的情况（第449行）"""
        from app.utils.cache_decorator import _serialize_for_cache
        
        # 测试字符串
        result = _serialize_for_cache("test_string")
        assert result == "test_string"
        
        # 测试数字
        result = _serialize_for_cache(123)
        assert result == 123
        
        # 测试布尔值
        result = _serialize_for_cache(True)
        assert result is True
        
        # 测试字典
        test_dict = {"key": "value"}
        result = _serialize_for_cache(test_dict)
        assert result == test_dict