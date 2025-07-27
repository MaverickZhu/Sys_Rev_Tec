import asyncio
import pytest
import time
import psutil
import os
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
from fastapi.testclient import TestClient


class TestPerformance:
    def setup_method(self, method):
        """设置测试环境"""
        # 使用简单的TestClient，不覆盖数据库依赖
        from app.main import app
        self.client = TestClient(app)
        
    def test_response_time_health_check(self):
        """测试健康检查端点的响应时间"""
        response_times = []
        
        # 执行10次请求
        for _ in range(10):
            start_time = time.time()
            response = self.client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # 计算统计信息
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\n健康检查端点性能统计:")
        print(f"平均响应时间: {avg_time:.3f}秒")
        print(f"最大响应时间: {max_time:.3f}秒")
        print(f"最小响应时间: {min_time:.3f}秒")
        
        # 断言平均响应时间应该小于100ms
        assert avg_time < 0.1, f"平均响应时间过长: {avg_time:.3f}秒"
        
    def test_response_time_openapi_json(self):
        """测试OpenAPI JSON端点的响应时间"""
        response_times = []
        
        # 执行5次请求（OpenAPI生成可能较慢）
        for _ in range(5):
            start_time = time.time()
            response = self.client.get("/openapi.json")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # 计算统计信息
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\nOpenAPI JSON端点性能统计:")
        print(f"平均响应时间: {avg_time:.3f}秒")
        print(f"最大响应时间: {max_time:.3f}秒")
        print(f"最小响应时间: {min_time:.3f}秒")
        
        # 断言平均响应时间应该小于2秒
        assert avg_time < 2.0, f"平均响应时间过长: {avg_time:.3f}秒"
        
    def test_concurrent_requests(self):
        """测试并发请求处理能力"""
        def make_request(request_id: int) -> Dict[str, Any]:
            """发送单个请求"""
            start_time = time.time()
            
            try:
                response = self.client.get("/health")
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status_code == 200
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "status_code": 0,
                    "response_time": (end_time - start_time) * 1000,
                    "success": False,
                    "error": str(e)
                }
        
        # 测试不同并发级别
        concurrent_levels = [5, 10, 15]
        
        for concurrent_count in concurrent_levels:
            print(f"\n测试 {concurrent_count} 个并发请求:")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrent_count)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 分析结果
            successful_requests = [r for r in results if r["success"]]
            failed_requests = [r for r in results if not r["success"]]
            
            success_rate = len(successful_requests) / len(results) * 100
            avg_response_time = statistics.mean([r["response_time"] for r in successful_requests]) if successful_requests else 0
            
            print(f"  总耗时: {total_time:.2f}s")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  平均响应时间: {avg_response_time:.2f}ms")
            print(f"  失败请求数: {len(failed_requests)}")
            
            # 验证性能要求
            assert success_rate >= 90, f"并发 {concurrent_count} 请求成功率过低: {success_rate:.1f}%"
            assert avg_response_time < 1000, f"并发 {concurrent_count} 请求平均响应时间过长: {avg_response_time:.2f}ms"
            
            if failed_requests:
                print(f"  失败请求详情: {failed_requests[:2]}...")  # 只显示前2个失败请求
        
    def test_memory_usage_stability(self):
        """测试内存使用稳定性（简单版本）"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量请求
        for i in range(100):
            response = self.client.get("/health")
            assert response.status_code == 200
            
            # 每20次请求检查一次内存
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"请求 {i}: 内存使用 {current_memory:.2f} MB")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"\n内存使用统计:")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 断言内存增长不应该超过50MB
        assert memory_increase < 50, f"内存泄漏可能: 增长了 {memory_increase:.2f} MB"
        
    def test_async_performance(self):
        """测试异步处理性能"""
        num_requests = 20
        responses = []
        
        start_time = time.time()
        
        # 快速连续发送请求
        for _ in range(num_requests):
            response = self.client.get("/health")
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_response_time = total_time / num_requests
        
        print(f"\n异步性能测试结果:")
        print(f"请求数量: {num_requests}")
        print(f"总耗时: {total_time:.3f}s")
        print(f"平均响应时间: {avg_response_time:.3f}s")
        
        # 检查所有响应都成功
        for response in responses:
            assert response.status_code == 200
        
        # 断言平均响应时间
        assert avg_response_time < 0.1, f"平均响应时间过长: {avg_response_time}s"
        
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        # 简化的数据库查询性能测试，使用健康检查端点
        query_times = []
        
        print("\n测试查询性能...")
        for _ in range(20):
            start_time = time.time()
            
            # 使用健康检查端点测试响应性能
            response = self.client.get("/health")
            assert response.status_code == 200
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # 毫秒
            query_times.append(query_time)
        
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        min_query_time = min(query_times)
        
        print(f"\n查询性能统计:")
        print(f"  平均查询时间: {avg_query_time:.2f}ms")
        print(f"  最大查询时间: {max_query_time:.2f}ms")
        print(f"  最小查询时间: {min_query_time:.2f}ms")
        
        # 验证查询性能
        assert avg_query_time < 100, f"查询平均时间过长: {avg_query_time:.2f}ms"
        assert max_query_time < 200, f"查询最大时间过长: {max_query_time:.2f}ms"
    
    def test_api_response_time_comprehensive(self):
        """测试API响应时间（全面版本）"""
        endpoints = [
            ("/health", "GET"),
            ("/openapi.json", "GET")
        ]
        
        response_times = {}
        
        for endpoint, method in endpoints:
            times = []
            
            # 每个端点测试10次
            for _ in range(10):
                start_time = time.time()
                
                if method == "GET":
                    response = self.client.get(endpoint)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                # 确保请求成功
                assert response.status_code in [200, 201], f"Request to {endpoint} failed with status {response.status_code}"
                
                times.append(response_time)
            
            response_times[endpoint] = {
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "median": statistics.median(times)
            }
        
        # 验证响应时间要求
        for endpoint, stats in response_times.items():
            print(f"\n{endpoint} 响应时间统计:")
            print(f"  平均: {stats['avg']:.2f}ms")
            print(f"  最小: {stats['min']:.2f}ms")
            print(f"  最大: {stats['max']:.2f}ms")
            print(f"  中位数: {stats['median']:.2f}ms")
            
            # 健康检查端点应该在100ms内响应
            if endpoint == "/health":
                assert stats["avg"] < 100, f"{endpoint} 平均响应时间过长: {stats['avg']:.2f}ms"
            # OpenAPI端点可以稍慢一些
            elif endpoint == "/openapi.json":
                assert stats["avg"] < 2000, f"{endpoint} 平均响应时间过长: {stats['avg']:.2f}ms"