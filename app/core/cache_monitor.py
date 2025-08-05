"""缓存监控模块

提供缓存性能监控、统计和报告功能
"""

import logging
import threading
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """缓存统计数据"""

    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    avg_response_time: float = 0.0
    cache_size: int = 0
    memory_usage: int = 0
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # 计算命中率
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests


@dataclass
class CacheOperation:
    """缓存操作记录"""

    operation_type: str  # 'get', 'set', 'delete', 'clear'
    cache_type: str  # 'user_permission', 'role_permission', 'resource_permission'
    key: str
    hit: bool
    response_time: float
    timestamp: datetime
    user_id: Optional[int] = None
    error: Optional[str] = None


class CacheMonitor:
    """缓存监控器"""

    def __init__(self, max_operations: int = 10000):
        self.max_operations = max_operations
        self.operations: deque = deque(maxlen=max_operations)
        self.stats_by_type: Dict[str, CacheStats] = defaultdict(CacheStats)
        self.global_stats = CacheStats()
        self.lock = threading.RLock()

        # 性能指标
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.hourly_stats: Dict[str, Dict[int, CacheStats]] = defaultdict(dict)

        logger.info("缓存监控器已初始化")

    def record_operation(self, operation: CacheOperation) -> None:
        """记录缓存操作

        Args:
            operation: 缓存操作记录
        """
        with self.lock:
            # 添加操作记录
            self.operations.append(operation)

            # 更新统计数据
            self._update_stats(operation)

            # 记录响应时间
            self.response_times[operation.cache_type].append(operation.response_time)

            # 更新小时统计
            self._update_hourly_stats(operation)

    def _update_stats(self, operation: CacheOperation) -> None:
        """更新统计数据

        Args:
            operation: 缓存操作记录
        """
        # 更新类型统计
        type_stats = self.stats_by_type[operation.cache_type]
        type_stats.total_requests += 1

        if operation.hit:
            type_stats.hits += 1
        else:
            type_stats.misses += 1

        # 重新计算命中率
        type_stats.hit_rate = type_stats.hits / type_stats.total_requests

        # 更新平均响应时间
        response_times = self.response_times[operation.cache_type]
        if response_times:
            type_stats.avg_response_time = sum(response_times) / len(response_times)

        type_stats.last_updated = datetime.now()

        # 更新全局统计
        self.global_stats.total_requests += 1
        if operation.hit:
            self.global_stats.hits += 1
        else:
            self.global_stats.misses += 1

        self.global_stats.hit_rate = (
            self.global_stats.hits / self.global_stats.total_requests
        )

        # 更新全局平均响应时间
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)

        if all_times:
            self.global_stats.avg_response_time = sum(all_times) / len(all_times)

        self.global_stats.last_updated = datetime.now()

    def _update_hourly_stats(self, operation: CacheOperation) -> None:
        """更新小时统计

        Args:
            operation: 缓存操作记录
        """
        hour = operation.timestamp.hour
        cache_type = operation.cache_type

        if hour not in self.hourly_stats[cache_type]:
            self.hourly_stats[cache_type][hour] = CacheStats()

        hourly_stat = self.hourly_stats[cache_type][hour]
        hourly_stat.total_requests += 1

        if operation.hit:
            hourly_stat.hits += 1
        else:
            hourly_stat.misses += 1

        hourly_stat.hit_rate = hourly_stat.hits / hourly_stat.total_requests
        hourly_stat.last_updated = datetime.now()

    def get_stats(self, cache_type: Optional[str] = None) -> Dict[str, Any]:
        """获取缓存统计信息

        Args:
            cache_type: 缓存类型，None表示获取全局统计

        Returns:
            Dict: 统计信息
        """
        with self.lock:
            if cache_type:
                stats = self.stats_by_type.get(cache_type, CacheStats())
                return asdict(stats)
            else:
                return {
                    "global": asdict(self.global_stats),
                    "by_type": {k: asdict(v) for k, v in self.stats_by_type.items()},
                }

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能报告

        Args:
            hours: 报告时间范围（小时）

        Returns:
            Dict: 性能报告
        """
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # 过滤最近的操作
            recent_operations = [
                op for op in self.operations if op.timestamp >= cutoff_time
            ]

            # 按类型分组统计
            type_performance = defaultdict(
                lambda: {
                    "total_requests": 0,
                    "hits": 0,
                    "misses": 0,
                    "hit_rate": 0.0,
                    "avg_response_time": 0.0,
                    "max_response_time": 0.0,
                    "min_response_time": float("inf"),
                    "errors": 0,
                }
            )

            for op in recent_operations:
                perf = type_performance[op.cache_type]
                perf["total_requests"] += 1

                if op.hit:
                    perf["hits"] += 1
                else:
                    perf["misses"] += 1

                perf["max_response_time"] = max(
                    perf["max_response_time"], op.response_time
                )
                perf["min_response_time"] = min(
                    perf["min_response_time"], op.response_time
                )

                if op.error:
                    perf["errors"] += 1

            # 计算平均值和命中率
            for cache_type, perf in type_performance.items():
                if perf["total_requests"] > 0:
                    perf["hit_rate"] = perf["hits"] / perf["total_requests"]

                response_times = [
                    op.response_time
                    for op in recent_operations
                    if op.cache_type == cache_type
                ]

                if response_times:
                    perf["avg_response_time"] = sum(response_times) / len(
                        response_times
                    )

                if perf["min_response_time"] == float("inf"):
                    perf["min_response_time"] = 0.0

            return {
                "time_range": f"最近 {hours} 小时",
                "total_operations": len(recent_operations),
                "performance_by_type": dict(type_performance),
                "generated_at": datetime.now().isoformat(),
            }

    def get_slow_operations(
        self, threshold: float = 0.1, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取慢操作列表

        Args:
            threshold: 响应时间阈值（秒）
            limit: 返回数量限制

        Returns:
            List: 慢操作列表
        """
        with self.lock:
            slow_ops = [
                {
                    "cache_type": op.cache_type,
                    "operation_type": op.operation_type,
                    "key": op.key,
                    "response_time": op.response_time,
                    "timestamp": op.timestamp.isoformat(),
                    "user_id": op.user_id,
                    "error": op.error,
                }
                for op in self.operations
                if op.response_time > threshold
            ]

            # 按响应时间降序排序
            slow_ops.sort(key=lambda x: x["response_time"], reverse=True)

            return slow_ops[:limit]

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误摘要

        Args:
            hours: 统计时间范围（小时）

        Returns:
            Dict: 错误摘要
        """
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            error_ops = [
                op for op in self.operations if op.timestamp >= cutoff_time and op.error
            ]

            # 按错误类型分组
            error_by_type = defaultdict(int)
            error_by_cache_type = defaultdict(int)

            for op in error_ops:
                error_by_type[op.error] += 1
                error_by_cache_type[op.cache_type] += 1

            return {
                "time_range": f"最近 {hours} 小时",
                "total_errors": len(error_ops),
                "error_by_type": dict(error_by_type),
                "error_by_cache_type": dict(error_by_cache_type),
                "recent_errors": [
                    {
                        "cache_type": op.cache_type,
                        "operation_type": op.operation_type,
                        "key": op.key,
                        "error": op.error,
                        "timestamp": op.timestamp.isoformat(),
                    }
                    for op in error_ops[-10:]  # 最近10个错误
                ],
            }

    def clear_old_data(self, days: int = 7) -> None:
        """清理旧数据

        Args:
            days: 保留天数
        """
        with self.lock:
            cutoff_time = datetime.now() - timedelta(days=days)

            # 清理旧操作记录
            old_count = len(self.operations)
            self.operations = deque(
                (op for op in self.operations if op.timestamp >= cutoff_time),
                maxlen=self.max_operations,
            )

            cleaned_count = old_count - len(self.operations)

            logger.info(f"清理了 {cleaned_count} 条旧的缓存操作记录")

    def reset_stats(self) -> None:
        """重置统计数据"""
        with self.lock:
            self.operations.clear()
            self.stats_by_type.clear()
            self.global_stats = CacheStats()
            self.response_times.clear()
            self.hourly_stats.clear()

            logger.info("缓存统计数据已重置")


# 全局缓存监控器实例
_cache_monitor = None
_monitor_lock = threading.Lock()


def get_cache_monitor() -> CacheMonitor:
    """获取缓存监控器实例

    Returns:
        CacheMonitor: 缓存监控器
    """
    global _cache_monitor

    if _cache_monitor is None:
        with _monitor_lock:
            if _cache_monitor is None:
                _cache_monitor = CacheMonitor()

    return _cache_monitor


def record_cache_operation(
    operation_type: str,
    cache_type: str,
    key: str,
    hit: bool,
    response_time: float,
    user_id: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """记录缓存操作

    Args:
        operation_type: 操作类型
        cache_type: 缓存类型
        key: 缓存键
        hit: 是否命中
        response_time: 响应时间
        user_id: 用户ID
        error: 错误信息
    """
    monitor = get_cache_monitor()
    operation = CacheOperation(
        operation_type=operation_type,
        cache_type=cache_type,
        key=key,
        hit=hit,
        response_time=response_time,
        timestamp=datetime.now(),
        user_id=user_id,
        error=error,
    )

    monitor.record_operation(operation)
