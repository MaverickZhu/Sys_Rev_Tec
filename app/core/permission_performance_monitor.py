#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限查询性能监控

提供权限查询性能监控和分析功能
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """查询指标"""
    query_type: str
    execution_time: float
    timestamp: datetime
    user_id: Optional[int] = None
    permission_code: Optional[str] = None
    resource_type: Optional[str] = None
    cache_hit: bool = False
    optimization_used: bool = False
    error: Optional[str] = None

@dataclass
class PerformanceStats:
    """性能统计"""
    total_queries: int = 0
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    cache_hit_rate: float = 0.0
    optimization_usage_rate: float = 0.0
    error_rate: float = 0.0
    queries_per_second: float = 0.0
    recent_queries: List[QueryMetrics] = field(default_factory=list)

class PermissionPerformanceMonitor:
    """权限查询性能监控器
    
    提供权限查询性能监控、统计和分析功能
    """
    
    def __init__(self, max_history_size: int = 10000, stats_window_minutes: int = 60):
        self.max_history_size = max_history_size
        self.stats_window_minutes = stats_window_minutes
        self.query_history: deque = deque(maxlen=max_history_size)
        self.stats_by_type: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self.lock = Lock()
        
        # 性能阈值
        self.slow_query_threshold = 1.0  # 秒
        self.high_error_rate_threshold = 0.05  # 5%
        self.low_cache_hit_rate_threshold = 0.7  # 70%
    
    def record_query(self, 
                    query_type: str,
                    execution_time: float,
                    user_id: Optional[int] = None,
                    permission_code: Optional[str] = None,
                    resource_type: Optional[str] = None,
                    cache_hit: bool = False,
                    optimization_used: bool = False,
                    error: Optional[str] = None) -> None:
        """记录查询指标
        
        Args:
            query_type: 查询类型
            execution_time: 执行时间（秒）
            user_id: 用户ID
            permission_code: 权限代码
            resource_type: 资源类型
            cache_hit: 是否命中缓存
            optimization_used: 是否使用优化
            error: 错误信息
        """
        metrics = QueryMetrics(
            query_type=query_type,
            execution_time=execution_time,
            timestamp=datetime.now(),
            user_id=user_id,
            permission_code=permission_code,
            resource_type=resource_type,
            cache_hit=cache_hit,
            optimization_used=optimization_used,
            error=error
        )
        
        with self.lock:
            self.query_history.append(metrics)
            self._update_stats(metrics)
    
    def _update_stats(self, metrics: QueryMetrics) -> None:
        """更新统计信息
        
        Args:
            metrics: 查询指标
        """
        stats = self.stats_by_type[metrics.query_type]
        
        # 更新基本统计
        stats.total_queries += 1
        
        # 更新执行时间统计
        total_time = stats.avg_execution_time * (stats.total_queries - 1) + metrics.execution_time
        stats.avg_execution_time = total_time / stats.total_queries
        stats.min_execution_time = min(stats.min_execution_time, metrics.execution_time)
        stats.max_execution_time = max(stats.max_execution_time, metrics.execution_time)
        
        # 更新最近查询
        stats.recent_queries.append(metrics)
        if len(stats.recent_queries) > 100:  # 保留最近100条
            stats.recent_queries.pop(0)
    
    def get_performance_stats(self, query_type: Optional[str] = None, 
                            window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """获取性能统计
        
        Args:
            query_type: 查询类型，None表示所有类型
            window_minutes: 时间窗口（分钟），None表示使用默认窗口
            
        Returns:
            Dict[str, Any]: 性能统计信息
        """
        window_minutes = window_minutes or self.stats_window_minutes
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        with self.lock:
            # 过滤时间窗口内的查询
            recent_queries = [q for q in self.query_history if q.timestamp >= cutoff_time]
            
            if query_type:
                recent_queries = [q for q in recent_queries if q.query_type == query_type]
            
            if not recent_queries:
                return {
                    "query_type": query_type or "all",
                    "window_minutes": window_minutes,
                    "total_queries": 0,
                    "stats": {}
                }
            
            # 计算统计信息
            stats = self._calculate_window_stats(recent_queries)
            
            # 按查询类型分组统计
            stats_by_type = {}
            if not query_type:
                type_groups = defaultdict(list)
                for q in recent_queries:
                    type_groups[q.query_type].append(q)
                
                for qtype, queries in type_groups.items():
                    stats_by_type[qtype] = self._calculate_window_stats(queries)
            
            return {
                "query_type": query_type or "all",
                "window_minutes": window_minutes,
                "total_queries": len(recent_queries),
                "overall_stats": stats,
                "stats_by_type": stats_by_type,
                "alerts": self._generate_alerts(stats, stats_by_type)
            }
    
    def _calculate_window_stats(self, queries: List[QueryMetrics]) -> Dict[str, Any]:
        """计算时间窗口内的统计信息
        
        Args:
            queries: 查询列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not queries:
            return {}
        
        execution_times = [q.execution_time for q in queries]
        cache_hits = sum(1 for q in queries if q.cache_hit)
        optimizations = sum(1 for q in queries if q.optimization_used)
        errors = sum(1 for q in queries if q.error)
        
        # 计算QPS
        time_span = (queries[-1].timestamp - queries[0].timestamp).total_seconds()
        qps = len(queries) / max(time_span, 1)
        
        return {
            "total_queries": len(queries),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "p95_execution_time": self._percentile(execution_times, 95),
            "p99_execution_time": self._percentile(execution_times, 99),
            "cache_hit_rate": cache_hits / len(queries),
            "optimization_usage_rate": optimizations / len(queries),
            "error_rate": errors / len(queries),
            "queries_per_second": qps,
            "slow_queries": len([t for t in execution_times if t > self.slow_query_threshold])
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数
        
        Args:
            data: 数据列表
            percentile: 百分位数
            
        Returns:
            float: 百分位数值
        """
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _generate_alerts(self, overall_stats: Dict[str, Any], 
                        stats_by_type: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成性能告警
        
        Args:
            overall_stats: 总体统计
            stats_by_type: 按类型统计
            
        Returns:
            List[Dict[str, Any]]: 告警列表
        """
        alerts = []
        
        # 检查总体性能
        if overall_stats:
            if overall_stats.get("avg_execution_time", 0) > self.slow_query_threshold:
                alerts.append({
                    "type": "slow_queries",
                    "severity": "warning",
                    "message": f"平均查询时间过长: {overall_stats['avg_execution_time']:.3f}s",
                    "threshold": self.slow_query_threshold
                })
            
            if overall_stats.get("error_rate", 0) > self.high_error_rate_threshold:
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "error",
                    "message": f"错误率过高: {overall_stats['error_rate']:.2%}",
                    "threshold": self.high_error_rate_threshold
                })
            
            if overall_stats.get("cache_hit_rate", 1) < self.low_cache_hit_rate_threshold:
                alerts.append({
                    "type": "low_cache_hit_rate",
                    "severity": "warning",
                    "message": f"缓存命中率过低: {overall_stats['cache_hit_rate']:.2%}",
                    "threshold": self.low_cache_hit_rate_threshold
                })
        
        # 检查各类型性能
        for query_type, stats in stats_by_type.items():
            if stats.get("avg_execution_time", 0) > self.slow_query_threshold:
                alerts.append({
                    "type": "slow_queries_by_type",
                    "severity": "warning",
                    "message": f"{query_type} 查询平均时间过长: {stats['avg_execution_time']:.3f}s",
                    "query_type": query_type,
                    "threshold": self.slow_query_threshold
                })
        
        return alerts
    
    def get_slow_queries(self, threshold: Optional[float] = None, 
                        limit: int = 50) -> List[Dict[str, Any]]:
        """获取慢查询列表
        
        Args:
            threshold: 慢查询阈值（秒）
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 慢查询列表
        """
        threshold = threshold or self.slow_query_threshold
        
        with self.lock:
            slow_queries = [
                {
                    "query_type": q.query_type,
                    "execution_time": q.execution_time,
                    "timestamp": q.timestamp.isoformat(),
                    "user_id": q.user_id,
                    "permission_code": q.permission_code,
                    "resource_type": q.resource_type,
                    "cache_hit": q.cache_hit,
                    "optimization_used": q.optimization_used,
                    "error": q.error
                }
                for q in self.query_history
                if q.execution_time > threshold
            ]
            
            # 按执行时间降序排序
            slow_queries.sort(key=lambda x: x["execution_time"], reverse=True)
            
            return slow_queries[:limit]
    
    def get_query_trends(self, hours: int = 24, 
                        interval_minutes: int = 60) -> Dict[str, Any]:
        """获取查询趋势
        
        Args:
            hours: 时间范围（小时）
            interval_minutes: 时间间隔（分钟）
            
        Returns:
            Dict[str, Any]: 查询趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        interval_delta = timedelta(minutes=interval_minutes)
        
        with self.lock:
            # 过滤时间范围内的查询
            recent_queries = [q for q in self.query_history if q.timestamp >= cutoff_time]
            
            if not recent_queries:
                return {"intervals": [], "trends": {}}
            
            # 生成时间间隔
            start_time = cutoff_time
            intervals = []
            trends = defaultdict(list)
            
            while start_time < datetime.now():
                end_time = start_time + interval_delta
                interval_queries = [
                    q for q in recent_queries 
                    if start_time <= q.timestamp < end_time
                ]
                
                interval_label = start_time.strftime("%H:%M")
                intervals.append(interval_label)
                
                # 计算间隔统计
                if interval_queries:
                    stats = self._calculate_window_stats(interval_queries)
                    trends["query_count"].append(len(interval_queries))
                    trends["avg_execution_time"].append(stats["avg_execution_time"])
                    trends["cache_hit_rate"].append(stats["cache_hit_rate"])
                    trends["error_rate"].append(stats["error_rate"])
                else:
                    trends["query_count"].append(0)
                    trends["avg_execution_time"].append(0)
                    trends["cache_hit_rate"].append(0)
                    trends["error_rate"].append(0)
                
                start_time = end_time
            
            return {
                "intervals": intervals,
                "trends": dict(trends),
                "total_queries": len(recent_queries),
                "time_range_hours": hours
            }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self.lock:
            self.query_history.clear()
            self.stats_by_type.clear()
            logger.info("性能监控统计信息已重置")
    
    def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """导出指标数据
        
        Args:
            format: 导出格式
            
        Returns:
            Dict[str, Any]: 导出的指标数据
        """
        with self.lock:
            metrics_data = {
                "export_time": datetime.now().isoformat(),
                "total_queries": len(self.query_history),
                "query_history": [
                    {
                        "query_type": q.query_type,
                        "execution_time": q.execution_time,
                        "timestamp": q.timestamp.isoformat(),
                        "user_id": q.user_id,
                        "permission_code": q.permission_code,
                        "resource_type": q.resource_type,
                        "cache_hit": q.cache_hit,
                        "optimization_used": q.optimization_used,
                        "error": q.error
                    }
                    for q in self.query_history
                ],
                "stats_by_type": {
                    qtype: {
                        "total_queries": stats.total_queries,
                        "avg_execution_time": stats.avg_execution_time,
                        "min_execution_time": stats.min_execution_time,
                        "max_execution_time": stats.max_execution_time,
                        "cache_hit_rate": stats.cache_hit_rate,
                        "optimization_usage_rate": stats.optimization_usage_rate,
                        "error_rate": stats.error_rate
                    }
                    for qtype, stats in self.stats_by_type.items()
                }
            }
            
            return metrics_data


# 全局监控器实例
_performance_monitor = None
_monitor_lock = Lock()

def get_permission_performance_monitor() -> PermissionPerformanceMonitor:
    """获取权限性能监控器实例
    
    Returns:
        PermissionPerformanceMonitor: 权限性能监控器实例
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PermissionPerformanceMonitor()
    
    return _performance_monitor


def monitor_permission_query(query_type: str):
    """权限查询监控装饰器
    
    Args:
        query_type: 查询类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_permission_performance_monitor()
            start_time = time.time()
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                
                # 从参数中提取相关信息
                user_id = kwargs.get('user_id') or (args[0] if args and hasattr(args[0], 'id') else None)
                permission_code = kwargs.get('permission_code')
                resource_type = kwargs.get('resource_type')
                
                monitor.record_query(
                    query_type=query_type,
                    execution_time=execution_time,
                    user_id=user_id,
                    permission_code=permission_code,
                    resource_type=resource_type,
                    error=error
                )
        
        return wrapper
    return decorator