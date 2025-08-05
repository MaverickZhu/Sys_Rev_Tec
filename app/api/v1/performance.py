#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控API端点
提供系统性能、业务指标和监控数据的HTTP接口
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse

from app.api.deps import get_current_user
from app.core.logger import logger
from app.models.user import User
from app.services.performance_metrics import enhanced_performance_monitor

router = APIRouter(tags=["performance"])


@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    获取Prometheus格式的性能指标

    Returns:
        str: Prometheus格式的指标数据
    """
    try:
        metrics = enhanced_performance_monitor.get_metrics()
        return Response(
            content=metrics, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"获取Prometheus指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标失败")


@router.get("/health")
async def get_system_health():
    """
    获取系统健康状态

    Returns:
        Dict: 系统健康指标
    """
    try:
        health = await enhanced_performance_monitor.collect_system_health()
        return {
            "status": "success",
            "data": {
                "cpu_usage": health.cpu_usage,
                "memory_usage": health.memory_usage,
                "disk_usage": health.disk_usage,
                "network_io": health.network_io,
                "process_count": health.process_count,
                "load_average": health.load_average,
                "uptime": health.uptime,
                "timestamp": health.timestamp.isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统健康状态失败")


@router.get("/business")
async def get_business_metrics():
    """
    获取业务指标

    Returns:
        Dict: 业务指标数据
    """
    try:
        metrics = await enhanced_performance_monitor.collect_business_metrics()
        return {
            "status": "success",
            "data": {
                "total_projects": metrics.total_projects,
                "total_documents": metrics.total_documents,
                "total_users": metrics.total_users,
                "active_sessions": metrics.active_sessions,
                "reports_generated": metrics.reports_generated,
                "api_calls_today": metrics.api_calls_today,
                "error_rate": metrics.error_rate,
                "avg_response_time": metrics.avg_response_time,
                "timestamp": metrics.timestamp.isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"获取业务指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取业务指标失败")


@router.get("/summary")
async def get_metrics_summary():
    """
    获取性能指标摘要

    Returns:
        Dict: 指标摘要数据
    """
    try:
        summary = enhanced_performance_monitor.get_metrics_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        logger.error(f"获取指标摘要失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标摘要失败")


@router.get("/report")
async def get_performance_report():
    """
    获取详细的性能报告

    Returns:
        Dict: 详细性能报告
    """
    try:
        report = await enhanced_performance_monitor.generate_performance_report()
        return {"status": "success", "data": report}
    except Exception as e:
        logger.error(f"生成性能报告失败: {e}")
        raise HTTPException(status_code=500, detail="生成性能报告失败")


@router.post("/api-performance")
async def record_api_performance(
    endpoint: str,
    method: str,
    response_time: float,
    status_code: int,
    current_user: User = Depends(get_current_user),
):
    """
    记录API性能指标（需要认证）

    Args:
        endpoint: API端点
        method: HTTP方法
        response_time: 响应时间（秒）
        status_code: HTTP状态码
        current_user: 当前用户

    Returns:
        Dict: 操作结果
    """
    try:
        enhanced_performance_monitor.record_api_performance(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
        )
        return {"status": "success", "message": "API性能指标记录成功"}
    except Exception as e:
        logger.error(f"记录API性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="记录API性能指标失败")


@router.post("/database-performance")
async def record_database_performance(
    operation: str,
    table: str,
    duration: float,
    slow_query_threshold: float = 1.0,
    current_user: User = Depends(get_current_user),
):
    """
    记录数据库性能指标（需要认证）

    Args:
        operation: 数据库操作类型
        table: 表名
        duration: 执行时间（秒）
        slow_query_threshold: 慢查询阈值（秒）
        current_user: 当前用户

    Returns:
        Dict: 操作结果
    """
    try:
        enhanced_performance_monitor.record_database_performance(
            operation=operation,
            table=table,
            duration=duration,
            slow_query_threshold=slow_query_threshold,
        )
        return {"status": "success", "message": "数据库性能指标记录成功"}
    except Exception as e:
        logger.error(f"记录数据库性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="记录数据库性能指标失败")


@router.post("/cache-performance")
async def record_cache_performance(
    memory_usage: int,
    key_count: int,
    eviction_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    记录缓存性能指标（需要认证）

    Args:
        memory_usage: 内存使用量（字节）
        key_count: 缓存键数量
        eviction_reason: 驱逐原因（可选）
        current_user: 当前用户

    Returns:
        Dict: 操作结果
    """
    try:
        enhanced_performance_monitor.record_cache_performance(
            memory_usage=memory_usage,
            key_count=key_count,
            eviction_reason=eviction_reason,
        )
        return {"status": "success", "message": "缓存性能指标记录成功"}
    except Exception as e:
        logger.error(f"记录缓存性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="记录缓存性能指标失败")


@router.get("/alerts")
async def get_performance_alerts(current_user: User = Depends(get_current_user)):
    """
    获取性能告警信息（需要认证）

    Args:
        current_user: 当前用户

    Returns:
        Dict: 告警信息
    """
    try:
        alert_summary = enhanced_performance_monitor._get_alert_summary()
        return {
            "status": "success",
            "data": {
                "alert_summary": alert_summary,
                "thresholds": enhanced_performance_monitor._alert_thresholds,
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"获取性能告警失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能告警失败")


@router.put("/thresholds")
async def update_alert_thresholds(
    thresholds: Dict[str, float], current_user: User = Depends(get_current_user)
):
    """
    更新告警阈值（需要认证）

    Args:
        thresholds: 新的告警阈值
        current_user: 当前用户

    Returns:
        Dict: 操作结果
    """
    try:
        # 验证阈值格式
        valid_keys = {
            "cpu_usage_warning",
            "cpu_usage_critical",
            "memory_usage_warning",
            "memory_usage_critical",
            "disk_usage_warning",
            "disk_usage_critical",
            "response_time_warning",
            "response_time_critical",
            "error_rate_warning",
            "error_rate_critical",
        }

        for key in thresholds.keys():
            if key not in valid_keys:
                raise HTTPException(status_code=400, detail=f"无效的阈值键: {key}")

        # 更新阈值
        enhanced_performance_monitor._alert_thresholds.update(thresholds)

        logger.info(f"用户 {current_user.username} 更新了告警阈值: {thresholds}")

        return {
            "status": "success",
            "message": "告警阈值更新成功",
            "data": enhanced_performance_monitor._alert_thresholds,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新告警阈值失败: {e}")
        raise HTTPException(status_code=500, detail="更新告警阈值失败")


@router.get("/trends")
async def get_performance_trends(
    hours: int = 24, current_user: User = Depends(get_current_user)
):
    """
    获取性能趋势数据（需要认证）

    Args:
        hours: 查询的小时数（默认24小时）
        current_user: 当前用户

    Returns:
        Dict: 性能趋势数据
    """
    try:
        if hours <= 0 or hours > 168:  # 最多7天
            raise HTTPException(status_code=400, detail="小时数必须在1-168之间")

        # 从历史数据中获取趋势
        history = enhanced_performance_monitor._metrics_history
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_history = [
            record for record in history if record["timestamp"] >= cutoff_time
        ]

        trends = enhanced_performance_monitor._calculate_performance_trends()

        return {
            "status": "success",
            "data": {
                "trends": trends,
                "data_points": len(filtered_history),
                "time_range": {
                    "start": cutoff_time.isoformat(),
                    "end": datetime.now().isoformat(),
                    "hours": hours,
                },
                "history": filtered_history[-100:],  # 最多返回最近100个数据点
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能趋势失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能趋势失败")


@router.get("/recommendations")
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_user),
):
    """
    获取性能优化建议（需要认证）

    Args:
        current_user: 当前用户

    Returns:
        Dict: 优化建议
    """
    try:
        # 收集当前指标
        system_health = await enhanced_performance_monitor.collect_system_health()
        business_metrics = await enhanced_performance_monitor.collect_business_metrics()

        # 生成优化建议
        recommendations = (
            enhanced_performance_monitor._generate_optimization_recommendations(
                system_health, business_metrics
            )
        )

        return {
            "status": "success",
            "data": {
                "recommendations": recommendations,
                "based_on": {
                    "system_health": {
                        "cpu_usage": system_health.cpu_usage,
                        "memory_usage": system_health.memory_usage,
                        "disk_usage": system_health.disk_usage,
                    },
                    "business_metrics": {
                        "total_projects": business_metrics.total_projects,
                        "total_documents": business_metrics.total_documents,
                        "total_users": business_metrics.total_users,
                    },
                },
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"获取优化建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取优化建议失败")


@router.get("/status")
async def get_monitoring_status():
    """
    获取监控系统状态

    Returns:
        Dict: 监控系统状态
    """
    try:
        return {
            "status": "success",
            "data": {
                "monitoring_active": True,
                "metrics_collected": len(enhanced_performance_monitor._metrics_history),
                "start_time": enhanced_performance_monitor._start_time,
                "uptime": datetime.now().timestamp()
                - enhanced_performance_monitor._start_time,
                "alert_thresholds_count": len(
                    enhanced_performance_monitor._alert_thresholds
                ),
                "prometheus_registry_active": enhanced_performance_monitor.registry
                is not None,
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取监控状态失败")
