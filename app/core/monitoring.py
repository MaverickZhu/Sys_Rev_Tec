#!/usr/bin/env python3
"""
监控和指标收集模块

提供系统监控、性能指标收集和健康检查功能，包括：
1. Prometheus指标收集
2. 应用性能监控
3. 数据库连接监控
4. 文件系统监控
5. 自定义业务指标
"""

import sys
import time
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from functools import wraps
from contextlib import contextmanager

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info,
        generate_latest, CONTENT_TYPE_LATEST,
        CollectorRegistry, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # 创建模拟类以避免导入错误
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return contextmanager(lambda: (yield))()
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass

from app.core.config import settings

logger = logging.getLogger(__name__)

class SystemMonitor:
    """系统监控器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.start_time = time.time()
            self._setup_metrics()
            SystemMonitor._initialized = True
    
    def _setup_metrics(self):
        """设置Prometheus指标"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus客户端不可用，监控功能受限")
            return
        
        # HTTP请求指标
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # 数据库指标
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections'
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation']
        )
        
        self.db_errors_total = Counter(
            'db_errors_total',
            'Total database errors',
            ['error_type']
        )
        
        # 系统资源指标
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            ['type']
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['path', 'type']
        )
        
        # 应用指标
        self.app_uptime_seconds = Gauge(
            'app_uptime_seconds',
            'Application uptime in seconds'
        )
        
        self.app_info = Info(
            'app_info',
            'Application information'
        )
        
        # OCR处理指标
        self.ocr_requests_total = Counter(
            'ocr_requests_total',
            'Total OCR processing requests',
            ['engine', 'status']
        )
        
        self.ocr_processing_duration = Histogram(
            'ocr_processing_duration_seconds',
            'OCR processing duration in seconds',
            ['engine']
        )
        
        # 文件上传指标
        self.file_uploads_total = Counter(
            'file_uploads_total',
            'Total file uploads',
            ['file_type', 'status']
        )
        
        self.file_upload_size_bytes = Histogram(
            'file_upload_size_bytes',
            'File upload size in bytes',
            ['file_type']
        )
        
        # 用户活动指标
        self.user_sessions_active = Gauge(
            'user_sessions_active',
            'Active user sessions'
        )
        
        self.user_actions_total = Counter(
            'user_actions_total',
            'Total user actions',
            ['action_type']
        )
        
        # 设置应用信息
        self.app_info.info({
            'version': settings.VERSION,
            'environment': settings.ENVIRONMENT,
            'python_version': sys.version.split()[0]
        })
    
    def update_system_metrics(self):
        """更新系统指标"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.system_memory_usage.labels(type='total').set(memory.total)
            self.system_memory_usage.labels(type='available').set(memory.available)
            self.system_memory_usage.labels(type='used').set(memory.used)
            
            # 磁盘使用情况
            disk_usage = psutil.disk_usage('/')
            self.system_disk_usage.labels(path='/', type='total').set(disk_usage.total)
            self.system_disk_usage.labels(path='/', type='used').set(disk_usage.used)
            self.system_disk_usage.labels(path='/', type='free').set(disk_usage.free)
            
            # 应用运行时间
            uptime = time.time() - self.start_time
            self.app_uptime_seconds.set(uptime)
            
        except Exception as e:
            logger.error(f"更新系统指标失败: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, duration: float, success: bool = True, error_type: str = None):
        """记录数据库查询指标"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.db_query_duration.labels(operation=operation).observe(duration)
        
        if not success and error_type:
            self.db_errors_total.labels(error_type=error_type).inc()
    
    def record_ocr_request(self, engine: str, duration: float, success: bool = True):
        """记录OCR处理指标"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        status = 'success' if success else 'error'
        self.ocr_requests_total.labels(engine=engine, status=status).inc()
        self.ocr_processing_duration.labels(engine=engine).observe(duration)
    
    def record_file_upload(self, file_type: str, file_size: int, success: bool = True):
        """记录文件上传指标"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        status = 'success' if success else 'error'
        self.file_uploads_total.labels(file_type=file_type, status=status).inc()
        
        if success:
            self.file_upload_size_bytes.labels(file_type=file_type).observe(file_size)
    
    def record_user_action(self, action_type: str):
        """记录用户行为指标"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.user_actions_total.labels(action_type=action_type).inc()
    
    def set_active_sessions(self, count: int):
        """设置活跃会话数"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.user_sessions_active.set(count)
    
    def set_active_db_connections(self, count: int):
        """设置活跃数据库连接数"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.db_connections_active.set(count)
    
    def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"
        
        # 更新系统指标
        self.update_system_metrics()
        
        # generate_latest返回bytes，需要转换为字符串
        metrics_bytes = generate_latest(REGISTRY)
        return metrics_bytes.decode('utf-8')
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态信息"""
        try:
            # 系统资源信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 应用运行时间
            uptime = time.time() - self.start_time
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    }
                },
                "application": {
                    "version": settings.VERSION,
                    "environment": settings.ENVIRONMENT,
                    "prometheus_available": PROMETHEUS_AVAILABLE
                }
            }
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

# 全局监控实例
monitor = SystemMonitor()

# 装饰器函数
def monitor_endpoint(endpoint_name: Optional[str] = None):
    """监控API端点的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 记录成功的请求
                monitor.record_http_request(
                    method="GET",  # 可以从request中获取
                    endpoint=endpoint,
                    status_code=200,
                    duration=duration
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # 记录失败的请求
                monitor.record_http_request(
                    method="GET",
                    endpoint=endpoint,
                    status_code=500,
                    duration=duration
                )
                
                raise e
        
        return wrapper
    return decorator

def monitor_db_operation(operation_name: str):
    """监控数据库操作的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                monitor.record_db_query(operation_name, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_type = type(e).__name__
                
                monitor.record_db_query(
                    operation_name, duration, success=False, error_type=error_type
                )
                raise e
        
        return wrapper
    return decorator

@contextmanager
def monitor_ocr_processing(engine: str):
    """监控OCR处理的上下文管理器"""
    start_time = time.time()
    success = False
    
    try:
        yield
        success = True
    finally:
        duration = time.time() - start_time
        monitor.record_ocr_request(engine, duration, success)

class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.performance")
    
    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """记录慢查询"""
        if duration > threshold:
            self.logger.warning(
                f"Slow query detected: {duration:.2f}s > {threshold}s",
                extra={
                    "query": query[:200],  # 截断长查询
                    "duration": duration,
                    "threshold": threshold
                }
            )
    
    def log_high_memory_usage(self, usage_percent: float, threshold: float = 80.0):
        """记录高内存使用"""
        if usage_percent > threshold:
            self.logger.warning(
                f"High memory usage: {usage_percent:.1f}% > {threshold}%",
                extra={
                    "memory_usage_percent": usage_percent,
                    "threshold": threshold
                }
            )
    
    def log_high_cpu_usage(self, usage_percent: float, threshold: float = 80.0):
        """记录高CPU使用"""
        if usage_percent > threshold:
            self.logger.warning(
                f"High CPU usage: {usage_percent:.1f}% > {threshold}%",
                extra={
                    "cpu_usage_percent": usage_percent,
                    "threshold": threshold
                }
            )
    
    @contextmanager
    def measure(self, operation_name: str):
        """测量操作执行时间的上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.logger.info(
                f"Operation '{operation_name}' completed in {duration:.3f}s",
                extra={
                    "operation": operation_name,
                    "duration": duration
                }
            )
    
    def time_it(self, operation_name: str = None):
        """装饰器：测量函数执行时间"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = operation_name or func.__name__
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.logger.info(
                        f"Function '{name}' executed in {duration:.3f}s",
                        extra={
                            "function": name,
                            "duration": duration
                        }
                    )
            return wrapper
        return decorator

# 全局性能日志记录器
perf_logger = PerformanceLogger()

def setup_monitoring():
    """设置监控系统"""
    logger.info("设置监控系统...")
    
    if PROMETHEUS_AVAILABLE:
        logger.info("Prometheus监控已启用")
    else:
        logger.warning("Prometheus客户端不可用，请安装: pip install prometheus-client")
    
    # 启动系统指标更新
    monitor.update_system_metrics()
    
    logger.info("监控系统设置完成")

if __name__ == "__main__":
    # 测试监控功能
    setup_monitoring()
    
    # 模拟一些指标
    monitor.record_http_request("GET", "/api/test", 200, 0.1)
    monitor.record_db_query("SELECT", 0.05)
    monitor.record_ocr_request("paddleocr", 2.5)
    monitor.record_file_upload("pdf", 1024000)
    
    # 输出指标
    print("=== Prometheus Metrics ===")
    print(monitor.get_metrics())
    
    print("\n=== Health Status ===")
    import json
    print(json.dumps(monitor.get_health_status(), indent=2))