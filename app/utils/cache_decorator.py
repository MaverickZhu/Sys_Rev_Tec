from functools import wraps
from typing import Any, Optional, Union, TYPE_CHECKING

# if TYPE_CHECKING:
#     from collections.abc import Callable  # 临时注释以解决JsonSchema问题
import hashlib
import json
from app.services.cache_service import cache_service
from app.core.logging import logger

def cache_result(
    expire: Optional[int] = None,
    prefix: str = "func",
    key_func: Optional[Any] = None,
    skip_cache: Optional[Any] = None
):
    """缓存函数结果的装饰器
    
    Args:
        expire: 缓存过期时间（秒）
        prefix: 缓存键前缀
        key_func: 自定义键生成函数
        skip_cache: 跳过缓存的条件函数
    """
    def decorator(func: Any) -> Any:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 过滤掉FastAPI相关参数用于缓存键生成
            filtered_args = []
            filtered_kwargs = {}
            
            # 过滤args - 跳过FastAPI依赖注入的对象
            for arg in args:
                if not _is_fastapi_dependency(arg):
                    filtered_args.append(arg)
            
            # 过滤kwargs - 跳过FastAPI相关参数
            for k, v in kwargs.items():
                if k not in ['request'] and not _is_fastapi_dependency(v):
                    filtered_kwargs[k] = v
            
            # 检查是否跳过缓存
            if skip_cache and skip_cache(*args, **kwargs):
                if hasattr(func, '__call__') and hasattr(func, '__code__'):
                    import inspect
                    if inspect.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                return func(*args, **kwargs)
            
            # 生成缓存键（使用过滤后的参数）
            if key_func:
                cache_key = key_func(*filtered_args, **filtered_kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, tuple(filtered_args), filtered_kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, prefix)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # 执行函数
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            if hasattr(func, '__call__') and hasattr(func, '__code__'):
                import inspect
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 缓存结果
            cache_service.set(cache_key, result, expire, prefix)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 过滤掉FastAPI相关参数用于缓存键生成
            filtered_args = []
            filtered_kwargs = {}
            
            # 过滤args - 跳过FastAPI依赖注入的对象
            for arg in args:
                if not _is_fastapi_dependency(arg):
                    filtered_args.append(arg)
            
            # 过滤kwargs - 跳过FastAPI相关参数
            for k, v in kwargs.items():
                if k not in ['request'] and not _is_fastapi_dependency(v):
                    filtered_kwargs[k] = v
            
            # 检查是否跳过缓存
            if skip_cache and skip_cache(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 生成缓存键（使用过滤后的参数）
            if key_func:
                cache_key = key_func(*filtered_args, **filtered_kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, tuple(filtered_args), filtered_kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, prefix)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # 执行函数
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_service.set(cache_key, result, expire, prefix)
            
            return result
        
        # 检查函数是否为异步函数
        import inspect
        if inspect.iscoroutinefunction(func):
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper
        
        # 添加缓存控制方法
        wrapper.cache_clear = lambda *args, **kwargs: _clear_cache(func.__name__, args, kwargs, prefix, key_func)
        wrapper.cache_key = lambda *args, **kwargs: key_func(*args, **kwargs) if key_func else _generate_cache_key(func.__name__, args, kwargs)
        
        return wrapper
    return decorator

def cache_model_result(
    model_name: str,
    expire: Optional[int] = None,
    include_user: bool = True
):
    """缓存模型查询结果的装饰器
    
    Args:
        model_name: 模型名称
        expire: 缓存过期时间（秒）
        include_user: 是否在缓存键中包含用户ID
    """
    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 过滤掉request参数用于缓存键生成
            filtered_args = args
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['request']}
            
            # 生成缓存键
            cache_key = _generate_model_cache_key(model_name, filtered_args, filtered_kwargs, include_user)
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, "model")
            if cached_result is not None:
                logger.debug(f"Model cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # 执行函数
            logger.debug(f"Model cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_service.set(cache_key, result, expire, "model")
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_clear = lambda *args, **kwargs: _clear_model_cache(model_name, args, kwargs, include_user)
        wrapper.cache_clear_all = lambda: cache_service.clear_pattern(f"{model_name}:*", "model")
        
        return wrapper
    return decorator

def invalidate_cache(patterns: Union[str, list], prefix: str = "app"):
    """缓存失效装饰器
    
    Args:
        patterns: 要清除的缓存模式（字符串或列表）
        prefix: 缓存键前缀
    """
    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 清除相关缓存
            if isinstance(patterns, str):
                pattern_list = [patterns]
            else:
                pattern_list = patterns
            
            for pattern in pattern_list:
                cleared = cache_service.clear_pattern(pattern, prefix)
                if cleared > 0:
                    logger.info(f"Invalidated {cleared} cache entries for pattern: {pattern}")
            
            return result
        return wrapper
    return decorator

def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    # 创建参数的哈希值，避免使用"func"键名以防止与FastAPI查询参数冲突
    key_data = {
        "function_name": func_name,
        "args": _serialize_args(args),
        "kwargs": _serialize_kwargs(kwargs)
    }
    
    key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{func_name}:{key_hash}"

def _generate_model_cache_key(model_name: str, args: tuple, kwargs: dict, include_user: bool) -> str:
    """生成模型缓存键"""
    key_parts = [model_name]
    
    # 添加用户ID（如果需要）
    if include_user:
        user_id = _extract_user_id(args, kwargs)
        if user_id:
            key_parts.append(f"user:{user_id}")
    
    # 添加参数哈希
    args_data = {
        "args": _serialize_args(args),
        "kwargs": _serialize_kwargs(kwargs)
    }
    args_string = json.dumps(args_data, sort_keys=True, ensure_ascii=False)
    args_hash = hashlib.md5(args_string.encode()).hexdigest()[:8]
    key_parts.append(args_hash)
    
    return ":".join(key_parts)

def _is_fastapi_dependency(obj) -> bool:
    """检查对象是否为FastAPI依赖注入对象"""
    if obj is None:
        return False
    
    obj_type_str = str(type(obj))
    
    # 检查常见的FastAPI依赖类型
    fastapi_types = [
        'Request', 'Session', 'User', 'HTTPConnection',
        'sqlalchemy', 'starlette', 'fastapi'
    ]
    
    for fastapi_type in fastapi_types:
        if fastapi_type in obj_type_str:
            return True
    
    # 检查是否有特定的FastAPI属性
    if hasattr(obj, 'scope') and hasattr(obj, 'receive'):
        return True  # Request对象
    
    if hasattr(obj, 'bind') and hasattr(obj, 'execute'):
        return True  # SQLAlchemy Session对象
    
    return False

def _serialize_args(args: tuple) -> list:
    """序列化位置参数"""
    serialized = []
    for i, arg in enumerate(args):
        # 跳过第一个参数如果它是self（实例方法）
        if i == 0 and hasattr(arg, '__class__') and hasattr(arg.__class__, '__module__'):
            continue
        
        # 跳过FastAPI依赖注入对象
        if _is_fastapi_dependency(arg):
            continue
            
        if hasattr(arg, 'id'):  # 数据库模型对象
            serialized.append(f"obj:{type(arg).__name__}:{arg.id}")
        elif hasattr(arg, '__dict__'):  # 其他对象
            serialized.append(f"obj:{type(arg).__name__}")
        else:
            serialized.append(str(arg))
    return serialized

def _serialize_kwargs(kwargs: dict) -> dict:
    """序列化关键字参数"""
    serialized = {}
    for key, value in kwargs.items():
        # 跳过FastAPI依赖注入对象
        if _is_fastapi_dependency(value):
            continue
            
        if hasattr(value, 'id'):  # 数据库模型对象
            serialized[key] = f"obj:{type(value).__name__}:{value.id}"
        elif hasattr(value, '__dict__'):  # 其他对象
            serialized[key] = f"obj:{type(value).__name__}"
        else:
            serialized[key] = str(value)
    return serialized

def _extract_user_id(args: tuple, kwargs: dict) -> Optional[str]:
    """从参数中提取用户ID"""
    # 从kwargs中查找
    for key in ['current_user', 'user', 'user_id']:
        if key in kwargs:
            user = kwargs[key]
            if hasattr(user, 'id'):
                return str(user.id)
            elif isinstance(user, (int, str)):
                return str(user)
    
    # 从args中查找（通常用户对象在后面）
    for arg in reversed(args):
        if hasattr(arg, 'id') and hasattr(arg, 'email'):  # 假设用户对象有id和email属性
            return str(arg.id)
    
    return None

def _clear_cache(func_name: str, args: tuple, kwargs: dict, prefix: str, key_func: Optional[Any]):
    """清除特定函数的缓存"""
    if key_func:
        cache_key = key_func(*args, **kwargs)
    else:
        cache_key = _generate_cache_key(func_name, args, kwargs)
    
    return cache_service.delete(cache_key, prefix)

def _clear_model_cache(model_name: str, args: tuple, kwargs: dict, include_user: bool):
    """清除特定模型的缓存"""
    cache_key = _generate_model_cache_key(model_name, args, kwargs, include_user)
    return cache_service.delete(cache_key, "model")

def fastapi_cache_result(
    expire: Optional[int] = None,
    prefix: str = "api",
    key_func: Optional[Any] = None,
    skip_cache: Optional[Any] = None
):
    """专门为FastAPI设计的缓存装饰器
    
    Args:
        expire: 缓存过期时间（秒）
        prefix: 缓存键前缀
        key_func: 自定义键生成函数
        skip_cache: 跳过缓存的条件函数
    """
    def decorator(func: Any) -> Any:
        import inspect
        logger.debug(f"fastapi_cache_result decorator applied to function: {func.__name__}")
        logger.debug(f"Function is coroutine: {inspect.iscoroutinefunction(func)}")
        
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                logger.debug(f"FastAPI cache decorator called for async function: {func.__name__}")
                # 生成缓存键，只使用查询参数
                cache_params = {}
                for k, v in kwargs.items():
                    if k in ['skip', 'limit'] or (isinstance(v, (str, int, float, bool)) and k not in ['db', 'current_user', 'request']):
                        cache_params[k] = v
                
                # 检查是否跳过缓存
                if skip_cache and skip_cache(*args, **kwargs):
                    return await func(*args, **kwargs)
                
                # 生成缓存键
                if key_func:
                    cache_key = key_func(**cache_params)
                else:
                    cache_key = _generate_cache_key(func.__name__, (), cache_params)
                
                # 尝试从缓存获取
                cached_result = cache_service.get(cache_key, prefix)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return _deserialize_from_cache(cached_result)
                
                # 执行函数
                logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
                result = await func(*args, **kwargs)
                logger.debug(f"Function result type: {type(result)}")
                
                # 序列化结果用于缓存（处理SQLAlchemy对象）
                serializable_result = _serialize_for_cache(result)
                logger.debug(f"Serialized result type: {type(serializable_result)}")
                cache_service.set(cache_key, serializable_result, expire, prefix)
                
                return serializable_result
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                logger.debug(f"FastAPI cache decorator called for sync function: {func.__name__}")
                # 生成缓存键，只使用查询参数
                cache_params = {}
                for k, v in kwargs.items():
                    if k in ['skip', 'limit'] or (isinstance(v, (str, int, float, bool)) and k not in ['db', 'current_user', 'request']):
                        cache_params[k] = v
                
                # 检查是否跳过缓存
                if skip_cache and skip_cache(*args, **kwargs):
                    logger.debug(f"Skipping cache for {func.__name__}")
                    return func(*args, **kwargs)
                
                # 生成缓存键
                if key_func:
                    cache_key = key_func(**cache_params)
                else:
                    cache_key = _generate_cache_key(func.__name__, (), cache_params)
                
                # 尝试从缓存获取
                cached_result = cache_service.get(cache_key, prefix)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return _deserialize_from_cache(cached_result)
                
                # 执行函数
                logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
                result = func(*args, **kwargs)
                logger.debug(f"Function result type: {type(result)}")
                
                # 序列化结果用于缓存（处理SQLAlchemy对象）
                serializable_result = _serialize_for_cache(result)
                logger.debug(f"Serialized result type: {type(serializable_result)}")
                cache_service.set(cache_key, serializable_result, expire, prefix)
                
                return serializable_result
        
        wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
        logger.debug(f"Selected wrapper type: {'async' if inspect.iscoroutinefunction(func) else 'sync'}")
        
        # 添加缓存控制方法
        wrapper.cache_clear = lambda **kwargs: _clear_cache_by_params(func.__name__, kwargs, prefix)
        wrapper.cache_key = lambda **kwargs: key_func(**kwargs) if key_func else _generate_cache_key(func.__name__, (), kwargs)
        
        return wrapper
    return decorator

def _serialize_for_cache(obj):
    """序列化对象用于缓存"""
    import decimal
    import datetime
    
    if obj is None:
        return None
    
    # 处理列表
    if isinstance(obj, list):
        return [_serialize_for_cache(item) for item in obj]
    
    # 处理SQLAlchemy对象
    if hasattr(obj, '__table__'):
        # 将SQLAlchemy对象转换为字典
        result = {}
        for column in obj.__table__.columns:
            try:
                value = getattr(obj, column.name)
                
                # 处理None值
                if value is None:
                    result[column.name] = None
                # 处理日期时间对象
                elif isinstance(value, (datetime.datetime, datetime.date)):
                    result[column.name] = value.isoformat()
                # 处理Decimal对象
                elif isinstance(value, decimal.Decimal):
                    result[column.name] = float(value)
                # 处理基本类型
                elif isinstance(value, (str, int, float, bool)):
                    result[column.name] = value
                # 其他类型转换为字符串
                else:
                    result[column.name] = str(value)
            except Exception as e:
                # 如果某个字段序列化失败，跳过它
                logger.warning(f"Failed to serialize field {column.name}: {e}")
                continue
        return result
    
    # 其他类型直接返回
    return obj

def _deserialize_from_cache(obj):
    """从缓存反序列化对象"""
    # 对于FastAPI，我们直接返回序列化后的字典
    # FastAPI会自动处理响应模型的序列化
    return obj

def _clear_cache_by_params(func_name: str, params: dict, prefix: str):
    """根据参数清除缓存"""
    cache_key = _generate_cache_key(func_name, (), params)
    return cache_service.delete(cache_key, prefix)

# 便捷的缓存装饰器
def cache_for(minutes: int = 60, prefix: str = "func"):
    """按分钟缓存的便捷装饰器"""
    return cache_result(expire=minutes * 60, prefix=prefix)

def cache_short(prefix: str = "func"):
    """短期缓存（5分钟）"""
    return cache_result(expire=300, prefix=prefix)

def cache_medium(prefix: str = "func"):
    """中期缓存（30分钟）"""
    return cache_result(expire=1800, prefix=prefix)

def cache_long(prefix: str = "func"):
    """长期缓存（2小时）"""
    return cache_result(expire=7200, prefix=prefix)

# FastAPI专用缓存装饰器
fastapi_cache_short = fastapi_cache_result(expire=300, prefix="api")  # 5分钟
fastapi_cache_medium = fastapi_cache_result(expire=1800, prefix="api")  # 30分钟
fastapi_cache_long = fastapi_cache_result(expire=3600, prefix="api")  # 1小时