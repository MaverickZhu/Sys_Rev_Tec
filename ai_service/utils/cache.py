# -*- coding: utf-8 -*-
"""
AI服务缓存管理
提供Redis缓存功能
"""

import json
import pickle
import hashlib
import logging
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from ai_service.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 全局Redis客户端
_redis_client: Optional[Redis] = None


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = settings.CACHE_TTL
    
    def _make_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key = ":".join(key_parts)
        return f"ai_service:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """生成数据哈希键"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return default
            
            # 尝试JSON解码
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # 如果JSON解码失败，尝试pickle
                try:
                    return pickle.loads(value)
                except:
                    # 如果都失败，返回原始字符串
                    return value.decode('utf-8')
                    
        except Exception as e:
            logger.warning(f"缓存获取失败 {key}: {e}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize_method: str = 'json'
    ) -> bool:
        """设置缓存值"""
        try:
            # 序列化数据
            if serialize_method == 'json':
                try:
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError):
                    # 如果JSON序列化失败，使用pickle
                    serialized_value = pickle.dumps(value)
            elif serialize_method == 'pickle':
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置TTL
            expire_time = ttl or self.default_ttl
            
            # 存储到Redis
            await self.redis.setex(key, expire_time, serialized_value)
            return True
            
        except Exception as e:
            logger.warning(f"缓存设置失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"缓存删除失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"缓存检查失败 {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.warning(f"缓存过期设置失败 {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """获取缓存剩余时间"""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.warning(f"缓存TTL获取失败 {key}: {e}")
            return -1
    
    # 向量缓存相关方法
    async def cache_embedding(
        self, 
        text: str, 
        model: str, 
        embedding: List[float],
        ttl: Optional[int] = None
    ) -> bool:
        """缓存文本嵌入向量"""
        text_hash = self._hash_key(text)
        key = self._make_key("embedding", model, text_hash)
        
        cache_data = {
            "text": text,
            "model": model,
            "embedding": embedding,
            "dimension": len(embedding)
        }
        
        return await self.set(
            key, 
            cache_data, 
            ttl or settings.VECTOR_CACHE_TTL,
            serialize_method='pickle'  # 使用pickle以保持数值精度
        )
    
    async def get_cached_embedding(
        self, 
        text: str, 
        model: str
    ) -> Optional[List[float]]:
        """获取缓存的文本嵌入向量"""
        text_hash = self._hash_key(text)
        key = self._make_key("embedding", model, text_hash)
        
        cache_data = await self.get(key)
        if cache_data and isinstance(cache_data, dict):
            return cache_data.get("embedding")
        
        return None
    
    async def cache_search_results(
        self,
        query: str,
        search_type: str,
        results: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """缓存搜索结果"""
        query_data = {
            "query": query,
            "search_type": search_type,
            "filters": filters or {}
        }
        query_hash = self._hash_key(query_data)
        key = self._make_key("search", search_type, query_hash)
        
        cache_data = {
            "query": query,
            "search_type": search_type,
            "filters": filters,
            "results": results,
            "count": len(results)
        }
        
        return await self.set(
            key,
            cache_data,
            ttl or settings.SEARCH_CACHE_TTL
        )
    
    async def get_cached_search_results(
        self,
        query: str,
        search_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的搜索结果"""
        query_data = {
            "query": query,
            "search_type": search_type,
            "filters": filters or {}
        }
        query_hash = self._hash_key(query_data)
        key = self._make_key("search", search_type, query_hash)
        
        cache_data = await self.get(key)
        if cache_data and isinstance(cache_data, dict):
            return cache_data.get("results")
        
        return None
    
    async def cache_document_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """缓存文档分块结果"""
        key = self._make_key("document_chunks", document_id)
        
        cache_data = {
            "document_id": document_id,
            "chunks": chunks,
            "count": len(chunks)
        }
        
        return await self.set(
            key,
            cache_data,
            ttl or settings.CACHE_TTL
        )
    
    async def get_cached_document_chunks(
        self,
        document_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的文档分块"""
        key = self._make_key("document_chunks", document_id)
        
        cache_data = await self.get(key)
        if cache_data and isinstance(cache_data, dict):
            return cache_data.get("chunks")
        
        return None
    
    # 批量操作
    async def mget(self, keys: List[str]) -> List[Any]:
        """批量获取缓存"""
        try:
            values = await self.redis.mget(keys)
            results = []
            
            for value in values:
                if value is None:
                    results.append(None)
                else:
                    try:
                        results.append(json.loads(value))
                    except json.JSONDecodeError:
                        try:
                            results.append(pickle.loads(value))
                        except:
                            results.append(value.decode('utf-8'))
            
            return results
            
        except Exception as e:
            logger.warning(f"批量缓存获取失败: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批量设置缓存"""
        try:
            # 序列化所有值
            serialized_mapping = {}
            for key, value in mapping.items():
                try:
                    serialized_mapping[key] = json.dumps(value)
                except (TypeError, ValueError):
                    serialized_mapping[key] = pickle.dumps(value)
            
            # 批量设置
            await self.redis.mset(serialized_mapping)
            
            # 设置过期时间
            if ttl:
                expire_time = ttl or self.default_ttl
                for key in mapping.keys():
                    await self.redis.expire(key, expire_time)
            
            return True
            
        except Exception as e:
            logger.warning(f"批量缓存设置失败: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"模式缓存删除失败 {pattern}: {e}")
            return 0
    
    async def clear_document_cache(self, document_id: str) -> int:
        """清除文档相关的所有缓存"""
        patterns = [
            self._make_key("document_chunks", document_id),
            self._make_key("embedding", "*", self._hash_key(document_id)),
            self._make_key("search", "*", f"*{document_id}*")
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            info = await self.redis.info()
            
            # 获取AI服务相关的键数量
            ai_keys = await self.redis.keys("ai_service:*")
            
            # 按类型统计键数量
            key_stats = {
                "embedding": 0,
                "search": 0,
                "document_chunks": 0,
                "other": 0
            }
            
            for key in ai_keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if ":embedding:" in key_str:
                    key_stats["embedding"] += 1
                elif ":search:" in key_str:
                    key_stats["search"] += 1
                elif ":document_chunks:" in key_str:
                    key_stats["document_chunks"] += 1
                else:
                    key_stats["other"] += 1
            
            return {
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "ai_service_keys": len(ai_keys),
                "key_stats": key_stats
            }
            
        except Exception as e:
            logger.warning(f"缓存统计获取失败: {e}")
            return {"error": str(e)}


async def create_redis_client() -> Redis:
    """创建Redis客户端"""
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,  # 保持二进制数据以支持pickle
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=True,
            max_connections=settings.REDIS_POOL_SIZE
        )
        
        # 测试连接
        await client.ping()
        logger.info("✅ Redis连接创建成功")
        
        return client
        
    except Exception as e:
        logger.error(f"❌ Redis连接创建失败: {e}")
        raise


async def get_redis_client() -> Redis:
    """获取Redis客户端"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await create_redis_client()
    
    return _redis_client


async def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    redis_client = await get_redis_client()
    return CacheManager(redis_client)


async def close_redis_client():
    """关闭Redis客户端"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("✅ Redis连接已关闭")


if __name__ == "__main__":
    # 测试缓存功能
    import asyncio
    
    async def test_cache():
        try:
            cache = await get_cache_manager()
            
            # 测试基本缓存
            await cache.set("test_key", {"message": "Hello, World!"}, ttl=60)
            value = await cache.get("test_key")
            print(f"缓存测试: {value}")
            
            # 测试向量缓存
            embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            await cache.cache_embedding("测试文本", "test_model", embedding)
            cached_embedding = await cache.get_cached_embedding("测试文本", "test_model")
            print(f"向量缓存测试: {cached_embedding}")
            
            # 获取统计信息
            stats = await cache.get_cache_stats()
            print(f"缓存统计: {stats}")
            
            await close_redis_client()
            
        except Exception as e:
            print(f"缓存测试失败: {e}")
    
    asyncio.run(test_cache())