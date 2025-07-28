"""缓存系统配置模块

提供缓存系统的配置管理和环境适配功能。
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from app.core.config import settings


@dataclass
class CacheStrategyConfig:
    """缓存策略配置"""
    cache_type: str = "hybrid"  # local, redis, hybrid
    ttl: int = 3600  # 默认1小时
    max_size: int = 1000  # 最大条目数
    eviction_policy: str = "lru"  # lru, lfu, ttl, random
    compression_enabled: bool = False
    key_prefix: str = "app"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cache_type": self.cache_type,
            "ttl": self.ttl,
            "max_size": self.max_size,
            "eviction_policy": self.eviction_policy,
            "compression_enabled": self.compression_enabled,
            "key_prefix": self.key_prefix,
        }


@dataclass
class MonitorConfig:
    """监控配置"""
    collection_interval: int = 60  # 指标收集间隔（秒）
    retention_hours: int = 24  # 历史数据保留时间（小时）
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "hit_rate_min": 0.8,
        "response_time_max": 100,  # 毫秒
        "memory_usage_max": 0.9,
        "error_rate_max": 0.05,
    })
    enable_alerts: bool = True
    export_enabled: bool = True
    export_interval: int = 3600  # 导出间隔（秒）


@dataclass
class OptimizerConfig:
    """优化器配置"""
    optimization_interval: int = 300  # 优化检查间隔（秒）
    auto_optimization: bool = True
    optimization_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "hit_rate_threshold": 0.7,
        "memory_threshold": 0.8,
        "response_time_threshold": 50,  # 毫秒
        "error_rate_threshold": 0.03,
    })
    max_concurrent_optimizations: int = 3
    optimization_cooldown: int = 600  # 优化冷却时间（秒）


@dataclass
class ManagerConfig:
    """管理器配置"""
    health_check_interval: int = 30  # 健康检查间隔（秒）
    batch_size: int = 100  # 批量操作默认大小
    timeout: int = 30  # 操作超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）
    enable_background_tasks: bool = True


@dataclass
class CacheSystemConfig:
    """缓存系统完整配置"""
    # 基础配置
    enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    redis_timeout: int = 5
    
    # 默认策略配置
    default_strategies: Dict[str, CacheStrategyConfig] = field(default_factory=dict)
    
    # 组件配置
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    manager: ManagerConfig = field(default_factory=ManagerConfig)
    
    # 环境特定配置
    environment: str = "development"
    debug: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.default_strategies:
            self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """设置默认策略"""
        self.default_strategies = {
            "default": CacheStrategyConfig(
                cache_type="hybrid",
                ttl=3600,
                max_size=1000,
                eviction_policy="lru",
                compression_enabled=False,
                key_prefix="app",
            ),
            "session": CacheStrategyConfig(
                cache_type="redis",
                ttl=1800,
                max_size=500,
                eviction_policy="ttl",
                compression_enabled=False,
                key_prefix="session",
            ),
            "api_response": CacheStrategyConfig(
                cache_type="local",
                ttl=300,
                max_size=2000,
                eviction_policy="lru",
                compression_enabled=True,
                key_prefix="api",
            ),
            "ocr_result": CacheStrategyConfig(
                cache_type="hybrid",
                ttl=7200,  # 2小时
                max_size=500,
                eviction_policy="lru",
                compression_enabled=True,
                key_prefix="ocr",
            ),
            "project_data": CacheStrategyConfig(
                cache_type="redis",
                ttl=1800,  # 30分钟
                max_size=200,
                eviction_policy="lru",
                compression_enabled=False,
                key_prefix="project",
            ),
            "user_data": CacheStrategyConfig(
                cache_type="redis",
                ttl=900,  # 15分钟
                max_size=1000,
                eviction_policy="ttl",
                compression_enabled=False,
                key_prefix="user",
            ),
        }
    
    def get_strategy_config(self, strategy_name: str) -> Optional[CacheStrategyConfig]:
        """获取策略配置"""
        return self.default_strategies.get(strategy_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "redis_url": self.redis_url,
            "redis_pool_size": self.redis_pool_size,
            "redis_timeout": self.redis_timeout,
            "strategies": {
                name: config.to_dict() 
                for name, config in self.default_strategies.items()
            },
            "monitor": {
                "collection_interval": self.monitor.collection_interval,
                "retention_hours": self.monitor.retention_hours,
                "alert_thresholds": self.monitor.alert_thresholds,
                "enable_alerts": self.monitor.enable_alerts,
                "export_enabled": self.monitor.export_enabled,
                "export_interval": self.monitor.export_interval,
            },
            "optimizer": {
                "optimization_interval": self.optimizer.optimization_interval,
                "auto_optimization": self.optimizer.auto_optimization,
                "optimization_thresholds": self.optimizer.optimization_thresholds,
                "max_concurrent_optimizations": self.optimizer.max_concurrent_optimizations,
                "optimization_cooldown": self.optimizer.optimization_cooldown,
            },
            "manager": {
                "health_check_interval": self.manager.health_check_interval,
                "batch_size": self.manager.batch_size,
                "timeout": self.manager.timeout,
                "max_retries": self.manager.max_retries,
                "retry_delay": self.manager.retry_delay,
                "enable_background_tasks": self.manager.enable_background_tasks,
            },
            "environment": self.environment,
            "debug": self.debug,
        }


def get_cache_config_for_environment(env: str = None) -> CacheSystemConfig:
    """根据环境获取缓存配置"""
    if env is None:
        env = settings.ENVIRONMENT
    
    # 基础配置
    config = CacheSystemConfig(
        enabled=settings.CACHE_ENABLED,
        redis_url=getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
        environment=env,
        debug=settings.DEBUG,
    )
    
    # 环境特定调整
    if env == "development":
        # 开发环境：更短的TTL，更小的缓存大小，更频繁的监控
        config.monitor.collection_interval = 30
        config.monitor.retention_hours = 12
        config.optimizer.optimization_interval = 180
        config.manager.health_check_interval = 15
        
        # 调整策略
        for strategy in config.default_strategies.values():
            strategy.ttl = min(strategy.ttl, 1800)  # 最大30分钟
            strategy.max_size = min(strategy.max_size, 500)  # 减小缓存大小
    
    elif env == "testing":
        # 测试环境：最小配置，快速过期
        config.monitor.collection_interval = 10
        config.monitor.retention_hours = 1
        config.optimizer.optimization_interval = 60
        config.manager.health_check_interval = 5
        
        # 调整策略
        for strategy in config.default_strategies.values():
            strategy.ttl = 60  # 1分钟
            strategy.max_size = 50  # 很小的缓存
    
    elif env == "production":
        # 生产环境：优化性能，更长的保留时间
        config.monitor.collection_interval = 120
        config.monitor.retention_hours = 72  # 3天
        config.optimizer.optimization_interval = 600  # 10分钟
        config.manager.health_check_interval = 60
        
        # 调整策略
        for strategy in config.default_strategies.values():
            strategy.max_size = strategy.max_size * 2  # 增大缓存大小
            if strategy.cache_type == "local":
                strategy.cache_type = "hybrid"  # 生产环境优先使用混合缓存
    
    return config


def load_cache_config_from_file(file_path: str) -> Optional[CacheSystemConfig]:
    """从文件加载缓存配置"""
    try:
        import json
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 创建基础配置
        config = CacheSystemConfig(
            enabled=config_data.get('enabled', True),
            redis_url=config_data.get('redis_url', 'redis://localhost:6379/0'),
            redis_pool_size=config_data.get('redis_pool_size', 10),
            redis_timeout=config_data.get('redis_timeout', 5),
            environment=config_data.get('environment', 'development'),
            debug=config_data.get('debug', False),
        )
        
        # 加载策略配置
        strategies_data = config_data.get('strategies', {})
        config.default_strategies = {}
        for name, strategy_data in strategies_data.items():
            config.default_strategies[name] = CacheStrategyConfig(**strategy_data)
        
        # 加载组件配置
        if 'monitor' in config_data:
            monitor_data = config_data['monitor']
            config.monitor = MonitorConfig(
                collection_interval=monitor_data.get('collection_interval', 60),
                retention_hours=monitor_data.get('retention_hours', 24),
                alert_thresholds=monitor_data.get('alert_thresholds', {}),
                enable_alerts=monitor_data.get('enable_alerts', True),
                export_enabled=monitor_data.get('export_enabled', True),
                export_interval=monitor_data.get('export_interval', 3600),
            )
        
        if 'optimizer' in config_data:
            optimizer_data = config_data['optimizer']
            config.optimizer = OptimizerConfig(
                optimization_interval=optimizer_data.get('optimization_interval', 300),
                auto_optimization=optimizer_data.get('auto_optimization', True),
                optimization_thresholds=optimizer_data.get('optimization_thresholds', {}),
                max_concurrent_optimizations=optimizer_data.get('max_concurrent_optimizations', 3),
                optimization_cooldown=optimizer_data.get('optimization_cooldown', 600),
            )
        
        if 'manager' in config_data:
            manager_data = config_data['manager']
            config.manager = ManagerConfig(
                health_check_interval=manager_data.get('health_check_interval', 30),
                batch_size=manager_data.get('batch_size', 100),
                timeout=manager_data.get('timeout', 30),
                max_retries=manager_data.get('max_retries', 3),
                retry_delay=manager_data.get('retry_delay', 1.0),
                enable_background_tasks=manager_data.get('enable_background_tasks', True),
            )
        
        return config
        
    except Exception as e:
        print(f"Failed to load cache config from file {file_path}: {e}")
        return None


def save_cache_config_to_file(config: CacheSystemConfig, file_path: str) -> bool:
    """保存缓存配置到文件"""
    try:
        import json
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Failed to save cache config to file {file_path}: {e}")
        return False


# 全局缓存配置实例
cache_config = get_cache_config_for_environment()


# 便捷函数
def get_default_cache_config() -> CacheSystemConfig:
    """获取默认缓存配置"""
    return cache_config


def get_strategy_config(strategy_name: str) -> Optional[CacheStrategyConfig]:
    """获取指定策略配置"""
    return cache_config.get_strategy_config(strategy_name)


def update_cache_config(new_config: Dict[str, Any]) -> bool:
    """更新缓存配置"""
    global cache_config
    try:
        # 这里可以实现配置的动态更新逻辑
        # 暂时返回True表示成功
        return True
    except Exception:
        return False