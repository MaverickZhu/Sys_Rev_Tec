#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存策略配置
定义不同类型数据的缓存策略和优化规则
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class CacheLevel(Enum):
    """缓存级别"""

    L1_MEMORY = "l1_memory"  # 内存缓存（最快）
    L2_REDIS = "l2_redis"  # Redis缓存（快）
    L3_DATABASE = "l3_database"  # 数据库缓存（慢）


class CachePriority(Enum):
    """缓存优先级"""

    CRITICAL = "critical"  # 关键数据，永不过期
    HIGH = "high"  # 高优先级，长期缓存
    MEDIUM = "medium"  # 中等优先级，中期缓存
    LOW = "low"  # 低优先级，短期缓存
    TEMPORARY = "temporary"  # 临时数据，很快过期


class EvictionPolicy(Enum):
    """缓存淘汰策略"""

    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于时间过期
    RANDOM = "random"  # 随机淘汰


@dataclass
class CacheStrategy:
    """缓存策略配置"""

    name: str
    level: CacheLevel
    priority: CachePriority
    ttl: int  # 生存时间（秒）
    max_size: Optional[int] = None  # 最大缓存项数
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    compression: bool = False  # 是否压缩
    serialization: str = "json"  # 序列化方式：json, pickle, msgpack
    key_prefix: str = ""  # 键前缀
    tags: List[str] = None  # 缓存标签

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class CacheStrategyManager:
    """缓存策略管理器"""

    def __init__(self):
        self.strategies = self._initialize_strategies()
        self.usage_stats = {}
        self.optimization_rules = self._initialize_optimization_rules()

    def _initialize_strategies(self) -> Dict[str, CacheStrategy]:
        """初始化缓存策略"""
        return {
            # 默认缓存策略
            "default": CacheStrategy(
                name="默认缓存",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=3600,  # 1小时
                max_size=1000,
                eviction_policy=EvictionPolicy.LRU,
                key_prefix="app",
                tags=["default"],
            ),
            # 用户会话缓存
            "user_session": CacheStrategy(
                name="用户会话",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.HIGH,
                ttl=3600,  # 1小时
                eviction_policy=EvictionPolicy.TTL,
                key_prefix="session",
                tags=["user", "auth"],
            ),
            # API响应缓存
            "api_response": CacheStrategy(
                name="API响应",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=300,  # 5分钟
                max_size=1000,
                eviction_policy=EvictionPolicy.LRU,
                key_prefix="api",
                tags=["api", "response"],
            ),
            # 数据库查询缓存
            "db_query": CacheStrategy(
                name="数据库查询",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=600,  # 10分钟
                max_size=500,
                eviction_policy=EvictionPolicy.LRU,
                key_prefix="db",
                tags=["database", "query"],
            ),
            # AI模型结果缓存
            "ai_model_result": CacheStrategy(
                name="AI模型结果",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.HIGH,
                ttl=3600,  # 1小时
                max_size=200,
                eviction_policy=EvictionPolicy.LFU,
                compression=True,
                serialization="pickle",
                key_prefix="ai",
                tags=["ai", "model", "result"],
            ),
            # 向量嵌入缓存
            "vector_embedding": CacheStrategy(
                name="向量嵌入",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.HIGH,
                ttl=86400,  # 24小时
                max_size=1000,
                eviction_policy=EvictionPolicy.LFU,
                compression=True,
                serialization="pickle",
                key_prefix="vector",
                tags=["vector", "embedding"],
            ),
            # 搜索结果缓存
            "search_result": CacheStrategy(
                name="搜索结果",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=1800,  # 30分钟
                max_size=300,
                eviction_policy=EvictionPolicy.LRU,
                key_prefix="search",
                tags=["search", "result"],
            ),
            # 文档分块缓存
            "document_chunks": CacheStrategy(
                name="文档分块",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=7200,  # 2小时
                max_size=100,
                eviction_policy=EvictionPolicy.LRU,
                compression=True,
                key_prefix="doc",
                tags=["document", "chunks"],
            ),
            # 系统配置缓存
            "system_config": CacheStrategy(
                name="系统配置",
                level=CacheLevel.L1_MEMORY,
                priority=CachePriority.CRITICAL,
                ttl=3600,  # 1小时
                eviction_policy=EvictionPolicy.TTL,
                key_prefix="config",
                tags=["system", "config"],
            ),
            # 统计数据缓存
            "statistics": CacheStrategy(
                name="统计数据",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.LOW,
                ttl=900,  # 15分钟
                max_size=50,
                eviction_policy=EvictionPolicy.TTL,
                key_prefix="stats",
                tags=["statistics", "metrics"],
            ),
            # 临时数据缓存
            "temporary": CacheStrategy(
                name="临时数据",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.TEMPORARY,
                ttl=60,  # 1分钟
                max_size=100,
                eviction_policy=EvictionPolicy.FIFO,
                key_prefix="temp",
                tags=["temporary"],
            ),
            # 报告缓存
            "report_cache": CacheStrategy(
                name="报告缓存",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=1800,  # 30分钟
                max_size=50,
                eviction_policy=EvictionPolicy.LRU,
                compression=True,
                key_prefix="report",
                tags=["report", "generated"],
            ),
        }

    def _initialize_optimization_rules(self) -> List[Dict[str, Any]]:
        """初始化优化规则"""
        return [
            {
                "name": "高命中率策略优化",
                "condition": lambda stats: stats.get("hit_rate", 0) > 0.9,
                "action": "increase_ttl",
                "factor": 1.5,
                "description": "命中率高于90%时，增加TTL以减少缓存更新频率",
            },
            {
                "name": "低命中率策略优化",
                "condition": lambda stats: stats.get("hit_rate", 0) < 0.5,
                "action": "decrease_ttl",
                "factor": 0.7,
                "description": "命中率低于50%时，减少TTL以提高数据新鲜度",
            },
            {
                "name": "内存使用优化",
                "condition": lambda stats: stats.get("memory_usage_mb", 0) > 500,
                "action": "enable_compression",
                "description": "内存使用超过500MB时，启用压缩以节省空间",
            },
            {
                "name": "频繁访问优化",
                "condition": lambda stats: stats.get("access_frequency", 0) > 100,
                "action": "upgrade_to_l1",
                "description": "访问频率超过100次/分钟时，升级到L1内存缓存",
            },
            {
                "name": "冷数据清理",
                "condition": lambda stats: stats.get("last_access_hours", 0) > 24,
                "action": "evict_cold_data",
                "description": "超过24小时未访问的数据标记为冷数据并清理",
            },
        ]

    def get_strategy(self, cache_type: str) -> Optional[CacheStrategy]:
        """获取缓存策略"""
        return self.strategies.get(cache_type)

    def update_strategy(self, cache_type: str, **kwargs) -> bool:
        """更新缓存策略"""
        if cache_type not in self.strategies:
            return False

        strategy = self.strategies[cache_type]
        for key, value in kwargs.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)

        return True

    def add_custom_strategy(self, cache_type: str, strategy: CacheStrategy) -> bool:
        """添加自定义缓存策略"""
        if cache_type in self.strategies:
            return False

        self.strategies[cache_type] = strategy
        return True

    def get_optimal_strategy(
        self, data_type: str, access_pattern: str, data_size: int, update_frequency: str
    ) -> CacheStrategy:
        """根据数据特征获取最优缓存策略"""

        # 基础策略选择
        if access_pattern == "frequent":
            base_strategy = "ai_model_result"
        elif access_pattern == "read_heavy":
            base_strategy = "db_query"
        elif access_pattern == "write_heavy":
            base_strategy = "temporary"
        else:
            base_strategy = "api_response"

        strategy = self.strategies[base_strategy]

        # 根据数据大小调整
        if data_size > 1024 * 1024:  # 大于1MB
            strategy.compression = True
            strategy.serialization = "pickle"

        # 根据更新频率调整TTL
        if update_frequency == "high":
            strategy.ttl = min(strategy.ttl, 300)  # 最多5分钟
        elif update_frequency == "low":
            strategy.ttl = max(strategy.ttl, 3600)  # 至少1小时

        return strategy

    def analyze_cache_performance(
        self, cache_type: str, stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析缓存性能"""
        strategy = self.get_strategy(cache_type)
        if not strategy:
            return {"error": "未找到缓存策略"}

        analysis = {
            "strategy_name": strategy.name,
            "current_performance": {
                "hit_rate": stats.get("hit_rate", 0),
                "avg_response_time": stats.get("avg_response_time", 0),
                "memory_usage": stats.get("memory_usage", 0),
                "eviction_count": stats.get("eviction_count", 0),
            },
            "recommendations": [],
            "optimization_applied": [],
        }

        # 应用优化规则
        for rule in self.optimization_rules:
            if rule["condition"](stats):
                analysis["recommendations"].append(
                    {
                        "rule": rule["name"],
                        "action": rule["action"],
                        "description": rule["description"],
                    }
                )

                # 自动应用某些优化
                if rule["action"] == "increase_ttl":
                    new_ttl = int(strategy.ttl * rule["factor"])
                    self.update_strategy(cache_type, ttl=new_ttl)
                    analysis["optimization_applied"].append(f"TTL增加到{new_ttl}秒")
                elif rule["action"] == "decrease_ttl":
                    new_ttl = int(strategy.ttl * rule["factor"])
                    self.update_strategy(cache_type, ttl=new_ttl)
                    analysis["optimization_applied"].append(f"TTL减少到{new_ttl}秒")
                elif rule["action"] == "enable_compression":
                    self.update_strategy(cache_type, compression=True)
                    analysis["optimization_applied"].append("启用压缩")

        return analysis

    def get_cache_hierarchy(self) -> Dict[str, List[str]]:
        """获取缓存层次结构"""
        hierarchy = {"L1_MEMORY": [], "L2_REDIS": [], "L3_DATABASE": []}

        for cache_type, strategy in self.strategies.items():
            hierarchy[strategy.level.value.upper()].append(cache_type)

        return hierarchy

    def get_priority_groups(self) -> Dict[str, List[str]]:
        """获取优先级分组"""
        groups = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": [], "TEMPORARY": []}

        for cache_type, strategy in self.strategies.items():
            groups[strategy.priority.value.upper()].append(cache_type)

        return groups

    def export_strategies(self) -> Dict[str, Any]:
        """导出缓存策略配置"""
        export_data = {
            "strategies": {},
            "hierarchy": self.get_cache_hierarchy(),
            "priority_groups": self.get_priority_groups(),
            "optimization_rules": self.optimization_rules,
            "export_time": time.time(),
        }

        for cache_type, strategy in self.strategies.items():
            export_data["strategies"][cache_type] = {
                "name": strategy.name,
                "level": strategy.level.value,
                "priority": strategy.priority.value,
                "ttl": strategy.ttl,
                "max_size": strategy.max_size,
                "eviction_policy": strategy.eviction_policy.value,
                "compression": strategy.compression,
                "serialization": strategy.serialization,
                "key_prefix": strategy.key_prefix,
                "tags": strategy.tags,
            }

        return export_data


# 全局缓存策略管理器实例
cache_strategy_manager = CacheStrategyManager()


# 便捷函数
def get_cache_strategy(cache_type: str) -> Optional[CacheStrategy]:
    """获取缓存策略的便捷函数"""
    return cache_strategy_manager.get_strategy(cache_type)


def optimize_cache_strategy(cache_type: str, stats: Dict[str, Any]) -> Dict[str, Any]:
    """优化缓存策略的便捷函数"""
    return cache_strategy_manager.analyze_cache_performance(cache_type, stats)


def get_all_cache_strategies() -> Dict[str, CacheStrategy]:
    """获取所有缓存策略的便捷函数"""
    return cache_strategy_manager.strategies


def update_cache_strategy(cache_type: str, **kwargs) -> bool:
    """更新缓存策略的便捷函数"""
    return cache_strategy_manager.update_strategy(cache_type, **kwargs)


if __name__ == "__main__":
    # 测试缓存策略管理器
    manager = CacheStrategyManager()

    # 获取API响应缓存策略
    api_strategy = manager.get_strategy("api_response")
    print(f"API响应缓存策略: {api_strategy}")

    # 分析缓存性能
    test_stats = {
        "hit_rate": 0.85,
        "avg_response_time": 0.05,
        "memory_usage": 256,
        "eviction_count": 10,
    }

    analysis = manager.analyze_cache_performance("api_response", test_stats)
    print(f"\n性能分析结果: {analysis}")

    # 导出策略配置
    export_data = manager.export_strategies()
    print(f"\n策略配置导出: {len(export_data['strategies'])}个策略")
