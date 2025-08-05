#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强监控中间件
自动收集API性能指标、错误率和系统资源使用情况
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logger import logger
from app.services.performance_metrics import enhanced_performance_monitor


class EnhancedMonitoringMiddleware(BaseHTTPMiddleware):
    """
    增强监控中间件

    功能:
    - 自动记录API请求性能指标
    - 收集错误率统计
    - 监控响应时间分布
    - 跟踪API使用模式
    - 检测异常请求
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.slow_request_threshold = 2.0  # 慢请求阈值（秒）
        self.excluded_paths = {
            "/metrics",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理HTTP请求并收集性能指标

        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: HTTP响应对象
        """
        # 记录请求开始时间
        start_time = time.time()
        request_timestamp = datetime.now()

        # 提取请求信息
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # 跳过排除的路径
        if any(excluded in path for excluded in self.excluded_paths):
            return await call_next(request)

        # 增加请求计数
        self.request_count += 1

        # 记录请求详情
        request_id = request.headers.get("x-request-id", f"req-{self.request_count}")

        logger.info(
            f"API请求开始: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "timestamp": request_timestamp.isoformat(),
            },
        )

        # 处理请求
        response = None
        error_occurred = False
        error_details = None

        try:
            response = await call_next(request)
        except Exception as e:
            error_occurred = True
            error_details = str(e)
            self.error_count += 1

            logger.error(
                f"API请求异常: {method} {path} - {error_details}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error": error_details,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 创建错误响应
            from fastapi.responses import JSONResponse

            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

        # 计算响应时间
        end_time = time.time()
        response_time = end_time - start_time

        # 获取响应状态码
        status_code = response.status_code if response else 500

        # 记录性能指标
        await self._record_performance_metrics(
            method=method,
            path=path,
            status_code=status_code,
            response_time=response_time,
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            error_occurred=error_occurred,
            error_details=error_details,
        )

        # 记录请求完成
        log_level = "warning" if response_time > self.slow_request_threshold else "info"
        log_message = (
            f"API请求完成: {method} {path} - {status_code} - {response_time:.3f}s"
        )

        if response_time > self.slow_request_threshold:
            log_message += " [慢请求]"

        getattr(logger, log_level)(
            log_message,
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time": response_time,
                "client_ip": client_ip,
                "slow_request": response_time > self.slow_request_threshold,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 添加响应头
        if response:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Server-Time"] = datetime.now().isoformat()

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址

        Args:
            request: HTTP请求对象

        Returns:
            str: 客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 使用客户端地址
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"

    async def _record_performance_metrics(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        client_ip: str,
        user_agent: str,
        request_id: str,
        error_occurred: bool,
        error_details: str = None,
    ):
        """
        记录性能指标到监控系统

        Args:
            method: HTTP方法
            path: 请求路径
            status_code: 响应状态码
            response_time: 响应时间
            client_ip: 客户端IP
            user_agent: 用户代理
            request_id: 请求ID
            error_occurred: 是否发生错误
            error_details: 错误详情
        """
        try:
            # 记录到增强性能监控器
            enhanced_performance_monitor.record_api_performance(
                endpoint=path,
                method=method,
                response_time=response_time,
                status_code=status_code,
            )

            # 记录API吞吐量
            endpoint_key = f"{method}:{path}"
            time.time()

            # 更新API吞吐量指标（简化实现）
            if hasattr(enhanced_performance_monitor, "api_throughput"):
                enhanced_performance_monitor.api_throughput.labels(
                    endpoint=endpoint_key
                ).set(
                    1
                )  # 这里应该实现更复杂的吞吐量计算

            # 计算错误率
            if status_code >= 400:
                error_rate = (self.error_count / self.request_count) * 100
                if hasattr(enhanced_performance_monitor, "api_error_rate"):
                    enhanced_performance_monitor.api_error_rate.labels(
                        endpoint=endpoint_key
                    ).set(error_rate)

            # 记录慢请求
            if response_time > self.slow_request_threshold:
                logger.warning(
                    f"检测到慢请求: {method} {path} - {response_time:.3f}s",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "response_time": response_time,
                        "threshold": self.slow_request_threshold,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                    },
                )

            # 记录错误详情
            if error_occurred and error_details:
                logger.error(
                    f"API错误详情: {method} {path} - {error_details}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "error_details": error_details,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                    },
                )

        except Exception as e:
            logger.error(f"记录性能指标失败: {e}")

    def get_middleware_stats(self) -> Dict[str, Any]:
        """
        获取中间件统计信息

        Returns:
            Dict: 统计信息
        """
        error_rate = (
            (self.error_count / self.request_count * 100)
            if self.request_count > 0
            else 0
        )

        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_percent": round(error_rate, 2),
            "slow_request_threshold": self.slow_request_threshold,
            "excluded_paths": list(self.excluded_paths),
        }


class PerformanceCollectorTask:
    """
    性能数据收集后台任务
    """

    def __init__(self, interval: int = 30):
        """
        初始化性能收集任务

        Args:
            interval: 收集间隔（秒）
        """
        self.interval = interval
        self.running = False
        self.task = None

    async def start(self):
        """
        启动性能收集任务
        """
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._collect_loop())
        logger.info(f"性能收集任务已启动，收集间隔: {self.interval}秒")

    async def stop(self):
        """
        停止性能收集任务
        """
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("性能收集任务已停止")

    async def _collect_loop(self):
        """
        性能收集循环
        """
        while self.running:
            try:
                # 收集系统健康指标
                await enhanced_performance_monitor.collect_system_health()

                # 收集业务指标
                await enhanced_performance_monitor.collect_business_metrics()

                logger.debug("性能指标收集完成")

            except Exception as e:
                logger.error(f"性能指标收集失败: {e}")

            # 等待下一次收集
            await asyncio.sleep(self.interval)


# 全局实例
performance_collector = PerformanceCollectorTask()


# 启动和停止函数
async def start_enhanced_monitoring():
    """
    启动增强监控
    """
    await performance_collector.start()
    logger.info("增强监控系统已启动")


async def stop_enhanced_monitoring():
    """
    停止增强监控
    """
    await performance_collector.stop()
    logger.info("增强监控系统已停止")


if __name__ == "__main__":
    # 测试增强监控中间件
    import asyncio

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.add_middleware(EnhancedMonitoringMiddleware)

    @app.get("/test")
    async def test_endpoint():
        await asyncio.sleep(0.1)  # 模拟处理时间
        return {"message": "测试成功"}

    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(3)  # 模拟慢请求
        return {"message": "慢请求完成"}

    @app.get("/error")
    async def error_endpoint():
        raise Exception("测试错误")

    # 测试客户端
    client = TestClient(app)

    print("测试增强监控中间件...")

    # 测试正常请求
    response = client.get("/test")
    print(f"正常请求: {response.status_code}")

    # 测试慢请求
    response = client.get("/slow")
    print(f"慢请求: {response.status_code}")

    # 测试错误请求
    response = client.get("/error")
    print(f"错误请求: {response.status_code}")

    print("测试完成")
