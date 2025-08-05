"""缓存健康检查模块

提供缓存系统健康状态监控、诊断和报告功能。
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.cache_config import get_cache_config_for_environment
from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheckResult(BaseModel):
    """健康检查结果"""

    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime
    response_time_ms: float


class SystemHealthReport(BaseModel):
    """系统健康报告"""

    overall_status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheckResult]
    summary: Dict[str, Any]
    recommendations: List[str] = []


class CacheHealthChecker:
    """缓存健康检查器"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.config = get_cache_config_for_environment(settings.ENVIRONMENT)
        self.health_history: List[SystemHealthReport] = []

        # 健康检查阈值
        self.thresholds = {
            "response_time_warning": 100,  # ms
            "response_time_critical": 500,  # ms
            "memory_usage_warning": 0.8,  # 80%
            "memory_usage_critical": 0.95,  # 95%
            "connection_warning": 0.8,  # 80% of max connections
            "connection_critical": 0.95,  # 95% of max connections
            "hit_rate_warning": 0.7,  # 70%
            "hit_rate_critical": 0.5,  # 50%
        }

    async def initialize(self):
        """初始化健康检查器"""
        try:
            # 优先使用REDIS_URL环境变量
            import os
            redis_url = os.getenv('REDIS_URL')
            
            if redis_url:
                # 使用REDIS_URL创建连接
                self.redis_client = redis.Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                logger.info(f"Cache health checker using REDIS_URL: {redis_url}")
            else:
                # 回退到单独的参数
                self.redis_client = redis.Redis(
                    host=getattr(settings, "REDIS_HOST", "redis"),
                    port=getattr(settings, "REDIS_PORT", 6379),
                    password=getattr(settings, "REDIS_PASSWORD", None),
                    db=getattr(settings, "REDIS_DB", 0),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                logger.info(f"Cache health checker using individual params: {getattr(settings, 'REDIS_HOST', 'redis')}:{getattr(settings, 'REDIS_PORT', 6379)}")

            # 测试连接
            await self.redis_client.ping()
            logger.info("Cache health checker initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache health checker: {e}")
            raise

    async def run_full_health_check(self) -> SystemHealthReport:
        """运行完整的健康检查"""
        try:
            start_time = time.time()
            checks = []

            # 执行各项检查
            checks.append(await self._check_redis_connectivity())
            checks.append(await self._check_redis_performance())
            checks.append(await self._check_memory_usage())
            checks.append(await self._check_connection_pool())
            checks.append(await self._check_cache_hit_rate())
            checks.append(await self._check_key_expiration())
            checks.append(await self._check_replication_status())

            # 计算总体状态
            overall_status = self._calculate_overall_status(checks)

            # 生成摘要
            summary = self._generate_summary(checks, time.time() - start_time)

            # 生成建议
            recommendations = self._generate_recommendations(checks)

            # 创建健康报告
            report = SystemHealthReport(
                overall_status=overall_status,
                timestamp=datetime.now(),
                checks=checks,
                summary=summary,
                recommendations=recommendations,
            )

            # 保存到历史记录
            self._save_health_report(report)

            return report

        except Exception as e:
            logger.error(f"Failed to run health check: {e}")
            return SystemHealthReport(
                overall_status=HealthStatus.UNKNOWN,
                timestamp=datetime.now(),
                checks=[],
                summary={"error": str(e)},
            )

    async def _check_redis_connectivity(self) -> HealthCheckResult:
        """检查Redis连接性"""
        start_time = time.time()

        try:
            # 测试基本连接
            await self.redis_client.ping()

            # 测试读写操作
            test_key = "health_check_test"
            await self.redis_client.set(test_key, "test_value", ex=10)
            value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)

            response_time = (time.time() - start_time) * 1000

            if value == "test_value":
                status = HealthStatus.HEALTHY
                message = "Redis connectivity is healthy"
            else:
                status = HealthStatus.CRITICAL
                message = "Redis read/write test failed"

            return HealthCheckResult(
                component="redis_connectivity",
                status=status,
                message=message,
                details={"response_time_ms": response_time},
                timestamp=datetime.now(),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="redis_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Redis connectivity failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time,
            )

    async def _check_redis_performance(self) -> HealthCheckResult:
        """检查Redis性能"""
        start_time = time.time()

        try:
            # 执行多个操作测试性能
            operations = []

            # SET操作
            set_start = time.time()
            await self.redis_client.set("perf_test_set", "value", ex=10)
            set_time = (time.time() - set_start) * 1000
            operations.append({"operation": "SET", "time_ms": set_time})

            # GET操作
            get_start = time.time()
            await self.redis_client.get("perf_test_set")
            get_time = (time.time() - get_start) * 1000
            operations.append({"operation": "GET", "time_ms": get_time})

            # DEL操作
            del_start = time.time()
            await self.redis_client.delete("perf_test_set")
            del_time = (time.time() - del_start) * 1000
            operations.append({"operation": "DEL", "time_ms": del_time})

            total_time = (time.time() - start_time) * 1000
            avg_time = sum(op["time_ms"] for op in operations) / len(operations)

            # 判断性能状态
            if avg_time < self.thresholds["response_time_warning"]:
                status = HealthStatus.HEALTHY
                message = "Redis performance is optimal"
            elif avg_time < self.thresholds["response_time_critical"]:
                status = HealthStatus.WARNING
                message = "Redis performance is slower than expected"
            else:
                status = HealthStatus.CRITICAL
                message = "Redis performance is critically slow"

            return HealthCheckResult(
                component="redis_performance",
                status=status,
                message=message,
                details={
                    "operations": operations,
                    "average_time_ms": avg_time,
                    "total_time_ms": total_time,
                },
                timestamp=datetime.now(),
                response_time_ms=total_time,
            )

        except Exception as e:
            return HealthCheckResult(
                component="redis_performance",
                status=HealthStatus.CRITICAL,
                message=f"Performance check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def _check_memory_usage(self) -> HealthCheckResult:
        """检查内存使用情况"""
        start_time = time.time()

        try:
            info = await self.redis_client.info("memory")

            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)

            if max_memory > 0:
                usage_ratio = used_memory / max_memory
            else:
                # 如果没有设置maxmemory，使用系统内存估算
                usage_ratio = 0.0

            # 判断内存状态
            if usage_ratio < self.thresholds["memory_usage_warning"]:
                status = HealthStatus.HEALTHY
                message = "Memory usage is normal"
            elif usage_ratio < self.thresholds["memory_usage_critical"]:
                status = HealthStatus.WARNING
                message = "Memory usage is high"
            else:
                status = HealthStatus.CRITICAL
                message = "Memory usage is critically high"

            return HealthCheckResult(
                component="memory_usage",
                status=status,
                message=message,
                details={
                    "used_memory_bytes": used_memory,
                    "max_memory_bytes": max_memory,
                    "usage_ratio": usage_ratio,
                    "used_memory_human": info.get("used_memory_human", "N/A"),
                    "memory_fragmentation_ratio": info.get(
                        "mem_fragmentation_ratio", 0
                    ),
                },
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheckResult(
                component="memory_usage",
                status=HealthStatus.CRITICAL,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def _check_connection_pool(self) -> HealthCheckResult:
        """检查连接池状态"""
        start_time = time.time()

        try:
            info = await self.redis_client.info("clients")

            connected_clients = info.get("connected_clients", 0)
            max_clients = info.get("maxclients", 10000)

            usage_ratio = connected_clients / max_clients

            # 判断连接池状态
            if usage_ratio < self.thresholds["connection_warning"]:
                status = HealthStatus.HEALTHY
                message = "Connection pool is healthy"
            elif usage_ratio < self.thresholds["connection_critical"]:
                status = HealthStatus.WARNING
                message = "Connection pool usage is high"
            else:
                status = HealthStatus.CRITICAL
                message = "Connection pool is nearly exhausted"

            return HealthCheckResult(
                component="connection_pool",
                status=status,
                message=message,
                details={
                    "connected_clients": connected_clients,
                    "max_clients": max_clients,
                    "usage_ratio": usage_ratio,
                    "blocked_clients": info.get("blocked_clients", 0),
                },
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheckResult(
                component="connection_pool",
                status=HealthStatus.CRITICAL,
                message=f"Connection pool check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def _check_cache_hit_rate(self) -> HealthCheckResult:
        """检查缓存命中率"""
        start_time = time.time()

        try:
            info = await self.redis_client.info("stats")

            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)

            total_requests = keyspace_hits + keyspace_misses

            if total_requests > 0:
                hit_rate = keyspace_hits / total_requests
            else:
                hit_rate = 0.0

            # 判断命中率状态
            if hit_rate >= self.thresholds["hit_rate_warning"]:
                status = HealthStatus.HEALTHY
                message = "Cache hit rate is good"
            elif hit_rate >= self.thresholds["hit_rate_critical"]:
                status = HealthStatus.WARNING
                message = "Cache hit rate is below optimal"
            else:
                status = HealthStatus.CRITICAL
                message = "Cache hit rate is critically low"

            return HealthCheckResult(
                component="cache_hit_rate",
                status=status,
                message=message,
                details={
                    "hit_rate": hit_rate,
                    "keyspace_hits": keyspace_hits,
                    "keyspace_misses": keyspace_misses,
                    "total_requests": total_requests,
                },
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheckResult(
                component="cache_hit_rate",
                status=HealthStatus.CRITICAL,
                message=f"Hit rate check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def _check_key_expiration(self) -> HealthCheckResult:
        """检查键过期情况"""
        start_time = time.time()

        try:
            info = await self.redis_client.info("keyspace")

            total_keys = 0
            expired_keys = 0

            # 解析keyspace信息
            for key, value in info.items():
                if key.startswith("db"):
                    # 解析db信息，格式如: "keys=1000,expires=500,avg_ttl=3600000"
                    parts = value.split(",")
                    for part in parts:
                        if part.startswith("keys="):
                            total_keys += int(part.split("=")[1])
                        elif part.startswith("expires="):
                            expired_keys += int(part.split("=")[1])

            if total_keys > 0:
                expiration_ratio = expired_keys / total_keys
            else:
                expiration_ratio = 0.0

            # 判断过期键状态（适当的过期比例是健康的）
            if 0.1 <= expiration_ratio <= 0.8:
                status = HealthStatus.HEALTHY
                message = "Key expiration is properly configured"
            elif expiration_ratio < 0.1:
                status = HealthStatus.WARNING
                message = "Very few keys have expiration set"
            else:
                status = HealthStatus.WARNING
                message = "High proportion of keys have expiration"

            return HealthCheckResult(
                component="key_expiration",
                status=status,
                message=message,
                details={
                    "total_keys": total_keys,
                    "keys_with_expiration": expired_keys,
                    "expiration_ratio": expiration_ratio,
                },
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheckResult(
                component="key_expiration",
                status=HealthStatus.WARNING,
                message=f"Key expiration check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def _check_replication_status(self) -> HealthCheckResult:
        """检查复制状态"""
        start_time = time.time()

        try:
            info = await self.redis_client.info("replication")

            role = info.get("role", "unknown")
            connected_slaves = info.get("connected_slaves", 0)

            if role == "master":
                if connected_slaves > 0:
                    status = HealthStatus.HEALTHY
                    message = f"Master with {connected_slaves} connected slaves"
                else:
                    status = HealthStatus.WARNING
                    message = "Master with no connected slaves"
            elif role == "slave":
                master_link_status = info.get("master_link_status", "unknown")
                if master_link_status == "up":
                    status = HealthStatus.HEALTHY
                    message = "Slave connected to master"
                else:
                    status = HealthStatus.CRITICAL
                    message = "Slave disconnected from master"
            else:
                status = HealthStatus.HEALTHY
                message = "Standalone Redis instance"

            return HealthCheckResult(
                component="replication_status",
                status=status,
                message=message,
                details={
                    "role": role,
                    "connected_slaves": connected_slaves,
                    "master_link_status": info.get("master_link_status", "N/A"),
                    "master_last_io_seconds_ago": info.get(
                        "master_last_io_seconds_ago", "N/A"
                    ),
                },
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheckResult(
                component="replication_status",
                status=HealthStatus.WARNING,
                message=f"Replication check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000,
            )

    def _calculate_overall_status(
        self, checks: List[HealthCheckResult]
    ) -> HealthStatus:
        """计算总体健康状态"""
        if not checks:
            return HealthStatus.UNKNOWN

        # 统计各状态数量
        status_counts = {
            HealthStatus.CRITICAL: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.HEALTHY: 0,
            HealthStatus.UNKNOWN: 0,
        }

        for check in checks:
            status_counts[check.status] += 1

        # 判断总体状态
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.HEALTHY] > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def _generate_summary(
        self, checks: List[HealthCheckResult], total_time: float
    ) -> Dict[str, Any]:
        """生成健康检查摘要"""
        summary = {
            "total_checks": len(checks),
            "total_time_seconds": round(total_time, 3),
            "status_breakdown": {
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "unknown": 0,
            },
            "average_response_time_ms": 0,
            "slowest_check": None,
            "fastest_check": None,
        }

        if not checks:
            return summary

        # 统计状态分布
        for check in checks:
            summary["status_breakdown"][check.status.value] += 1

        # 计算响应时间统计
        response_times = [check.response_time_ms for check in checks]
        summary["average_response_time_ms"] = round(
            sum(response_times) / len(response_times), 2
        )

        # 找出最慢和最快的检查
        slowest = max(checks, key=lambda x: x.response_time_ms)
        fastest = min(checks, key=lambda x: x.response_time_ms)

        summary["slowest_check"] = {
            "component": slowest.component,
            "response_time_ms": slowest.response_time_ms,
        }

        summary["fastest_check"] = {
            "component": fastest.component,
            "response_time_ms": fastest.response_time_ms,
        }

        return summary

    def _generate_recommendations(self, checks: List[HealthCheckResult]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        for check in checks:
            if check.status == HealthStatus.CRITICAL:
                if check.component == "redis_connectivity":
                    recommendations.append("检查Redis服务器状态和网络连接")
                elif check.component == "memory_usage":
                    recommendations.append("考虑增加Redis内存限制或清理过期数据")
                elif check.component == "connection_pool":
                    recommendations.append("增加Redis最大连接数或优化连接池配置")
                elif check.component == "cache_hit_rate":
                    recommendations.append("优化缓存策略，增加缓存TTL或预热关键数据")

            elif check.status == HealthStatus.WARNING:
                if check.component == "redis_performance":
                    recommendations.append("监控Redis性能，考虑优化查询或增加资源")
                elif check.component == "key_expiration":
                    recommendations.append("检查键过期策略配置")
                elif check.component == "replication_status":
                    recommendations.append("检查Redis复制配置和网络状态")

        # 通用建议
        if any(check.response_time_ms > 200 for check in checks):
            recommendations.append("某些检查响应时间较长，建议监控系统负载")

        return recommendations

    def _save_health_report(self, report: SystemHealthReport):
        """保存健康报告到历史记录"""
        try:
            self.health_history.append(report)

            # 保持历史记录在合理范围内（最近100次检查）
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-50:]

        except Exception as e:
            logger.error(f"Failed to save health report: {e}")

    def get_health_history(self, limit: int = 10) -> List[SystemHealthReport]:
        """获取健康检查历史"""
        return self.health_history[-limit:]

    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """获取健康趋势分析"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_reports = [
                report
                for report in self.health_history
                if report.timestamp >= cutoff_time
            ]

            if not recent_reports:
                return {"error": "No recent health data available"}

            # 分析趋势
            trends = {
                "total_reports": len(recent_reports),
                "time_range_hours": hours,
                "status_distribution": {
                    "healthy": 0,
                    "warning": 0,
                    "critical": 0,
                    "unknown": 0,
                },
                "average_response_times": {},
                "component_reliability": {},
            }

            # 统计状态分布
            for report in recent_reports:
                trends["status_distribution"][report.overall_status.value] += 1

            # 计算组件可靠性
            component_stats = {}
            for report in recent_reports:
                for check in report.checks:
                    if check.component not in component_stats:
                        component_stats[check.component] = {
                            "total": 0,
                            "healthy": 0,
                            "response_times": [],
                        }

                    component_stats[check.component]["total"] += 1
                    component_stats[check.component]["response_times"].append(
                        check.response_time_ms
                    )

                    if check.status == HealthStatus.HEALTHY:
                        component_stats[check.component]["healthy"] += 1

            # 计算可靠性百分比和平均响应时间
            for component, stats in component_stats.items():
                reliability = (stats["healthy"] / stats["total"]) * 100
                avg_response_time = sum(stats["response_times"]) / len(
                    stats["response_times"]
                )

                trends["component_reliability"][component] = round(reliability, 2)
                trends["average_response_times"][component] = round(
                    avg_response_time, 2
                )

            return trends

        except Exception as e:
            logger.error(f"Failed to analyze health trends: {e}")
            return {"error": str(e)}

    async def cleanup(self):
        """清理资源"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Cache health checker cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup cache health checker: {e}")


# 全局健康检查器实例
_cache_health_checker: Optional[CacheHealthChecker] = None


def get_cache_health_checker() -> CacheHealthChecker:
    """获取缓存健康检查器实例"""
    global _cache_health_checker
    if _cache_health_checker is None:
        _cache_health_checker = CacheHealthChecker()
    return _cache_health_checker


async def run_cache_health_check() -> SystemHealthReport:
    """运行缓存健康检查"""
    checker = get_cache_health_checker()
    if checker.redis_client is None:
        await checker.initialize()
    return await checker.run_full_health_check()


async def get_cache_health_status() -> HealthStatus:
    """获取缓存健康状态"""
    try:
        report = await run_cache_health_check()
        return report.overall_status
    except Exception as e:
        logger.error(f"Failed to get cache health status: {e}")
        return HealthStatus.UNKNOWN
