from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.user import User
from app.api.deps import get_current_user
from app.services.cache_service import cache_service
from app.middleware.rate_limit import loose_rate_limit, moderate_rate_limit
from app.core.logging import logger
from app.core.config import settings
from app.schemas.response import ResponseModel

router = APIRouter()


class ClearCacheRequest(BaseModel):
    pattern: str = "*"
    prefix: str = "app"


@router.get(
    "/stats",
    summary="获取缓存统计信息",
    description="获取当前缓存的统计信息，包括键数量、内存使用等",
    response_model=ResponseModel[Dict[str, Any]]
)
async def get_cache_stats(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> ResponseModel[Dict[str, Any]]:
    """
    获取缓存统计信息
    
    - **返回**: 缓存统计信息和健康状态
    - **权限**: 需要用户登录认证
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200,
            message="Cache is disabled",
            data={"cache_enabled": False}
        )
    
    try:
        stats = await cache_service.get_stats()
        health = await cache_service.health_check()
        
        return ResponseModel(
            code=200,
            message="Cache statistics retrieved successfully",
            data={
                "cache_enabled": True,
                "health": health,
                "statistics": stats
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.post(
    "/clear",
    summary="清除缓存",
    description="清除指定模式的缓存数据",
    response_model=ResponseModel[Dict[str, Any]]
)
async def clear_cache(
    request: Request,
    cache_request: ClearCacheRequest,
    current_user: User = Depends(get_current_user)
) -> ResponseModel[Dict[str, Any]]:
    """
    清除缓存
    
    - **pattern**: 缓存键模式（可选，如 'ocr:*' 清除所有OCR相关缓存）
    - **返回**: 清除操作结果
    - **权限**: 需要用户登录认证
    """
    if not settings.CACHE_ENABLED:
        return ResponseModel(
            code=200,
            message="Cache is disabled",
            data={"cache_enabled": False}
        )
    
    try:
        cleared_count = await cache_service.clear_pattern(cache_request.pattern, cache_request.prefix)
        
        logger.info(f"User {current_user.id} cleared {cleared_count} cache entries with pattern: {cache_request.pattern}")
        
        return ResponseModel(
            code=200,
            message=f"Successfully cleared {cleared_count} cache entries",
            data={
                "pattern": cache_request.pattern,
                "prefix": cache_request.prefix,
                "cleared_count": cleared_count
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get(
    "/health",
    summary="缓存健康检查",
    description="检查Redis缓存服务的健康状态",
    response_model=ResponseModel[Dict[str, Any]]
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
            data={"cache_enabled": False, "healthy": True}
        )
    
    try:
        health = await cache_service.health_check()
        is_healthy = health.get("status") == "healthy"
        
        return ResponseModel(
            code=200 if is_healthy else 503,
            message="Cache health check completed",
            data={
                "healthy": is_healthy,
                "status": health.get("status", "unknown"),
                "message": health.get("message", "No message"),
                "response_time_ms": health.get("response_time_ms")
            }
        )
    except Exception as e:
        return ResponseModel(
            code=503,
            message="Cache health check failed",
            data={
                "healthy": False,
                "error": str(e)
            }
        )