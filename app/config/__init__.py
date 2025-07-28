#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块
包含应用程序的各种配置
"""

from .cache_strategy import (
    CacheLevel,
    CachePriority,
    EvictionPolicy,
    CacheStrategy,
    CacheStrategyManager,
    cache_strategy_manager,
    get_cache_strategy,
    optimize_cache_strategy
)

__all__ = [
    "CacheLevel",
    "CachePriority",
    "EvictionPolicy",
    "CacheStrategy",
    "CacheStrategyManager",
    "cache_strategy_manager",
    "get_cache_strategy",
    "optimize_cache_strategy"
]