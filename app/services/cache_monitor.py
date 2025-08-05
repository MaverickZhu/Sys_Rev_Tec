#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存监控和指标收集
提供缓存性能监控、指标收集和告警功能
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.multi_level_cache import CacheHitType, get_multi_cache_service

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    RATE = "rate"  # 速率


@dataclass
class CacheMetric:
    """缓存指标"""

    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass
class CacheAlert:
    """缓存告警"""

    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metric_name: str
    threshold: float
    current_value: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class CachePerformanceSnapshot:
    """缓存性能快照"""

    timestamp: datetime
    hit_rate: float
    miss_rate: float
    l1_hit_rate: float
    l2_hit_rate: float
    avg_response_time: float
    total_requests: int
    total_hits: int
    total_misses: int
    memory_usage: float
    redis_usage: float
    error_rate: float
    active_connections: int


@dataclass
class CacheMetrics:
    """缓存指标集合"""

    hit_rate: float
    miss_rate: float
    l1_hit_rate: float
    l2_hit_rate: float
    avg_response_time: float
    total_requests: int
    total_hits: int
    total_misses: int
    memory_usage: float
    redis_usage: float
    error_rate: float
    active_connections: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class PerformanceReport:
    """性能报告"""

    report_id: str
    start_time: datetime
    end_time: datetime
    summary: Dict[str, Any]
    metrics: List[CacheMetrics]
    alerts: List[CacheAlert]
    recommendations: List[str]
    health_score: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "report_id": self.report_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "summary": self.summary,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "alerts": [asdict(alert) for alert in self.alerts],
            "recommendations": self.recommendations,
            "health_score": self.health_score,
        }


class CacheMonitor:
    """缓存监控器"""

    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[CacheAlert] = []
        self.snapshots: deque = deque(maxlen=1440)  # 24小时的分钟级快照
        self.alert_rules: Dict[str, Dict] = {}
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()

        # 性能统计
        self.request_times: deque = deque(maxlen=10000)
        self.hit_miss_stats = {
            "total_requests": 0,
            "total_hits": 0,
            "total_misses": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "errors": 0,
        }

        self._initialize_alert_rules()

    def _initialize_alert_rules(self):
        """初始化告警规则"""
        self.alert_rules = {
            "hit_rate_low": {
                "metric": "cache_hit_rate",
                "operator": "<",
                "threshold": 0.7,  # 命中率低于70%
                "level": AlertLevel.WARNING,
                "title": "缓存命中率过低",
                "message": "缓存命中率低于70%，可能影响系统性能",
            },
            "hit_rate_critical": {
                "metric": "cache_hit_rate",
                "operator": "<",
                "threshold": 0.5,  # 命中率低于50%
                "level": AlertLevel.CRITICAL,
                "title": "缓存命中率严重过低",
                "message": "缓存命中率低于50%，严重影响系统性能",
            },
            "response_time_high": {
                "metric": "avg_response_time",
                "operator": ">",
                "threshold": 100.0,  # 响应时间超过100ms
                "level": AlertLevel.WARNING,
                "title": "缓存响应时间过长",
                "message": "平均响应时间超过100ms",
            },
            "error_rate_high": {
                "metric": "error_rate",
                "operator": ">",
                "threshold": 0.05,  # 错误率超过5%
                "level": AlertLevel.ERROR,
                "title": "缓存错误率过高",
                "message": "缓存错误率超过5%",
            },
            "memory_usage_high": {
                "metric": "memory_usage",
                "operator": ">",
                "threshold": 0.9,  # 内存使用率超过90%
                "level": AlertLevel.WARNING,
                "title": "缓存内存使用率过高",
                "message": "缓存内存使用率超过90%",
            },
        }

    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("Cache monitoring is already running")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(
            f"Cache monitoring started with {self.collection_interval}s interval"
        )

    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Cache monitoring stopped")

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待

    async def _collect_metrics(self):
        """收集指标"""
        try:
            cache_service = await get_multi_cache_service()
            stats = await cache_service.get_comprehensive_stats()

            now = datetime.now()

            # 计算各种指标
            total_requests = stats.get("total_requests", 0)
            total_hits = stats.get("total_hits", 0)
            total_misses = stats.get("total_misses", 0)

            hit_rate = total_hits / total_requests if total_requests > 0 else 0
            miss_rate = total_misses / total_requests if total_requests > 0 else 0

            l1_stats = stats.get("l1_stats", {})
            l2_stats = stats.get("l2_stats", {})

            l1_hit_rate = l1_stats.get("hit_rate", 0)
            l2_hit_rate = l2_stats.get("hit_rate", 0)

            # 计算平均响应时间
            avg_response_time = self._calculate_avg_response_time()

            # 内存使用情况
            memory_usage = l1_stats.get("memory_usage_ratio", 0)
            redis_usage = l2_stats.get("memory_usage_ratio", 0)

            # 错误率
            error_rate = (
                self.hit_miss_stats["errors"] / total_requests
                if total_requests > 0
                else 0
            )

            # 活跃连接数
            active_connections = l2_stats.get("active_connections", 0)

            # 创建性能快照
            snapshot = CachePerformanceSnapshot(
                timestamp=now,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                l1_hit_rate=l1_hit_rate,
                l2_hit_rate=l2_hit_rate,
                avg_response_time=avg_response_time,
                total_requests=total_requests,
                total_hits=total_hits,
                total_misses=total_misses,
                memory_usage=memory_usage,
                redis_usage=redis_usage,
                error_rate=error_rate,
                active_connections=active_connections,
            )

            with self._lock:
                self.snapshots.append(snapshot)

            # 记录指标
            metrics = [
                CacheMetric("cache_hit_rate", MetricType.GAUGE, hit_rate, now),
                CacheMetric("cache_miss_rate", MetricType.GAUGE, miss_rate, now),
                CacheMetric("l1_hit_rate", MetricType.GAUGE, l1_hit_rate, now),
                CacheMetric("l2_hit_rate", MetricType.GAUGE, l2_hit_rate, now),
                CacheMetric(
                    "avg_response_time", MetricType.GAUGE, avg_response_time, now
                ),
                CacheMetric("total_requests", MetricType.COUNTER, total_requests, now),
                CacheMetric("memory_usage", MetricType.GAUGE, memory_usage, now),
                CacheMetric("redis_usage", MetricType.GAUGE, redis_usage, now),
                CacheMetric("error_rate", MetricType.GAUGE, error_rate, now),
                CacheMetric(
                    "active_connections", MetricType.GAUGE, active_connections, now
                ),
            ]

            for metric in metrics:
                with self._lock:
                    self.metrics[metric.name].append(metric)

            logger.debug(f"Collected {len(metrics)} cache metrics")

        except Exception as e:
            logger.error(f"Failed to collect cache metrics: {e}")

    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if not self.request_times:
            return 0.0

        # 计算最近1000个请求的平均响应时间
        recent_times = list(self.request_times)[-1000:]
        return sum(recent_times) / len(recent_times) if recent_times else 0.0

    async def _check_alerts(self):
        """检查告警"""
        try:
            # 获取最新的指标值
            latest_metrics = {}
            with self._lock:
                for metric_name, metric_deque in self.metrics.items():
                    if metric_deque:
                        latest_metrics[metric_name] = metric_deque[-1].value

            # 检查每个告警规则
            for rule_name, rule in self.alert_rules.items():
                metric_name = rule["metric"]
                if metric_name not in latest_metrics:
                    continue

                current_value = latest_metrics[metric_name]
                threshold = rule["threshold"]
                operator = rule["operator"]

                # 检查是否触发告警
                triggered = False
                if operator == ">" and current_value > threshold:
                    triggered = True
                elif operator == "<" and current_value < threshold:
                    triggered = True
                elif operator == ">=" and current_value >= threshold:
                    triggered = True
                elif operator == "<=" and current_value <= threshold:
                    triggered = True
                elif operator == "==" and current_value == threshold:
                    triggered = True

                if triggered:
                    # 检查是否已有未解决的相同告警
                    existing_alert = next(
                        (
                            alert
                            for alert in self.alerts
                            if alert.metric_name == metric_name and not alert.resolved
                        ),
                        None,
                    )

                    if not existing_alert:
                        # 创建新告警
                        alert = CacheAlert(
                            id=f"{rule_name}_{int(time.time())}",
                            level=rule["level"],
                            title=rule["title"],
                            message=f"{rule['message']} (当前值: {current_value:.3f}, 阈值: {threshold})",
                            timestamp=datetime.now(),
                            metric_name=metric_name,
                            threshold=threshold,
                            current_value=current_value,
                        )

                        with self._lock:
                            self.alerts.append(alert)

                        logger.warning(f"Cache alert triggered: {alert.title}")
                else:
                    # 检查是否需要解决告警
                    for alert in self.alerts:
                        if (
                            alert.metric_name == metric_name
                            and not alert.resolved
                            and alert.level == rule["level"]
                        ):
                            alert.resolved = True
                            alert.resolved_at = datetime.now()
                            logger.info(f"Cache alert resolved: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to check cache alerts: {e}")

    def record_request_time(self, response_time: float):
        """记录请求响应时间"""
        with self._lock:
            self.request_times.append(response_time)

    def record_cache_hit(self, hit_type: CacheHitType):
        """记录缓存命中"""
        with self._lock:
            self.hit_miss_stats["total_requests"] += 1

            if hit_type == CacheHitType.L1_HIT:
                self.hit_miss_stats["total_hits"] += 1
                self.hit_miss_stats["l1_hits"] += 1
            elif hit_type == CacheHitType.L2_HIT:
                self.hit_miss_stats["total_hits"] += 1
            elif hit_type == CacheHitType.MISS:
                self.hit_miss_stats["total_misses"] += 1

    def record_cache_error(self):
        """记录缓存错误"""
        with self._lock:
            self.hit_miss_stats["errors"] += 1

    def get_current_metrics(
        self, cache_type: Optional[str] = None
    ) -> Optional[CacheMetrics]:
        """获取当前缓存指标"""
        with self._lock:
            latest_snapshot = self.snapshots[-1] if self.snapshots else None

        if not latest_snapshot:
            return None

        return CacheMetrics(
            hit_rate=latest_snapshot.hit_rate,
            miss_rate=latest_snapshot.miss_rate,
            l1_hit_rate=latest_snapshot.l1_hit_rate,
            l2_hit_rate=latest_snapshot.l2_hit_rate,
            avg_response_time=latest_snapshot.avg_response_time,
            total_requests=latest_snapshot.total_requests,
            total_hits=latest_snapshot.total_hits,
            total_misses=latest_snapshot.total_misses,
            memory_usage=latest_snapshot.memory_usage,
            redis_usage=latest_snapshot.redis_usage,
            error_rate=latest_snapshot.error_rate,
            active_connections=latest_snapshot.active_connections,
            timestamp=latest_snapshot.timestamp,
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        with self._lock:
            latest_snapshot = self.snapshots[-1] if self.snapshots else None
            active_alerts = [alert for alert in self.alerts if not alert.resolved]
            recent_snapshots = list(self.snapshots)[-60:]  # 最近1小时

        return {
            "current_status": {
                "hit_rate": latest_snapshot.hit_rate if latest_snapshot else 0,
                "avg_response_time": (
                    latest_snapshot.avg_response_time if latest_snapshot else 0
                ),
                "total_requests": (
                    latest_snapshot.total_requests if latest_snapshot else 0
                ),
                "memory_usage": latest_snapshot.memory_usage if latest_snapshot else 0,
                "redis_usage": latest_snapshot.redis_usage if latest_snapshot else 0,
                "error_rate": latest_snapshot.error_rate if latest_snapshot else 0,
                "active_connections": (
                    latest_snapshot.active_connections if latest_snapshot else 0
                ),
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len(
                    [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
                ),
                "warning_count": len(
                    [a for a in active_alerts if a.level == AlertLevel.WARNING]
                ),
                "recent_alerts": [asdict(alert) for alert in active_alerts[:5]],
            },
            "trends": {
                "hit_rate_trend": [s.hit_rate for s in recent_snapshots],
                "response_time_trend": [s.avg_response_time for s in recent_snapshots],
                "request_count_trend": [s.total_requests for s in recent_snapshots],
                "timestamps": [s.timestamp.isoformat() for s in recent_snapshots],
            },
            "health_score": self._calculate_health_score(
                latest_snapshot, active_alerts
            ),
        }

    def _calculate_health_score(
        self, snapshot: Optional[CachePerformanceSnapshot], alerts: List[CacheAlert]
    ) -> float:
        """计算健康评分 (0-100)"""
        if not snapshot:
            return 0.0

        score = 100.0

        # 命中率影响 (40%权重)
        hit_rate_score = min(snapshot.hit_rate * 100, 100)
        score = score * 0.6 + hit_rate_score * 0.4

        # 响应时间影响 (30%权重)
        response_time_penalty = min(snapshot.avg_response_time / 100, 1.0) * 30
        score -= response_time_penalty

        # 错误率影响 (20%权重)
        error_penalty = snapshot.error_rate * 100 * 0.2
        score -= error_penalty

        # 告警影响 (10%权重)
        alert_penalty = 0
        for alert in alerts:
            if alert.level == AlertLevel.CRITICAL:
                alert_penalty += 5
            elif alert.level == AlertLevel.ERROR:
                alert_penalty += 3
            elif alert.level == AlertLevel.WARNING:
                alert_penalty += 1

        score -= min(alert_penalty, 10)

        return max(score, 0.0)

    async def configure(self, config: Dict[str, Any]) -> None:
        """配置缓存监控器"""
        try:
            logger.info("Configuring cache monitor...")

            # 更新收集间隔
            if "collection_interval" in config:
                self.collection_interval = config["collection_interval"]
                logger.info(f"Collection interval set to {self.collection_interval}s")

            # 更新告警阈值
            if "alert_thresholds" in config:
                thresholds = config["alert_thresholds"]

                # 更新命中率告警阈值
                if "hit_rate_min" in thresholds:
                    self.alert_rules["hit_rate_low"]["threshold"] = thresholds[
                        "hit_rate_min"
                    ]
                    self.alert_rules["hit_rate_critical"]["threshold"] = (
                        thresholds["hit_rate_min"] - 0.2
                    )

                # 更新响应时间告警阈值
                if "response_time_max" in thresholds:
                    self.alert_rules["response_time_high"]["threshold"] = thresholds[
                        "response_time_max"
                    ]

                # 更新内存使用率告警阈值
                if "memory_usage_max" in thresholds:
                    self.alert_rules["memory_usage_high"]["threshold"] = thresholds[
                        "memory_usage_max"
                    ]

                logger.info(f"Alert thresholds updated: {thresholds}")

            # 更新数据保留时间
            if "retention_hours" in config:
                retention_hours = config["retention_hours"]
                max_snapshots = retention_hours * 60  # 分钟级快照
                self.snapshots = deque(list(self.snapshots), maxlen=max_snapshots)
                logger.info(f"Data retention set to {retention_hours} hours")

            logger.info("Cache monitor configuration completed")

        except Exception as e:
            logger.error(f"Failed to configure cache monitor: {e}")
            raise

    async def start_background_collection(self) -> None:
        """启动后台指标收集任务"""
        try:
            if not self.is_monitoring:
                await self.start_monitoring()
            logger.info("Background collection task started")
        except Exception as e:
            logger.error(f"Failed to start background collection: {e}")
            raise


# 全局缓存监控器实例
_cache_monitor: Optional[CacheMonitor] = None


def get_cache_monitor() -> CacheMonitor:
    """获取缓存监控器实例"""
    global _cache_monitor

    if _cache_monitor is None:
        _cache_monitor = CacheMonitor()

    return _cache_monitor
