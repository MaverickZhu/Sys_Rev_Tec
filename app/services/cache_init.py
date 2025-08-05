"""缓存系统初始化模块

提供缓存系统的统一初始化和配置管理功能。
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.cache_manager import cache_manager
from app.services.cache_monitor import get_cache_monitor
from app.services.cache_optimizer import cache_optimizer
from app.services.cache_service import cache_service
from app.config.cache_strategy import cache_strategy_manager

logger = logging.getLogger(__name__)


class CacheSystemInitializer:
    """缓存系统初始化器"""

    def __init__(self):
        self.initialized = False
        self.components_status: Dict[str, bool] = {
            "cache_service": False,
            "cache_strategy": False,
            "cache_monitor": False,
            "cache_optimizer": False,
            "cache_manager": False,
        }

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化缓存系统

        Args:
            config: 可选的配置参数

        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            logger.warning("Cache system already initialized")
            return True

        if not settings.CACHE_ENABLED:
            logger.info("Cache is disabled, skipping initialization")
            return True

        logger.info("Starting cache system initialization...")

        try:
            # 1. 初始化缓存策略管理器
            await self._initialize_strategy_manager(config)

            # 2. 初始化缓存服务
            await self._initialize_cache_service(config)

            # 3. 初始化性能监控器
            await self._initialize_monitor(config)

            # 4. 初始化优化器
            await self._initialize_optimizer(config)

            # 5. 初始化缓存管理器
            await self._initialize_manager(config)

            # 6. 执行系统健康检查
            await self._perform_health_check()

            # 7. 启动后台任务
            await self._start_background_tasks()

            self.initialized = True
            logger.info("Cache system initialization completed successfully")
            return True

        except Exception as e:
            logger.error(f"Cache system initialization failed: {e}")
            await self._cleanup_partial_initialization()
            return False

    async def _initialize_strategy_manager(
        self, config: Optional[Dict[str, Any]]
    ) -> None:
        """初始化缓存策略管理器"""
        try:
            logger.info("Initializing cache strategy manager...")
            
            from app.config.cache_strategy import CacheStrategy, CacheLevel, CachePriority, EvictionPolicy

            # 检查默认策略是否已存在，如果不存在则创建
            if not cache_strategy_manager.get_strategy("default"):
                default_strategy = CacheStrategy(
                    name="default",
                    level=CacheLevel.L1_MEMORY,
                    priority=CachePriority.MEDIUM,
                    ttl=3600,
                    max_size=1000,
                    eviction_policy=EvictionPolicy.LRU,
                    key_prefix="default:"
                )
                cache_strategy_manager.add_custom_strategy("default", default_strategy)
            
            # 检查会话策略是否已存在
            if not cache_strategy_manager.get_strategy("session") and not cache_strategy_manager.get_strategy("user_session"):
                session_strategy = CacheStrategy(
                    name="session",
                    level=CacheLevel.L2_REDIS,
                    priority=CachePriority.HIGH,
                    ttl=1800,
                    max_size=500,
                    eviction_policy=EvictionPolicy.TTL,
                    key_prefix="session:"
                )
                cache_strategy_manager.add_custom_strategy("session", session_strategy)
            
            # 检查API响应策略是否已存在
            if not cache_strategy_manager.get_strategy("api_response"):
                api_response_strategy = CacheStrategy(
                    name="api_response",
                    level=CacheLevel.L2_REDIS,
                    priority=CachePriority.MEDIUM,
                    ttl=600,
                    max_size=2000,
                    eviction_policy=EvictionPolicy.LRU,
                    key_prefix="api:"
                )
                cache_strategy_manager.add_custom_strategy("api_response", api_response_strategy)
            
            # 如果配置中有自定义策略，则添加
            if config and "strategies" in config:
                for strategy_name, strategy_config in config["strategies"].items():
                    custom_strategy = CacheStrategy(
                        name=strategy_name,
                        level=getattr(CacheLevel, strategy_config.get("level", "L1_MEMORY")),
                        priority=getattr(CachePriority, strategy_config.get("priority", "MEDIUM")),
                        ttl=strategy_config.get("ttl", 3600),
                        max_size=strategy_config.get("max_size", 1000),
                        eviction_policy=getattr(EvictionPolicy, strategy_config.get("eviction_policy", "LRU")),
                        key_prefix=strategy_config.get("key_prefix", f"{strategy_name}:")
                    )
                    cache_strategy_manager.add_custom_strategy(strategy_name, custom_strategy)

            self.components_status["cache_strategy"] = True
            logger.info("Cache strategy manager initialized with default strategies")

        except Exception as e:
            logger.error(f"Failed to initialize cache strategy manager: {e}")
            raise

    async def _initialize_cache_service(self, config: Optional[Dict[str, Any]]) -> None:
        """初始化缓存服务"""
        try:
            logger.info("Initializing cache service...")

            # 首先初始化缓存服务（创建Redis连接池等）
            await cache_service.initialize()
            
            # 然后验证连接状态
            health = await cache_service.health_check()
            if health.get("status") != "healthy":
                raise Exception(f"Cache service health check failed: {health}")

            self.components_status["cache_service"] = True
            logger.info("Cache service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            raise

    async def _initialize_monitor(self, config: Optional[Dict[str, Any]]) -> None:
        """初始化性能监控器"""
        try:
            logger.info("Initializing cache monitor...")

            # 获取监控器实例
            monitor = get_cache_monitor()

            # 启动监控器
            await monitor.start_monitoring()

            # 设置监控配置
            monitor_config = {
                "collection_interval": 60,  # 60秒收集一次指标
                "retention_hours": 24,  # 保留24小时历史数据
                "alert_thresholds": {
                    "hit_rate_min": 0.8,
                    "response_time_max": 100,
                    "memory_usage_max": 0.9,
                },
            }

            if config and "monitor" in config:
                monitor_config.update(config["monitor"])

            await monitor.configure(monitor_config)

            self.components_status["cache_monitor"] = True
            logger.info("Cache monitor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache monitor: {e}")
            raise

    async def _initialize_optimizer(self, config: Optional[Dict[str, Any]]) -> None:
        """初始化缓存优化器"""
        try:
            logger.info("Initializing cache optimizer...")

            # 设置优化器配置
            optimizer_config = {
                "optimization_interval": 300,  # 5分钟执行一次优化检查
                "auto_optimization": True,  # 启用自动优化
                "optimization_thresholds": {
                    "hit_rate_threshold": 0.7,
                    "memory_threshold": 0.8,
                    "response_time_threshold": 50,
                },
            }

            if config and "optimizer" in config:
                optimizer_config.update(config["optimizer"])

            await cache_optimizer.configure(optimizer_config)

            # 启动优化器
            if optimizer_config.get("auto_optimization", True):
                await cache_optimizer.start_scheduler()

            self.components_status["cache_optimizer"] = True
            logger.info("Cache optimizer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache optimizer: {e}")
            raise

    async def _initialize_manager(self, config: Optional[Dict[str, Any]]) -> None:
        """初始化缓存管理器"""
        try:
            logger.info("Initializing cache manager...")

            # 初始化缓存管理器
            await cache_manager.initialize()

            # 设置管理器配置
            manager_config = {
                "health_check_interval": 30,  # 30秒执行一次健康检查
                "batch_size": 100,  # 批量操作默认大小
                "timeout": 30,  # 操作超时时间
            }

            if config and "manager" in config:
                manager_config.update(config["manager"])

            await cache_manager.configure(manager_config)

            self.components_status["cache_manager"] = True
            logger.info("Cache manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise

    async def _perform_health_check(self) -> None:
        """执行系统健康检查"""
        try:
            logger.info("Performing cache system health check...")

            # 检查各组件状态
            system_status = await cache_manager.get_system_status()

            if not system_status.redis_connected:
                raise Exception("Redis connection failed")

            if system_status.local_cache_size < 0:
                raise Exception("Local cache initialization failed")

            logger.info(f"Cache system health check passed: {system_status}")

        except Exception as e:
            logger.error(f"Cache system health check failed: {e}")
            raise

    async def _start_background_tasks(self) -> None:
        """启动后台任务"""
        try:
            logger.info("Starting cache system background tasks...")

            # 启动监控任务
            monitor = get_cache_monitor()
            asyncio.create_task(monitor.start_background_collection())

            # 启动优化任务
            asyncio.create_task(cache_optimizer.start_background_optimization())

            # 健康检查任务已在 cache_manager.initialize() 中启动
            # 这里不需要重复启动

            logger.info("Cache system background tasks started")

        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
            raise

    async def _cleanup_partial_initialization(self) -> None:
        """清理部分初始化的组件"""
        logger.info("Cleaning up partially initialized cache system...")

        try:
            # 停止已启动的组件
            if self.components_status.get("cache_optimizer"):
                await cache_optimizer.stop_scheduler()

            if self.components_status.get("cache_monitor"):
                monitor = get_cache_monitor()
                await monitor.stop_monitoring()

            if self.components_status.get("cache_manager"):
                await cache_manager.shutdown()

            # 重置状态
            self.components_status = {k: False for k in self.components_status}

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def shutdown(self) -> None:
        """关闭缓存系统"""
        if not self.initialized:
            logger.info("Cache system not initialized, nothing to shutdown")
            return

        logger.info("Shutting down cache system...")

        try:
            # 按相反顺序关闭组件
            await cache_manager.shutdown()
            await cache_optimizer.stop_scheduler()
            monitor = get_cache_monitor()
            await monitor.stop_monitoring()
            await cache_service.close()

            self.initialized = False
            self.components_status = {k: False for k in self.components_status}

            logger.info("Cache system shutdown completed")

        except Exception as e:
            logger.error(f"Error during cache system shutdown: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取缓存系统状态"""
        return {
            "initialized": self.initialized,
            "components_status": self.components_status.copy(),
            "cache_enabled": settings.CACHE_ENABLED,
        }


# 全局缓存系统初始化器实例
cache_system_initializer = CacheSystemInitializer()


# 便捷函数
async def initialize_cache_system(config: Optional[Dict[str, Any]] = None) -> bool:
    """初始化缓存系统的便捷函数"""
    return await cache_system_initializer.initialize(config)


async def shutdown_cache_system() -> None:
    """关闭缓存系统的便捷函数"""
    await cache_system_initializer.shutdown()


def get_cache_system_status() -> Dict[str, Any]:
    """获取缓存系统状态的便捷函数"""
    return cache_system_initializer.get_status()
