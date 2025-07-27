# -*- coding: utf-8 -*-
"""
AI服务健康检查和监控API路由
提供服务状态检查、性能监控和系统信息的REST API接口
"""

import logging
import time
import psutil
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ai_service.config import get_settings
from ai_service.database import get_vector_db
from ai_service.vectorization import get_vectorization_service
from ai_service.search import get_search_service
from ai_service.utils.cache import get_cache_manager
from ai_service.utils.logging import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger()

# 创建路由器
router = APIRouter(prefix="/health", tags=["health"])


# 响应模型
class HealthStatus(BaseModel):
    """健康状态"""
    status: str = Field(..., description="服务状态 (healthy/unhealthy/degraded)")
    timestamp: float = Field(..., description="检查时间戳")
    uptime: float = Field(..., description="运行时间（秒）")
    version: str = Field(..., description="服务版本")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="各组件检查结果")


class SystemInfo(BaseModel):
    """系统信息"""
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    load_average: List[float] = Field(..., description="系统负载")
    process_count: int = Field(..., description="进程数量")
    network_connections: int = Field(..., description="网络连接数")
    python_version: str = Field(..., description="Python版本")
    platform: str = Field(..., description="操作系统平台")


class ServiceMetrics(BaseModel):
    """服务指标"""
    total_requests: int = Field(..., description="总请求数")
    active_connections: int = Field(..., description="活跃连接数")
    cache_hit_rate: float = Field(..., description="缓存命中率")
    average_response_time: float = Field(..., description="平均响应时间")
    error_rate: float = Field(..., description="错误率")
    vectorization_count: int = Field(..., description="向量化次数")
    search_count: int = Field(..., description="搜索次数")
    last_activity: float = Field(..., description="最后活动时间")


class DetailedHealthResponse(BaseModel):
    """详细健康检查响应"""
    health: HealthStatus = Field(..., description="健康状态")
    system: SystemInfo = Field(..., description="系统信息")
    metrics: ServiceMetrics = Field(..., description="服务指标")
    dependencies: Dict[str, Dict[str, Any]] = Field(..., description="依赖服务状态")


# 全局变量用于跟踪服务启动时间
service_start_time = time.time()


# 辅助函数
def get_system_info() -> SystemInfo:
    """获取系统信息"""
    try:
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # 系统负载
        try:
            load_average = list(psutil.getloadavg())
        except AttributeError:
            # Windows系统不支持getloadavg
            load_average = [0.0, 0.0, 0.0]
        
        # 进程数量
        process_count = len(psutil.pids())
        
        # 网络连接数
        try:
            network_connections = len(psutil.net_connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            network_connections = 0
        
        # Python版本和平台
        import sys
        import platform
        python_version = sys.version
        platform_info = platform.platform()
        
        return SystemInfo(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            load_average=load_average,
            process_count=process_count,
            network_connections=network_connections,
            python_version=python_version,
            platform=platform_info
        )
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        # 返回默认值
        return SystemInfo(
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            load_average=[0.0, 0.0, 0.0],
            process_count=0,
            network_connections=0,
            python_version="unknown",
            platform="unknown"
        )


async def check_database_health(vector_db) -> Dict[str, Any]:
    """检查数据库健康状态"""
    try:
        start_time = time.time()
        health_status = await vector_db.health_check()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if health_status.get("status") == "healthy" else "unhealthy",
            "response_time": response_time,
            "details": health_status,
            "last_check": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": 0.0,
            "error": str(e),
            "last_check": time.time()
        }


async def check_cache_health(cache_manager) -> Dict[str, Any]:
    """检查缓存健康状态"""
    try:
        start_time = time.time()
        
        # 测试缓存连接
        test_key = "health_check_test"
        test_value = "test_value"
        
        await cache_manager.set(test_key, test_value, ttl=10)
        retrieved_value = await cache_manager.get(test_key)
        await cache_manager.delete(test_key)
        
        response_time = time.time() - start_time
        
        if retrieved_value == test_value:
            return {
                "status": "healthy",
                "response_time": response_time,
                "last_check": time.time()
            }
        else:
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": "缓存读写测试失败",
                "last_check": time.time()
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": 0.0,
            "error": str(e),
            "last_check": time.time()
        }


async def check_vectorization_health(vectorization_service) -> Dict[str, Any]:
    """检查向量化服务健康状态"""
    try:
        start_time = time.time()
        health_status = await vectorization_service.health_check()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if health_status.get("status") == "healthy" else "unhealthy",
            "response_time": response_time,
            "details": health_status,
            "last_check": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": 0.0,
            "error": str(e),
            "last_check": time.time()
        }


async def check_search_health(search_service) -> Dict[str, Any]:
    """检查搜索服务健康状态"""
    try:
        start_time = time.time()
        health_status = await search_service.health_check()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if health_status.get("status") == "healthy" else "unhealthy",
            "response_time": response_time,
            "details": health_status,
            "last_check": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": 0.0,
            "error": str(e),
            "last_check": time.time()
        }


# API端点
@router.get(
    "/",
    response_model=HealthStatus,
    summary="基础健康检查",
    description="快速检查AI服务的基本健康状态"
)
async def basic_health_check():
    """基础健康检查"""
    try:
        current_time = time.time()
        uptime = current_time - service_start_time
        
        # 基础检查
        checks = {
            "service": {
                "status": "healthy",
                "uptime": uptime,
                "last_check": current_time
            }
        }
        
        return HealthStatus(
            status="healthy",
            timestamp=current_time,
            uptime=uptime,
            version="1.0.0",
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"健康检查失败: {str(e)}"
        )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    summary="详细健康检查",
    description="全面检查AI服务及其依赖的健康状态"
)
async def detailed_health_check(
    vector_db = Depends(get_vector_db),
    vectorization_service = Depends(get_vectorization_service),
    search_service = Depends(get_search_service),
    cache_manager = Depends(get_cache_manager)
):
    """详细健康检查"""
    try:
        current_time = time.time()
        uptime = current_time - service_start_time
        
        # 并行检查所有组件
        db_check, cache_check, vectorization_check, search_check = await asyncio.gather(
            check_database_health(vector_db),
            check_cache_health(cache_manager),
            check_vectorization_health(vectorization_service),
            check_search_health(search_service),
            return_exceptions=True
        )
        
        # 处理异常结果
        if isinstance(db_check, Exception):
            db_check = {"status": "unhealthy", "error": str(db_check)}
        if isinstance(cache_check, Exception):
            cache_check = {"status": "unhealthy", "error": str(cache_check)}
        if isinstance(vectorization_check, Exception):
            vectorization_check = {"status": "unhealthy", "error": str(vectorization_check)}
        if isinstance(search_check, Exception):
            search_check = {"status": "unhealthy", "error": str(search_check)}
        
        # 组装检查结果
        checks = {
            "database": db_check,
            "cache": cache_check,
            "vectorization": vectorization_check,
            "search": search_check
        }
        
        # 确定整体状态
        unhealthy_services = [name for name, check in checks.items() if check.get("status") != "healthy"]
        
        if not unhealthy_services:
            overall_status = "healthy"
        elif len(unhealthy_services) < len(checks) / 2:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        # 获取系统信息
        system_info = get_system_info()
        
        # 获取服务指标
        try:
            vectorization_stats = await vectorization_service.get_service_stats()
            search_stats = await search_service.get_service_stats()
            
            metrics = ServiceMetrics(
                total_requests=vectorization_stats.get("total_requests", 0) + search_stats.get("total_requests", 0),
                active_connections=0,  # 需要从连接池获取
                cache_hit_rate=search_stats.get("cache_hit_rate", 0.0),
                average_response_time=(
                    vectorization_stats.get("average_response_time", 0.0) + 
                    search_stats.get("average_response_time", 0.0)
                ) / 2,
                error_rate=(
                    vectorization_stats.get("error_rate", 0.0) + 
                    search_stats.get("error_rate", 0.0)
                ) / 2,
                vectorization_count=vectorization_stats.get("total_vectorizations", 0),
                search_count=search_stats.get("total_searches", 0),
                last_activity=max(
                    vectorization_stats.get("last_activity", 0.0),
                    search_stats.get("last_activity", 0.0)
                )
            )
        except Exception as e:
            logger.warning(f"获取服务指标失败: {e}")
            metrics = ServiceMetrics(
                total_requests=0,
                active_connections=0,
                cache_hit_rate=0.0,
                average_response_time=0.0,
                error_rate=0.0,
                vectorization_count=0,
                search_count=0,
                last_activity=0.0
            )
        
        # 依赖服务状态
        dependencies = {
            "postgresql": db_check,
            "redis": cache_check,
            "ollama": vectorization_check.get("details", {}).get("ollama", {"status": "unknown"}),
            "azure_openai": vectorization_check.get("details", {}).get("azure_openai", {"status": "unknown"})
        }
        
        health_status = HealthStatus(
            status=overall_status,
            timestamp=current_time,
            uptime=uptime,
            version="1.0.0",
            checks=checks
        )
        
        response = DetailedHealthResponse(
            health=health_status,
            system=system_info,
            metrics=metrics,
            dependencies=dependencies
        )
        
        # 根据状态返回适当的HTTP状态码
        if overall_status == "healthy":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response.dict()
            )
        elif overall_status == "degraded":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response.dict()
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response.dict()
            )
            
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"详细健康检查失败: {str(e)}"
        )


@router.get(
    "/ready",
    summary="就绪检查",
    description="检查服务是否准备好接收请求"
)
async def readiness_check(
    vector_db = Depends(get_vector_db),
    cache_manager = Depends(get_cache_manager)
):
    """就绪检查"""
    try:
        # 检查关键依赖
        db_check = await check_database_health(vector_db)
        cache_check = await check_cache_health(cache_manager)
        
        if db_check["status"] == "healthy" and cache_check["status"] == "healthy":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ready",
                    "timestamp": time.time(),
                    "checks": {
                        "database": db_check,
                        "cache": cache_check
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "timestamp": time.time(),
                    "checks": {
                        "database": db_check,
                        "cache": cache_check
                    }
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": time.time(),
                "error": str(e)
            }
        )


@router.get(
    "/live",
    summary="存活检查",
    description="检查服务是否存活"
)
async def liveness_check():
    """存活检查"""
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "alive",
                "timestamp": time.time(),
                "uptime": time.time() - service_start_time
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "dead",
                "timestamp": time.time(),
                "error": str(e)
            }
        )


@router.get(
    "/metrics",
    summary="Prometheus指标",
    description="获取Prometheus格式的指标数据"
)
async def prometheus_metrics(
    vectorization_service = Depends(get_vectorization_service),
    search_service = Depends(get_search_service)
):
    """Prometheus指标"""
    try:
        # 获取服务统计
        vectorization_stats = await vectorization_service.get_service_stats()
        search_stats = await search_service.get_service_stats()
        
        # 系统指标
        system_info = get_system_info()
        
        # 构建Prometheus格式的指标
        metrics = []
        
        # 服务指标
        metrics.append(f"ai_service_uptime_seconds {time.time() - service_start_time}")
        metrics.append(f"ai_service_vectorization_total {vectorization_stats.get('total_vectorizations', 0)}")
        metrics.append(f"ai_service_search_total {search_stats.get('total_searches', 0)}")
        metrics.append(f"ai_service_cache_hit_rate {search_stats.get('cache_hit_rate', 0.0)}")
        
        # 系统指标
        metrics.append(f"ai_service_cpu_usage_percent {system_info.cpu_usage}")
        metrics.append(f"ai_service_memory_usage_percent {system_info.memory_usage}")
        metrics.append(f"ai_service_disk_usage_percent {system_info.disk_usage}")
        
        # 响应时间指标
        metrics.append(f"ai_service_vectorization_response_time_seconds {vectorization_stats.get('average_response_time', 0.0)}")
        metrics.append(f"ai_service_search_response_time_seconds {search_stats.get('average_response_time', 0.0)}")
        
        # 错误率指标
        metrics.append(f"ai_service_vectorization_error_rate {vectorization_stats.get('error_rate', 0.0)}")
        metrics.append(f"ai_service_search_error_rate {search_stats.get('error_rate', 0.0)}")
        
        metrics_text = "\n".join(metrics) + "\n"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=metrics_text,
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"获取Prometheus指标失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f"# 获取指标失败: {str(e)}\n",
            media_type="text/plain"
        )


@router.get(
    "/version",
    summary="版本信息",
    description="获取AI服务的版本信息"
)
async def version_info():
    """版本信息"""
    try:
        import sys
        import platform
        from ai_service import __version__
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "service_name": "AI Service",
                "version": __version__,
                "python_version": sys.version,
                "platform": platform.platform(),
                "build_time": "2025-07-27",
                "git_commit": "unknown",
                "environment": get_settings().ENVIRONMENT
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"获取版本信息失败: {str(e)}"
            }
        )