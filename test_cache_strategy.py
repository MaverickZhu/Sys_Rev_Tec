#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('/app')

try:
    print("=== Testing cache strategy manager ===")
    
    # 测试导入
    from app.config.cache_strategy import cache_strategy_manager, CacheStrategyManager
    print(f"Imported cache_strategy_manager: {type(cache_strategy_manager)}")
    
    # 检查初始化
    print(f"Manager initialized: {hasattr(cache_strategy_manager, 'strategies')}")
    
    # 检查所有策略
    all_strategies = cache_strategy_manager.strategies
    print(f"Total strategies: {len(all_strategies)}")
    
    for name, strategy in all_strategies.items():
        print(f"- {name}: {strategy.name} (level: {strategy.level}, ttl: {strategy.ttl})")
    
    # 特别检查default策略
    print("\n=== Checking default strategy ===")
    default_strategy = cache_strategy_manager.get_strategy("default")
    if default_strategy:
        print(f"Default strategy found: {default_strategy.name}")
        print(f"Level: {default_strategy.level}")
        print(f"TTL: {default_strategy.ttl}")
        print(f"Key prefix: {default_strategy.key_prefix}")
    else:
        print("ERROR: Default strategy not found!")
        
        # 尝试手动检查strategies字典
        print("\nManual check of strategies dict:")
        if 'default' in cache_strategy_manager.strategies:
            print("'default' key exists in strategies dict")
        else:
            print("'default' key NOT found in strategies dict")
            
        # 检查所有键
        print(f"All keys: {list(cache_strategy_manager.strategies.keys())}")
    
    # 测试创建新的管理器实例
    print("\n=== Testing new manager instance ===")
    new_manager = CacheStrategyManager()
    print(f"New manager strategies count: {len(new_manager.strategies)}")
    new_default = new_manager.get_strategy("default")
    if new_default:
        print(f"New manager has default strategy: {new_default.name}")
    else:
        print("New manager also missing default strategy!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()