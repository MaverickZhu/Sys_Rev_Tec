#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存装饰器模块

提供函数和模型查询结果的缓存装饰器
"""

import datetime
import decimal
import hashlib
import inspect
import json
from functools import wraps
from typing import TYPE_CHECKING, Any, Optional, Union

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.user import User
from app.services.cache_service import cache_service


def _is_fastapi_dependency(obj: Any) -> bool:
    """检查对象是否为FastAPI依赖注入对象"""
    return isinstance(obj, (Request, Session, User))


def _serialize_for_cache_key(obj: Any) -> str:
    """序列化对象用于生成缓存键"""
    if obj is None:
        return "None"
    elif isinstance(obj, (str, int, float, bool)):
        return str(obj)
    elif isinstance(obj, (list, tuple)):
        return json.dumps([_serialize_for_cache_key(item) for item in obj])
    elif isinstance(obj, dict):
        return json.dumps(
            {k: _serialize_for_cache_key(v) for k, v in sorted(obj.items())}
        )
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif hasattr(obj, "id"):
        return f"{obj.__class__.__name__}:{obj.id}"
    else:
        return str(obj)


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    # 序列化参数
    args_str = _serialize_for_cache_key(args)
    kwargs_str = _serialize_for_cache_key(kwargs)

    # 组合所有信息
    key_data = f"{func_name}:{args_str}:{kwargs_str}"

    # 生成SHA256哈希（用于缓存键，非安全用途）
    return hashlib.sha256(key_data.encode("utf-8")).hexdigest()[:16]


def _generate_model_cache_key(
    model_name: str, args: tuple, kwargs: dict, include_user: bool = True
) -> str:
    """生成模型缓存键"""
    user_id = "anonymous"

    if include_user:
        # 从参数中查找用户ID
        for arg in args:
            if hasattr(arg, "id") and isinstance(arg, User):
                user_id = str(arg.id)
                break

        for value in kwargs.values():
            if hasattr(value, "id") and isinstance(value, User):
                user_id = str(value.id)
                break

    # 过滤掉用户对象
    filtered_args = tuple(arg for arg in args if not isinstance(arg, User))
    filtered_kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, User)}

    # 序列化参数
    args_str = _serialize_for_cache_key(filtered_args)
    kwargs_str = _serialize_for_cache_key(filtered_kwargs)

    # 组合所有信息
    key_data = f"{model_name}:{user_id}:{args_str}:{kwargs_str}"

    # 生成SHA256哈希（用于缓存键，非安全用途）
    return hashlib.sha256(key_data.encode("utf-8")).hexdigest()[:16]


def _clear_cache(
    func_name: str,
    args: tuple,
    kwargs: dict,
    prefix: str,
    key_func: Optional[Any] = None,
) -> bool:
    """清除特定函数调用的缓存"""
    if key_func:
        cache_key = key_func(*args, **kwargs)
    else:
        cache_key = _generate_cache_key(func_name, args, kwargs)

    return cache_service.delete(cache_key, prefix)


def cache_result(
    expire: Optional[int] = None,
    prefix: str = "func",
    key_func: Optional[Any] = None,
    skip_cache: Optional[Any] = None,
):
    """缓存函数结果的装饰器

    Args:
        expire: 缓存过期时间(秒)
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
                if k not in ["request"] and not _is_fastapi_dependency(v):
                    filtered_kwargs[k] = v

            # 检查是否跳过缓存
            if skip_cache and skip_cache(*args, **kwargs):
                return await func(*args, **kwargs)

            # 生成缓存键(使用过滤后的参数)
            if key_func:
                cache_key = key_func(*filtered_args, **filtered_kwargs)
            else:
                cache_key = _generate_cache_key(
                    func.__name__, tuple(filtered_args), filtered_kwargs
                )

            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, prefix)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result

            # 执行函数
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

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
                if k not in ["request"] and not _is_fastapi_dependency(v):
                    filtered_kwargs[k] = v

            # 检查是否跳过缓存
            if skip_cache and skip_cache(*args, **kwargs):
                return func(*args, **kwargs)

            # 生成缓存键(使用过滤后的参数)
            if key_func:
                cache_key = key_func(*filtered_args, **filtered_kwargs)
            else:
                cache_key = _generate_cache_key(
                    func.__name__, tuple(filtered_args), filtered_kwargs
                )

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
        if inspect.iscoroutinefunction(func):
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper

        # 添加缓存控制方法
        def cache_clear(*args, **kwargs):
            return _clear_cache(func.__name__, args, kwargs, prefix, key_func)

        def cache_key(*args, **kwargs):
            if key_func:
                return key_func(*args, **kwargs)
            else:
                return _generate_cache_key(func.__name__, args, kwargs)

        wrapper.cache_clear = cache_clear
        wrapper.cache_key = cache_key

        return wrapper

    return decorator


# 预定义的常用缓存装饰器
fastapi_cache_short = cache_result(expire=300, prefix="api_short")  # 5分钟
fastapi_cache_medium = cache_result(expire=1800, prefix="api_medium")  # 30分钟
fastapi_cache_long = cache_result(expire=3600, prefix="api_long")  # 1小时


def cache_model_result(
    model_name: str, expire: Optional[int] = None, include_user: bool = True
):
    """缓存模型查询结果的装饰器

    Args:
        model_name: 模型名称
        expire: 缓存过期时间(秒)
        include_user: 是否在缓存键中包含用户ID
    """

    def decorator(func: Any) -> Any:

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 过滤掉request参数用于缓存键生成
            filtered_args = args
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["request"]}

            # 生成缓存键
            cache_key = _generate_model_cache_key(
                model_name, filtered_args, filtered_kwargs, include_user
            )

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
        def cache_clear(*args, **kwargs):
            filtered_args = args
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["request"]}
            cache_key = _generate_model_cache_key(
                model_name, filtered_args, filtered_kwargs, include_user
            )
            return cache_service.delete(cache_key, "model")

        def cache_key(*args, **kwargs):
            filtered_args = args
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["request"]}
            return _generate_model_cache_key(
                model_name, filtered_args, filtered_kwargs, include_user
            )

        wrapper.cache_clear = cache_clear
        wrapper.cache_key = cache_key

        return wrapper

    return decorator


def invalidate_cache_on_change(cache_keys: list):
    """在数据变更时失效相关缓存的装饰器

    Args:
        cache_keys: 需要失效的缓存键列表
    """

    def decorator(func: Any) -> Any:

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 执行原函数
            result = await func(*args, **kwargs)

            # 失效相关缓存
            for cache_key in cache_keys:
                cache_service.delete_pattern(cache_key)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 执行原函数
            result = func(*args, **kwargs)

            # 失效相关缓存
            for cache_key in cache_keys:
                cache_service.delete_pattern(cache_key)

            return result

        # 检查函数是否为异步函数
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
