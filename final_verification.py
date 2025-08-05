#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证缓存策略管理器
"""

import sys
sys.path.append('/app')

from app.config.cache_strategy import cache_strategy_manager

def final_verification():
    """最终验证"""
    print("=== 最终验证缓存策略管理器 ===")
    
    print(f"策略总数: {len(cache_strategy_manager.strategies)}")
    print(f"包含default策略: {'default' in cache_strategy_manager.strategies}")
    
    if 'default' in cache_strategy_manager.strategies:
        default_strategy = cache_strategy_manager.get_strategy('default')
        print(f"Default策略详情:")
        print(f"  名称: {default_strategy.name}")
        print(f"  级别: {default_strategy.level}")
        print(f"  优先级: {default_strategy.priority}")
        print(f"  TTL: {default_strategy.ttl}秒")
        print(f"  键前缀: {default_strategy.key_prefix}")
        print(f"  标签: {default_strategy.tags}")
        print("\n✅ DEFAULT策略已成功初始化！")
    else:
        print("\n❌ DEFAULT策略仍然缺失！")
    
    print(f"\n所有策略列表:")
    for name, strategy in cache_strategy_manager.strategies.items():
        print(f"  - {name}: {strategy.name}")
    
    return 'default' in cache_strategy_manager.strategies

if __name__ == "__main__":
    success = final_verification()
    if success:
        print("\n🎉 缓存策略管理器问题已完全解决！")
    else:
        print("\n⚠️ 问题仍然存在，需要进一步调查。")