from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.logger import logger


class CacheStrategy(ABC):
    """缓存策略基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.usage_count = 0

    @abstractmethod
    async def should_cache(self, key: str, value: Any, **kwargs) -> bool:
        """判断是否应该缓存"""

    @abstractmethod
    async def get_ttl(self, key: str, value: Any, **kwargs) -> Optional[int]:
        """获取TTL时间（秒）"""

    @abstractmethod
    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        """判断是否应该驱逐"""

    def update_usage(self):
        """更新使用统计"""
        self.last_used = datetime.now()
        self.usage_count += 1


class LRUStrategy(CacheStrategy):
    """LRU缓存策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("LRU", config)
        self.max_size = config.get("max_size", 1000)
        self.default_ttl = config.get("default_ttl", 3600)

    async def should_cache(self, key: str, value: Any, **kwargs) -> bool:
        return True

    async def get_ttl(self, key: str, value: Any, **kwargs) -> Optional[int]:
        return kwargs.get("ttl", self.default_ttl)

    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        # 基于访问时间的LRU逻辑
        last_access = metadata.get("last_access")
        if not last_access:
            return True

        # 如果超过一定时间未访问，则驱逐
        threshold = datetime.now() - timedelta(hours=1)
        return last_access < threshold


class TTLStrategy(CacheStrategy):
    """TTL缓存策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("TTL", config)
        self.default_ttl = config.get("default_ttl", 1800)
        self.max_ttl = config.get("max_ttl", 7200)

    async def should_cache(self, key: str, value: Any, **kwargs) -> bool:
        return True

    async def get_ttl(self, key: str, value: Any, **kwargs) -> Optional[int]:
        ttl = kwargs.get("ttl", self.default_ttl)
        return min(ttl, self.max_ttl)

    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        # TTL策略主要依赖Redis的过期机制
        return False


class SizeBasedStrategy(CacheStrategy):
    """基于大小的缓存策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("SizeBased", config)
        self.max_value_size = config.get("max_value_size", 1024 * 1024)  # 1MB
        self.default_ttl = config.get("default_ttl", 3600)

    async def should_cache(self, key: str, value: Any, **kwargs) -> bool:
        # 检查值的大小
        try:
            import sys

            value_size = sys.getsizeof(value)
            return value_size <= self.max_value_size
        except Exception:
            return True

    async def get_ttl(self, key: str, value: Any, **kwargs) -> Optional[int]:
        return kwargs.get("ttl", self.default_ttl)

    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        return False


class CacheStrategyManager:
    """缓存策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, CacheStrategy] = {}
        self.default_strategy = "LRU"
        self._initialize_default_strategies()

    def _initialize_default_strategies(self):
        """初始化默认策略"""
        # LRU策略
        lru_config = {"max_size": 1000, "default_ttl": 3600}
        self.strategies["LRU"] = LRUStrategy(lru_config)
        
        # 默认策略（使用LRU）
        default_config = {"max_size": 1000, "default_ttl": 3600}
        self.strategies["default"] = LRUStrategy(default_config)

        # TTL策略
        ttl_config = {"default_ttl": 1800, "max_ttl": 7200}
        self.strategies["TTL"] = TTLStrategy(ttl_config)

        # 基于大小的策略
        size_config = {"max_value_size": 1024 * 1024, "default_ttl": 3600}
        self.strategies["SizeBased"] = SizeBasedStrategy(size_config)

    async def create_strategy(self, name: str, config: Dict[str, Any]) -> bool:
        """创建并注册缓存策略"""
        try:
            # 根据配置创建相应的策略实例
            cache_type = config.get("cache_type", "lru").lower()

            if cache_type == "lru":
                strategy = LRUStrategy(config)
            elif cache_type == "ttl":
                strategy = TTLStrategy(config)
            elif cache_type == "size":
                strategy = SizeBasedStrategy(config)
            else:
                # 默认使用LRU策略
                strategy = LRUStrategy(config)

            # 使用自定义名称
            strategy.name = name
            self.strategies[name] = strategy
            logger.info(f"Created and registered cache strategy: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create strategy {name}: {e}")
            return False

    async def register_strategy(self, strategy: CacheStrategy) -> bool:
        """注册缓存策略"""
        try:
            self.strategies[strategy.name] = strategy
            logger.info(f"Registered cache strategy: {strategy.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register strategy {strategy.name}: {e}")
            return False

    async def get_strategy(self, name: str) -> Optional[CacheStrategy]:
        """获取缓存策略"""
        strategy = self.strategies.get(name)
        if strategy:
            strategy.update_usage()
        return strategy

    async def remove_strategy(self, name: str) -> bool:
        """移除缓存策略"""
        if name in self.strategies and name != self.default_strategy:
            del self.strategies[name]
            logger.info(f"Removed cache strategy: {name}")
            return True
        return False

    async def list_strategies(self) -> List[str]:
        """列出所有策略名称"""
        return list(self.strategies.keys())

    async def get_strategy_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取策略信息"""
        strategy = self.strategies.get(name)
        if not strategy:
            return None

        return {
            "name": strategy.name,
            "config": strategy.config,
            "created_at": strategy.created_at.isoformat(),
            "last_used": strategy.last_used.isoformat(),
            "usage_count": strategy.usage_count,
        }

    async def update_strategy_config(self, name: str, config: Dict[str, Any]) -> bool:
        """更新策略配置"""
        strategy = self.strategies.get(name)
        if not strategy:
            return False

        try:
            strategy.config.update(config)
            logger.info(f"Updated config for strategy: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update strategy config {name}: {e}")
            return False

    async def get_default_strategy(self) -> CacheStrategy:
        """获取默认策略"""
        return self.strategies[self.default_strategy]

    async def set_default_strategy(self, name: str) -> bool:
        """设置默认策略"""
        if name in self.strategies:
            self.default_strategy = name
            logger.info(f"Set default strategy to: {name}")
            return True
        return False

    async def evaluate_caching_decision(
        self, key: str, value: Any, strategy_name: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """评估缓存决策"""
        strategy_name = strategy_name or self.default_strategy
        strategy = await self.get_strategy(strategy_name)

        if not strategy:
            strategy = await self.get_default_strategy()

        should_cache = await strategy.should_cache(key, value, **kwargs)
        ttl = await strategy.get_ttl(key, value, **kwargs) if should_cache else None

        return {
            "should_cache": should_cache,
            "ttl": ttl,
            "strategy_used": strategy.name,
            "timestamp": datetime.now().isoformat(),
        }
