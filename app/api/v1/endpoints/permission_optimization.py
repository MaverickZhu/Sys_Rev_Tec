"""权限查询优化API接口

提供权限查询性能优化相关的API端点
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.permission_query_optimizer import (
    get_permission_query_optimizer,
    batch_check_user_permissions,
    preload_user_permissions_data,
    optimize_single_permission_check
)
from app.db.permission_indexes import get_permission_index_optimizer
from app.core.permission_performance_monitor import get_permission_performance_monitor
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.permission import PermissionOptimizationResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求模型
class BatchPermissionCheckRequest(BaseModel):
    """批量权限检查请求"""
    user_ids: List[int]
    permission_codes: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "user_ids": [1, 2, 3],
                "permission_codes": ["user:read", "user:write", "admin:manage"]
            }
        }


class BatchResourcePermissionCheckRequest(BaseModel):
    """批量资源权限检查请求"""
    user_ids: List[int]
    resource_checks: List[Dict[str, str]]  # [{"resource_type": "document", "resource_id": "123", "operation": "read"}]
    
    class Config:
        schema_extra = {
            "example": {
                "user_ids": [1, 2, 3],
                "resource_checks": [
                    {"resource_type": "document", "resource_id": "123", "operation": "read"},
                    {"resource_type": "project", "resource_id": "456", "operation": "write"}
                ]
            }
        }


class PermissionOptimizationRequest(BaseModel):
    """权限优化请求"""
    user_id: int
    permission_code: str
    use_cache: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "permission_code": "user:read",
                "use_cache": True
            }
        }


# 响应模型
class BatchPermissionCheckResponse(BaseModel):
    """批量权限检查响应"""
    success: bool
    data: Dict[int, Dict[str, bool]]
    message: str
    query_time_ms: float
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "1": {"user:read": True, "user:write": False},
                    "2": {"user:read": True, "user:write": True}
                },
                "message": "批量权限检查完成",
                "query_time_ms": 15.5
            }
        }


class PermissionUsageAnalysisResponse(BaseModel):
    """权限使用分析响应"""
    success: bool
    data: Dict[str, Any]
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "permission_usage": [
                        {"code": "user:read", "name": "用户查看", "usage_count": 150}
                    ],
                    "role_usage": [
                        {"code": "admin", "name": "管理员", "user_count": 5}
                    ],
                    "query_stats": {
                        "total_queries": 1000,
                        "cache_hits": 800,
                        "db_queries": 200
                    }
                },
                "message": "权限使用分析完成"
            }
        }


class IndexOptimizationResponse(BaseModel):
    """索引优化响应"""
    success: bool
    data: Dict[str, Any]
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "success": ["CREATE INDEX idx_users_primary_role_id..."],
                    "failed": []
                },
                "message": "索引优化完成"
            }
        }


class UserPermissionSummaryResponse(BaseModel):
    """用户权限摘要响应"""
    success: bool
    data: Dict[str, Any]
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "user_id": 1,
                    "is_superuser": False,
                    "role_code": "admin",
                    "permission_count": 25,
                    "resource_permission_count": 10,
                    "permissions": ["user:read", "user:write"],
                    "resource_permissions": {}
                },
                "message": "用户权限摘要获取成功"
            }
        }


@router.post(
    "/batch-check-permissions",
    response_model=BatchPermissionCheckResponse,
    summary="批量权限检查",
    description="批量检查多个用户的多个权限，提供高性能的权限验证"
)
@require_permission("admin:permission:read")
def batch_check_permissions(
    request: BatchPermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """批量权限检查
    
    Args:
        request: 批量权限检查请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        BatchPermissionCheckResponse: 检查结果
    """
    try:
        start_time = datetime.utcnow()
        
        # 执行批量权限检查
        result = batch_check_user_permissions(
            user_ids=request.user_ids,
            permission_codes=request.permission_codes,
            db=db
        )
        
        end_time = datetime.utcnow()
        query_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"用户 {current_user.id} 执行批量权限检查: "
            f"{len(request.user_ids)} 用户, {len(request.permission_codes)} 权限, "
            f"耗时 {query_time_ms:.2f}ms"
        )
        
        return BatchPermissionCheckResponse(
            success=True,
            data=result,
            message=f"成功检查 {len(request.user_ids)} 个用户的 {len(request.permission_codes)} 个权限",
            query_time_ms=query_time_ms
        )
        
    except Exception as e:
        logger.error(f"批量权限检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量权限检查失败: {str(e)}"
        )


@router.post(
    "/batch-check-resource-permissions",
    response_model=BatchPermissionCheckResponse,
    summary="批量资源权限检查",
    description="批量检查多个用户的多个资源权限"
)
@require_permission("admin:permission:read")
def batch_check_resource_permissions(
    request: BatchResourcePermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """批量资源权限检查
    
    Args:
        request: 批量资源权限检查请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        BatchPermissionCheckResponse: 检查结果
    """
    try:
        start_time = datetime.utcnow()
        
        # 转换资源检查格式
        resource_checks = [
            (check["resource_type"], check["resource_id"], check["operation"])
            for check in request.resource_checks
        ]
        
        # 执行批量资源权限检查
        optimizer = get_permission_query_optimizer(db)
        result = optimizer.batch_check_resource_permissions(
            user_ids=request.user_ids,
            resource_checks=resource_checks
        )
        
        end_time = datetime.utcnow()
        query_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"用户 {current_user.id} 执行批量资源权限检查: "
            f"{len(request.user_ids)} 用户, {len(request.resource_checks)} 资源检查, "
            f"耗时 {query_time_ms:.2f}ms"
        )
        
        return BatchPermissionCheckResponse(
            success=True,
            data=result,
            message=f"成功检查 {len(request.user_ids)} 个用户的 {len(request.resource_checks)} 个资源权限",
            query_time_ms=query_time_ms
        )
        
    except Exception as e:
        logger.error(f"批量资源权限检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量资源权限检查失败: {str(e)}"
        )


@router.post(
    "/optimize-permission-check",
    response_model=PermissionOptimizationResponse,
    summary="优化权限检查",
    description="使用优化算法进行单个权限检查"
)
@require_permission("admin:permission:read")
def optimize_permission_check(
    request: PermissionOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """优化权限检查
    
    Args:
        request: 权限优化请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PermissionOptimizationResponse: 检查结果
    """
    try:
        start_time = datetime.utcnow()
        
        # 执行优化权限检查
        result = optimize_single_permission_check(
            user_id=request.user_id,
            permission_code=request.permission_code,
            db=db
        )
        
        end_time = datetime.utcnow()
        query_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"用户 {current_user.id} 执行优化权限检查: "
            f"用户 {request.user_id}, 权限 {request.permission_code}, "
            f"结果 {result}, 耗时 {query_time_ms:.2f}ms"
        )
        
        return PermissionOptimizationResponse(
            success=True,
            data={
                "user_id": request.user_id,
                "permission_code": request.permission_code,
                "has_permission": result,
                "query_time_ms": query_time_ms,
                "use_cache": request.use_cache
            },
            message="权限检查完成"
        )
        
    except Exception as e:
        logger.error(f"优化权限检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"优化权限检查失败: {str(e)}"
        )


@router.get(
    "/user/{user_id}/permission-summary",
    response_model=UserPermissionSummaryResponse,
    summary="获取用户权限摘要",
    description="获取指定用户的权限摘要信息"
)
@require_permission("admin:permission:read")
def get_user_permission_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户权限摘要
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        UserPermissionSummaryResponse: 权限摘要
    """
    try:
        optimizer = get_permission_query_optimizer(db)
        result = optimizer.get_user_permission_summary(user_id)
        
        logger.info(f"用户 {current_user.id} 获取用户 {user_id} 的权限摘要")
        
        return UserPermissionSummaryResponse(
            success=True,
            data=result,
            message="用户权限摘要获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取用户权限摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限摘要失败: {str(e)}"
        )


@router.get(
    "/usage-analysis",
    response_model=PermissionUsageAnalysisResponse,
    summary="权限使用分析",
    description="分析权限和角色的使用情况"
)
@require_permission("admin:permission:read")
def analyze_permission_usage(
    days: int = Query(30, description="分析天数", ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """权限使用分析
    
    Args:
        days: 分析天数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PermissionUsageAnalysisResponse: 分析结果
    """
    try:
        optimizer = get_permission_query_optimizer(db)
        result = optimizer.analyze_permission_usage(days)
        
        logger.info(f"用户 {current_user.id} 执行权限使用分析，分析天数: {days}")
        
        return PermissionUsageAnalysisResponse(
            success=True,
            data=result,
            message=f"权限使用分析完成（{days}天）"
        )
        
    except Exception as e:
        logger.error(f"权限使用分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"权限使用分析失败: {str(e)}"
        )


@router.get(
    "/index-suggestions",
    summary="获取索引优化建议",
    description="获取数据库索引优化建议"
)
@require_permission("admin:system:manage")
def get_index_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取索引优化建议
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Dict: 索引优化建议
    """
    try:
        optimizer = get_permission_query_optimizer(db)
        suggestions = optimizer.suggest_index_optimizations()
        
        logger.info(f"用户 {current_user.id} 获取索引优化建议")
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
                "count": len(suggestions)
            },
            "message": "索引优化建议获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取索引优化建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取索引优化建议失败: {str(e)}"
        )


@router.post(
    "/apply-index-optimizations",
    response_model=IndexOptimizationResponse,
    summary="应用索引优化",
    description="应用数据库索引优化"
)
@require_permission("admin:system:manage")
def apply_index_optimizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """应用索引优化
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        IndexOptimizationResponse: 优化结果
    """
    try:
        optimizer = get_permission_query_optimizer(db)
        result = optimizer.apply_index_optimizations()
        
        logger.info(
            f"用户 {current_user.id} 应用索引优化: "
            f"成功 {len(result.get('success', []))}, "
            f"失败 {len(result.get('failed', []))}"
        )
        
        return IndexOptimizationResponse(
            success=True,
            data=result,
            message="索引优化应用完成"
        )
        
    except Exception as e:
        logger.error(f"应用索引优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"应用索引优化失败: {str(e)}"
        )


@router.get(
    "/preload-users",
    summary="预加载用户权限",
    description="预加载指定用户的权限数据到缓存"
)
@require_permission("admin:permission:read")
def preload_users_permissions(
    user_ids: List[int] = Query(..., description="用户ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """预加载用户权限
    
    Args:
        user_ids: 用户ID列表
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Dict: 预加载结果
    """
    try:
        start_time = datetime.utcnow()
        
        # 预加载用户权限数据
        result = preload_user_permissions_data(user_ids, db)
        
        end_time = datetime.utcnow()
        query_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"用户 {current_user.id} 预加载 {len(user_ids)} 个用户的权限数据, "
            f"耗时 {query_time_ms:.2f}ms"
        )
        
        return {
            "success": True,
            "data": {
                "loaded_users": list(result.keys()),
                "user_count": len(result),
                "query_time_ms": query_time_ms
            },
            "message": f"成功预加载 {len(result)} 个用户的权限数据"
        }
        
    except Exception as e:
        logger.error(f"预加载用户权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预加载用户权限失败: {str(e)}"
        )


# ==================== 索引优化相关API ====================

@router.post(
    "/indexes/create",
    response_model=PermissionOptimizationResponse,
    summary="创建权限索引",
    description="创建权限相关的数据库索引以提升查询性能"
)
@require_permission("admin:system:manage")
def create_permission_indexes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建权限相关索引
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PermissionOptimizationResponse: 创建结果
    """
    try:
        index_optimizer = get_permission_index_optimizer(db)
        result = index_optimizer.create_permission_indexes()
        
        logger.info(
            f"用户 {current_user.id} 创建权限索引: "
            f"成功 {result['success_count']}/{result['total_count']}"
        )
        
        return PermissionOptimizationResponse(
            success=True,
            message=f"索引创建完成，成功创建 {result['success_count']}/{result['total_count']} 个索引",
            data=result
        )
        
    except Exception as e:
        logger.error(f"创建权限索引失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建权限索引失败: {str(e)}"
        )


@router.delete(
    "/indexes",
    response_model=PermissionOptimizationResponse,
    summary="删除权限索引",
    description="删除权限相关的数据库索引"
)
@require_permission("admin:system:manage")
def drop_permission_indexes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除权限相关索引
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PermissionOptimizationResponse: 删除结果
    """
    try:
        index_optimizer = get_permission_index_optimizer(db)
        result = index_optimizer.drop_permission_indexes()
        
        logger.info(
            f"用户 {current_user.id} 删除权限索引: "
            f"成功删除 {result['success_count']} 个索引"
        )
        
        return PermissionOptimizationResponse(
            success=True,
            message=f"索引删除完成，成功删除 {result['success_count']} 个索引",
            data=result
        )
        
    except Exception as e:
        logger.error(f"删除权限索引失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除权限索引失败: {str(e)}"
        )


@router.get(
    "/indexes/analyze",
    response_model=PermissionOptimizationResponse,
    summary="分析权限索引",
    description="分析权限查询的索引使用情况"
)
@require_permission("admin:system:manage")
def analyze_permission_indexes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分析权限查询索引
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PermissionOptimizationResponse: 分析结果
    """
    try:
        index_optimizer = get_permission_index_optimizer(db)
        result = index_optimizer.analyze_permission_queries()
        
        logger.info(f"用户 {current_user.id} 分析权限查询索引")
        
        return PermissionOptimizationResponse(
            success=True,
            message="权限查询索引分析完成",
            data=result
        )
        
    except Exception as e:
        logger.error(f"分析权限查询索引失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析权限查询索引失败: {str(e)}"
        )


@router.post(
    "/database/optimize",
    response_model=PermissionOptimizationResponse,
    summary="优化数据库",
    description="执行数据库优化操作（VACUUM、ANALYZE、REINDEX）"
)
@require_permission("admin:system:manage")
def optimize_database(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """优化数据库
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PermissionOptimizationResponse: 优化结果
    """
    try:
        index_optimizer = get_permission_index_optimizer(db)
        result = index_optimizer.optimize_database()
        
        logger.info(
            f"用户 {current_user.id} 执行数据库优化: "
            f"{'成功' if result['success'] else '失败'}"
        )
        
        return PermissionOptimizationResponse(
            success=result["success"],
            message="数据库优化完成" if result["success"] else "数据库优化失败",
            data=result
        )
        
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库优化失败: {str(e)}"
        )


# ==================== 性能监控相关API ====================

@router.get(
    "/performance/stats",
    summary="获取性能统计",
    description="获取权限查询性能统计信息"
)
@require_permission("admin:system:monitor")
def get_performance_stats(
    query_type: Optional[str] = Query(None, description="查询类型"),
    window_minutes: int = Query(60, description="时间窗口（分钟）", ge=1, le=1440),
    current_user: User = Depends(get_current_active_user)
):
    """获取性能统计
    
    Args:
        query_type: 查询类型
        window_minutes: 时间窗口（分钟）
        current_user: 当前用户
        
    Returns:
        Dict: 性能统计信息
    """
    try:
        monitor = get_permission_performance_monitor()
        stats = monitor.get_performance_stats(query_type, window_minutes)
        
        logger.info(
            f"用户 {current_user.id} 获取性能统计: "
            f"类型={query_type or 'all'}, 窗口={window_minutes}分钟"
        )
        
        return {
            "success": True,
            "data": stats,
            "message": "性能统计获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能统计失败: {str(e)}"
        )


@router.get(
    "/performance/slow-queries",
    summary="获取慢查询",
    description="获取权限查询中的慢查询列表"
)
@require_permission("admin:system:monitor")
def get_slow_queries(
    threshold: float = Query(1.0, description="慢查询阈值（秒）", ge=0.1),
    limit: int = Query(50, description="返回数量限制", ge=1, le=500),
    current_user: User = Depends(get_current_active_user)
):
    """获取慢查询列表
    
    Args:
        threshold: 慢查询阈值（秒）
        limit: 返回数量限制
        current_user: 当前用户
        
    Returns:
        Dict: 慢查询列表
    """
    try:
        monitor = get_permission_performance_monitor()
        slow_queries = monitor.get_slow_queries(threshold, limit)
        
        logger.info(
            f"用户 {current_user.id} 获取慢查询: "
            f"阈值={threshold}s, 限制={limit}, 找到={len(slow_queries)}条"
        )
        
        return {
            "success": True,
            "data": {
                "slow_queries": slow_queries,
                "count": len(slow_queries),
                "threshold": threshold
            },
            "message": f"找到 {len(slow_queries)} 条慢查询"
        }
        
    except Exception as e:
        logger.error(f"获取慢查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取慢查询失败: {str(e)}"
        )


@router.get(
    "/performance/trends",
    summary="获取性能趋势",
    description="获取权限查询性能趋势数据"
)
@require_permission("admin:system:monitor")
def get_performance_trends(
    hours: int = Query(24, description="时间范围（小时）", ge=1, le=168),
    interval_minutes: int = Query(60, description="时间间隔（分钟）", ge=5, le=1440),
    current_user: User = Depends(get_current_active_user)
):
    """获取性能趋势
    
    Args:
        hours: 时间范围（小时）
        interval_minutes: 时间间隔（分钟）
        current_user: 当前用户
        
    Returns:
        Dict: 性能趋势数据
    """
    try:
        monitor = get_permission_performance_monitor()
        trends = monitor.get_query_trends(hours, interval_minutes)
        
        logger.info(
            f"用户 {current_user.id} 获取性能趋势: "
            f"范围={hours}小时, 间隔={interval_minutes}分钟"
        )
        
        return {
            "success": True,
            "data": trends,
            "message": "性能趋势获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取性能趋势失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能趋势失败: {str(e)}"
        )


@router.post(
    "/performance/reset",
    summary="重置性能统计",
    description="重置权限查询性能统计数据"
)
@require_permission("admin:system:manage")
def reset_performance_stats(
    current_user: User = Depends(get_current_active_user)
):
    """重置性能统计
    
    Args:
        current_user: 当前用户
        
    Returns:
        Dict: 重置结果
    """
    try:
        monitor = get_permission_performance_monitor()
        monitor.reset_stats()
        
        logger.info(f"用户 {current_user.id} 重置性能统计数据")
        
        return {
            "success": True,
            "message": "性能统计数据已重置"
        }
        
    except Exception as e:
        logger.error(f"重置性能统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置性能统计失败: {str(e)}"
        )


@router.get(
    "/performance/export",
    summary="导出性能数据",
    description="导出权限查询性能监控数据"
)
@require_permission("admin:system:monitor")
def export_performance_data(
    format: str = Query("json", description="导出格式"),
    current_user: User = Depends(get_current_active_user)
):
    """导出性能数据
    
    Args:
        format: 导出格式
        current_user: 当前用户
        
    Returns:
        Dict: 导出的性能数据
    """
    try:
        monitor = get_permission_performance_monitor()
        data = monitor.export_metrics(format)
        
        logger.info(
            f"用户 {current_user.id} 导出性能数据: "
            f"格式={format}, 查询数={data['total_queries']}"
        )
        
        return {
            "success": True,
            "data": data,
            "message": "性能数据导出成功"
        }
        
    except Exception as e:
        logger.error(f"导出性能数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出性能数据失败: {str(e)}"
        )