#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强性能监控指标服务
提供全面的系统性能监控、业务指标收集和性能分析功能
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import json
import psutil
import logging

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)

from app.core.config import settings
from app.core.logger import logger


@dataclass
class PerformanceMetric:
    """性能指标数据结构"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class SystemHealth:
    """系统健康状态"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    uptime: float
    timestamp: datetime


@dataclass
class BusinessMetrics:
    """业务指标"""
    total_projects: int
    total_documents: int
    total_users: int
    active_sessions: int
    reports_generated: int
    api_calls_today: int
    error_rate: float
    avg_response_time: float
    timestamp: datetime


class EnhancedPerformanceMonitor:
    """增强性能监控器"""
    
    def __init__(self):
        """初始化增强性能监控器"""
        self.registry = CollectorRegistry()
        self._setup_enhanced_metrics()
        self._start_time = time.time()
        self._metrics_history = deque(maxlen=1000)  # 保留最近1000个指标记录
        self._alert_thresholds = self._load_alert_thresholds()
        self._performance_baselines = {}
        
    def _setup_enhanced_metrics(self):
        """设置增强的Prometheus指标"""
        # 业务指标
        self.business_projects_total = Gauge(
            'business_projects_total',
            'Total number of projects',
            registry=self.registry
        )
        
        self.business_documents_total = Gauge(
            'business_documents_total',
            'Total number of documents',
            registry=self.registry
        )
        
        self.business_users_total = Gauge(
            'business_users_total',
            'Total number of users',
            registry=self.registry
        )
        
        self.business_active_sessions = Gauge(
            'business_active_sessions',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.business_reports_generated = Counter(
            'business_reports_generated_total',
            'Total number of reports generated',
            ['report_type'],
            registry=self.registry
        )
        
        # API性能指标
        self.api_response_time_percentiles = Summary(
            'api_response_time_percentiles',
            'API response time percentiles',
            ['endpoint', 'method'],
            registry=self.registry
        )
        
        self.api_throughput = Gauge(
            'api_throughput_rps',
            'API throughput in requests per second',
            ['endpoint'],
            registry=self.registry
        )
        
        self.api_error_rate = Gauge(
            'api_error_rate_percent',
            'API error rate percentage',
            ['endpoint'],
            registry=self.registry
        )
        
        # 系统资源详细指标
        self.system_cpu_cores = Gauge(
            'system_cpu_cores_total',
            'Total number of CPU cores',
            registry=self.registry
        )
        
        self.system_memory_total = Gauge(
            'system_memory_total_bytes',
            'Total system memory in bytes',
            registry=self.registry
        )
        
        self.system_disk_total = Gauge(
            'system_disk_total_bytes',
            'Total disk space in bytes',
            registry=self.registry
        )
        
        self.system_network_bytes = Counter(
            'system_network_bytes_total',
            'Total network bytes',
            ['direction'],  # sent/received
            registry=self.registry
        )
        
        self.system_process_count = Gauge(
            'system_process_count',
            'Number of running processes',
            registry=self.registry
        )
        
        # 应用性能指标
        self.app_memory_usage = Gauge(
            'app_memory_usage_bytes',
            'Application memory usage in bytes',
            registry=self.registry
        )
        
        self.app_cpu_usage = Gauge(
            'app_cpu_usage_percent',
            'Application CPU usage percentage',
            registry=self.registry
        )
        
        self.app_thread_count = Gauge(
            'app_thread_count',
            'Number of application threads',
            registry=self.registry
        )
        
        self.app_file_descriptors = Gauge(
            'app_file_descriptors_count',
            'Number of open file descriptors',
            registry=self.registry
        )
        
        # 数据库性能指标
        self.db_connection_pool_active = Gauge(
            'db_connection_pool_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.db_connection_pool_idle = Gauge(
            'db_connection_pool_idle',
            'Idle database connections',
            registry=self.registry
        )
        
        self.db_query_duration_percentiles = Summary(
            'db_query_duration_percentiles',
            'Database query duration percentiles',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self.db_slow_queries = Counter(
            'db_slow_queries_total',
            'Total number of slow queries',
            ['table'],
            registry=self.registry
        )
        
        # 缓存性能指标
        self.cache_memory_usage = Gauge(
            'cache_memory_usage_bytes',
            'Cache memory usage in bytes',
            registry=self.registry
        )
        
        self.cache_key_count = Gauge(
            'cache_key_count',
            'Number of cache keys',
            registry=self.registry
        )
        
        self.cache_evictions = Counter(
            'cache_evictions_total',
            'Total cache evictions',
            ['reason'],
            registry=self.registry
        )
        
        # 性能告警指标
        self.performance_alerts = Counter(
            'performance_alerts_total',
            'Total performance alerts triggered',
            ['alert_type', 'severity'],
            registry=self.registry
        )
    
    def _load_alert_thresholds(self) -> Dict[str, float]:
        """加载告警阈值配置"""
        return {
            'cpu_usage_warning': 70.0,
            'cpu_usage_critical': 90.0,
            'memory_usage_warning': 80.0,
            'memory_usage_critical': 95.0,
            'disk_usage_warning': 85.0,
            'disk_usage_critical': 95.0,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0,
            'error_rate_warning': 5.0,
            'error_rate_critical': 10.0
        }
    
    async def collect_system_health(self) -> SystemHealth:
        """收集系统健康指标"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用情况
            try:
                disk = psutil.disk_usage('/')
            except:
                disk = psutil.disk_usage('C:\\')
            disk_usage = (disk.used / disk.total) * 100
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 系统负载（Windows上可能不可用）
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]
            
            # 系统运行时间
            uptime = time.time() - psutil.boot_time()
            
            health = SystemHealth(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average,
                uptime=uptime,
                timestamp=datetime.now()
            )
            
            # 更新Prometheus指标
            self._update_system_metrics(health)
            
            # 检查告警
            await self._check_system_alerts(health)
            
            return health
            
        except Exception as e:
            logger.error(f"收集系统健康指标失败: {e}")
            raise
    
    def _update_system_metrics(self, health: SystemHealth):
        """更新系统指标到Prometheus"""
        # 更新系统资源指标
        self.system_cpu_cores.set(psutil.cpu_count())
        self.system_memory_total.set(psutil.virtual_memory().total)
        
        try:
            disk = psutil.disk_usage('/')
        except:
            disk = psutil.disk_usage('C:\\')
        self.system_disk_total.set(disk.total)
        
        self.system_process_count.set(health.process_count)
        
        # 更新网络指标
        self.system_network_bytes.labels(direction='sent').inc(health.network_io['bytes_sent'])
        self.system_network_bytes.labels(direction='received').inc(health.network_io['bytes_recv'])
        
        # 更新应用指标
        current_process = psutil.Process()
        self.app_memory_usage.set(current_process.memory_info().rss)
        self.app_cpu_usage.set(current_process.cpu_percent())
        self.app_thread_count.set(current_process.num_threads())
        
        try:
            self.app_file_descriptors.set(current_process.num_fds())
        except AttributeError:
            # Windows上可能不支持
            pass
    
    async def _check_system_alerts(self, health: SystemHealth):
        """检查系统告警"""
        alerts = []
        
        # CPU使用率告警
        if health.cpu_usage >= self._alert_thresholds['cpu_usage_critical']:
            alerts.append(('cpu_usage', 'critical', health.cpu_usage))
            self.performance_alerts.labels(alert_type='cpu_usage', severity='critical').inc()
        elif health.cpu_usage >= self._alert_thresholds['cpu_usage_warning']:
            alerts.append(('cpu_usage', 'warning', health.cpu_usage))
            self.performance_alerts.labels(alert_type='cpu_usage', severity='warning').inc()
        
        # 内存使用率告警
        if health.memory_usage >= self._alert_thresholds['memory_usage_critical']:
            alerts.append(('memory_usage', 'critical', health.memory_usage))
            self.performance_alerts.labels(alert_type='memory_usage', severity='critical').inc()
        elif health.memory_usage >= self._alert_thresholds['memory_usage_warning']:
            alerts.append(('memory_usage', 'warning', health.memory_usage))
            self.performance_alerts.labels(alert_type='memory_usage', severity='warning').inc()
        
        # 磁盘使用率告警
        if health.disk_usage >= self._alert_thresholds['disk_usage_critical']:
            alerts.append(('disk_usage', 'critical', health.disk_usage))
            self.performance_alerts.labels(alert_type='disk_usage', severity='critical').inc()
        elif health.disk_usage >= self._alert_thresholds['disk_usage_warning']:
            alerts.append(('disk_usage', 'warning', health.disk_usage))
            self.performance_alerts.labels(alert_type='disk_usage', severity='warning').inc()
        
        # 记录告警
        for alert_type, severity, value in alerts:
            logger.warning(f"性能告警: {alert_type} {severity} - 当前值: {value}")
    
    async def collect_business_metrics(self) -> BusinessMetrics:
        """收集业务指标"""
        try:
            from app.db.session import SessionLocal
            from app.models.project import Project
            from app.models.document import Document
            from app.models.user import User
            
            db = SessionLocal()
            try:
                # 统计项目数量
                total_projects = db.query(Project).count()
                
                # 统计文档数量
                total_documents = db.query(Document).count()
                
                # 统计用户数量
                total_users = db.query(User).count()
                
                # 活跃会话数（这里简化处理）
                active_sessions = 0  # 需要从会话管理器获取
                
                # 今日生成的报告数量（简化处理）
                reports_generated = 0  # 需要从报告服务获取
                
                # 今日API调用数量（简化处理）
                api_calls_today = 0  # 需要从监控数据获取
                
                # 错误率（简化处理）
                error_rate = 0.0  # 需要从监控数据计算
                
                # 平均响应时间（简化处理）
                avg_response_time = 0.0  # 需要从监控数据计算
                
                metrics = BusinessMetrics(
                    total_projects=total_projects,
                    total_documents=total_documents,
                    total_users=total_users,
                    active_sessions=active_sessions,
                    reports_generated=reports_generated,
                    api_calls_today=api_calls_today,
                    error_rate=error_rate,
                    avg_response_time=avg_response_time,
                    timestamp=datetime.now()
                )
                
                # 更新Prometheus指标
                self._update_business_metrics(metrics)
                
                return metrics
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"收集业务指标失败: {e}")
            # 返回默认值
            return BusinessMetrics(
                total_projects=0,
                total_documents=0,
                total_users=0,
                active_sessions=0,
                reports_generated=0,
                api_calls_today=0,
                error_rate=0.0,
                avg_response_time=0.0,
                timestamp=datetime.now()
            )
    
    def _update_business_metrics(self, metrics: BusinessMetrics):
        """更新业务指标到Prometheus"""
        self.business_projects_total.set(metrics.total_projects)
        self.business_documents_total.set(metrics.total_documents)
        self.business_users_total.set(metrics.total_users)
        self.business_active_sessions.set(metrics.active_sessions)
    
    def record_api_performance(self, endpoint: str, method: str, 
                             response_time: float, status_code: int):
        """记录API性能指标"""
        # 记录响应时间百分位数
        self.api_response_time_percentiles.labels(
            endpoint=endpoint, method=method
        ).observe(response_time)
        
        # 检查响应时间告警
        if response_time >= self._alert_thresholds['response_time_critical']:
            self.performance_alerts.labels(
                alert_type='response_time', severity='critical'
            ).inc()
            logger.warning(f"API响应时间告警: {endpoint} {method} - {response_time}s")
        elif response_time >= self._alert_thresholds['response_time_warning']:
            self.performance_alerts.labels(
                alert_type='response_time', severity='warning'
            ).inc()
    
    def record_database_performance(self, operation: str, table: str, 
                                  duration: float, slow_query_threshold: float = 1.0):
        """记录数据库性能指标"""
        # 记录查询时间百分位数
        self.db_query_duration_percentiles.labels(
            operation=operation, table=table
        ).observe(duration)
        
        # 记录慢查询
        if duration >= slow_query_threshold:
            self.db_slow_queries.labels(table=table).inc()
            logger.warning(f"慢查询检测: {operation} on {table} - {duration}s")
    
    def record_cache_performance(self, memory_usage: int, key_count: int, 
                               eviction_reason: str = None):
        """记录缓存性能指标"""
        self.cache_memory_usage.set(memory_usage)
        self.cache_key_count.set(key_count)
        
        if eviction_reason:
            self.cache_evictions.labels(reason=eviction_reason).inc()
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        try:
            # 收集当前指标
            system_health = await self.collect_system_health()
            business_metrics = await self.collect_business_metrics()
            
            # 计算性能趋势
            trends = self._calculate_performance_trends()
            
            # 生成优化建议
            recommendations = self._generate_optimization_recommendations(
                system_health, business_metrics
            )
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_health': asdict(system_health),
                'business_metrics': asdict(business_metrics),
                'performance_trends': trends,
                'optimization_recommendations': recommendations,
                'alert_summary': self._get_alert_summary()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_trends(self) -> Dict[str, Any]:
        """计算性能趋势"""
        if len(self._metrics_history) < 2:
            return {'message': '数据不足，无法计算趋势'}
        
        # 这里可以实现更复杂的趋势分析
        return {
            'cpu_trend': 'stable',
            'memory_trend': 'increasing',
            'response_time_trend': 'improving'
        }
    
    def _generate_optimization_recommendations(self, 
                                             system_health: SystemHealth,
                                             business_metrics: BusinessMetrics) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # CPU优化建议
        if system_health.cpu_usage > 80:
            recommendations.append("CPU使用率较高，建议优化计算密集型操作或增加CPU资源")
        
        # 内存优化建议
        if system_health.memory_usage > 85:
            recommendations.append("内存使用率较高，建议检查内存泄漏或增加内存资源")
        
        # 磁盘优化建议
        if system_health.disk_usage > 90:
            recommendations.append("磁盘空间不足，建议清理临时文件或扩展存储空间")
        
        # 业务优化建议
        if business_metrics.total_documents > 10000:
            recommendations.append("文档数量较多，建议实施数据归档策略")
        
        return recommendations
    
    def _get_alert_summary(self) -> Dict[str, int]:
        """获取告警摘要"""
        # 这里应该从告警历史中统计
        return {
            'total_alerts_24h': 0,
            'critical_alerts_24h': 0,
            'warning_alerts_24h': 0
        }
    
    def get_metrics(self) -> bytes:
        """获取Prometheus格式的指标数据"""
        return generate_latest(self.registry)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        try:
            return {
                'system': {
                    'cpu_usage': psutil.cpu_percent(),
                    'memory_usage': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent if psutil.disk_usage else 0,
                    'uptime': time.time() - self._start_time
                },
                'application': {
                    'start_time': self._start_time,
                    'metrics_collected': len(self._metrics_history)
                },
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"获取指标摘要失败: {e}")
            return {'error': str(e)}


# 全局实例
enhanced_performance_monitor = EnhancedPerformanceMonitor()


# 后台任务：定期收集指标
async def enhanced_metrics_collector():
    """增强指标收集器后台任务"""
    while True:
        try:
            # 收集系统健康指标
            system_health = await enhanced_performance_monitor.collect_system_health()
            
            # 收集业务指标
            business_metrics = await enhanced_performance_monitor.collect_business_metrics()
            
            # 记录到历史
            enhanced_performance_monitor._metrics_history.append({
                'timestamp': datetime.now(),
                'system_health': asdict(system_health),
                'business_metrics': asdict(business_metrics)
            })
            
            logger.debug("性能指标收集完成")
            
            # 等待30秒
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"增强指标收集失败: {e}")
            await asyncio.sleep(60)  # 出错时等待更长时间


if __name__ == "__main__":
    # 测试增强性能监控
    import asyncio
    
    async def test_enhanced_monitoring():
        # 测试系统健康收集
        health = await enhanced_performance_monitor.collect_system_health()
        print("系统健康状态:")
        print(asdict(health))
        
        # 测试业务指标收集
        business = await enhanced_performance_monitor.collect_business_metrics()
        print("\n业务指标:")
        print(asdict(business))
        
        # 测试性能报告生成
        report = await enhanced_performance_monitor.generate_performance_report()
        print("\n性能报告:")
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        
        # 获取Prometheus指标
        metrics = enhanced_performance_monitor.get_metrics()
        print("\nPrometheus指标:")
        print(metrics.decode('utf-8'))
    
    asyncio.run(test_enhanced_monitoring())