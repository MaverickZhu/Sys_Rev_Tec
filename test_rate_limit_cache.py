#!/usr/bin/env python3
"""
测试API限流和缓存功能

这个脚本用于测试：
1. API限流是否正常工作
2. 缓存功能是否正常工作
3. Redis连接是否正常
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, Any

# 测试配置
BASE_URL = "http://127.0.0.1:8001"
API_BASE = f"{BASE_URL}/api/v1"


class APITester:
    def __init__(self):
        self.session = None
        self.auth_token = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """测试健康检查端点"""
        print("\n=== 测试健康检查 ===")
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                print(f"健康检查状态: {response.status}")
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return response.status == 200
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False
    
    async def test_cache_health(self):
        """测试缓存健康检查"""
        print("\n=== 测试缓存健康检查 ===")
        try:
            async with self.session.get(f"{API_BASE}/cache/health") as response:
                data = await response.json()
                print(f"缓存健康检查状态: {response.status}")
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return data.get('data', {}).get('healthy', False)
        except Exception as e:
            print(f"缓存健康检查失败: {e}")
            return False
    
    async def test_rate_limiting(self):
        """测试API限流功能"""
        print("\n=== 测试API限流功能 ===")
        
        # 测试健康检查端点的限流（应该比较宽松）
        endpoint = f"{API_BASE}/health"
        success_count = 0
        rate_limited_count = 0
        
        print(f"快速发送20个请求到 {endpoint}")
        
        tasks = []
        for i in range(20):
            tasks.append(self.make_request(endpoint, i))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"请求 {i+1}: 异常 - {result}")
            else:
                status, response_time = result
                if status == 200:
                    success_count += 1
                    print(f"请求 {i+1}: 成功 (状态: {status}, 耗时: {response_time:.3f}s)")
                elif status == 429:
                    rate_limited_count += 1
                    print(f"请求 {i+1}: 被限流 (状态: {status}, 耗时: {response_time:.3f}s)")
                else:
                    print(f"请求 {i+1}: 其他状态 {status} (耗时: {response_time:.3f}s)")
        
        print(f"\n限流测试结果:")
        print(f"- 成功请求: {success_count}")
        print(f"- 被限流请求: {rate_limited_count}")
        print(f"- 总请求数: {len(results)}")
        
        return rate_limited_count > 0  # 如果有请求被限流，说明限流功能正常
    
    async def make_request(self, url: str, request_id: int):
        """发送单个请求并记录响应时间"""
        start_time = time.time()
        try:
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                return response.status, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return None, response_time
    
    async def login(self):
        """登录获取认证token"""
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        try:
            async with self.session.post(f"{API_BASE}/login/access-token", data=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    return True
                else:
                    print(f"登录失败，状态码: {response.status}")
                    return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False
    
    def get_auth_headers(self):
        """获取认证头"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def test_cache_functionality(self):
        """测试缓存功能"""
        print("\n=== 测试缓存功能 ===")
        
        # 先尝试登录
        if not await self.login():
            print("登录失败，跳过缓存功能测试")
            return False
        
        # 测试OCR统计信息的缓存
        endpoint = f"{API_BASE}/ocr/statistics"
        headers = self.get_auth_headers()
        
        print("第一次请求OCR统计信息（应该从数据库获取）")
        start_time = time.time()
        try:
            async with self.session.get(endpoint, headers=headers) as response:
                first_response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    print(f"第一次请求成功 (耗时: {first_response_time:.3f}s)")
                    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"第一次请求失败，状态码: {response.status}")
                    if response.status == 401:
                        print("认证失败，可能是用户不存在或密码错误")
                    return False
        except Exception as e:
            print(f"第一次请求异常: {e}")
            return False
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        print("\n第二次请求OCR统计信息（应该从缓存获取，更快）")
        start_time = time.time()
        try:
            async with self.session.get(endpoint, headers=headers) as response:
                second_response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    print(f"第二次请求成功 (耗时: {second_response_time:.3f}s)")
                    
                    # 比较响应时间
                    if second_response_time < first_response_time:
                        print(f"✅ 缓存生效！第二次请求更快 ({second_response_time:.3f}s < {first_response_time:.3f}s)")
                        return True
                    else:
                        print(f"⚠️ 缓存可能未生效，第二次请求耗时: {second_response_time:.3f}s")
                        return False
                else:
                    print(f"第二次请求失败，状态码: {response.status}")
                    return False
        except Exception as e:
            print(f"第二次请求异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始API限流和缓存功能测试...")
        print(f"测试目标: {BASE_URL}")
        
        results = {
            "health_check": False,
            "cache_health": False,
            "rate_limiting": False,
            "cache_functionality": False
        }
        
        # 1. 健康检查
        results["health_check"] = await self.test_health_check()
        
        # 2. 缓存健康检查
        results["cache_health"] = await self.test_cache_health()
        
        # 3. 限流功能测试
        results["rate_limiting"] = await self.test_rate_limiting()
        
        # 4. 缓存功能测试
        results["cache_functionality"] = await self.test_cache_functionality()
        
        # 输出测试结果
        print("\n" + "="*50)
        print("测试结果汇总:")
        print("="*50)
        
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            test_name_cn = {
                "health_check": "健康检查",
                "cache_health": "缓存健康检查",
                "rate_limiting": "API限流功能",
                "cache_functionality": "缓存功能"
            }.get(test_name, test_name)
            print(f"{test_name_cn}: {status}")
        
        passed_count = sum(results.values())
        total_count = len(results)
        
        print(f"\n总体结果: {passed_count}/{total_count} 项测试通过")
        
        if passed_count == total_count:
            print("🎉 所有测试都通过了！API限流和缓存功能正常工作。")
        else:
            print("⚠️ 部分测试失败，请检查配置和服务状态。")
        
        return results


async def main():
    """主函数"""
    async with APITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())