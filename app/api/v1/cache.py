from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.schemas.response import ResponseModel
from app.services.cache_service import cache_service
from app.services.cache_manager import cache_manager
from app.services.cache_monitor import get_cache_monitor
from app.services.cache_optimizer import cache_optimizer

router = APIRouter()


class ClearCacheRequest(BaseModel):
    pattern: str = "*"
    prefix: str = "app"


class CacheSetRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None
    cache_type: str = "default"


class CacheGetRequest(BaseModel):
    key: str
    cache_type: str = "default"


class BatchCacheRequest(BaseModel):
    keys: List[str]
    cache_type: str = "default"


class BatchCacheSetRequest(BaseModel):
    items: Dict[str, Any]
    ttl: Optional[int] = None
    cache_type: str = "default"


class WarmupCacheRequest(BaseModel):
    cache_type: str = "default"
    data: Dict[str, Any]


class OptimizationRequest(BaseModel):
    optimization_type: Optional[str] = None
    force: bool = False


@router.get(
    "/stats",
    summary="获取缓存统计信息",
    description="获取当前缓存的统计信息，包括键数量、内存使用等",
    response_model=ResponseModel[Dict[str, Any]],
)
async def get_cache_stats(request: Request) -> ResponseModel[Dict[str, Any]]:
    """
    获取缓存统计信息

    - **返回**: 缓存统计信息和健康状态
    - **权限**: 公开接口，无需认证
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        stats = cache_service.get_stats()
        health = cache_service.health_check()

        return ResponseModel(
            code=200,
            message="Cache statistics retrieved successfully",
            data={"cache_enabled": True, "health": health, "statistics": stats},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}",
        )


@router.post(
    "/clear",
    summary="清除缓存",
    description="清除指定模式的缓存数据",
    response_model=ResponseModel[Dict[str, Any]],
)
async def clear_cache(
    request: Request, cache_request: ClearCacheRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    清除缓存

    - **pattern**: 缓存键模式（可选，如 'ocr:*' 清除所有OCR相关缓存）
    - **返回**: 清除操作结果
    - **权限**: 公开接口，无需认证
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        cleared_count = cache_service.clear_pattern(
            cache_request.pattern, cache_request.prefix
        )

        logger.info(
            f"Cleared {cleared_count} cache entries with pattern: "
            f"{cache_request.pattern}"
        )

        return ResponseModel(
            code=200,
            message=f"Successfully cleared {cleared_count} cache entries",
            data={
                "pattern": cache_request.pattern,
                "prefix": cache_request.prefix,
                "cleared_count": cleared_count,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )


@router.get(
    "/health",
    summary="缓存健康检查",
    description="检查Redis缓存服务的健康状态",
    response_model=ResponseModel[Dict[str, Any]],
)
async def get_cache_health(request: Request) -> ResponseModel[Dict[str, Any]]:
    """
    缓存健康检查

    - **返回**: 缓存服务健康状态
    - **权限**: 公开接口，无需认证
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200,
            message="Cache is disabled",
            data={"cache_enabled": False, "healthy": True},
        )

    try:
        health = cache_service.health_check()
        is_healthy = health.get("status") == "healthy"

        return ResponseModel(
            code=200 if is_healthy else 503,
            message="Cache health check completed",
            data={
                "healthy": is_healthy,
                "status": health.get("status", "unknown"),
                "message": health.get("message", "No message"),
                "response_time_ms": health.get("response_time_ms"),
            },
        )
    except Exception as e:
        return ResponseModel(
            code=503,
            message="Cache health check failed",
            data={"healthy": False, "error": str(e)},
        )


@router.post(
    "/set",
    summary="设置缓存",
    description="设置缓存键值对",
    response_model=ResponseModel[Dict[str, Any]],
)
async def set_cache(
    request: Request, cache_request: CacheSetRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    设置缓存

    - **key**: 缓存键
    - **value**: 缓存值
    - **ttl**: 过期时间（秒）
    - **cache_type**: 缓存类型
    - **返回**: 设置操作结果
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        success = await cache_manager.set(
            cache_request.key,
            cache_request.value,
            ttl=cache_request.ttl,
            cache_type=cache_request.cache_type,
        )

        return ResponseModel(
            code=200,
            message="Cache set successfully" if success else "Failed to set cache",
            data={
                "key": cache_request.key,
                "success": success,
                "cache_type": cache_request.cache_type,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set cache: {str(e)}",
        )


@router.post(
    "/get",
    summary="获取缓存",
    description="获取指定键的缓存值",
    response_model=ResponseModel[Dict[str, Any]],
)
async def get_cache(
    request: Request, cache_request: CacheGetRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    获取缓存

    - **key**: 缓存键
    - **cache_type**: 缓存类型
    - **返回**: 缓存值和元数据
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        value = await cache_manager.get(
            cache_request.key, cache_type=cache_request.cache_type
        )

        return ResponseModel(
            code=200,
            message="Cache retrieved successfully",
            data={
                "key": cache_request.key,
                "value": value,
                "found": value is not None,
                "cache_type": cache_request.cache_type,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache: {str(e)}",
        )


@router.post(
    "/batch/set",
    summary="批量设置缓存",
    description="批量设置多个缓存键值对",
    response_model=ResponseModel[Dict[str, Any]],
)
async def batch_set_cache(
    request: Request, cache_request: BatchCacheSetRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    批量设置缓存

    - **items**: 键值对字典
    - **ttl**: 过期时间（秒）
    - **cache_type**: 缓存类型
    - **返回**: 批量设置操作结果
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        results = await cache_manager.batch_set(
            cache_request.items,
            ttl=cache_request.ttl,
            cache_type=cache_request.cache_type,
        )

        success_count = sum(1 for r in results.values() if r)
        total_count = len(results)

        return ResponseModel(
            code=200,
            message=f"Batch set completed: {success_count}/{total_count} successful",
            data={
                "results": results,
                "success_count": success_count,
                "total_count": total_count,
                "cache_type": cache_request.cache_type,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch set cache: {str(e)}",
        )


@router.post(
    "/batch/get",
    summary="批量获取缓存",
    description="批量获取多个缓存值",
    response_model=ResponseModel[Dict[str, Any]],
)
async def batch_get_cache(
    request: Request, cache_request: BatchCacheRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    批量获取缓存

    - **keys**: 缓存键列表
    - **cache_type**: 缓存类型
    - **返回**: 批量获取结果
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        results = await cache_manager.batch_get(
            cache_request.keys, cache_type=cache_request.cache_type
        )

        found_count = sum(1 for v in results.values() if v is not None)
        total_count = len(results)

        return ResponseModel(
            code=200,
            message=f"Batch get completed: {found_count}/{total_count} found",
            data={
                "results": results,
                "found_count": found_count,
                "total_count": total_count,
                "cache_type": cache_request.cache_type,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch get cache: {str(e)}",
        )


@router.get(
    "/metrics",
    summary="获取缓存性能指标",
    description="获取缓存系统的详细性能指标",
    response_model=ResponseModel[Dict[str, Any]],
)
async def get_cache_metrics(request: Request) -> ResponseModel[Dict[str, Any]]:
    """
    获取缓存性能指标

    - **返回**: 详细的性能指标数据
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        monitor = get_cache_monitor()
        current_metrics = await monitor.get_current_metrics()
        historical_metrics = await monitor.get_historical_metrics()
        system_status = await cache_manager.get_system_status()

        return ResponseModel(
            code=200,
            message="Cache metrics retrieved successfully",
            data={
                "current_metrics": current_metrics,
                "historical_metrics": historical_metrics,
                "system_status": system_status,
                "timestamp": current_metrics.timestamp.isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache metrics: {str(e)}",
        )


@router.get(
    "/report",
    summary="获取缓存性能报告",
    description="获取缓存系统的性能分析报告",
    response_model=ResponseModel[Dict[str, Any]],
)
async def get_cache_report(request: Request) -> ResponseModel[Dict[str, Any]]:
    """
    获取缓存性能报告

    - **返回**: 性能分析报告和优化建议
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        monitor = get_cache_monitor()
        report = await monitor.generate_performance_report()

        return ResponseModel(
            code=200,
            message="Cache performance report generated successfully",
            data={
                "report": {
                    "performance_score": report.performance_score,
                    "recommendations": report.recommendations,
                    "period_start": report.period_start.isoformat(),
                    "period_end": report.period_end.isoformat(),
                    "total_requests": report.total_requests,
                    "avg_hit_rate": report.avg_hit_rate,
                    "avg_response_time": report.avg_response_time,
                    "peak_memory_usage": report.peak_memory_usage,
                }
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cache report: {str(e)}",
        )


@router.post(
    "/warmup",
    summary="缓存预热",
    description="预热指定类型的缓存数据",
    response_model=ResponseModel[Dict[str, Any]],
)
async def warmup_cache(
    request: Request, warmup_request: WarmupCacheRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    缓存预热

    - **cache_type**: 缓存类型
    - **data**: 预热数据
    - **返回**: 预热操作结果
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        success = await cache_manager.warmup_cache(
            warmup_request.cache_type, warmup_request.data
        )

        return ResponseModel(
            code=200,
            message="Cache warmup completed successfully" if success else "Cache warmup failed",
            data={
                "cache_type": warmup_request.cache_type,
                "success": success,
                "data_count": len(warmup_request.data),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warmup cache: {str(e)}",
        )


@router.post(
    "/optimize",
    summary="触发缓存优化",
    description="手动触发缓存性能优化",
    response_model=ResponseModel[Dict[str, Any]],
)
async def trigger_optimization(
    request: Request, opt_request: OptimizationRequest
) -> ResponseModel[Dict[str, Any]]:
    """
    触发缓存优化

    - **optimization_type**: 优化类型（可选）
    - **force**: 是否强制执行
    - **返回**: 优化任务信息
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        task_id = await cache_manager.trigger_optimization(
            optimization_type=opt_request.optimization_type,
            force=opt_request.force,
        )

        return ResponseModel(
            code=200,
            message="Optimization task triggered successfully",
            data={
                "task_id": task_id,
                "optimization_type": opt_request.optimization_type,
                "force": opt_request.force,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger optimization: {str(e)}",
        )


@router.get(
    "/optimization/status",
    summary="获取优化任务状态",
    description="获取当前优化任务的状态信息",
    response_model=ResponseModel[Dict[str, Any]],
)
async def get_optimization_status(request: Request) -> ResponseModel[Dict[str, Any]]:
    """
    获取优化任务状态

    - **返回**: 优化任务状态列表
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        tasks = await cache_manager.get_optimization_tasks()

        return ResponseModel(
            code=200,
            message="Optimization tasks retrieved successfully",
            data={
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "optimization_type": task.optimization_type,
                        "status": task.status,
                        "created_at": task.created_at.isoformat(),
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "result": task.result,
                        "error": task.error,
                    }
                    for task in tasks
                ],
                "total_tasks": len(tasks),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimization status: {str(e)}",
        )


@router.get(
    "/export",
    summary="导出缓存指标",
    description="导出缓存性能指标数据",
    response_model=ResponseModel[Dict[str, Any]],
)
async def export_cache_metrics(request: Request) -> ResponseModel[Dict[str, Any]]:
    """
    导出缓存指标

    - **返回**: 导出的指标数据文件路径
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200, message="Cache is disabled", data={"cache_enabled": False}
        )

    try:
        file_path = await cache_manager.export_metrics()

        monitor = get_cache_monitor()
        current_metrics = monitor.get_current_metrics()
        
        return ResponseModel(
            code=200,
            message="Cache metrics exported successfully",
            data={
                "file_path": file_path,
                "export_time": current_metrics.timestamp.isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export cache metrics: {str(e)}",
        )
