#!/usr/bin/env python3

import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

import psutil

from app.core.config import settings

"""
Monitoring and metrics collection module.

Provides system monitoring, performance metrics collection and health check functionality, including:
1. Prometheus metrics collection
2. Application performance monitoring
3. Database connection monitoring
4. File system monitoring
5. Custom business metrics
"""


try:
    from prometheus_client import (
        REGISTRY,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create mock classes to avoid import errors
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def time(self):
            return contextmanager(lambda: (yield))()

        def labels(self, *args, **kwargs):
            return self

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Info:
        def __init__(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

    def generate_latest(registry):
        return b"# Prometheus client not available\n"


logger = logging.getLogger(__name__)


class SystemMonitor:
    """System monitor."""

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
        """Setup Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning(
                "Prometheus client not available, monitoring features limited"
            )
            return

        # HTTP request metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
        )

        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
        )

        # Database metrics
        self.db_connections_active = Gauge(
            "db_connections_active", "Active database connections"
        )

        self.db_query_duration = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
        )

        self.db_errors_total = Counter(
            "db_errors_total", "Total database errors", ["error_type"]
        )

        # System resource metrics
        self.system_cpu_usage = Gauge(
            "system_cpu_usage_percent", "System CPU usage percentage"
        )

        self.system_memory_usage = Gauge(
            "system_memory_usage_bytes", "System memory usage in bytes", ["type"]
        )

        self.system_disk_usage = Gauge(
            "system_disk_usage_bytes", "System disk usage in bytes", ["path", "type"]
        )

        # Application metrics
        self.app_uptime_seconds = Gauge(
            "app_uptime_seconds", "Application uptime in seconds"
        )

        self.app_info = Info("app_info", "Application information")

        # OCR processing metrics
        self.ocr_requests_total = Counter(
            "ocr_requests_total", "Total OCR processing requests", ["engine", "status"]
        )

        self.ocr_processing_duration = Histogram(
            "ocr_processing_duration_seconds",
            "OCR processing duration in seconds",
            ["engine"],
        )

        # File upload metrics
        self.file_uploads_total = Counter(
            "file_uploads_total", "Total file uploads", ["file_type", "status"]
        )

        self.file_upload_size_bytes = Histogram(
            "file_upload_size_bytes", "File upload size in bytes", ["file_type"]
        )

        # User activity metrics
        self.user_sessions_active = Gauge(
            "user_sessions_active", "Active user sessions"
        )

        self.user_actions_total = Counter(
            "user_actions_total", "Total user actions", ["action_type"]
        )

        # Set application info
        self.app_info.info(
            {
                "version": getattr(settings, "VERSION", "1.0.0"),
                "environment": getattr(settings, "ENVIRONMENT", "development"),
                "python_version": sys.version.split()[0],
            }
        )

    def update_system_metrics(self):
        """Update system metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.labels(type="total").set(memory.total)
            self.system_memory_usage.labels(type="available").set(memory.available)
            self.system_memory_usage.labels(type="used").set(memory.used)

            # Disk usage
            disk_usage = psutil.disk_usage("/")
            self.system_disk_usage.labels(path="/", type="total").set(disk_usage.total)
            self.system_disk_usage.labels(path="/", type="used").set(disk_usage.used)
            self.system_disk_usage.labels(path="/", type="free").set(disk_usage.free)

            # Application uptime
            uptime = time.time() - self.start_time
            self.app_uptime_seconds.set(uptime)

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_db_query(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        error_type: str = None,
    ):
        """Record database query metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.db_query_duration.labels(operation=operation).observe(duration)

        if not success and error_type:
            self.db_errors_total.labels(error_type=error_type).inc()

    def record_ocr_request(self, engine: str, duration: float, success: bool = True):
        """Record OCR processing metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        status = "success" if success else "error"
        self.ocr_requests_total.labels(engine=engine, status=status).inc()
        self.ocr_processing_duration.labels(engine=engine).observe(duration)

    def record_file_upload(self, file_type: str, file_size: int, success: bool = True):
        """Record file upload metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        status = "success" if success else "error"
        self.file_uploads_total.labels(file_type=file_type, status=status).inc()

        if success:
            self.file_upload_size_bytes.labels(file_type=file_type).observe(file_size)

    def record_user_action(self, action_type: str):
        """Record user action metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.user_actions_total.labels(action_type=action_type).inc()

    def set_active_sessions(self, count: int):
        """Set active session count."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.user_sessions_active.set(count)

    def set_active_db_connections(self, count: int):
        """Set active database connection count."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.db_connections_active.set(count)

    def get_metrics(self) -> str:
        """Get Prometheus format metrics."""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"

        # Update system metrics
        self.update_system_metrics()

        # generate_latest returns bytes, need to convert to string
        metrics_bytes = generate_latest(REGISTRY)
        return metrics_bytes.decode("utf-8")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status information."""
        try:
            # System resource information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Application uptime
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
                        "percent": memory.percent,
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100,
                    },
                },
                "application": {
                    "version": getattr(settings, "VERSION", "1.0.0"),
                    "environment": getattr(settings, "ENVIRONMENT", "development"),
                    "prometheus_available": PROMETHEUS_AVAILABLE,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }


# Global monitoring instance
monitor = SystemMonitor()


# Decorator functions
def monitor_endpoint(endpoint_name: Optional[str] = None):
    """Decorator for monitoring API endpoints."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record successful request
                monitor.record_http_request(
                    method="GET",  # Can be obtained from request
                    endpoint=endpoint,
                    status_code=200,
                    duration=duration,
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                # Record failed request
                monitor.record_http_request(
                    method="GET", endpoint=endpoint, status_code=500, duration=duration
                )

                raise e

        return wrapper

    return decorator


def monitor_db_operation(operation_name: str):
    """Decorator for monitoring database operations."""

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
    """Context manager for monitoring OCR processing."""
    start_time = time.time()
    success = False

    try:
        yield
        success = True
    finally:
        duration = time.time() - start_time
        monitor.record_ocr_request(engine, duration, success)


class PerformanceLogger:
    """Performance logger."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.performance")

    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Log slow queries."""
        if duration > threshold:
            self.logger.warning(
                f"Slow query detected: {duration:.2f}s > {threshold}s",
                extra={
                    "query": query[:200],  # Truncate long queries
                    "duration": duration,
                    "threshold": threshold,
                },
            )

    def log_high_memory_usage(self, usage_percent: float, threshold: float = 80.0):
        """Log high memory usage."""
        if usage_percent > threshold:
            self.logger.warning(
                f"High memory usage: {usage_percent:.1f}% > {threshold}%",
                extra={"memory_usage_percent": usage_percent, "threshold": threshold},
            )

    def log_high_cpu_usage(self, usage_percent: float, threshold: float = 80.0):
        """Log high CPU usage."""
        if usage_percent > threshold:
            self.logger.warning(
                f"High CPU usage: {usage_percent:.1f}% > {threshold}%",
                extra={"cpu_usage_percent": usage_percent, "threshold": threshold},
            )

    @contextmanager
    def measure(self, operation_name: str):
        """Context manager for measuring operation execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.logger.info(
                f"Operation '{operation_name}' completed in {duration:.3f}s",
                extra={"operation": operation_name, "duration": duration},
            )

    def time_it(self, operation_name: str = None):
        """Decorator: measure function execution time."""

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
                        extra={"function": name, "duration": duration},
                    )

            return wrapper

        return decorator


# Global performance logger
perf_logger = PerformanceLogger()


def setup_monitoring():
    """Setup monitoring system."""
    logger.info("Setting up monitoring system...")

    if PROMETHEUS_AVAILABLE:
        logger.info("Prometheus monitoring enabled")
    else:
        logger.warning(
            "Prometheus client not available, please install: pip install prometheus-client"
        )

    # Start system metrics update
    monitor.update_system_metrics()

    logger.info("Monitoring system setup complete")


if __name__ == "__main__":
    # Test monitoring functionality
    setup_monitoring()

    # Simulate some metrics
    monitor.record_http_request("GET", "/api/test", 200, 0.1)
    monitor.record_db_query("SELECT", 0.05)
    monitor.record_ocr_request("paddleocr", 2.5)
    monitor.record_file_upload("pdf", 1024000)

    # Output metrics
    print("=== Prometheus Metrics ===")
    print(monitor.get_metrics())

    print("\n=== Health Status ===")
    print(json.dumps(monitor.get_health_status(), indent=2))
