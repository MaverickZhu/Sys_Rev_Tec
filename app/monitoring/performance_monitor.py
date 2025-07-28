#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控模块
集成Prometheus指标收集和缓存性能优化
"""

import time
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import asynccontextmanager
import asyncio
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
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.registry = CollectorRegistry()
        self._setup_metrics()
        self._start_time = time.time()
        
    def _setup_metrics(self):
        """设置Prometheus指标"""
        # HTTP请求指标
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # 缓存指标
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            registry=self.registry
        )
        
        self.cache_operation_duration = Histogram(
            'cache_operation_duration_seconds',
            'Cache operation duration in seconds',
            ['operation'],
            registry=self.registry
        )
        
        # 数据库指标
        self.db_operations_total = Counter(
            'db_operations_total',
            'Total database operations',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self.db_operation_duration = Histogram(
            'db_operation_duration_seconds',
            'Database operation duration in seconds',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self.db_connection_pool_size = Gauge(
            'db_connection_pool_size',
            'Database connection pool size',
            registry=self.registry
        )
        
        # AI服务指标
        self.ai_requests_total = Counter(
            'ai_requests_total',
            'Total AI service requests',
            ['model', 'operation'],
            registry=self.registry
        )
        
        self.ai_request_duration = Histogram(
            'ai_request_duration_seconds',
            'AI request duration in seconds',
            ['model', 'operation'],
            registry=self.registry
        )
        
        self.ai_model_load_time = Summary(
            'ai_model_load_time_seconds',
            'AI model loading time',
            ['model'],
            registry=self.registry
        )
        
        # 系统资源指标
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        # 应用指标
        self.app_uptime_seconds = Gauge(
            'app_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        self.error_rate = Gauge(
            'error_rate',
            'Application error rate',
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str, duration: float):
        """记录缓存操作指标"""
        self.cache_operations_total.labels(
            operation=operation,
            result=result
        ).inc()
        
        self.cache_operation_duration.labels(
            operation=operation
        ).observe(duration)
    
    def record_db_operation(self, operation: str, table: str, duration: float):
        """记录数据库操作指标"""
        self.db_operations_total.labels(
            operation=operation,
            table=table
        ).inc()
        
        self.db_operation_duration.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_ai_request(self, model: str, operation: str, duration: float):
        """记录AI请求指标"""
        self.ai_requests_total.labels(
            model=model,
            operation=operation
        ).inc()
        
        self.ai_request_duration.labels(
            model=model,
            operation=operation
        ).observe(duration)
    
    def update_system_metrics(self):
        """更新系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.set(disk_percent)
            
            # 应用运行时间
            uptime = time.time() - self._start_time
            self.app_uptime_seconds.set(uptime)
            
        except Exception as e:
            logger.error(f"更新系统指标失败: {e}")
    
    async def update_cache_metrics(self):
        """更新缓存指标"""
        try:
            stats = cache_service.get_stats()
            if stats.get('connected'):
                # 计算缓存命中率
                hits = stats.get('keyspace_hits', 0)
                misses = stats.get('keyspace_misses', 0)
                total = hits + misses
                
                if total > 0:
                    hit_ratio = hits / total
                    self.cache_hit_ratio.set(hit_ratio)
                    
        except Exception as e:
            logger.error(f"更新缓存指标失败: {e}")
    
    def get_metrics(self) -> str:
        """获取Prometheus格式的指标数据"""
        return generate_latest(self.registry)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        try:
            # 更新系统指标
            self.update_system_metrics()
            
            return {
                'system': {
                    'cpu_usage': psutil.cpu_percent(),
                    'memory_usage': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'uptime': time.time() - self._start_time
                },
                'cache': cache_service.get_stats(),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"获取指标摘要失败: {e}")
            return {'error': str(e)}


# 性能监控装饰器
def monitor_performance(operation_type: str = 'general'):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 记录成功的操作
                if operation_type == 'cache':
                    performance_monitor.record_cache_operation(
                        func.__name__, 'success', duration
                    )
                elif operation_type == 'db':
                    table = kwargs.get('table', 'unknown')
                    performance_monitor.record_db_operation(
                        func.__name__, table, duration
                    )
                elif operation_type == 'ai':
                    model = kwargs.get('model', 'unknown')
                    performance_monitor.record_ai_request(
                        model, func.__name__, duration
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # 记录失败的操作
                if operation_type == 'cache':
                    performance_monitor.record_cache_operation(
                        func.__name__, 'error', duration
                    )
                elif operation_type == 'db':
                    table = kwargs.get('table', 'unknown')
                    performance_monitor.record_db_operation(
                        func.__name__, table, duration
                    )
                elif operation_type == 'ai':
                    model = kwargs.get('model', 'unknown')
                    performance_monitor.record_ai_request(
                        model, func.__name__, duration
                    )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 记录成功的操作
                if operation_type == 'cache':
                    performance_monitor.record_cache_operation(
                        func.__name__, 'success', duration
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # 记录失败的操作
                if operation_type == 'cache':
                    performance_monitor.record_cache_operation(
                        func.__name__, 'error', duration
                    )
                
                raise
        
        # 根据函数类型选择包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def performance_context(operation_type: str, **labels):
    """性能监控上下文管理器"""
    start_time = time.time()
    try:
        yield
        duration = time.time() - start_time
        
        # 记录成功的操作
        if operation_type == 'http':
            performance_monitor.record_http_request(
                labels.get('method', 'unknown'),
                labels.get('endpoint', 'unknown'),
                labels.get('status_code', 200),
                duration
            )
        
    except Exception as e:
        duration = time.time() - start_time
        
        # 记录失败的操作
        if operation_type == 'http':
            performance_monitor.record_http_request(
                labels.get('method', 'unknown'),
                labels.get('endpoint', 'unknown'),
                labels.get('status_code', 500),
                duration
            )
        
        raise


class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        self.hit_stats = {}
        self.miss_stats = {}
        self.optimization_rules = []
    
    def analyze_cache_patterns(self) -> Dict[str, Any]:
        """分析缓存使用模式"""
        try:
            stats = cache_service.get_stats()
            
            analysis = {
                'hit_rate': self._calculate_hit_rate(stats),
                'memory_usage': stats.get('used_memory', 'N/A'),
                'recommendations': self._generate_recommendations(stats)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"缓存模式分析失败: {e}")
            return {'error': str(e)}
    
    def _calculate_hit_rate(self, stats: Dict[str, Any]) -> float:
        """计算缓存命中率"""
        hits = stats.get('keyspace_hits', 0)
        misses = stats.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return (hits / total) * 100
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        hit_rate = self._calculate_hit_rate(stats)
        
        if hit_rate < 70:
            recommendations.append("缓存命中率较低，建议增加缓存TTL或优化缓存键策略")
        
        if hit_rate > 95:
            recommendations.append("缓存命中率很高，可以考虑减少缓存空间以节省内存")
        
        memory_usage = stats.get('used_memory', '')
        if 'MB' in str(memory_usage) and int(memory_usage.replace('MB', '')) > 500:
            recommendations.append("缓存内存使用较高，建议清理过期数据或调整缓存策略")
        
        return recommendations
    
    async def optimize_cache_strategy(self) -> Dict[str, Any]:
        """优化缓存策略"""
        try:
            # 分析当前缓存状态
            analysis = self.analyze_cache_patterns()
            
            # 执行优化操作
            optimizations = []
            
            # 清理过期缓存
            if analysis.get('hit_rate', 0) < 50:
                # 清理模式匹配的过期缓存
                cleared = cache_service.clear_pattern('*:expired:*')
                if cleared > 0:
                    optimizations.append(f"清理了 {cleared} 个过期缓存项")
            
            return {
                'analysis': analysis,
                'optimizations': optimizations,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"缓存策略优化失败: {e}")
            return {'error': str(e)}


# 全局实例
performance_monitor = PerformanceMonitor()
cache_optimizer = CacheOptimizer()


# 后台任务：定期更新指标
async def metrics_updater():
    """定期更新指标的后台任务"""
    while True:
        try:
            # 更新系统指标
            performance_monitor.update_system_metrics()
            
            # 更新缓存指标
            await performance_monitor.update_cache_metrics()
            
            # 等待30秒
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"指标更新任务失败: {e}")
            await asyncio.sleep(60)  # 出错时等待更长时间


if __name__ == "__main__":
    # 测试性能监控
    import asyncio
    
    async def test_monitoring():
        # 测试HTTP请求监控
        performance_monitor.record_http_request('GET', '/api/test', 200, 0.1)
        
        # 测试缓存操作监控
        performance_monitor.record_cache_operation('get', 'hit', 0.01)
        
        # 获取指标
        metrics = performance_monitor.get_metrics()
        print("Prometheus指标:")
        print(metrics.decode('utf-8'))
        
        # 获取指标摘要
        summary = performance_monitor.get_metrics_summary()
        print("\n指标摘要:")
        print(summary)
        
        # 测试缓存优化
        optimization = await cache_optimizer.optimize_cache_strategy()
        print("\n缓存优化结果:")
        print(optimization)
    
    asyncio.run(test_monitoring())