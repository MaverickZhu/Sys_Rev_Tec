#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理模块

提供AI服务的缓存功能
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client=None, default_ttl: int = 3600):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, prefix: str, data: Any) -> str:
        """生成缓存键"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)

        hash_obj = hashlib.md5(data_str.encode("utf-8"))
        return f"{prefix}:{hash_obj.hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            # 优先使用Redis
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)

            # 回退到内存缓存
            if key in self.memory_cache:
                cache_item = self.memory_cache[key]
                if cache_item["expires_at"] > datetime.now():
                    return cache_item["value"]
                else:
                    # 过期删除
                    del self.memory_cache[key]

            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl

            # 优先使用Redis
            if self.redis_client:
                serialized_value = json.dumps(value, ensure_ascii=False)
                result = self.redis_client.setex(key, ttl, serialized_value)
                return bool(result)

            # 回退到内存缓存
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self.memory_cache[key] = {"value": value, "expires_at": expires_at}
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            # Redis删除
            if self.redis_client:
                self.redis_client.delete(key)

            # 内存缓存删除
            if key in self.memory_cache:
                del self.memory_cache[key]

            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_prefix(self, prefix: str) -> bool:
        """清除指定前缀的缓存"""
        try:
            # Redis清除
            if self.redis_client:
                keys = self.redis_client.keys(f"{prefix}:*")
                if keys:
                    self.redis_client.delete(*keys)

            # 内存缓存清除
            keys_to_delete = [
                k for k in self.memory_cache.keys() if k.startswith(f"{prefix}:")
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]

            return True

        except Exception as e:
            logger.error(f"Cache clear prefix error for {prefix}: {e}")
            return False

    async def get_embedding_cache(self, text: str, model: str) -> Optional[list]:
        """获取嵌入向量缓存"""
        key = self._generate_key(f"embedding:{model}", text)
        return await self.get(key)

    async def set_embedding_cache(
        self, text: str, model: str, embedding: list, ttl: Optional[int] = None
    ) -> bool:
        """设置嵌入向量缓存"""
        key = self._generate_key(f"embedding:{model}", text)
        return await self.set(key, embedding, ttl)

    async def get_analysis_cache(
        self, text: str, analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """获取分析结果缓存"""
        key = self._generate_key(f"analysis:{analysis_type}", text)
        return await self.get(key)

    async def set_analysis_cache(
        self,
        text: str,
        analysis_type: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """设置分析结果缓存"""
        key = self._generate_key(f"analysis:{analysis_type}", text)
        return await self.set(key, result, ttl)

    async def get_search_cache(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """获取搜索结果缓存"""
        cache_data = {"query": query, "filters": filters or {}}
        key = self._generate_key("search", cache_data)
        return await self.get(key)

    async def set_search_cache(
        self,
        query: str,
        result: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置搜索结果缓存"""
        cache_data = {"query": query, "filters": filters or {}}
        key = self._generate_key("search", cache_data)
        return await self.set(key, result, ttl)

    async def clear_all(self) -> bool:
        """清除所有缓存"""
        try:
            # Redis清除
            if self.redis_client:
                self.redis_client.flushdb()

            # 内存缓存清除
            self.memory_cache.clear()

            return True

        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "redis_available": self.redis_client is not None,
            "default_ttl": self.default_ttl,
        }

        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats["redis_memory_usage"] = info.get("used_memory_human", "N/A")
                stats["redis_keys"] = info.get("db0", {}).get("keys", 0)
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
                stats["redis_error"] = str(e)

        return stats


# 全局缓存管理器实例
cache_manager = CacheManager()
