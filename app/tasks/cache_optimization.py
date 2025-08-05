#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存优化任务调度器
实现自动化的缓存性能监控和优化策略调整
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config.cache_strategy import cache_strategy_manager
from app.monitoring.performance_monitor import CacheOptimizer, PerformanceMonitor
from app.services.cache_service import cache_service


@dataclass
class OptimizationTask:
    """优化任务"""

    task_id: str
    cache_type: str
    task_type: str  # analyze, optimize, cleanup, report
    priority: int  # 1-10, 10最高
    scheduled_time: datetime
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3


class CacheOptimizationScheduler:
    """缓存优化调度器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        self.cache_optimizer = CacheOptimizer()
        self.tasks: List[OptimizationTask] = []
        self.running = False
        self.optimization_history: List[Dict[str, Any]] = []
        self.last_optimization_time = {}

        # 优化配置
        self.config = {
            "analysis_interval": 300,  # 5分钟分析一次
            "optimization_interval": 1800,  # 30分钟优化一次
            "cleanup_interval": 3600,  # 1小时清理一次
            "report_interval": 86400,  # 24小时生成报告
            "max_concurrent_tasks": 3,
            "optimization_threshold": {
                "hit_rate_low": 0.6,
                "hit_rate_high": 0.95,
                "memory_usage_high": 0.8,
                "response_time_high": 1.0,
            },
        }

    async def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        self.logger.info("缓存优化调度器启动")

        # 启动后台任务
        await asyncio.gather(
            self._schedule_periodic_tasks(),
            self._execute_tasks(),
            self._monitor_system_health(),
        )

    async def stop(self):
        """停止调度器"""
        self.running = False
        self.logger.info("缓存优化调度器停止")

    async def _schedule_periodic_tasks(self):
        """调度周期性任务"""
        while self.running:
            try:
                current_time = datetime.now()

                # 调度分析任务
                await self._schedule_analysis_tasks(current_time)

                # 调度优化任务
                await self._schedule_optimization_tasks(current_time)

                # 调度清理任务
                await self._schedule_cleanup_tasks(current_time)

                # 调度报告任务
                await self._schedule_report_tasks(current_time)

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                self.logger.error(f"调度任务时发生错误: {e}")
                await asyncio.sleep(60)

    async def _schedule_analysis_tasks(self, current_time: datetime):
        """调度分析任务"""
        for cache_type in cache_strategy_manager.strategies.keys():
            last_analysis = self.last_optimization_time.get(
                f"{cache_type}_analysis", current_time - timedelta(hours=1)
            )

            if (current_time - last_analysis).total_seconds() >= self.config[
                "analysis_interval"
            ]:
                task = OptimizationTask(
                    task_id=f"analysis_{cache_type}_{int(time.time())}",
                    cache_type=cache_type,
                    task_type="analyze",
                    priority=5,
                    scheduled_time=current_time,
                )
                self.tasks.append(task)
                self.last_optimization_time[f"{cache_type}_analysis"] = current_time

    async def _schedule_optimization_tasks(self, current_time: datetime):
        """调度优化任务"""
        for cache_type in cache_strategy_manager.strategies.keys():
            last_optimization = self.last_optimization_time.get(
                f"{cache_type}_optimization", current_time - timedelta(hours=2)
            )

            if (current_time - last_optimization).total_seconds() >= self.config[
                "optimization_interval"
            ]:
                # 检查是否需要优化
                if await self._should_optimize(cache_type):
                    task = OptimizationTask(
                        task_id=f"optimize_{cache_type}_{int(time.time())}",
                        cache_type=cache_type,
                        task_type="optimize",
                        priority=8,
                        scheduled_time=current_time,
                    )
                    self.tasks.append(task)
                    self.last_optimization_time[f"{cache_type}_optimization"] = (
                        current_time
                    )

    async def _schedule_cleanup_tasks(self, current_time: datetime):
        """调度清理任务"""
        last_cleanup = self.last_optimization_time.get(
            "global_cleanup", current_time - timedelta(hours=2)
        )

        if (current_time - last_cleanup).total_seconds() >= self.config[
            "cleanup_interval"
        ]:
            task = OptimizationTask(
                task_id=f"cleanup_{int(time.time())}",
                cache_type="all",
                task_type="cleanup",
                priority=3,
                scheduled_time=current_time,
            )
            self.tasks.append(task)
            self.last_optimization_time["global_cleanup"] = current_time

    async def _schedule_report_tasks(self, current_time: datetime):
        """调度报告任务"""
        last_report = self.last_optimization_time.get(
            "daily_report", current_time - timedelta(days=2)
        )

        if (current_time - last_report).total_seconds() >= self.config[
            "report_interval"
        ]:
            task = OptimizationTask(
                task_id=f"report_{int(time.time())}",
                cache_type="all",
                task_type="report",
                priority=2,
                scheduled_time=current_time,
            )
            self.tasks.append(task)
            self.last_optimization_time["daily_report"] = current_time

    async def _should_optimize(self, cache_type: str) -> bool:
        """判断是否需要优化"""
        try:
            stats = await self._get_cache_stats(cache_type)
            threshold = self.config["optimization_threshold"]

            # 检查各项指标
            hit_rate = stats.get("hit_rate", 1.0)
            memory_usage_ratio = stats.get("memory_usage_ratio", 0.0)
            avg_response_time = stats.get("avg_response_time", 0.0)

            return (
                hit_rate < threshold["hit_rate_low"]
                or hit_rate > threshold["hit_rate_high"]
                or memory_usage_ratio > threshold["memory_usage_high"]
                or avg_response_time > threshold["response_time_high"]
            )
        except Exception as e:
            self.logger.error(f"检查优化需求时发生错误: {e}")
            return False

    async def _execute_tasks(self):
        """执行任务"""
        while self.running:
            try:
                # 获取待执行的任务
                pending_tasks = [t for t in self.tasks if t.status == "pending"]

                if not pending_tasks:
                    await asyncio.sleep(10)
                    continue

                # 按优先级和时间排序
                pending_tasks.sort(key=lambda x: (-x.priority, x.scheduled_time))

                # 限制并发任务数
                running_tasks = [t for t in self.tasks if t.status == "running"]
                available_slots = self.config["max_concurrent_tasks"] - len(
                    running_tasks
                )

                if available_slots <= 0:
                    await asyncio.sleep(5)
                    continue

                # 执行任务
                tasks_to_execute = pending_tasks[:available_slots]
                await asyncio.gather(
                    *[self._execute_single_task(task) for task in tasks_to_execute]
                )

            except Exception as e:
                self.logger.error(f"执行任务时发生错误: {e}")
                await asyncio.sleep(10)

    async def _execute_single_task(self, task: OptimizationTask):
        """执行单个任务"""
        task.status = "running"
        start_time = time.time()

        try:
            self.logger.info(f"开始执行任务: {task.task_id}")

            if task.task_type == "analyze":
                result = await self._execute_analysis_task(task)
            elif task.task_type == "optimize":
                result = await self._execute_optimization_task(task)
            elif task.task_type == "cleanup":
                result = await self._execute_cleanup_task(task)
            elif task.task_type == "report":
                result = await self._execute_report_task(task)
            else:
                raise ValueError(f"未知任务类型: {task.task_type}")

            task.result = result
            task.status = "completed"
            task.execution_time = time.time() - start_time

            self.logger.info(
                f"任务执行完成: {task.task_id}, 耗时: {task.execution_time:.2f}秒"
            )

        except Exception as e:
            task.error_message = str(e)
            task.status = "failed"
            task.execution_time = time.time() - start_time
            task.retry_count += 1

            self.logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")

            # 重试逻辑
            if task.retry_count < task.max_retries:
                task.status = "pending"
                task.scheduled_time = datetime.now() + timedelta(minutes=5)
                self.logger.info(f"任务将在5分钟后重试: {task.task_id}")

    async def _execute_analysis_task(self, task: OptimizationTask) -> Dict[str, Any]:
        """执行分析任务"""
        cache_type = task.cache_type
        stats = await self._get_cache_stats(cache_type)

        # 使用缓存策略管理器分析性能
        analysis = cache_strategy_manager.analyze_cache_performance(cache_type, stats)

        # 记录分析结果
        self.optimization_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "cache_type": cache_type,
                "action": "analysis",
                "stats": stats,
                "analysis": analysis,
            }
        )

        return {
            "cache_type": cache_type,
            "stats": stats,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_optimization_task(
        self, task: OptimizationTask
    ) -> Dict[str, Any]:
        """执行优化任务"""
        cache_type = task.cache_type

        # 获取当前统计信息
        stats = await self._get_cache_stats(cache_type)

        # 执行优化
        optimization_result = await self.cache_optimizer.optimize_cache_strategy(
            cache_type, stats
        )

        # 应用优化建议
        applied_optimizations = []
        for recommendation in optimization_result.get("recommendations", []):
            try:
                success = await self._apply_optimization(cache_type, recommendation)
                if success:
                    applied_optimizations.append(recommendation)
            except Exception as e:
                self.logger.error(f"应用优化建议失败: {e}")

        # 记录优化结果
        self.optimization_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "cache_type": cache_type,
                "action": "optimization",
                "before_stats": stats,
                "recommendations": optimization_result.get("recommendations", []),
                "applied_optimizations": applied_optimizations,
            }
        )

        return {
            "cache_type": cache_type,
            "optimization_result": optimization_result,
            "applied_optimizations": applied_optimizations,
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_cleanup_task(self, task: OptimizationTask) -> Dict[str, Any]:
        """执行清理任务"""
        cleanup_results = {}

        if task.cache_type == "all":
            # 全局清理
            for cache_type in cache_strategy_manager.strategies.keys():
                result = await self._cleanup_cache_type(cache_type)
                cleanup_results[cache_type] = result
        else:
            # 单个缓存类型清理
            cleanup_results[task.cache_type] = await self._cleanup_cache_type(
                task.cache_type
            )

        return {
            "cleanup_results": cleanup_results,
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_report_task(self, task: OptimizationTask) -> Dict[str, Any]:
        """执行报告任务"""
        # 生成性能报告
        report = await self._generate_performance_report()

        # 保存报告
        report_file = (
            f"cache_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(f"reports/{report_file}", "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

        return {
            "report": report,
            "report_file": report_file,
            "timestamp": datetime.now().isoformat(),
        }

    async def _get_cache_stats(self, cache_type: str) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            # 从性能监控器获取统计信息
            stats = await self.performance_monitor.get_cache_metrics(cache_type)

            # 从缓存服务获取额外信息
            cache_info = await cache_service.get_stats()

            return {
                "hit_rate": stats.get("hit_rate", 0.0),
                "miss_rate": stats.get("miss_rate", 0.0),
                "avg_response_time": stats.get("avg_response_time", 0.0),
                "memory_usage": cache_info.get("memory_usage_mb", 0),
                "memory_usage_ratio": cache_info.get("memory_usage_mb", 0)
                / 1024,  # 假设1GB限制
                "key_count": cache_info.get("key_count", 0),
                "eviction_count": stats.get("eviction_count", 0),
                "connection_count": cache_info.get("connection_count", 0),
                "last_access_time": stats.get("last_access_time", time.time()),
            }
        except Exception as e:
            self.logger.error(f"获取缓存统计信息失败: {e}")
            return {}

    async def _apply_optimization(
        self, cache_type: str, recommendation: Dict[str, Any]
    ) -> bool:
        """应用优化建议"""
        try:
            action = recommendation.get("action")

            if action == "increase_ttl":
                factor = recommendation.get("factor", 1.5)
                strategy = cache_strategy_manager.get_strategy(cache_type)
                if strategy:
                    new_ttl = int(strategy.ttl * factor)
                    return cache_strategy_manager.update_strategy(
                        cache_type, ttl=new_ttl
                    )

            elif action == "decrease_ttl":
                factor = recommendation.get("factor", 0.7)
                strategy = cache_strategy_manager.get_strategy(cache_type)
                if strategy:
                    new_ttl = int(strategy.ttl * factor)
                    return cache_strategy_manager.update_strategy(
                        cache_type, ttl=new_ttl
                    )

            elif action == "enable_compression":
                return cache_strategy_manager.update_strategy(
                    cache_type, compression=True
                )

            elif action == "upgrade_to_l1":
                from app.config.cache_strategy import CacheLevel

                return cache_strategy_manager.update_strategy(
                    cache_type, level=CacheLevel.L1_MEMORY
                )

            elif action == "evict_cold_data":
                # 清理冷数据
                await self._cleanup_cache_type(cache_type)
                return True

            return False

        except Exception as e:
            self.logger.error(f"应用优化建议失败: {e}")
            return False

    async def _cleanup_cache_type(self, cache_type: str) -> Dict[str, Any]:
        """清理指定类型的缓存"""
        try:
            strategy = cache_strategy_manager.get_strategy(cache_type)
            if not strategy:
                return {"error": "未找到缓存策略"}

            # 清理过期键
            pattern = f"{strategy.key_prefix}:*"
            cleared_count = await cache_service.clear_pattern(pattern)

            return {
                "cache_type": cache_type,
                "pattern": pattern,
                "cleared_count": cleared_count,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
            return {"error": str(e)}

    async def _generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            "report_time": datetime.now().isoformat(),
            "summary": {},
            "cache_types": {},
            "optimization_history": self.optimization_history[-100:],  # 最近100条记录
            "recommendations": [],
        }

        # 汇总统计
        total_hit_rate = 0
        total_memory_usage = 0
        cache_count = 0

        for cache_type in cache_strategy_manager.strategies.keys():
            try:
                stats = await self._get_cache_stats(cache_type)
                strategy = cache_strategy_manager.get_strategy(cache_type)

                report["cache_types"][cache_type] = {
                    "strategy": asdict(strategy) if strategy else {},
                    "stats": stats,
                    "performance_score": self._calculate_performance_score(stats),
                }

                total_hit_rate += stats.get("hit_rate", 0)
                total_memory_usage += stats.get("memory_usage", 0)
                cache_count += 1

            except Exception as e:
                self.logger.error(f"生成{cache_type}报告时发生错误: {e}")

        # 汇总信息
        if cache_count > 0:
            report["summary"] = {
                "total_cache_types": cache_count,
                "average_hit_rate": total_hit_rate / cache_count,
                "total_memory_usage_mb": total_memory_usage,
                "optimization_count": len(
                    [
                        h
                        for h in self.optimization_history
                        if h.get("action") == "optimization"
                    ]
                ),
                "last_optimization": max(
                    [h.get("timestamp", "") for h in self.optimization_history] + [""]
                ),
            }

        return report

    def _calculate_performance_score(self, stats: Dict[str, Any]) -> float:
        """计算性能评分"""
        try:
            hit_rate = stats.get("hit_rate", 0)
            response_time = stats.get("avg_response_time", 1.0)
            memory_ratio = stats.get("memory_usage_ratio", 0)

            # 评分算法（0-100分）
            hit_rate_score = hit_rate * 40  # 命中率占40%
            response_time_score = max(0, 30 - response_time * 30)  # 响应时间占30%
            memory_score = max(0, 30 - memory_ratio * 30)  # 内存使用占30%

            return min(100, hit_rate_score + response_time_score + memory_score)

        except Exception:
            return 0.0

    async def _monitor_system_health(self):
        """监控系统健康状态"""
        while self.running:
            try:
                # 检查Redis连接
                if not await cache_service.is_connected():
                    self.logger.warning("Redis连接异常")

                # 检查内存使用
                cache_stats = await cache_service.get_stats()
                memory_usage = cache_stats.get("memory_usage_mb", 0)
                if memory_usage > 1024:  # 超过1GB
                    self.logger.warning(f"缓存内存使用过高: {memory_usage}MB")

                # 清理完成的任务
                completed_tasks = [
                    t for t in self.tasks if t.status in ["completed", "failed"]
                ]
                if len(completed_tasks) > 100:
                    # 保留最近50个任务
                    self.tasks = [
                        t for t in self.tasks if t.status not in ["completed", "failed"]
                    ] + completed_tasks[-50:]

                await asyncio.sleep(300)  # 5分钟检查一次

            except Exception as e:
                self.logger.error(f"系统健康监控错误: {e}")
                await asyncio.sleep(300)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        for task in self.tasks:
            if task.task_id == task_id:
                return asdict(task)
        return None

    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        recent_history = self.optimization_history[-24:]  # 最近24条记录

        summary = {
            "total_optimizations": len(
                [h for h in recent_history if h.get("action") == "optimization"]
            ),
            "total_analyses": len(
                [h for h in recent_history if h.get("action") == "analysis"]
            ),
            "active_tasks": len(
                [t for t in self.tasks if t.status in ["pending", "running"]]
            ),
            "completed_tasks": len([t for t in self.tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in self.tasks if t.status == "failed"]),
            "last_optimization_time": self.last_optimization_time,
            "running": self.running,
        }

        return summary


# 全局调度器实例
cache_optimization_scheduler = CacheOptimizationScheduler()


if __name__ == "__main__":
    # 测试调度器
    async def test_scheduler():
        scheduler = CacheOptimizationScheduler()
        await scheduler.start()

    asyncio.run(test_scheduler())
