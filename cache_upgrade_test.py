#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存系统升级测试脚本
验证缓存性能和功能
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# 导入缓存相关模块
try:
    from app.core.cache_health_check import run_cache_health_check
    from app.services.multi_level_cache import MultiLevelCacheService
    from app.config.cache_strategy import CacheStrategy, CacheLevel
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在项目根目录运行此脚本")
    exit(1)


class CacheUpgradeTest:
    """缓存系统升级测试类"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        self.cache_service = None
    
    async def initialize(self):
        """初始化测试环境"""
        try:
            print("🔧 初始化缓存服务...")
            self.cache_service = MultiLevelCacheService()
            await self.cache_service.initialize()
            print("✅ 缓存服务初始化成功")
            return True
        except Exception as e:
            print(f"❌ 缓存服务初始化失败: {e}")
            return False
    
    async def test_cache_health(self) -> Dict[str, Any]:
        """测试缓存健康状态"""
        print("\n🏥 测试缓存健康状态...")
        start_time = time.time()
        
        try:
            health_report = await run_cache_health_check()
            duration = time.time() - start_time
            
            # 分析健康状态
            healthy_count = sum(1 for check in health_report.checks if check.status.value == 'healthy')
            total_checks = len(health_report.checks)
            health_score = (healthy_count / total_checks) * 100 if total_checks > 0 else 0
            
            result = {
                "test_name": "cache_health_check",
                "status": "passed" if health_score >= 70 else "failed",
                "duration": round(duration, 3),
                "details": {
                    "overall_status": health_report.overall_status.value,
                    "health_score": round(health_score, 2),
                    "total_checks": total_checks,
                    "healthy_checks": healthy_count,
                    "average_response_time": health_report.summary.get("average_response_time_ms", 0)
                },
                "message": f"健康检查完成，得分: {health_score:.1f}%"
            }
            
            print(f"✅ 缓存健康检查完成 - 得分: {health_score:.1f}%")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": "cache_health_check",
                "status": "failed",
                "duration": round(duration, 3),
                "error": str(e),
                "message": f"健康检查失败: {e}"
            }
            print(f"❌ 缓存健康检查失败: {e}")
            return result
    
    async def test_cache_performance(self) -> Dict[str, Any]:
        """测试缓存性能"""
        print("\n⚡ 测试缓存性能...")
        start_time = time.time()
        
        try:
            if not self.cache_service:
                raise Exception("缓存服务未初始化")
            
            # 创建测试策略
            from app.config.cache_strategy import CachePriority
            strategy = CacheStrategy(
                name="performance_test",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=300,
                key_prefix="test"
            )
            
            # 性能测试参数
            test_keys = [f"perf_test_{i}" for i in range(100)]
            test_value = {"data": "test_value" * 10, "timestamp": time.time()}
            
            # 写入性能测试
            write_start = time.time()
            write_success = 0
            for key in test_keys:
                try:
                    success = await self.cache_service.set(key, test_value, strategy)
                    if success:
                        write_success += 1
                except Exception:
                    pass
            write_duration = time.time() - write_start
            
            # 读取性能测试
            read_start = time.time()
            read_success = 0
            cache_hits = 0
            for key in test_keys:
                try:
                    value, hit_type = await self.cache_service.get(key, strategy)
                    if value is not None:
                        read_success += 1
                        if hit_type.value != 'miss':
                            cache_hits += 1
                except Exception:
                    pass
            read_duration = time.time() - read_start
            
            # 计算性能指标
            write_ops_per_sec = len(test_keys) / write_duration if write_duration > 0 else 0
            read_ops_per_sec = len(test_keys) / read_duration if read_duration > 0 else 0
            cache_hit_rate = (cache_hits / len(test_keys)) * 100 if len(test_keys) > 0 else 0
            
            total_duration = time.time() - start_time
            
            # 判断测试结果
            performance_score = 0
            if write_ops_per_sec >= 100:  # 写入性能 >= 100 ops/s
                performance_score += 25
            if read_ops_per_sec >= 200:   # 读取性能 >= 200 ops/s
                performance_score += 25
            if cache_hit_rate >= 80:      # 缓存命中率 >= 80%
                performance_score += 50
            
            result = {
                "test_name": "cache_performance",
                "status": "passed" if performance_score >= 70 else "failed",
                "duration": round(total_duration, 3),
                "details": {
                    "write_ops_per_sec": round(write_ops_per_sec, 2),
                    "read_ops_per_sec": round(read_ops_per_sec, 2),
                    "cache_hit_rate": round(cache_hit_rate, 2),
                    "write_success_rate": round((write_success / len(test_keys)) * 100, 2),
                    "read_success_rate": round((read_success / len(test_keys)) * 100, 2),
                    "performance_score": performance_score
                },
                "message": f"性能测试完成 - 得分: {performance_score}%"
            }
            
            print(f"✅ 缓存性能测试完成 - 得分: {performance_score}%")
            print(f"   写入性能: {write_ops_per_sec:.1f} ops/s")
            print(f"   读取性能: {read_ops_per_sec:.1f} ops/s")
            print(f"   缓存命中率: {cache_hit_rate:.1f}%")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": "cache_performance",
                "status": "failed",
                "duration": round(duration, 3),
                "error": str(e),
                "message": f"性能测试失败: {e}"
            }
            print(f"❌ 缓存性能测试失败: {e}")
            return result
    
    async def test_cache_functionality(self) -> Dict[str, Any]:
        """测试缓存功能"""
        print("\n🔧 测试缓存功能...")
        start_time = time.time()
        
        try:
            if not self.cache_service:
                raise Exception("缓存服务未初始化")
            
            from app.config.cache_strategy import CachePriority
            strategy = CacheStrategy(
                name="functionality_test",
                level=CacheLevel.L2_REDIS,
                priority=CachePriority.MEDIUM,
                ttl=60,
                key_prefix="func_test"
            )
            
            test_cases = [
                {"key": "string_test", "value": "test_string_value"},
                {"key": "dict_test", "value": {"name": "test", "value": 123}},
                {"key": "list_test", "value": [1, 2, 3, "test"]},
                {"key": "number_test", "value": 42.5}
            ]
            
            passed_tests = 0
            total_tests = len(test_cases) * 2  # set + get for each case
            
            for case in test_cases:
                # 测试设置
                set_success = await self.cache_service.set(case["key"], case["value"], strategy)
                if set_success:
                    passed_tests += 1
                
                # 测试获取
                retrieved_value, hit_type = await self.cache_service.get(case["key"], strategy)
                if retrieved_value == case["value"]:
                    passed_tests += 1
            
            # 测试删除功能
            delete_success = await self.cache_service.delete("string_test", strategy)
            if delete_success:
                passed_tests += 1
            total_tests += 1
            
            # 验证删除效果
            deleted_value, _ = await self.cache_service.get("string_test", strategy)
            if deleted_value is None:
                passed_tests += 1
            total_tests += 1
            
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            duration = time.time() - start_time
            
            result = {
                "test_name": "cache_functionality",
                "status": "passed" if success_rate >= 90 else "failed",
                "duration": round(duration, 3),
                "details": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": round(success_rate, 2)
                },
                "message": f"功能测试完成 - 成功率: {success_rate:.1f}%"
            }
            
            print(f"✅ 缓存功能测试完成 - 成功率: {success_rate:.1f}%")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": "cache_functionality",
                "status": "failed",
                "duration": round(duration, 3),
                "error": str(e),
                "message": f"功能测试失败: {e}"
            }
            print(f"❌ 缓存功能测试失败: {e}")
            return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始缓存系统升级测试...")
        print("=" * 50)
        
        # 初始化
        if not await self.initialize():
            return {
                "error": "初始化失败",
                "timestamp": datetime.now().isoformat()
            }
        
        # 运行测试
        tests = [
            self.test_cache_health(),
            self.test_cache_functionality(),
            self.test_cache_performance()
        ]
        
        for test_coro in tests:
            result = await test_coro
            self.test_results["tests"].append(result)
            
            if result["status"] == "passed":
                self.test_results["summary"]["passed"] += 1
            else:
                self.test_results["summary"]["failed"] += 1
            
            self.test_results["summary"]["total_tests"] += 1
        
        # 计算总体成功率
        total = self.test_results["summary"]["total_tests"]
        passed = self.test_results["summary"]["passed"]
        self.test_results["summary"]["success_rate"] = round((passed / total) * 100, 2) if total > 0 else 0
        
        # 清理资源
        if self.cache_service:
            try:
                await self.cache_service.cleanup()
            except Exception:
                pass
        
        print("\n" + "=" * 50)
        print(f"🎯 测试完成! 总体成功率: {self.test_results['summary']['success_rate']}%")
        print(f"   通过: {passed}/{total} 测试")
        
        return self.test_results
    
    def save_report(self, filename: str = "cache_upgrade_test_report.json"):
        """保存测试报告"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"📄 测试报告已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")


async def main():
    """主函数"""
    tester = CacheUpgradeTest()
    results = await tester.run_all_tests()
    tester.save_report()
    
    # 输出简要结果
    if "error" not in results:
        success_rate = results["summary"]["success_rate"]
        if success_rate >= 80:
            print("\n🎉 缓存系统升级测试通过!")
        else:
            print("\n⚠️  缓存系统升级测试部分通过，需要关注失败项目")
    else:
        print("\n❌ 缓存系统升级测试失败")


if __name__ == "__main__":
    asyncio.run(main())