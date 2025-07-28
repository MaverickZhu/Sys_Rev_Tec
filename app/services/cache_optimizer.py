#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存优化调度器
实现自动化的缓存性能优化任务调度和执行
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import defaultdict

from app.core.logger import logger
from app.services.cache_service import cache_service
from app.services.cache_monitor import get_cache_monitor, CacheMetrics
from app.config.cache_strategy import (
    get_cache_strategy, 
    get_all_cache_strategies,
    update_cache_strategy,
    CacheStrategy,
    CacheLevel,
    EvictionPolicy
)


class OptimizationTaskStatus(Enum):
    """优化任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OptimizationType(Enum):
    """优化类型"""
    TTL_ADJUSTMENT = "ttl_adjustment"
    EVICTION_POLICY = "eviction_policy"
    COMPRESSION = "compression"
    CACHE_LEVEL = "cache_level"
    MEMORY_CLEANUP = "memory_cleanup"
    PRELOAD = "preload"


@dataclass
class OptimizationTask:
    """
    优化任务数据类
    """
    task_id: str
    cache_type: str
    optimization_type: OptimizationType
    status: OptimizationTaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    result: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['optimization_type'] = self.optimization_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class CacheOptimizer:
    """
    缓存优化调度器
    """
    
    def __init__(self):
        self.tasks: Dict[str, OptimizationTask] = {}
        self.scheduler_active = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self.optimization_handlers: Dict[OptimizationType, Callable] = {
            OptimizationType.TTL_ADJUSTMENT: self._optimize_ttl,
            OptimizationType.EVICTION_POLICY: self._optimize_eviction_policy,
            OptimizationType.COMPRESSION: self._optimize_compression,
            OptimizationType.CACHE_LEVEL: self._optimize_cache_level,
            OptimizationType.MEMORY_CLEANUP: self._cleanup_memory,
            OptimizationType.PRELOAD: self._preload_cache
        }
        self.optimization_thresholds = {
            'low_hit_rate': 70.0,
            'high_response_time': 100.0,  # ms
            'high_memory_usage': 1024 * 1024 * 1024,  # 1GB
            'high_error_rate': 5.0
        }
    
    async def start_scheduler(self, interval: int = 300):
        """
        启动优化调度器
        
        Args:
            interval: 调度间隔（秒）
        """
        if self.scheduler_active:
            logger.warning("优化调度器已经在运行中")
            return
        
        self.scheduler_active = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop(interval))
        logger.info(f"缓存优化调度器已启动，间隔: {interval}秒")
    
    async def stop_scheduler(self):
        """
        停止优化调度器
        """
        self.scheduler_active = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("缓存优化调度器已停止")
    
    async def _scheduler_loop(self, interval: int):
        """
        调度器循环
        """
        while self.scheduler_active:
            try:
                await self._analyze_and_optimize()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(interval)
    
    async def _analyze_and_optimize(self):
        """
        分析缓存性能并执行优化
        """
        try:
            strategies = get_all_cache_strategies()
            
            for cache_type in strategies.keys():
                # 获取当前指标
                monitor = get_cache_monitor()
                metrics = monitor.get_current_metrics(cache_type)
                if not metrics:
                    continue
                
                # 分析性能问题
                issues = self._analyze_performance_issues(metrics)
                
                # 为每个问题创建优化任务
                for issue_type, parameters in issues:
                    await self._create_optimization_task(
                        cache_type, issue_type, parameters
                    )
                    
        except Exception as e:
            logger.error(f"分析和优化失败: {e}")
    
    def _analyze_performance_issues(
        self, 
        metrics: CacheMetrics
    ) -> List[Tuple[OptimizationType, Dict[str, Any]]]:
        """
        分析性能问题
        
        Args:
            metrics: 缓存指标
            
        Returns:
            问题类型和参数列表
        """
        issues = []
        
        # 低命中率问题
        if metrics.hit_rate < self.optimization_thresholds['low_hit_rate']:
            issues.append((
                OptimizationType.TTL_ADJUSTMENT,
                {'current_hit_rate': metrics.hit_rate, 'action': 'increase_ttl'}
            ))
        
        # 高响应时间问题
        if metrics.avg_response_time > self.optimization_thresholds['high_response_time']:
            issues.append((
                OptimizationType.COMPRESSION,
                {'current_response_time': metrics.avg_response_time}
            ))
        
        # 高内存使用问题
        if metrics.memory_usage > self.optimization_thresholds['high_memory_usage']:
            issues.append((
                OptimizationType.MEMORY_CLEANUP,
                {'current_memory_usage': metrics.memory_usage}
            ))
        
        # 高错误率问题
        if metrics.error_rate > self.optimization_thresholds['high_error_rate']:
            issues.append((
                OptimizationType.CACHE_LEVEL,
                {'current_error_rate': metrics.error_rate}
            ))
        
        return issues
    
    async def _create_optimization_task(
        self, 
        cache_type: str, 
        optimization_type: OptimizationType,
        parameters: Dict[str, Any]
    ) -> str:
        """
        创建优化任务
        
        Args:
            cache_type: 缓存类型
            optimization_type: 优化类型
            parameters: 优化参数
            
        Returns:
            任务ID
        """
        task_id = f"{cache_type}_{optimization_type.value}_{int(time.time())}"
        
        # 检查是否已有相同类型的任务在运行
        existing_task = self._find_running_task(cache_type, optimization_type)
        if existing_task:
            logger.debug(f"跳过重复的优化任务: {task_id}")
            return existing_task.task_id
        
        task = OptimizationTask(
            task_id=task_id,
            cache_type=cache_type,
            optimization_type=optimization_type,
            status=OptimizationTaskStatus.PENDING,
            created_at=datetime.now(),
            parameters=parameters
        )
        
        self.tasks[task_id] = task
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task))
        
        logger.info(f"创建优化任务: {task_id}")
        return task_id
    
    def _find_running_task(
        self, 
        cache_type: str, 
        optimization_type: OptimizationType
    ) -> Optional[OptimizationTask]:
        """
        查找正在运行的相同类型任务
        """
        for task in self.tasks.values():
            if (
                task.cache_type == cache_type and 
                task.optimization_type == optimization_type and 
                task.status == OptimizationTaskStatus.RUNNING
            ):
                return task
        return None
    
    async def _execute_task(self, task: OptimizationTask):
        """
        执行优化任务
        
        Args:
            task: 优化任务
        """
        try:
            task.status = OptimizationTaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"开始执行优化任务: {task.task_id}")
            
            # 获取对应的处理函数
            handler = self.optimization_handlers.get(task.optimization_type)
            if not handler:
                raise ValueError(f"未知的优化类型: {task.optimization_type}")
            
            # 执行优化
            result = await handler(task.cache_type, task.parameters)
            
            task.result = result
            task.status = OptimizationTaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(f"优化任务完成: {task.task_id}")
            
        except Exception as e:
            task.status = OptimizationTaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"优化任务失败 {task.task_id}: {e}")
    
    async def _optimize_ttl(
        self, 
        cache_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化TTL设置
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                raise ValueError(f"未找到缓存策略: {cache_type}")
            
            current_ttl = strategy.ttl
            action = parameters.get('action', 'increase_ttl')
            
            if action == 'increase_ttl':
                # 增加TTL以提高命中率
                new_ttl = min(current_ttl * 1.5, 86400)  # 最大24小时
            else:
                # 减少TTL以释放内存
                new_ttl = max(current_ttl * 0.7, 300)  # 最小5分钟
            
            # 更新策略
            new_strategy = CacheStrategy(
                name=strategy.name,
                level=strategy.level,
                ttl=int(new_ttl),
                max_size=strategy.max_size,
                eviction_policy=strategy.eviction_policy,
                compression=strategy.compression,
                key_prefix=strategy.key_prefix
            )
            
            update_cache_strategy(cache_type, new_strategy)
            
            return {
                'old_ttl': current_ttl,
                'new_ttl': int(new_ttl),
                'action': action,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"TTL优化失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _optimize_eviction_policy(
        self, 
        cache_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化淘汰策略
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                raise ValueError(f"未找到缓存策略: {cache_type}")
            
            current_policy = strategy.eviction_policy
            
            # 根据内存使用情况选择合适的淘汰策略
            memory_usage = parameters.get('current_memory_usage', 0)
            
            if memory_usage > self.optimization_thresholds['high_memory_usage']:
                # 内存使用高，使用LRU策略
                new_policy = EvictionPolicy.LRU
            else:
                # 内存使用正常，使用LFU策略
                new_policy = EvictionPolicy.LFU
            
            if new_policy == current_policy:
                return {'success': True, 'message': '当前策略已是最优'}
            
            # 更新策略
            new_strategy = CacheStrategy(
                name=strategy.name,
                level=strategy.level,
                ttl=strategy.ttl,
                max_size=strategy.max_size,
                eviction_policy=new_policy,
                compression=strategy.compression,
                key_prefix=strategy.key_prefix
            )
            
            update_cache_strategy(cache_type, new_strategy)
            
            return {
                'old_policy': current_policy.value,
                'new_policy': new_policy.value,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"淘汰策略优化失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _optimize_compression(
        self, 
        cache_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化压缩设置
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                raise ValueError(f"未找到缓存策略: {cache_type}")
            
            current_compression = strategy.compression
            response_time = parameters.get('current_response_time', 0)
            
            # 如果响应时间高且未启用压缩，启用压缩
            if response_time > 50 and not current_compression:
                new_compression = True
            # 如果响应时间很高且已启用压缩，禁用压缩
            elif response_time > 200 and current_compression:
                new_compression = False
            else:
                return {'success': True, 'message': '当前压缩设置已是最优'}
            
            # 更新策略
            new_strategy = CacheStrategy(
                name=strategy.name,
                level=strategy.level,
                ttl=strategy.ttl,
                max_size=strategy.max_size,
                eviction_policy=strategy.eviction_policy,
                compression=new_compression,
                key_prefix=strategy.key_prefix
            )
            
            update_cache_strategy(cache_type, new_strategy)
            
            return {
                'old_compression': current_compression,
                'new_compression': new_compression,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"压缩优化失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _optimize_cache_level(
        self, 
        cache_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化缓存级别
        """
        try:
            strategy = get_cache_strategy(cache_type)
            if not strategy:
                raise ValueError(f"未找到缓存策略: {cache_type}")
            
            current_level = strategy.level
            error_rate = parameters.get('current_error_rate', 0)
            
            # 根据错误率调整缓存级别
            if error_rate > 10 and current_level == CacheLevel.L2:
                # 错误率高，改为混合缓存以提高可靠性
                new_level = CacheLevel.HYBRID
            elif error_rate < 1 and current_level == CacheLevel.HYBRID:
                # 错误率低，可以使用纯Redis缓存
                new_level = CacheLevel.L2
            else:
                return {'success': True, 'message': '当前缓存级别已是最优'}
            
            # 更新策略
            new_strategy = CacheStrategy(
                name=strategy.name,
                level=new_level,
                ttl=strategy.ttl,
                max_size=strategy.max_size,
                eviction_policy=strategy.eviction_policy,
                compression=strategy.compression,
                key_prefix=strategy.key_prefix
            )
            
            update_cache_strategy(cache_type, new_strategy)
            
            return {
                'old_level': current_level.value,
                'new_level': new_level.value,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"缓存级别优化失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _cleanup_memory(
        self, 
        cache_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        清理内存
        """
        try:
            # 清理过期的本地缓存
            await cache_service._evict_local_cache_if_needed()
            
            # 清理特定类型的缓存
            deleted_count = await cache_service.clear_pattern("*", cache_type)
            
            return {
                'deleted_keys': deleted_count,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"内存清理失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _preload_cache(
        self, 
        cache_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        预加载缓存
        """
        try:
            # 这里可以实现具体的预加载逻辑
            # 例如从数据库加载热点数据
            
            # 示例：预加载一些测试数据
            test_data = {
                f"preload_key_{i}": f"preload_value_{i}" 
                for i in range(10)
            }
            
            success = await cache_service.warmup_cache(cache_type, test_data)
            
            return {
                'preloaded_keys': len(test_data),
                'success': success
            }
            
        except Exception as e:
            logger.error(f"缓存预加载失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_task(self, task_id: str) -> Optional[OptimizationTask]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详情
        """
        return self.tasks.get(task_id)
    
    def get_tasks(
        self, 
        cache_type: Optional[str] = None,
        status: Optional[OptimizationTaskStatus] = None,
        limit: int = 100
    ) -> List[OptimizationTask]:
        """
        获取任务列表
        
        Args:
            cache_type: 缓存类型过滤
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        
        # 过滤
        if cache_type:
            tasks = [t for t in tasks if t.cache_type == cache_type]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [OptimizationTaskStatus.COMPLETED, OptimizationTaskStatus.FAILED]:
            return False
        
        task.status = OptimizationTaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        logger.info(f"任务已取消: {task_id}")
        return True
    
    async def manual_optimize(
        self, 
        cache_type: str, 
        optimization_type: OptimizationType,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        手动触发优化
        
        Args:
            cache_type: 缓存类型
            optimization_type: 优化类型
            parameters: 优化参数
            
        Returns:
            任务ID
        """
        if parameters is None:
            parameters = {}
        
        return await self._create_optimization_task(
            cache_type, optimization_type, parameters
        )
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        获取优化摘要
        
        Returns:
            优化摘要信息
        """
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == OptimizationTaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == OptimizationTaskStatus.FAILED])
        running_tasks = len([t for t in self.tasks.values() if t.status == OptimizationTaskStatus.RUNNING])
        
        return {
            'scheduler_active': self.scheduler_active,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'running_tasks': running_tasks,
            'success_rate': (completed_tasks / max(total_tasks, 1)) * 100,
            'optimization_thresholds': self.optimization_thresholds
        }


# 全局优化器实例
cache_optimizer = CacheOptimizer()