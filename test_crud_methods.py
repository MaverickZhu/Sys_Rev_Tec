#!/usr/bin/env python3
"""
测试CRUD方法是否正常工作
"""

import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from app.crud.crud_user import user as user_crud
from app.core.cache_warmup import get_cache_warmup_manager
import asyncio

def test_crud_methods():
    """测试CRUD方法"""
    print("=== 测试CRUD方法 ===")
    
    db = SessionLocal()
    try:
        # 测试 get_all_users 方法
        print("\n1. 测试 get_all_users 方法:")
        try:
            users = user_crud.get_all_users(db)
            print(f"   成功获取 {len(users)} 个用户")
            if users:
                print(f"   第一个用户: {users[0].username}")
        except Exception as e:
            print(f"   错误: {e}")
        
        # 测试 get_active_users 方法
        print("\n2. 测试 get_active_users 方法:")
        try:
            active_users = user_crud.get_active_users(db, limit=10)
            print(f"   成功获取 {len(active_users)} 个活跃用户")
        except Exception as e:
            print(f"   错误: {e}")
        
        # 测试 get_recently_active_users 方法
        print("\n3. 测试 get_recently_active_users 方法:")
        try:
            recent_users = user_crud.get_recently_active_users(db, days=30)
            print(f"   成功获取 {len(recent_users)} 个最近活跃用户")
        except Exception as e:
            print(f"   错误: {e}")
            
    finally:
        db.close()

async def test_cache_warmup():
    """测试缓存预热"""
    print("\n=== 测试缓存预热 ===")
    
    db = SessionLocal()
    try:
        warmup_manager = get_cache_warmup_manager()
        
        print("\n测试预热关键权限数据:")
        try:
            await warmup_manager.warmup_critical_permissions(db)
            print("   预热关键权限数据成功")
        except Exception as e:
            print(f"   预热关键权限数据失败: {e}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_crud_methods()
    asyncio.run(test_cache_warmup())