#!/usr/bin/env python3
"""
数据库优化管理脚本
用于创建索引、分析查询性能和优化数据库配置
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal, engine
from app.db.database_optimization import (
    create_database_indexes,
    analyze_query_performance,
    optimize_database_settings
)
from app.core.config import settings

def create_indexes():
    """创建数据库索引"""
    print("开始创建数据库索引...")
    try:
        create_database_indexes()
        print("✅ 数据库索引创建完成")
    except Exception as e:
        print(f"❌ 创建索引失败: {e}")
        return False
    return True

def analyze_performance():
    """分析查询性能"""
    print("开始分析查询性能...")
    try:
        analyze_query_performance()
        print("✅ 查询性能分析完成")
    except Exception as e:
        print(f"❌ 性能分析失败: {e}")
        return False
    return True

def optimize_config():
    """优化数据库配置"""
    print("开始优化数据库配置...")
    try:
        db = SessionLocal()
        optimize_database_settings()
        db.close()
        print("✅ 数据库配置优化完成")
    except Exception as e:
        print(f"❌ 配置优化失败: {e}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="数据库优化管理工具")
    parser.add_argument(
        "--create-indexes", 
        action="store_true", 
        help="创建数据库索引"
    )
    parser.add_argument(
        "--analyze-performance", 
        action="store_true", 
        help="分析查询性能"
    )
    parser.add_argument(
        "--optimize-config", 
        action="store_true", 
        help="优化数据库配置"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="执行所有优化操作"
    )
    
    args = parser.parse_args()
    
    if not any([args.create_indexes, args.analyze_performance, args.optimize_config, args.all]):
        parser.print_help()
        return
    
    print(f"数据库连接: {settings.SQLALCHEMY_DATABASE_URI}")
    print("=" * 50)
    
    success = True
    
    if args.all or args.create_indexes:
        success &= create_indexes()
    
    if args.all or args.analyze_performance:
        success &= analyze_performance()
    
    if args.all or args.optimize_config:
        success &= optimize_config()
    
    print("=" * 50)
    if success:
        print("✅ 所有操作完成")
    else:
        print("❌ 部分操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()