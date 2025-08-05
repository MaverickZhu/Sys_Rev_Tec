#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CacheStrategyManager初始化过程 - 详细调试
"""

import sys
import os
sys.path.append('/app')

from app.config.cache_strategy import CacheStrategyManager, CacheStrategy, CacheLevel, CachePriority, EvictionPolicy

def test_strategies_creation():
    """测试策略创建过程"""
    print("=== 详细调试_initialize_strategies方法 ===")
    
    # 手动创建策略字典，模拟_initialize_strategies方法
    print("\n1. 手动创建策略字典:")
    
    strategies = {}
    
    # 添加default策略
    print("添加default策略...")
    default_strategy = CacheStrategy(
        name="默认缓存",
        level=CacheLevel.L2_REDIS,
        priority=CachePriority.MEDIUM,
        ttl=3600,  # 1小时
        max_size=1000,
        eviction_policy=EvictionPolicy.LRU,
        key_prefix="app",
        tags=["default"],
    )
    strategies["default"] = default_strategy
    print(f"添加default策略后，字典包含: {list(strategies.keys())}")
    
    # 添加其他策略
    print("\n添加其他策略...")
    
    # 用户会话缓存
    strategies["user_session"] = CacheStrategy(
        name="用户会话",
        level=CacheLevel.L2_REDIS,
        priority=CachePriority.HIGH,
        ttl=3600,  # 1小时
        eviction_policy=EvictionPolicy.TTL,
        key_prefix="session",
        tags=["user", "auth"],
    )
    
    # API响应缓存
    strategies["api_response"] = CacheStrategy(
        name="API响应",
        level=CacheLevel.L2_REDIS,
        priority=CachePriority.MEDIUM,
        ttl=300,  # 5分钟
        max_size=1000,
        eviction_policy=EvictionPolicy.LRU,
        key_prefix="api",
        tags=["api", "response"],
    )
    
    print(f"添加所有策略后，字典包含: {list(strategies.keys())}")
    print(f"字典中是否包含default策略: {'default' in strategies}")
    
    return strategies

def test_manager_creation():
    """测试管理器创建"""
    print("\n\n=== 测试CacheStrategyManager创建过程 ===")
    
    # 创建管理器实例
    manager = CacheStrategyManager()
    
    print(f"管理器创建后策略数量: {len(manager.strategies)}")
    print(f"管理器策略列表: {list(manager.strategies.keys())}")
    print(f"是否包含default策略: {'default' in manager.strategies}")
    
    # 检查每个策略的详细信息
    print("\n策略详细信息:")
    for name, strategy in manager.strategies.items():
        print(f"  {name}: {strategy.name} (level={strategy.level}, priority={strategy.priority})")
    
    return manager

def debug_initialize_strategies():
    """调试_initialize_strategies方法"""
    print("\n\n=== 调试_initialize_strategies方法 ===")
    
    # 创建管理器实例但不调用__init__
    manager = object.__new__(CacheStrategyManager)
    
    # 手动调用_initialize_strategies
    print("手动调用_initialize_strategies方法...")
    strategies_dict = manager._initialize_strategies()
    
    print(f"返回的策略数量: {len(strategies_dict)}")
    print(f"返回的策略列表: {list(strategies_dict.keys())}")
    print(f"是否包含default策略: {'default' in strategies_dict}")
    
    # 检查返回字典的内容
    if strategies_dict:
        print("\n返回字典中的策略详情:")
        for name, strategy in strategies_dict.items():
            print(f"  {name}: {strategy.name}")
    
    return strategies_dict

def check_source_code():
    """检查源代码"""
    print("\n\n=== 检查源代码 ===")
    
    # 读取cache_strategy.py文件
    try:
        with open('/app/app/config/cache_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找_initialize_strategies方法
        start_idx = content.find('def _initialize_strategies')
        if start_idx != -1:
            # 找到方法结束位置
            lines = content[start_idx:].split('\n')
            method_lines = []
            indent_level = None
            
            for line in lines:
                if line.strip().startswith('def _initialize_strategies'):
                    indent_level = len(line) - len(line.lstrip())
                    method_lines.append(line)
                elif indent_level is not None:
                    current_indent = len(line) - len(line.lstrip())
                    if line.strip() and current_indent <= indent_level:
                        break
                    method_lines.append(line)
            
            print("_initialize_strategies方法源代码:")
            for i, line in enumerate(method_lines[:50]):  # 只显示前50行
                print(f"{i+1:2d}: {line}")
                if '"default"' in line:
                    print(f"    ^^^ 找到default策略定义在第{i+1}行")
    
    except Exception as e:
        print(f"读取源代码时出错: {e}")

if __name__ == "__main__":
    try:
        # 测试手动创建策略
        manual_strategies = test_strategies_creation()
        
        # 测试管理器创建
        manager = test_manager_creation()
        
        # 调试_initialize_strategies方法
        debug_strategies = debug_initialize_strategies()
        
        # 检查源代码
        check_source_code()
        
        print("\n\n=== 总结 ===")
        print(f"手动创建策略数量: {len(manual_strategies)}")
        print(f"手动创建是否包含default: {'default' in manual_strategies}")
        print(f"管理器策略数量: {len(manager.strategies)}")
        print(f"管理器是否包含default: {'default' in manager.strategies}")
        print(f"调试方法返回策略数量: {len(debug_strategies)}")
        print(f"调试方法是否包含default: {'default' in debug_strategies}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()