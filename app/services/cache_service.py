#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存服务模块
提供Redis缓存操作的核心功能
"""

import gzip
import pickle
from datetime import datetime
from typing import Any, Dict, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config.cache_strategy import (
    CacheLevel,
    CacheStrategy,
    get_cache_strategy,
)
from app.core.config import settings
from app.core.logger import logger


class CacheService:
    """
    缓存服务类
    提供统一的缓存操作接口
    """

    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.local_cache: Dict[str, Any] = {}  # L1本地缓存
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }
        self._connection_pool = None
        self.is_enabled = getattr(settings, "CACHE_ENABLED", True)

    async def initialize(self):
        """
        初始化缓存服务
        """
        if not self.is_enabled:
            logger.info("Cache is disabled")
            return

        try:
            # 优先使用REDIS_URL环境变量
            import os
            redis_url = os.getenv('REDIS_URL')
            
            if redis_url:
                # 使用REDIS_URL创建连接池
                self._connection_pool = redis.ConnectionPool.from_url(
                    redis_url,
                    decode_responses=False,  # 保持二进制数据
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                )
                logger.info(f"使用REDIS_URL连接Redis: {redis_url}")
            else:
                # 回退到单独的参数
                self._connection_pool = redis.ConnectionPool(
                    host=getattr(settings, "REDIS_HOST", "redis"),
                    port=getattr(settings, "REDIS_PORT", 6379),
                    password=getattr(settings, "REDIS_PASSWORD", None),
                    db=getattr(settings, "REDIS_DB", 0),
                    decode_responses=False,  # 保持二进制数据
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                )
                logger.info(f"使用单独参数连接Redis: {getattr(settings, 'REDIS_HOST', 'redis')}:{getattr(settings, 'REDIS_PORT', 6379)}")

            self.redis_client = Redis(connection_pool=self._connection_pool)

            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis缓存服务初始化成功")

        except Exception as e:
            logger.error(f"Redis缓存服务初始化失败: {e}")
            self.is_enabled = False
            raise

    async def close(self):
        """
        关闭缓存服务
        """
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            logger.info("缓存服务已关闭")
        except Exception as e:
            logger.error(f"关闭缓存服务失败: {e}")

    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键
            cache_type: 缓存类型

        Returns:
            缓存值或None
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                logger.warning(f"未找到缓存策略: {cache_type}")
                return None

            full_key = f"{strategy.key_prefix}:{key}"

            # L1缓存查找
            if strategy.level == CacheLevel.L1_MEMORY:
                if full_key in self.local_cache:
                    self.cache_stats["hits"] += 1
                    return self.local_cache[full_key]

            # L2 Redis缓存查找
            if strategy.level == CacheLevel.L2_REDIS and self.redis_client:
                value = await self.redis_client.get(full_key)
                if value is not None:
                    self.cache_stats["hits"] += 1
                    deserialized_value = self._deserialize(value, strategy)

                    # 回填L1缓存（对于L2_REDIS策略，也可以回填到L1）
                    self.local_cache[full_key] = deserialized_value
                    await self._evict_local_cache_if_needed()

                    return deserialized_value

            self.cache_stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"获取缓存失败 {full_key}: {e}")
            self.cache_stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "default",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            cache_type: 缓存类型
            ttl: 过期时间（秒），不指定则使用策略默认值

        Returns:
            是否设置成功
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                logger.warning(f"未找到缓存策略: {cache_type}")
                return False

            full_key = f"{strategy.key_prefix}:{key}"
            effective_ttl = ttl or strategy.ttl

            # L1缓存设置
            if strategy.level == CacheLevel.L1_MEMORY:
                self.local_cache[full_key] = value
                await self._evict_local_cache_if_needed()

            # L2 Redis缓存设置
            if strategy.level == CacheLevel.L2_REDIS and self.redis_client:
                serialized_value = self._serialize(value, strategy)
                if effective_ttl > 0:
                    await self.redis_client.setex(
                        full_key, effective_ttl, serialized_value
                    )
                else:
                    await self.redis_client.set(full_key, serialized_value)

            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"设置缓存失败 {full_key}: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def delete(self, key: str, cache_type: str = "default") -> bool:
        """
        删除缓存

        Args:
            key: 缓存键
            cache_type: 缓存类型

        Returns:
            是否删除成功
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                return False

            full_key = f"{strategy.key_prefix}:{key}"
            success = True

            # 删除L1缓存
            if strategy.level == CacheLevel.L1_MEMORY:
                self.local_cache.pop(full_key, None)

            # 删除L2缓存
            if strategy.level == CacheLevel.L2_REDIS and self.redis_client:
                result = await self.redis_client.delete(full_key)
                success = result > 0

            self.cache_stats["deletes"] += 1
            return success

        except Exception as e:
            logger.error(f"删除缓存失败 {full_key}: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def exists(self, key: str, cache_type: str = "default") -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键
            cache_type: 缓存类型

        Returns:
            是否存在
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                return False

            full_key = f"{strategy.key_prefix}:{key}"

            # 检查L1缓存
            if strategy.level in [CacheLevel.L1, CacheLevel.HYBRID]:
                if full_key in self.local_cache:
                    return True

            # 检查L2缓存
            if (
                strategy.level in [CacheLevel.L2, CacheLevel.HYBRID]
                and self.redis_client
            ):
                return await self.redis_client.exists(full_key) > 0

            return False

        except Exception as e:
            logger.error(f"检查缓存存在性失败 {full_key}: {e}")
            return False

    async def clear_pattern(self, pattern: str, cache_type: str = "default") -> int:
        """
        按模式清除缓存

        Args:
            pattern: 匹配模式（支持通配符*）
            cache_type: 缓存类型

        Returns:
            删除的键数量
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                return 0

            search_pattern = f"{strategy.key_prefix}:{pattern}"
            deleted_count = 0

            # 清除L1缓存
            if strategy.level in [CacheLevel.L1, CacheLevel.HYBRID]:
                keys_to_delete = [
                    k
                    for k in self.local_cache.keys()
                    if k.startswith(search_pattern.replace("*", ""))
                ]
                for key in keys_to_delete:
                    self.local_cache.pop(key, None)
                    deleted_count += 1

            # 清除L2缓存
            if (
                strategy.level in [CacheLevel.L2, CacheLevel.HYBRID]
                and self.redis_client
            ):
                keys = await self.redis_client.keys(search_pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    deleted_count += deleted

            logger.info(f"清除了 {deleted_count} 个匹配模式的键: {search_pattern}")
            return deleted_count

        except Exception as e:
            logger.error(f"按模式清除缓存失败 {pattern}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        try:
            stats = {
                "enabled": self.is_enabled,
                "connected": self.redis_client is not None,
                "local_cache_size": len(self.local_cache),
                "cache_stats": self.cache_stats.copy(),
            }

            # 计算命中率
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            if total_requests > 0:
                stats["hit_rate"] = (self.cache_stats["hits"] / total_requests) * 100
            else:
                stats["hit_rate"] = 0.0

            # Redis统计信息
            if self.redis_client:
                try:
                    info = await self.redis_client.info()
                    stats.update(
                        {
                            "redis_memory_used": info.get("used_memory_human", "0B"),
                            "redis_memory_peak": info.get(
                                "used_memory_peak_human", "0B"
                            ),
                            "redis_connected_clients": info.get("connected_clients", 0),
                            "redis_total_commands": info.get(
                                "total_commands_processed", 0
                            ),
                            "redis_keyspace_hits": info.get("keyspace_hits", 0),
                            "redis_keyspace_misses": info.get("keyspace_misses", 0),
                        }
                    )
                except Exception as e:
                    logger.error(f"获取Redis统计信息失败: {e}")

            return stats

        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {e}")
            return {"enabled": False, "connected": False, "error": str(e)}

    def _serialize(self, value: Any, strategy: CacheStrategy) -> bytes:
        """
        序列化缓存值

        Args:
            value: 要序列化的值
            strategy: 缓存策略

        Returns:
            序列化后的字节数据
        """
        try:
            if strategy.compression:
                # 使用pickle序列化后压缩
                pickled_data = pickle.dumps(value)
                return gzip.compress(pickled_data)
            else:
                # 直接pickle序列化
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            raise

    def _deserialize(self, data: bytes, strategy: CacheStrategy) -> Any:
        """
        反序列化缓存值

        Args:
            data: 序列化的字节数据
            strategy: 缓存策略

        Returns:
            反序列化后的值
        """
        try:
            if strategy.compression:
                # 解压缩后反序列化
                decompressed_data = gzip.decompress(data)
                return pickle.loads(decompressed_data)
            else:
                # 直接反序列化
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            raise

    async def _evict_local_cache_if_needed(self):
        """
        根据需要清理本地缓存
        """
        max_local_cache_size = getattr(settings, "MAX_LOCAL_CACHE_SIZE", 1000)

        if len(self.local_cache) > max_local_cache_size:
            # 简单的LRU策略：删除一半的缓存项
            items_to_remove = len(self.local_cache) // 2
            keys_to_remove = list(self.local_cache.keys())[:items_to_remove]

            for key in keys_to_remove:
                self.local_cache.pop(key, None)

            logger.info(f"本地缓存清理完成，删除了 {items_to_remove} 个项目")

    async def clear_all(self, cache_type: str = None) -> bool:
        """
        清空缓存

        Args:
            cache_type: 缓存类型，None表示清空所有

        Returns:
            是否清空成功
        """
        try:
            if cache_type:
                # 清空特定类型的缓存
                strategy = get_cache_strategy(cache_type)
                if not strategy:
                    return False

                pattern = f"{strategy.key_prefix}:*"
                return await self.clear_pattern("*", cache_type) > 0
            else:
                # 清空所有缓存
                self.local_cache.clear()
                if self.redis_client:
                    await self.redis_client.flushdb()

                # 重置统计信息
                self.cache_stats = {
                    "hits": 0,
                    "misses": 0,
                    "sets": 0,
                    "deletes": 0,
                    "errors": 0,
                }

                logger.info("所有缓存已清空")
                return True

        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        health_status = {
            "status": "healthy",
            "enabled": self.is_enabled,
            "local_cache_enabled": True,
            "redis_enabled": self.redis_client is not None,
            "timestamp": datetime.now().isoformat(),
        }

        # 检查Redis连接
        redis_connected = False
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health_status["redis_status"] = "connected"
                redis_connected = True
            except Exception as e:
                health_status["redis_status"] = "disconnected"
                health_status["redis_error"] = str(e)
                health_status["status"] = "degraded"

        # 添加redis_connected字段供cache_manager使用
        health_status["redis_connected"] = redis_connected

        # 检查本地缓存
        health_status["local_cache_size"] = len(self.local_cache)
        health_status["cache_stats"] = self.cache_stats.copy()

        return health_status

    async def warmup_cache(self, cache_type: str, data: Dict[str, Any]) -> bool:
        """
        缓存预热

        Args:
            cache_type: 缓存类型
            data: 预热数据字典

        Returns:
            是否预热成功
        """
        try:
            success_count = 0
            total_count = len(data)

            for key, value in data.items():
                if await self.set(key, value, cache_type=cache_type):
                    success_count += 1

            logger.info(f"缓存预热完成: {success_count}/{total_count} 项成功")
            return success_count == total_count

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
            return False


# 全局缓存实例
cache_service = CacheService()
