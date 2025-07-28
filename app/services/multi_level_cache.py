#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多级缓存架构实现
提供L1内存缓存 + L2 Redis缓存的多级缓存策略
"""

import asyncio
import json
import pickle
import gzip
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import OrderedDict

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config.cache_strategy import CacheStrategy, CacheLevel, EvictionPolicy
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheHitType(Enum):
    """缓存命中类型"""
    L1_HIT = "l1_hit"      # L1缓存命中
    L2_HIT = "l2_hit"      # L2缓存命中
    MISS = "miss"          # 缓存未命中


@dataclass
class CacheItem:
    """缓存项"""
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[int] = None
    compressed: bool = False
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """更新访问时间和次数"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计信息"""
    l1_hits: int = 0
    l2_hits: int = 0
    misses: int = 0
    l1_size: int = 0
    l2_size: int = 0
    l1_memory_usage: int = 0
    evictions: int = 0
    
    @property
    def total_requests(self) -> int:
        return self.l1_hits + self.l2_hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.l1_hits + self.l2_hits) / self.total_requests
    
    @property
    def l1_hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.l1_hits / self.total_requests


class L1MemoryCache:
    """L1内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    def get(self, key: str) -> Tuple[Any, CacheHitType]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None, CacheHitType.MISS
            
            item = self._cache[key]
            
            # 检查是否过期
            if item.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                return None, CacheHitType.MISS
            
            # 更新访问信息
            item.touch()
            # 移到末尾（LRU策略）
            self._cache.move_to_end(key)
            
            self._stats.l1_hits += 1
            return item.value, CacheHitType.L1_HIT
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            try:
                # 检查是否需要淘汰
                if len(self._cache) >= self.max_size and key not in self._cache:
                    self._evict_one()
                
                # 创建缓存项
                item = CacheItem(
                    value=value,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    ttl=ttl or self.default_ttl
                )
                
                self._cache[key] = item
                self._cache.move_to_end(key)
                
                return True
            except Exception as e:
                logger.error(f"L1 cache set error: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def _evict_one(self):
        """淘汰一个缓存项（LRU策略）"""
        if self._cache:
            # 移除最旧的项
            self._cache.popitem(last=False)
            self._stats.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            self._stats.l1_size = len(self._cache)
            # 估算内存使用量
            self._stats.l1_memory_usage = sum(
                len(str(k)) + len(str(v.value)) for k, v in self._cache.items()
            )
            
            return {
                "size": self._stats.l1_size,
                "max_size": self.max_size,
                "hits": self._stats.l1_hits,
                "memory_usage_bytes": self._stats.l1_memory_usage,
                "evictions": self._stats.evictions
            }


class MultiLevelCacheService:
    """多级缓存服务"""
    
    def __init__(self):
        self.l1_cache = L1MemoryCache(
            max_size=getattr(settings, 'L1_CACHE_SIZE', 1000),
            default_ttl=getattr(settings, 'L1_CACHE_TTL', 300)
        )
        self.redis_client: Optional[Redis] = None
        self._stats = CacheStats()
        self._initialized = False
    
    async def initialize(self):
        """初始化缓存服务"""
        if self._initialized:
            return
        
        try:
            # 初始化Redis连接
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=False,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Multi-level cache service initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, using L1 cache only: {e}")
            self.redis_client = None
        
        self._initialized = True
    
    async def get(self, key: str, strategy: CacheStrategy) -> Tuple[Any, CacheHitType]:
        """获取缓存值（多级查找）"""
        if not self._initialized:
            await self.initialize()
        
        # 构建完整键名
        full_key = f"{strategy.key_prefix}:{key}" if strategy.key_prefix else key
        
        # L1缓存查找
        if strategy.level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
            value, hit_type = self.l1_cache.get(full_key)
            if hit_type == CacheHitType.L1_HIT:
                return value, hit_type
        
        # L2 Redis缓存查找
        if strategy.level == CacheLevel.L2_REDIS and self.redis_client:
            try:
                cached_data = await self.redis_client.get(full_key)
                if cached_data:
                    # 反序列化
                    value = self._deserialize(cached_data, strategy)
                    
                    # 回填到L1缓存
                    self.l1_cache.set(full_key, value, strategy.ttl)
                    
                    self._stats.l2_hits += 1
                    return value, CacheHitType.L2_HIT
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        self._stats.misses += 1
        return None, CacheHitType.MISS
    
    async def set(self, key: str, value: Any, strategy: CacheStrategy) -> bool:
        """设置缓存值（多级存储）"""
        if not self._initialized:
            await self.initialize()
        
        # 构建完整键名
        full_key = f"{strategy.key_prefix}:{key}" if strategy.key_prefix else key
        
        success = True
        
        # L1缓存存储
        if strategy.level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
            self.l1_cache.set(full_key, value, strategy.ttl)
        
        # L2 Redis缓存存储
        if strategy.level == CacheLevel.L2_REDIS and self.redis_client:
            try:
                # 序列化
                serialized_data = self._serialize(value, strategy)
                
                # 存储到Redis
                await self.redis_client.setex(
                    full_key, 
                    strategy.ttl, 
                    serialized_data
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                success = False
        
        return success
    
    async def delete(self, key: str, strategy: CacheStrategy) -> bool:
        """删除缓存项"""
        if not self._initialized:
            await self.initialize()
        
        # 构建完整键名
        full_key = f"{strategy.key_prefix}:{key}" if strategy.key_prefix else key
        
        success = True
        
        # 从L1缓存删除
        self.l1_cache.delete(full_key)
        
        # 从L2 Redis缓存删除
        if self.redis_client:
            try:
                await self.redis_client.delete(full_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                success = False
        
        return success
    
    async def clear_by_tags(self, tags: List[str]) -> int:
        """根据标签清除缓存"""
        if not self.redis_client:
            return 0
        
        try:
            # 构建标签模式
            patterns = [f"*{tag}*" for tag in tags]
            deleted_count = 0
            
            for pattern in patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
            
            # 清除L1缓存中匹配的项
            self.l1_cache.clear()  # 简化实现，清除所有L1缓存
            
            return deleted_count
        except Exception as e:
            logger.error(f"Clear by tags error: {e}")
            return 0
    
    async def warmup_cache(self, warmup_data: Dict[str, Any], strategy: CacheStrategy):
        """缓存预热"""
        logger.info(f"Starting cache warmup with {len(warmup_data)} items")
        
        for key, value in warmup_data.items():
            await self.set(key, value, strategy)
        
        logger.info("Cache warmup completed")
    
    def _serialize(self, value: Any, strategy: CacheStrategy) -> bytes:
        """序列化数据"""
        if strategy.serialization == "json":
            data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        elif strategy.serialization == "pickle":
            data = pickle.dumps(value)
        else:
            # 默认使用pickle
            data = pickle.dumps(value)
        
        # 压缩
        if strategy.compression:
            data = gzip.compress(data)
        
        return data
    
    def _deserialize(self, data: bytes, strategy: CacheStrategy) -> Any:
        """反序列化数据"""
        # 解压缩
        if strategy.compression:
            data = gzip.decompress(data)
        
        if strategy.serialization == "json":
            return json.loads(data.decode('utf-8'))
        elif strategy.serialization == "pickle":
            return pickle.loads(data)
        else:
            # 默认使用pickle
            return pickle.loads(data)
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        l1_stats = self.l1_cache.get_stats()
        
        redis_stats = {}
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_stats = {
                    "connected": True,
                    "memory_usage": info.get("used_memory_human", "N/A"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "connected_clients": info.get("connected_clients", 0)
                }
            except Exception as e:
                redis_stats = {"connected": False, "error": str(e)}
        else:
            redis_stats = {"connected": False}
        
        return {
            "l1_cache": l1_stats,
            "l2_redis": redis_stats,
            "overall": {
                "total_requests": self._stats.total_requests,
                "hit_rate": self._stats.hit_rate,
                "l1_hit_rate": self._stats.l1_hit_rate,
                "l1_hits": self._stats.l1_hits,
                "l2_hits": self._stats.l2_hits,
                "misses": self._stats.misses
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "l1_cache": True,
            "l2_redis": False,
            "overall": False
        }
        
        # 检查Redis连接
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["l2_redis"] = True
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
        
        health["overall"] = health["l1_cache"] or health["l2_redis"]
        
        return health
    
    async def close(self):
        """关闭缓存服务"""
        if self.redis_client:
            await self.redis_client.close()
        self.l1_cache.clear()
        logger.info("Multi-level cache service closed")


# 全局多级缓存服务实例
_multi_cache_service: Optional[MultiLevelCacheService] = None


async def get_multi_cache_service() -> MultiLevelCacheService:
    """获取多级缓存服务实例"""
    global _multi_cache_service
    
    if _multi_cache_service is None:
        _multi_cache_service = MultiLevelCacheService()
        await _multi_cache_service.initialize()
    
    return _multi_cache_service