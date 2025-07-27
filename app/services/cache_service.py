from typing import Any, Optional, Union, Dict, List
import json
import pickle
from datetime import datetime, timedelta
import redis
from app.core.config import settings
from app.core.logging import logger

class CacheService:
    """缓存服务类，提供Redis缓存功能"""
    
    def __init__(self):
        self.redis_client = None
        self.is_enabled = settings.CACHE_ENABLED
        self._connect()
    
    def _connect(self):
        """连接Redis"""
        if not self.is_enabled:
            logger.info("Cache is disabled")
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_enabled = False
            self.redis_client = None
    
    def _get_key(self, key: str, prefix: str = "app") -> str:
        """生成缓存键"""
        return f"{prefix}:{key}"
    
    def set(self, key: str, value: Any, expire: Optional[int] = None, prefix: str = "app") -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），默认使用配置中的值
            prefix: 键前缀
            
        Returns:
            bool: 是否设置成功
        """
        if not self.is_enabled or not self.redis_client:
            return False
            
        try:
            cache_key = self._get_key(key, prefix)
            
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            elif isinstance(value, (int, float, str, bool)):
                serialized_value = str(value)
            else:
                # 对于复杂对象使用pickle
                serialized_value = pickle.dumps(value).hex()
                cache_key += ":pickle"
            
            # 设置过期时间
            if expire is None:
                expire = settings.CACHE_EXPIRE_TIME
            
            result = self.redis_client.setex(cache_key, expire, serialized_value)
            logger.debug(f"Cache set: {cache_key} (expire: {expire}s)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    def get(self, key: str, prefix: str = "app") -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            缓存值或None
        """
        if not self.is_enabled or not self.redis_client:
            return None
            
        try:
            cache_key = self._get_key(key, prefix)
            
            # 尝试获取普通缓存
            value = self.redis_client.get(cache_key)
            if value is not None:
                try:
                    # 尝试JSON反序列化
                    return json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    # 如果不是JSON，返回字符串
                    return value
            
            # 尝试获取pickle缓存
            pickle_key = cache_key + ":pickle"
            pickle_value = self.redis_client.get(pickle_key)
            if pickle_value is not None:
                try:
                    return pickle.loads(bytes.fromhex(pickle_value))
                except Exception as e:
                    logger.error(f"Failed to deserialize pickle cache {key}: {e}")
                    return None
            
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
            return None
    
    def delete(self, key: str, prefix: str = "app") -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            bool: 是否删除成功
        """
        if not self.is_enabled or not self.redis_client:
            return False
            
        try:
            cache_key = self._get_key(key, prefix)
            pickle_key = cache_key + ":pickle"
            
            # 删除两种可能的键
            result1 = self.redis_client.delete(cache_key)
            result2 = self.redis_client.delete(pickle_key)
            
            success = result1 > 0 or result2 > 0
            if success:
                logger.debug(f"Cache deleted: {cache_key}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {e}")
            return False
    
    def exists(self, key: str, prefix: str = "app") -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            bool: 是否存在
        """
        if not self.is_enabled or not self.redis_client:
            return False
            
        try:
            cache_key = self._get_key(key, prefix)
            pickle_key = cache_key + ":pickle"
            
            return (self.redis_client.exists(cache_key) > 0 or 
                   self.redis_client.exists(pickle_key) > 0)
            
        except Exception as e:
            logger.error(f"Failed to check cache existence {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str, prefix: str = "app") -> int:
        """根据模式清除缓存
        
        Args:
            pattern: 匹配模式（支持*通配符）
            prefix: 键前缀
            
        Returns:
            int: 删除的键数量
        """
        if not self.is_enabled or not self.redis_client:
            return 0
            
        try:
            search_pattern = self._get_key(pattern, prefix)
            keys = self.redis_client.keys(search_pattern)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {search_pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        if not self.is_enabled or not self.redis_client:
            return {"enabled": False, "connected": False}
            
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> str:
        """计算缓存命中率"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return "N/A"
        
        hit_rate = (hits / total) * 100
        return f"{hit_rate:.2f}%"
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        if not self.is_enabled:
            return {
                "status": "disabled",
                "message": "Cache is disabled"
            }
            
        try:
            if not self.redis_client:
                return {
                    "status": "error",
                    "message": "Redis client not initialized"
                }
            
            # 测试连接
            start_time = datetime.now()
            self.redis_client.ping()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "message": "Cache is working properly",
                "response_time_ms": round(response_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "error",
                "message": f"Cache health check failed: {str(e)}"
            }

# 创建全局缓存服务实例
cache_service = CacheService()

# 便捷函数
def cache_set(key: str, value: Any, expire: Optional[int] = None, prefix: str = "app") -> bool:
    """设置缓存的便捷函数"""
    return cache_service.set(key, value, expire, prefix)

def cache_get(key: str, prefix: str = "app") -> Optional[Any]:
    """获取缓存的便捷函数"""
    return cache_service.get(key, prefix)

def cache_delete(key: str, prefix: str = "app") -> bool:
    """删除缓存的便捷函数"""
    return cache_service.delete(key, prefix)

def cache_exists(key: str, prefix: str = "app") -> bool:
    """检查缓存存在的便捷函数"""
    return cache_service.exists(key, prefix)

def cache_clear_pattern(pattern: str, prefix: str = "app") -> int:
    """清除缓存模式的便捷函数"""
    return cache_service.clear_pattern(pattern, prefix)