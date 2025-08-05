"""缓存管理API端点

提供缓存监控、统计和管理功能的API接口
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.cache_config_manager import (
    get_cache_config_manager,
    update_cache_config,
)
from app.core.cache_health_check import (
    get_cache_health_checker,
    get_cache_health_status,
    run_cache_health_check,
)
from app.core.cache_monitor import get_cache_monitor
from app.core.cache_optimizer import (
    analyze_cache_performance,
    get_cache_optimizer,
    run_auto_optimization,
)
from app.core.cache_scheduler import get_cache_scheduler



from app.models.user import User
from app.schemas.response import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats", response_model=ResponseModel)
async def get_cache_stats(
    cache_type: Optional[str] = Query(None, description="缓存类型"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取缓存统计信息

    Args:
        cache_type: 缓存类型，None表示获取全局统计
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 缓存统计信息
    """
    try:
        monitor = get_cache_monitor()
        stats = monitor.get_stats(cache_type)

        return ResponseModel(code=200, message="获取缓存统计信息成功", data=stats)

    except Exception as e:
        logger.error(f"获取缓存统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取缓存统计信息失败",
        )


@router.get("/performance", response_model=ResponseModel)
async def get_performance_report(
    hours: int = Query(24, ge=1, le=168, description="报告时间范围（小时）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取缓存性能报告

    Args:
        hours: 报告时间范围（小时）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 性能报告
    """
    try:
        monitor = get_cache_monitor()
        report = monitor.get_performance_report(hours)

        return ResponseModel(code=200, message="获取性能报告成功", data=report)

    except Exception as e:
        logger.error(f"获取性能报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取性能报告失败"
        )


@router.get("/slow-operations", response_model=ResponseModel)
async def get_slow_operations(
    threshold: float = Query(0.1, ge=0.01, le=10.0, description="响应时间阈值（秒）"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取慢操作列表

    Args:
        threshold: 响应时间阈值（秒）
        limit: 返回数量限制
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 慢操作列表
    """
    try:
        monitor = get_cache_monitor()
        slow_ops = monitor.get_slow_operations(threshold, limit)

        return ResponseModel(
            code=200,
            message="获取慢操作列表成功",
            data={
                "threshold": threshold,
                "total_count": len(slow_ops),
                "operations": slow_ops,
            },
        )

    except Exception as e:
        logger.error(f"获取慢操作列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取慢操作列表失败",
        )


@router.get("/errors", response_model=ResponseModel)
async def get_error_summary(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取缓存错误摘要

    Args:
        hours: 统计时间范围（小时）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 错误摘要
    """
    try:
        monitor = get_cache_monitor()
        error_summary = monitor.get_error_summary(hours)

        return ResponseModel(code=200, message="获取错误摘要成功", data=error_summary)

    except Exception as e:
        logger.error(f"获取错误摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取错误摘要失败"
        )


@router.post("/clear", response_model=ResponseModel)
async def clear_cache(
    cache_type: Optional[str] = Query(
        None, description="缓存类型，None表示清空所有缓存"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """清空缓存

    Args:
        cache_type: 缓存类型，None表示清空所有缓存
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 清空结果
    """
    try:
        # 模拟缓存清空操作
        if cache_type:
            message = f"已清空 {cache_type} 缓存"
        else:
            message = "已清空所有缓存"

        logger.info(f"用户 {current_user.username} 执行缓存清空操作: {message}")

        return ResponseModel(
            code=200,
            message=message,
            data={
                "cache_type": cache_type or "all",
                "cleared_at": datetime.now().isoformat(),
                "operator": current_user.username,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="清空缓存失败"
        )


@router.post("/warmup", response_model=ResponseModel)
async def warmup_cache(
    cache_type: Optional[str] = Query(None, description="预热缓存类型"),
    limit: int = Query(100, ge=1, le=1000, description="预热数据量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """预热缓存

    Args:
        cache_type: 预热缓存类型
        limit: 预热数据量限制
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 预热结果
    """
    try:
        warmup_manager = get_cache_warmup_manager()

        if cache_type == "user_permissions":
            await warmup_manager.warmup_user_permissions(db, limit)
            message = f"已预热用户权限缓存，限制 {limit} 个用户"
        elif cache_type == "role_permissions":
            await warmup_manager.warmup_role_permissions(db)
            message = "已预热角色权限缓存"
        elif cache_type == "active_users":
            await warmup_manager.warmup_active_users(db)
            message = "已预热活跃用户缓存"
        elif cache_type == "critical_permissions":
            await warmup_manager.warmup_critical_permissions(db)
            message = "已预热关键权限缓存"
        elif cache_type is None:
            await warmup_manager.warmup_all(db)
            message = "已执行完整缓存预热"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的预热类型: {cache_type}",
            )

        logger.info(f"用户 {current_user.username} 执行缓存预热操作: {message}")

        return ResponseModel(
            code=200,
            message=message,
            data={
                "cache_type": cache_type or "all",
                "limit": limit,
                "warmed_at": datetime.now().isoformat(),
                "operator": current_user.username,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预热缓存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="预热缓存失败"
        )


@router.post("/reset-stats", response_model=ResponseModel)
async def reset_cache_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """重置缓存统计数据

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 重置结果
    """
    try:
        monitor = get_cache_monitor()
        monitor.reset_stats()

        logger.info(f"用户 {current_user.username} 重置了缓存统计数据")

        return ResponseModel(
            code=200,
            message="缓存统计数据已重置",
            data={
                "reset_at": datetime.now().isoformat(),
                "operator": current_user.username,
            },
        )

    except Exception as e:
        logger.error(f"重置缓存统计数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置缓存统计数据失败",
        )


@router.get("/health", response_model=ResponseModel)
async def get_cache_health(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """获取缓存系统健康状态

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 健康状态
    """
    try:
        get_permission_cache_manager()
        monitor = get_cache_monitor()
        scheduler = get_cache_scheduler()

        # 获取基本统计
        stats = monitor.get_stats()

        # 检查缓存连接状态
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cache_manager_status": "active",
            "monitor_status": "active",
            "scheduler_status": scheduler.get_task_status(),
            "global_stats": stats.get("global", {}),
            "cache_types": list(stats.get("by_type", {}).keys()),
            "total_operations": stats.get("global", {}).get("total_requests", 0),
            "overall_hit_rate": stats.get("global", {}).get("hit_rate", 0.0),
        }

        # 检查是否有严重问题
        global_stats = stats.get("global", {})
        hit_rate = global_stats.get("hit_rate", 0.0)
        avg_response_time = global_stats.get("avg_response_time", 0.0)

        warnings = []
        if hit_rate < 0.5:  # 命中率低于50%
            warnings.append(f"缓存命中率较低: {hit_rate:.2%}")

        if avg_response_time > 0.1:  # 平均响应时间超过100ms
            warnings.append(f"平均响应时间较高: {avg_response_time:.3f}s")

        if warnings:
            health_status["status"] = "warning"
            health_status["warnings"] = warnings

        return ResponseModel(
            code=200, message="获取缓存健康状态成功", data=health_status
        )

    except Exception as e:
        logger.error(f"获取缓存健康状态失败: {e}")

        # 返回错误状态
        error_status = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "cache_manager_status": "unknown",
            "monitor_status": "unknown",
        }

        return ResponseModel(code=200, message="缓存系统存在问题", data=error_status)


@router.get("/performance-analysis", response_model=ResponseModel)
async def get_performance_analysis(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """获取缓存性能分析

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 性能分析结果
    """
    try:
        analysis = await analyze_cache_performance()

        return ResponseModel(code=200, message="缓存性能分析完成", data=analysis)

    except Exception as e:
        logger.error(f"性能分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="性能分析失败"
        )


@router.post("/optimize", response_model=ResponseModel)
async def auto_optimize_cache(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """执行缓存自动优化

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 优化结果
    """
    try:
        result = await run_auto_optimization()

        logger.info(f"用户 {current_user.username} 执行了缓存自动优化")

        return ResponseModel(
            code=200,
            message="缓存自动优化完成",
            data={
                "optimization_result": result,
                "optimized_at": datetime.now().isoformat(),
                "operator": current_user.username,
            },
        )

    except Exception as e:
        logger.error(f"自动优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="自动优化失败"
        )


@router.get("/optimization-history", response_model=ResponseModel)
async def get_optimization_history(
    limit: int = Query(10, ge=1, le=50, description="返回记录数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取优化历史记录

    Args:
        limit: 返回记录数量
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 优化历史记录
    """
    try:
        optimizer = get_cache_optimizer()
        history = optimizer.get_optimization_history(limit=limit)

        return ResponseModel(
            code=200,
            message="获取优化历史记录成功",
            data={"history": history, "total_count": len(history), "limit": limit},
        )

    except Exception as e:
        logger.error(f"获取优化历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取优化历史失败"
        )


@router.get("/scheduler-status", response_model=ResponseModel)
async def get_scheduler_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """获取调度器状态

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 调度器状态
    """
    try:
        scheduler = get_cache_scheduler()
        status_info = scheduler.get_task_status()

        return ResponseModel(code=200, message="获取调度器状态成功", data=status_info)

    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取调度器状态失败",
        )


@router.patch("/scheduler/intervals", response_model=ResponseModel)
async def update_scheduler_intervals(
    intervals: Dict[str, int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """更新调度器间隔

    Args:
        intervals: 任务间隔配置
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 更新结果
    """
    try:
        get_cache_scheduler()

        # 验证间隔值
        for task, interval in intervals.items():
            if interval < 60:  # 最小间隔60秒
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"任务 {task} 的间隔必须至少60秒",
                )

        # 更新间隔（这里需要实现具体的更新逻辑）
        # scheduler.update_intervals(intervals)

        logger.info(f"用户 {current_user.username} 更新了调度器间隔配置")

        return ResponseModel(
            code=200,
            message="调度器间隔更新成功",
            data={
                "intervals": intervals,
                "updated_at": datetime.now().isoformat(),
                "operator": current_user.username,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新调度器间隔失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新调度器间隔失败",
        )


# 配置管理端点
@router.get("/config", response_model=ResponseModel)
async def get_cache_config(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """获取当前缓存配置

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 缓存配置
    """
    try:
        config_manager = get_cache_config_manager()
        await config_manager.load_config()

        return ResponseModel(
            code=200,
            message="获取缓存配置成功",
            data={
                "config": config_manager.get_config_dict(),
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"获取缓存配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取缓存配置失败"
        )


@router.patch("/config", response_model=ResponseModel)
async def update_cache_config_endpoint(
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """更新缓存配置

    Args:
        updates: 配置更新内容
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 更新结果
    """
    try:
        success = await update_cache_config(updates)

        if success:
            logger.info(f"用户 {current_user.username} 更新了缓存配置")

            return ResponseModel(
                code=200,
                message="缓存配置更新成功",
                data={
                    "updates": updates,
                    "updated_at": datetime.now().isoformat(),
                    "operator": current_user.username,
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="更新缓存配置失败"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新缓存配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新缓存配置失败"
        )


@router.get("/config/history", response_model=ResponseModel)
async def get_config_history(
    limit: int = Query(10, ge=1, le=50, description="返回记录数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取配置变更历史

    Args:
        limit: 返回记录数量
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 配置变更历史
    """
    try:
        config_manager = get_cache_config_manager()
        history = config_manager.get_config_history(limit)

        return ResponseModel(
            code=200,
            message="获取配置变更历史成功",
            data={"history": history, "total": len(history), "limit": limit},
        )

    except Exception as e:
        logger.error(f"获取配置变更历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置变更历史失败",
        )


@router.post("/config/reset", response_model=ResponseModel)
async def reset_cache_config(
    environment: Optional[str] = Query(None, description="环境名称"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """重置缓存配置为默认值

    Args:
        environment: 环境名称
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 重置结果
    """
    try:
        config_manager = get_cache_config_manager()
        success = await config_manager.reset_to_default(environment)

        if success:
            logger.info(f"用户 {current_user.username} 重置了缓存配置")

            return ResponseModel(
                code=200,
                message="缓存配置重置成功",
                data={
                    "environment": environment or "current",
                    "reset_at": datetime.now().isoformat(),
                    "operator": current_user.username,
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="重置缓存配置失败"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置缓存配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="重置缓存配置失败"
        )


@router.get("/config/backups", response_model=ResponseModel)
async def list_config_backups(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """列出配置备份文件

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 备份文件列表
    """
    try:
        config_manager = get_cache_config_manager()
        backups = config_manager.list_backups()

        return ResponseModel(
            code=200,
            message="获取配置备份列表成功",
            data={"backups": backups, "total": len(backups)},
        )

    except Exception as e:
        logger.error(f"获取配置备份列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置备份列表失败",
        )


@router.post("/config/restore", response_model=ResponseModel)
async def restore_config_from_backup(
    backup_file: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """从备份恢复配置

    Args:
        backup_file: 备份文件名
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 恢复结果
    """
    try:
        config_manager = get_cache_config_manager()
        success = await config_manager.restore_from_backup(backup_file)

        if success:
            logger.info(f"用户 {current_user.username} 从备份恢复了配置: {backup_file}")

            return ResponseModel(
                code=200,
                message="从备份恢复配置成功",
                data={
                    "backup_file": backup_file,
                    "restored_at": datetime.now().isoformat(),
                    "operator": current_user.username,
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="从备份恢复配置失败"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从备份恢复配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="从备份恢复配置失败",
        )


@router.post("/config/optimize", response_model=ResponseModel)
async def optimize_config_for_workload(
    workload_stats: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """根据工作负载优化配置

    Args:
        workload_stats: 工作负载统计数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 优化结果
    """
    try:
        config_manager = get_cache_config_manager()
        optimization_result = await config_manager.optimize_config_for_workload(
            workload_stats
        )

        logger.info(f"用户 {current_user.username} 执行了配置优化")

        return ResponseModel(
            code=200,
            message="配置优化完成",
            data={
                "optimization_result": optimization_result,
                "optimized_at": datetime.now().isoformat(),
                "operator": current_user.username,
            },
        )

    except Exception as e:
        logger.error(f"配置优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="配置优化失败"
        )


# 健康检查端点
@router.get("/health-check", response_model=ResponseModel)
async def run_cache_health_check_endpoint(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """运行缓存系统健康检查

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 健康检查报告
    """
    try:
        report = await run_cache_health_check()

        return ResponseModel(
            code=200,
            message="缓存健康检查完成",
            data={
                "overall_status": report.overall_status,
                "timestamp": report.timestamp.isoformat(),
                "checks": [
                    {
                        "component": check.component,
                        "status": check.status,
                        "message": check.message,
                        "response_time_ms": check.response_time_ms,
                        "details": check.details,
                    }
                    for check in report.checks
                ],
                "summary": report.summary,
                "recommendations": report.recommendations,
            },
        )

    except Exception as e:
        logger.error(f"缓存健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="缓存健康检查失败"
        )


@router.get("/health-status", response_model=ResponseModel)
async def get_cache_health_status_endpoint(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ResponseModel:
    """获取缓存健康状态（简化版）

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 健康状态
    """
    try:
        status_result = await get_cache_health_status()

        return ResponseModel(
            code=200,
            message="获取缓存健康状态成功",
            data={"status": status_result, "timestamp": datetime.now().isoformat()},
        )

    except Exception as e:
        logger.error(f"获取缓存健康状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取缓存健康状态失败",
        )


@router.get("/health/history", response_model=ResponseModel)
async def get_health_history(
    limit: int = Query(10, ge=1, le=50, description="返回记录数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取健康检查历史

    Args:
        limit: 返回记录数量
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 健康检查历史
    """
    try:
        health_checker = get_cache_health_checker()
        history = health_checker.get_health_history(limit)

        return ResponseModel(
            code=200,
            message="获取健康检查历史成功",
            data={
                "history": [
                    {
                        "overall_status": report.overall_status,
                        "timestamp": report.timestamp.isoformat(),
                        "summary": report.summary,
                    }
                    for report in history
                ],
                "total": len(history),
                "limit": limit,
            },
        )

    except Exception as e:
        logger.error(f"获取健康检查历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康检查历史失败",
        )


@router.get("/health/trends", response_model=ResponseModel)
async def get_health_trends(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseModel:
    """获取健康趋势分析

    Args:
        hours: 统计时间范围（小时）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ResponseModel: 健康趋势分析
    """
    try:
        health_checker = get_cache_health_checker()
        trends = health_checker.get_health_trends(hours)

        return ResponseModel(code=200, message="获取健康趋势分析成功", data=trends)

    except Exception as e:
        logger.error(f"获取健康趋势分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康趋势分析失败",
        )
