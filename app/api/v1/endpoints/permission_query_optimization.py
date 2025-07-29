"""权限查询性能优化API

提供权限查询性能优化相关的API接口
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.core.permission_query_optimizer import get_permission_query_optimizer
from app.core.permission_preloader import get_permission_preloader
from app.core.permission_batch_checker import (
    get_permission_batch_checker, 
    BatchCheckRequest, 
    CheckMode, 
    CheckStrategy
)
from app.core.permissions import require_permission

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic模型
class BatchPermissionCheckRequest(BaseModel):
    """批量权限检查请求"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    permission_codes: List[str] = Field(..., description="权限代码列表")
    mode: str = Field(default="balanced", description="检查模式: fast, accurate, balanced")
    strategy: str = Field(default="batch_optimized", description="检查策略: parallel, sequential, batch_optimized")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    preload_missing: bool = Field(default=True, description="是否预加载缺失数据")


class ResourcePermissionCheckRequest(BaseModel):
    """资源权限检查请求"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    resource_checks: List[Dict[str, str]] = Field(..., description="资源检查列表")
    mode: str = Field(default="balanced", description="检查模式")


class PreloadRequest(BaseModel):
    """预加载请求"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    permission_codes: Optional[List[str]] = Field(None, description="权限代码列表")
    priority: int = Field(default=1, ge=1, le=5, description="优先级(1-5)")
    requester: str = Field(default="api", description="请求者标识")


class OptimizationConfigUpdate(BaseModel):
    """优化配置更新"""
    max_batch_size: Optional[int] = Field(None, description="最大批量大小")
    max_users_per_batch: Optional[int] = Field(None, description="每批最大用户数")
    max_permissions_per_batch: Optional[int] = Field(None, description="每批最大权限数")
    cache_ttl: Optional[int] = Field(None, description="缓存TTL")
    enable_preloading: Optional[bool] = Field(None, description="启用预加载")
    parallel_threshold: Optional[int] = Field(None, description="并行处理阈值")
    optimization_level: Optional[int] = Field(None, ge=1, le=3, description="优化级别")


@router.post("/batch-check", summary="批量权限检查")
@require_permission("admin:system:monitor")
async def batch_check_permissions(
    request: BatchPermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量检查用户权限
    
    支持多种检查模式和策略，提供高性能的批量权限验证
    """
    logger.info(f"用户 {current_user.username} 请求批量权限检查: {len(request.user_ids)} 用户, {len(request.permission_codes)} 权限")
    
    try:
        # 验证模式和策略
        try:
            mode = CheckMode(request.mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的检查模式: {request.mode}")
        
        try:
            strategy = CheckStrategy(request.strategy)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的检查策略: {request.strategy}")
        
        # 创建批量检查请求
        batch_request = BatchCheckRequest(
            user_ids=request.user_ids,
            permission_codes=request.permission_codes,
            mode=mode,
            strategy=strategy,
            use_cache=request.use_cache,
            preload_missing=request.preload_missing
        )
        
        # 执行批量检查
        checker = get_permission_batch_checker(db)
        result = checker.batch_check(batch_request)
        
        return {
            "success": True,
            "message": "批量权限检查完成",
            "data": {
                "user_permissions": result.user_permissions,
                "execution_time": result.execution_time,
                "cache_hit_rate": result.cache_hit_rate,
                "total_checks": result.total_checks,
                "successful_checks": result.successful_checks,
                "metadata": result.metadata
            }
        }
        
    except Exception as e:
        logger.error(f"批量权限检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量权限检查失败: {str(e)}")


@router.post("/batch-check-resources", summary="批量资源权限检查")
@require_permission("admin:system:monitor")
async def batch_check_resource_permissions(
    request: ResourcePermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量检查用户资源权限
    
    检查用户对特定资源的操作权限
    """
    logger.info(f"用户 {current_user.username} 请求批量资源权限检查: {len(request.user_ids)} 用户, {len(request.resource_checks)} 资源")
    
    try:
        # 转换资源检查格式
        resource_checks = []
        for check in request.resource_checks:
            resource_checks.append((
                check.get("resource_type", ""),
                check.get("resource_id", ""),
                check.get("operation", "")
            ))
        
        # 验证模式
        try:
            mode = CheckMode(request.mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的检查模式: {request.mode}")
        
        # 创建批量检查请求
        batch_request = BatchCheckRequest(
            user_ids=request.user_ids,
            permission_codes=[],
            resource_checks=resource_checks,
            mode=mode
        )
        
        # 执行批量检查
        checker = get_permission_batch_checker(db)
        result = checker.batch_check(batch_request)
        
        return {
            "success": True,
            "message": "批量资源权限检查完成",
            "data": {
                "resource_permissions": result.resource_permissions,
                "execution_time": result.execution_time,
                "cache_hit_rate": result.cache_hit_rate,
                "total_checks": result.total_checks,
                "metadata": result.metadata
            }
        }
        
    except Exception as e:
        logger.error(f"批量资源权限检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量资源权限检查失败: {str(e)}")


@router.post("/preload", summary="请求权限预加载")
@require_permission("admin:system:manage")
async def request_permission_preload(
    request: PreloadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """请求权限数据预加载
    
    将用户权限数据预加载到缓存中，提升后续查询性能
    """
    logger.info(f"用户 {current_user.username} 请求权限预加载: {len(request.user_ids)} 用户")
    
    try:
        preloader = get_permission_preloader(db)
        
        success = preloader.request_preload(
            user_ids=request.user_ids,
            permission_codes=request.permission_codes,
            priority=request.priority,
            requester=f"api:{current_user.username}"
        )
        
        if success:
            return {
                "success": True,
                "message": f"权限预加载请求已提交: {len(request.user_ids)} 用户",
                "data": {
                    "user_count": len(request.user_ids),
                    "permission_count": len(request.permission_codes) if request.permission_codes else 0,
                    "priority": request.priority,
                    "requested_at": datetime.utcnow().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=500, detail="预加载请求提交失败")
            
    except Exception as e:
        logger.error(f"权限预加载请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"权限预加载请求失败: {str(e)}")


@router.post("/auto-preload", summary="自动预加载")
@require_permission("admin:system:manage")
async def auto_preload_by_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """基于访问模式自动预加载
    
    分析用户访问模式，自动预加载频繁访问的用户权限数据
    """
    logger.info(f"用户 {current_user.username} 请求自动预加载")
    
    try:
        preloader = get_permission_preloader(db)
        result = preloader.auto_preload_by_patterns()
        
        return {
            "success": True,
            "message": "自动预加载完成",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"自动预加载失败: {e}")
        raise HTTPException(status_code=500, detail=f"自动预加载失败: {str(e)}")


@router.get("/preload/stats", summary="获取预加载统计")
@require_permission("admin:system:monitor")
async def get_preload_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限预加载统计信息"""
    logger.info(f"用户 {current_user.username} 查询预加载统计")
    
    try:
        preloader = get_permission_preloader(db)
        stats = preloader.get_preload_stats()
        
        return {
            "success": True,
            "message": "获取预加载统计成功",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取预加载统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预加载统计失败: {str(e)}")


@router.get("/preload/patterns", summary="获取访问模式分析")
@require_permission("admin:system:monitor")
async def get_access_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户访问模式分析结果"""
    logger.info(f"用户 {current_user.username} 查询访问模式")
    
    try:
        preloader = get_permission_preloader(db)
        patterns = preloader.analyze_access_patterns()
        
        return {
            "success": True,
            "message": "获取访问模式分析成功",
            "data": patterns
        }
        
    except Exception as e:
        logger.error(f"获取访问模式分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取访问模式分析失败: {str(e)}")


@router.get("/batch-check/stats", summary="获取批量检查统计")
@require_permission("admin:system:monitor")
async def get_batch_check_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取批量权限检查统计信息"""
    logger.info(f"用户 {current_user.username} 查询批量检查统计")
    
    try:
        checker = get_permission_batch_checker(db)
        stats = checker.get_batch_check_stats()
        
        return {
            "success": True,
            "message": "获取批量检查统计成功",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取批量检查统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取批量检查统计失败: {str(e)}")


@router.get("/query-optimizer/stats", summary="获取查询优化器统计")
@require_permission("admin:system:monitor")
async def get_query_optimizer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限查询优化器统计信息"""
    logger.info(f"用户 {current_user.username} 查询优化器统计")
    
    try:
        optimizer = get_permission_query_optimizer(db)
        
        return {
            "success": True,
            "message": "获取查询优化器统计成功",
            "data": {
                "query_stats": optimizer.query_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取查询优化器统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取查询优化器统计失败: {str(e)}")


@router.get("/usage-analysis", summary="权限使用分析")
@require_permission("admin:system:monitor")
async def analyze_permission_usage(
    days: int = Query(default=30, ge=1, le=365, description="分析天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分析权限使用情况
    
    分析指定天数内的权限使用频率和模式
    """
    logger.info(f"用户 {current_user.username} 请求权限使用分析: {days} 天")
    
    try:
        optimizer = get_permission_query_optimizer(db)
        analysis = optimizer.analyze_permission_usage(days)
        
        return {
            "success": True,
            "message": f"权限使用分析完成 ({days} 天)",
            "data": analysis
        }
        
    except Exception as e:
        logger.error(f"权限使用分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"权限使用分析失败: {str(e)}")


@router.get("/index-suggestions", summary="获取索引优化建议")
@require_permission("admin:system:manage")
async def get_index_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据库索引优化建议"""
    logger.info(f"用户 {current_user.username} 查询索引优化建议")
    
    try:
        optimizer = get_permission_query_optimizer(db)
        suggestions = optimizer.suggest_index_optimizations()
        
        return {
            "success": True,
            "message": "获取索引优化建议成功",
            "data": {
                "suggestions": suggestions,
                "suggestion_count": len(suggestions),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取索引优化建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取索引优化建议失败: {str(e)}")


@router.post("/apply-index-optimizations", summary="应用索引优化")
@require_permission("admin:system:manage")
async def apply_index_optimizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """应用数据库索引优化
    
    警告：此操作会修改数据库结构，请谨慎使用
    """
    logger.warning(f"用户 {current_user.username} 请求应用索引优化")
    
    try:
        optimizer = get_permission_query_optimizer(db)
        result = optimizer.apply_index_optimizations()
        
        return {
            "success": True,
            "message": "索引优化应用完成",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"应用索引优化失败: {e}")
        raise HTTPException(status_code=500, detail=f"应用索引优化失败: {str(e)}")


@router.put("/config", summary="更新优化配置")
@require_permission("admin:system:manage")
async def update_optimization_config(
    config: OptimizationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新权限查询优化配置"""
    logger.info(f"用户 {current_user.username} 更新优化配置")
    
    try:
        # 更新批量检查器配置
        checker = get_permission_batch_checker(db)
        config_dict = config.dict(exclude_unset=True)
        
        if config_dict:
            result = checker.update_config(config_dict)
            
            return {
                "success": True,
                "message": "优化配置更新成功",
                "data": result
            }
        else:
            return {
                "success": True,
                "message": "没有配置需要更新",
                "data": {"current_config": checker.config}
            }
        
    except Exception as e:
        logger.error(f"更新优化配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新优化配置失败: {str(e)}")


@router.post("/reset-stats", summary="重置统计信息")
@require_permission("admin:system:manage")
async def reset_optimization_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置权限查询优化统计信息"""
    logger.info(f"用户 {current_user.username} 重置优化统计")
    
    try:
        # 重置批量检查器统计
        checker = get_permission_batch_checker(db)
        batch_result = checker.reset_stats()
        
        # 清除预加载器访问模式
        preloader = get_permission_preloader(db)
        pattern_result = preloader.clear_patterns()
        
        return {
            "success": True,
            "message": "优化统计信息已重置",
            "data": {
                "batch_checker": batch_result,
                "preloader_patterns": pattern_result,
                "reset_time": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"重置优化统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置优化统计失败: {str(e)}")


@router.get("/user/{user_id}/summary", summary="获取用户权限摘要")
@require_permission("admin:system:monitor")
async def get_user_permission_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的权限摘要信息"""
    logger.info(f"用户 {current_user.username} 查询用户 {user_id} 权限摘要")
    
    try:
        optimizer = get_permission_query_optimizer(db)
        summary = optimizer.get_user_permission_summary(user_id)
        
        return {
            "success": True,
            "message": "获取用户权限摘要成功",
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"获取用户权限摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户权限摘要失败: {str(e)}")


@router.get("/health", summary="优化系统健康检查")
async def optimization_health_check(
    db: Session = Depends(get_db)
):
    """权限查询优化系统健康检查"""
    try:
        # 检查各组件状态
        optimizer = get_permission_query_optimizer(db)
        checker = get_permission_batch_checker(db)
        preloader = get_permission_preloader(db)
        
        # 获取基本统计信息
        optimizer_stats = optimizer.query_stats
        checker_stats = checker.get_batch_check_stats()
        preloader_stats = preloader.get_preload_stats()
        
        return {
            "success": True,
            "message": "权限查询优化系统运行正常",
            "data": {
                "status": "healthy",
                "components": {
                    "query_optimizer": {
                        "status": "active",
                        "total_queries": optimizer_stats.get('total_queries', 0)
                    },
                    "batch_checker": {
                        "status": "active",
                        "total_batch_checks": checker_stats.get('total_batch_checks', 0)
                    },
                    "preloader": {
                        "status": "active",
                        "total_requests": preloader_stats.get('total_requests', 0)
                    }
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"优化系统健康检查失败: {e}")
        return {
            "success": False,
            "message": "权限查询优化系统异常",
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }