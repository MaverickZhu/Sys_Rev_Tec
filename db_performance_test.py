#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能压力测试脚本
"""

import asyncio
import asyncpg
import time
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'sys_rev_tech',
    'user': 'postgres',
    'password': 'sys_rev_password'
}

class DatabasePerformanceTest:
    def __init__(self):
        self.results = []
        self.lock = threading.Lock()
    
    async def create_connection(self):
        """创建数据库连接"""
        try:
            conn = await asyncpg.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return None
    
    async def simple_query_test(self, conn, query_id):
        """简单查询测试"""
        start_time = time.time()
        try:
            result = await conn.fetchval("SELECT 1")
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # 转换为毫秒
            
            with self.lock:
                self.results.append({
                    'query_id': query_id,
                    'type': 'simple_query',
                    'duration': duration,
                    'success': True
                })
            return duration
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            with self.lock:
                self.results.append({
                    'query_id': query_id,
                    'type': 'simple_query',
                    'duration': duration,
                    'success': False,
                    'error': str(e)
                })
            return None
    
    async def user_query_test(self, conn, query_id):
        """用户表查询测试"""
        start_time = time.time()
        try:
            result = await conn.fetch("SELECT id, username, email FROM users LIMIT 10")
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            with self.lock:
                self.results.append({
                    'query_id': query_id,
                    'type': 'user_query',
                    'duration': duration,
                    'success': True,
                    'rows': len(result)
                })
            return duration
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            with self.lock:
                self.results.append({
                    'query_id': query_id,
                    'type': 'user_query',
                    'duration': duration,
                    'success': False,
                    'error': str(e)
                })
            return None
    
    async def concurrent_test(self, num_connections=10, queries_per_connection=5):
        """并发测试"""
        print(f"开始并发测试: {num_connections} 个连接，每个连接 {queries_per_connection} 个查询")
        
        tasks = []
        for conn_id in range(num_connections):
            conn = await self.create_connection()
            if conn:
                for query_id in range(queries_per_connection):
                    # 交替执行简单查询和用户查询
                    if query_id % 2 == 0:
                        task = self.simple_query_test(conn, f"{conn_id}-{query_id}")
                    else:
                        task = self.user_query_test(conn, f"{conn_id}-{query_id}")
                    tasks.append(task)
        
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_duration = end_time - start_time
        print(f"并发测试完成，总耗时: {total_duration:.2f} 秒")
        
        return total_duration
    
    def analyze_results(self):
        """分析测试结果"""
        if not self.results:
            print("没有测试结果")
            return
        
        print("\n" + "="*50)
        print("数据库性能测试结果分析")
        print("="*50)
        
        # 按查询类型分组
        simple_queries = [r for r in self.results if r['type'] == 'simple_query' and r['success']]
        user_queries = [r for r in self.results if r['type'] == 'user_query' and r['success']]
        
        # 简单查询统计
        if simple_queries:
            durations = [r['duration'] for r in simple_queries]
            print(f"\n📊 简单查询性能 (SELECT 1):")
            print(f"  总查询数: {len(simple_queries)}")
            print(f"  平均响应时间: {statistics.mean(durations):.2f} ms")
            print(f"  最快响应时间: {min(durations):.2f} ms")
            print(f"  最慢响应时间: {max(durations):.2f} ms")
            if len(durations) > 1:
                print(f"  响应时间标准差: {statistics.stdev(durations):.2f} ms")
        
        # 用户查询统计
        if user_queries:
            durations = [r['duration'] for r in user_queries]
            print(f"\n👥 用户查询性能 (SELECT users):")
            print(f"  总查询数: {len(user_queries)}")
            print(f"  平均响应时间: {statistics.mean(durations):.2f} ms")
            print(f"  最快响应时间: {min(durations):.2f} ms")
            print(f"  最慢响应时间: {max(durations):.2f} ms")
            if len(durations) > 1:
                print(f"  响应时间标准差: {statistics.stdev(durations):.2f} ms")
        
        # 错误统计
        errors = [r for r in self.results if not r['success']]
        if errors:
            print(f"\n❌ 错误统计:")
            print(f"  错误查询数: {len(errors)}")
            print(f"  成功率: {((len(self.results) - len(errors)) / len(self.results) * 100):.2f}%")
        else:
            print(f"\n✅ 所有查询都成功执行")
            print(f"  成功率: 100.00%")
        
        # 总体统计
        all_successful = [r for r in self.results if r['success']]
        if all_successful:
            all_durations = [r['duration'] for r in all_successful]
            print(f"\n📈 总体性能:")
            print(f"  总查询数: {len(self.results)}")
            print(f"  成功查询数: {len(all_successful)}")
            print(f"  平均响应时间: {statistics.mean(all_durations):.2f} ms")
            print(f"  QPS (每秒查询数): {len(all_successful) / (max(all_durations) / 1000):.2f}")

async def main():
    """主函数"""
    print("数据库性能压力测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test = DatabasePerformanceTest()
    
    # 测试数据库连接
    print("\n🔍 测试数据库连接...")
    conn = await test.create_connection()
    if not conn:
        print("❌ 数据库连接失败，测试终止")
        return
    
    print("✅ 数据库连接成功")
    await conn.close()
    
    # 执行并发测试
    print("\n🚀 开始性能测试...")
    await test.concurrent_test(num_connections=5, queries_per_connection=10)
    
    # 分析结果
    test.analyze_results()
    
    print("\n" + "="*50)
    print("测试完成")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())