#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存性能优化API端点
提供缓存监控和优化功能的REST接口
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from app.config.cache_strategy import (
    cache_strategy_manager, 
    get_cache_strategy, 
    optimize_cache_strategy,
    CacheStrategy
)
from app.tasks.cache_optimization import (
    cache_optimization_scheduler,
    OptimizationTask
)
from app.monitoring.performance_monitor import PerformanceMonitor, CacheOptimizer
from app.services.cache_service import cache_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cache-optimization", tags=["缓存优化"])
logger = logging.getLogger(__name__)

# 初始化监控组件
performance_monitor = PerformanceMonitor()
cache_optimizer = CacheOptimizer()


@router.get("/strategies", summary="获取所有缓存策略")
async def get_cache_strategies(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取所有缓存策略配置
    """
    try:
        strategies = cache_strategy_manager.export_strategies()
        return {
            "success": True,
            "data": strategies,
            "message": "获取缓存策略成功"
        }
    except Exception as e:
        logger.error(f"获取缓存策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存策略失败: {str(e)}")


@router.get("/strategies/{cache_type}", summary="获取指定缓存策略")
async def get_cache_strategy_detail(
    cache_type: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取指定类型的缓存策略详情
    """
    try:
        strategy = get_cache_strategy(cache_type)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"未找到缓存策略: {cache_type}")
        
        return {
            "success": True,
            "data": {
                "cache_type": cache_type,
                "strategy": {
                    "name": strategy.name,
                    "level": strategy.level.value,
                    "priority": strategy.priority.value,
                    "ttl": strategy.ttl,
                    "max_size": strategy.max_size,
                    "eviction_policy": strategy.eviction_policy.value,
                    "compression": strategy.compression,
                    "serialization": strategy.serialization,
                    "key_prefix": strategy.key_prefix,
                    "tags": strategy.tags
                }
            },
            "message": "获取缓存策略详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存策略详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存策略详情失败: {str(e)}")


@router.put("/strategies/{cache_type}", summary="更新缓存策略")
async def update_cache_strategy(
    cache_type: str,
    strategy_update: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    更新指定类型的缓存策略
    """
    try:
        # 验证缓存类型是否存在
        if not get_cache_strategy(cache_type):
            raise HTTPException(status_code=404, detail=f"未找到缓存策略: {cache_type}")
        
        # 更新策略
        success = cache_strategy_manager.update_strategy(cache_type, **strategy_update)
        if not success:
            raise HTTPException(status_code=400, detail="更新缓存策略失败")
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 更新了缓存策略 {cache_type}: {strategy_update}")
        
        return {
            "success": True,
            "data": {
                "cache_type": cache_type,
                "updated_fields": list(strategy_update.keys())
            },
            "message": "更新缓存策略成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新缓存策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新缓存策略失败: {str(e)}")


@router.get("/stats", summary="获取缓存统计信息")
async def get_cache_stats(
    cache_type: Optional[str] = Query(None, description="缓存类型，不指定则返回所有类型"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取缓存统计信息
    """
    try:
        if cache_type:
            # 获取指定类型的统计信息
            stats = await _get_cache_type_stats(cache_type)
            return {
                "success": True,
                "data": {cache_type: stats},
                "message": f"获取{cache_type}缓存统计信息成功"
            }
        else:
            # 获取所有类型的统计信息
            all_stats = {}
            for ct in cache_strategy_manager.strategies.keys():
                try:
                    all_stats[ct] = await _get_cache_type_stats(ct)
                except Exception as e:
                    logger.warning(f"获取{ct}统计信息失败: {e}")
                    all_stats[ct] = {"error": str(e)}
            
            return {
                "success": True,
                "data": all_stats,
                "message": "获取所有缓存统计信息成功"
            }
    except Exception as e:
        logger.error(f"获取缓存统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计信息失败: {str(e)}")


@router.post("/analyze/{cache_type}", summary="分析缓存性能")
async def analyze_cache_performance(
    cache_type: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    分析指定缓存类型的性能
    """
    try:
        # 验证缓存类型
        if not get_cache_strategy(cache_type):
            raise HTTPException(status_code=404, detail=f"未找到缓存策略: {cache_type}")
        
        # 获取统计信息
        stats = await _get_cache_type_stats(cache_type)
        
        # 执行性能分析
        analysis = optimize_cache_strategy(cache_type, stats)
        
        return {
            "success": True,
            "data": {
                "cache_type": cache_type,
                "stats": stats,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            },
            "message": "缓存性能分析完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析缓存性能失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析缓存性能失败: {str(e)}")


@router.post("/optimize/{cache_type}", summary="优化缓存策略")
async def optimize_cache(
    cache_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    优化指定缓存类型的策略
    """
    try:
        # 验证缓存类型
        if not get_cache_strategy(cache_type):
            raise HTTPException(status_code=404, detail=f"未找到缓存策略: {cache_type}")
        
        # 创建优化任务
        task = OptimizationTask(
            task_id=f"manual_optimize_{cache_type}_{int(datetime.now().timestamp())}",
            cache_type=cache_type,
            task_type="optimize",
            priority=9,  # 手动优化高优先级
            scheduled_time=datetime.now()
        )
        
        # 添加到调度器
        cache_optimization_scheduler.tasks.append(task)
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 手动触发了缓存优化: {cache_type}")
        
        return {
            "success": True,
            "data": {
                "task_id": task.task_id,
                "cache_type": cache_type,
                "status": "scheduled"
            },
            "message": "缓存优化任务已创建"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建缓存优化任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建缓存优化任务失败: {str(e)}")


@router.post("/cleanup/{cache_type}", summary="清理缓存")
async def cleanup_cache(
    cache_type: str,
    pattern: Optional[str] = Query(None, description="清理模式，不指定则清理所有"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    清理指定缓存类型的数据
    """
    try:
        # 验证缓存类型
        strategy = get_cache_strategy(cache_type)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"未找到缓存策略: {cache_type}")
        
        # 构建清理模式
        if pattern:
            cleanup_pattern = f"{strategy.key_prefix}:{pattern}"
        else:
            cleanup_pattern = f"{strategy.key_prefix}:*"
        
        # 执行清理
        cleared_count = await cache_service.clear_pattern(cleanup_pattern)
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 清理了缓存 {cache_type}, 模式: {cleanup_pattern}, 清理数量: {cleared_count}")
        
        return {
            "success": True,
            "data": {
                "cache_type": cache_type,
                "pattern": cleanup_pattern,
                "cleared_count": cleared_count,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"清理缓存成功，共清理 {cleared_count} 个键"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.get("/tasks", summary="获取优化任务列表")
async def get_optimization_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取缓存优化任务列表
    """
    try:
        tasks = cache_optimization_scheduler.tasks
        
        # 状态过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按时间排序并限制数量
        tasks = sorted(tasks, key=lambda x: x.scheduled_time, reverse=True)[:limit]
        
        # 转换为字典格式
        task_data = []
        for task in tasks:
            task_data.append({
                "task_id": task.task_id,
                "cache_type": task.cache_type,
                "task_type": task.task_type,
                "priority": task.priority,
                "status": task.status,
                "scheduled_time": task.scheduled_time.isoformat(),
                "execution_time": task.execution_time,
                "retry_count": task.retry_count,
                "error_message": task.error_message
            })
        
        return {
            "success": True,
            "data": {
                "tasks": task_data,
                "total": len(task_data),
                "summary": cache_optimization_scheduler.get_optimization_summary()
            },
            "message": "获取优化任务列表成功"
        }
    except Exception as e:
        logger.error(f"获取优化任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取优化任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}", summary="获取任务详情")
async def get_task_detail(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取指定任务的详细信息
    """
    try:
        task_status = cache_optimization_scheduler.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")
        
        return {
            "success": True,
            "data": task_status,
            "message": "获取任务详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/scheduler/start", summary="启动优化调度器")
async def start_scheduler(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    启动缓存优化调度器
    """
    try:
        if cache_optimization_scheduler.running:
            return {
                "success": True,
                "data": {"status": "already_running"},
                "message": "调度器已在运行中"
            }
        
        # 在后台启动调度器
        background_tasks.add_task(cache_optimization_scheduler.start)
        
        logger.info(f"用户 {current_user.username} 启动了缓存优化调度器")
        
        return {
            "success": True,
            "data": {"status": "starting"},
            "message": "缓存优化调度器启动中"
        }
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")


@router.post("/scheduler/stop", summary="停止优化调度器")
async def stop_scheduler(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    停止缓存优化调度器
    """
    try:
        if not cache_optimization_scheduler.running:
            return {
                "success": True,
                "data": {"status": "already_stopped"},
                "message": "调度器已停止"
            }
        
        await cache_optimization_scheduler.stop()
        
        logger.info(f"用户 {current_user.username} 停止了缓存优化调度器")
        
        return {
            "success": True,
            "data": {"status": "stopped"},
            "message": "缓存优化调度器已停止"
        }
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")


@router.get("/scheduler/status", summary="获取调度器状态")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取缓存优化调度器状态
    """
    try:
        summary = cache_optimization_scheduler.get_optimization_summary()
        
        return {
            "success": True,
            "data": {
                "running": cache_optimization_scheduler.running,
                "summary": summary,
                "config": cache_optimization_scheduler.config
            },
            "message": "获取调度器状态成功"
        }
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")


@router.get("/report", summary="生成性能报告")
async def generate_performance_report(
    days: int = Query(7, ge=1, le=30, description="报告天数"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    生成缓存性能报告
    """
    try:
        # 获取历史数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 生成报告数据
        report_data = {
            "report_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days": days
            },
            "cache_types": {},
            "summary": {},
            "recommendations": []
        }
        
        # 收集各缓存类型的数据
        total_hit_rate = 0
        total_memory_usage = 0
        cache_count = 0
        
        for cache_type in cache_strategy_manager.strategies.keys():
            try:
                stats = await _get_cache_type_stats(cache_type)
                strategy = get_cache_strategy(cache_type)
                
                # 计算性能评分
                performance_score = _calculate_performance_score(stats)
                
                report_data["cache_types"][cache_type] = {
                    "strategy": {
                        "name": strategy.name,
                        "level": strategy.level.value,
                        "priority": strategy.priority.value,
                        "ttl": strategy.ttl
                    },
                    "stats": stats,
                    "performance_score": performance_score
                }
                
                total_hit_rate += stats.get("hit_rate", 0)
                total_memory_usage += stats.get("memory_usage", 0)
                cache_count += 1
                
                # 生成建议
                if performance_score < 70:
                    report_data["recommendations"].append({
                        "cache_type": cache_type,
                        "issue": "性能评分较低",
                        "recommendation": "建议优化缓存策略或增加缓存容量",
                        "priority": "high" if performance_score < 50 else "medium"
                    })
                
            except Exception as e:
                logger.warning(f"生成{cache_type}报告数据失败: {e}")
        
        # 汇总信息
        if cache_count > 0:
            report_data["summary"] = {
                "total_cache_types": cache_count,
                "average_hit_rate": total_hit_rate / cache_count,
                "total_memory_usage_mb": total_memory_usage,
                "report_generated_at": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "data": report_data,
            "message": f"生成{days}天性能报告成功"
        }
    except Exception as e:
        logger.error(f"生成性能报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成性能报告失败: {str(e)}")


async def _get_cache_type_stats(cache_type: str) -> Dict[str, Any]:
    """
    获取指定缓存类型的统计信息
    """
    try:
        # 从性能监控器获取指标
        cache_metrics = await performance_monitor.get_cache_metrics(cache_type)
        
        # 从缓存服务获取基础信息
        cache_info = await cache_service.get_stats()
        
        return {
            "hit_rate": cache_metrics.get("hit_rate", 0.0),
            "miss_rate": cache_metrics.get("miss_rate", 0.0),
            "avg_response_time": cache_metrics.get("avg_response_time", 0.0),
            "memory_usage": cache_info.get("memory_usage_mb", 0),
            "key_count": cache_info.get("key_count", 0),
            "eviction_count": cache_metrics.get("eviction_count", 0),
            "operation_count": cache_metrics.get("operation_count", 0),
            "last_access_time": cache_metrics.get("last_access_time", datetime.now().timestamp())
        }
    except Exception as e:
        logger.error(f"获取{cache_type}统计信息失败: {e}")
        return {"error": str(e)}


def _calculate_performance_score(stats: Dict[str, Any]) -> float:
    """
    计算缓存性能评分（0-100分）
    """
    try:
        hit_rate = stats.get("hit_rate", 0)
        response_time = stats.get("avg_response_time", 1.0)
        memory_usage = stats.get("memory_usage", 0)
        
        # 评分算法
        hit_rate_score = hit_rate * 40  # 命中率占40%
        response_time_score = max(0, 30 - response_time * 30)  # 响应时间占30%
        memory_score = max(0, 30 - (memory_usage / 1024) * 30)  # 内存使用占30%
        
        return min(100, hit_rate_score + response_time_score + memory_score)
    except Exception:
        return 0.0