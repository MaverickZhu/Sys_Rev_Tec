#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('/app')

try:
    print("=== Testing add_custom_strategy method ===")
    
    from app.config.cache_strategy import cache_strategy_manager, CacheStrategy, CacheLevel, CachePriority, EvictionPolicy
    
    print(f"Initial strategies count: {len(cache_strategy_manager.strategies)}")
    print(f"Initial strategies: {list(cache_strategy_manager.strategies.keys())}")
    
    # 检查default策略是否存在
    default_exists = cache_strategy_manager.get_strategy("default")
    print(f"Default strategy exists: {default_exists is not None}")
    
    if not default_exists:
        print("\n=== Attempting to add default strategy ===")
        
        # 创建default策略
        default_strategy = CacheStrategy(
            name="default",
            level=CacheLevel.L1_MEMORY,
            priority=CachePriority.MEDIUM,
            ttl=3600,
            max_size=1000,
            eviction_policy=EvictionPolicy.LRU,
            key_prefix="default:"
        )
        
        print(f"Created strategy: {default_strategy.name}")
        
        # 尝试添加策略
        result = cache_strategy_manager.add_custom_strategy("default", default_strategy)
        print(f"add_custom_strategy result: {result}")
        
        # 再次检查
        print(f"Strategies count after add: {len(cache_strategy_manager.strategies)}")
        print(f"Strategies after add: {list(cache_strategy_manager.strategies.keys())}")
        
        # 检查default策略是否现在存在
        default_after = cache_strategy_manager.get_strategy("default")
        print(f"Default strategy exists after add: {default_after is not None}")
        
        if default_after:
            print(f"Default strategy details: {default_after.name}, level: {default_after.level}")
    
    # 测试add_custom_strategy方法的内部逻辑
    print("\n=== Testing add_custom_strategy with test strategy ===")
    test_strategy = CacheStrategy(
        name="test_strategy",
        level=CacheLevel.L2_REDIS,
        priority=CachePriority.LOW,
        ttl=1800,
        max_size=500,
        eviction_policy=EvictionPolicy.LRU,
        key_prefix="test:"
    )
    
    test_result = cache_strategy_manager.add_custom_strategy("test_strategy", test_strategy)
    print(f"Test strategy add result: {test_result}")
    
    test_exists = cache_strategy_manager.get_strategy("test_strategy")
    print(f"Test strategy exists: {test_exists is not None}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()