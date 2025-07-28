#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器
整合所有缓存相关服务，提供统一的管理接口
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import json

from app.core.logger import logger
from app.services.cache_service import cache_service
from app.services.cache_monitor import get_cache_monitor, CacheMetrics, PerformanceReport
from app.services.cache_optimizer import (
    cache_optimizer, 
    OptimizationTask, 
    OptimizationType,
    OptimizationTaskStatus
)
from app.config.cache_strategy import (
    get_cache_strategy,
    get_all_cache_strategies,
    update_cache_strategy,
    CacheStrategy
)


@dataclass
class CacheSystemStatus:
    """
    缓存系统状态
    """
    redis_connected: bool
    local_cache_size: int
    total_strategies: int
    active_optimizations: int
    system_health_score: float
    last_check_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['last_check_time'] = self.last_check_time.isoformat()
        return data


@dataclass
class CacheOperationResult:
    """
    缓存操作结果
    """
    success: bool
    operation: str
    cache_type: str
    key: Optional[str] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class CacheManager:
    """
    缓存管理器
    统一管理所有缓存相关功能
    """
    
    def __init__(self):
        self.initialized = False
        self._health_check_interval = 60  # 健康检查间隔（秒）
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_status: Optional[CacheSystemStatus] = None
    
    async def initialize(self) -> bool:
        """
        初始化缓存管理器
        
        Returns:
            是否初始化成功
        """
        try:
            # 初始化缓存服务
            await cache_service.initialize()
            
            # 启动优化调度器
            await cache_optimizer.start_scheduler()
            
            # 启动健康检查
            await self._start_health_check()
            
            self.initialized = True
            logger.info("缓存管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"缓存管理器初始化失败: {e}")
            return False
    
    async def shutdown(self):
        """
        关闭缓存管理器
        """
        try:
            # 停止健康检查
            await self._stop_health_check()
            
            # 停止优化调度器
            await cache_optimizer.stop_scheduler()
            
            # 关闭缓存服务
            await cache_service.close()
            
            self.initialized = False
            logger.info("缓存管理器已关闭")
            
        except Exception as e:
            logger.error(f"缓存管理器关闭失败: {e}")
    
    async def _start_health_check(self):
        """
        启动健康检查任务
        """
        if self._health_check_task:
            return
        
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("缓存健康检查已启动")
    
    async def _stop_health_check(self):
        """
        停止健康检查任务
        """
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
        logger.info("缓存健康检查已停止")
    
    async def _health_check_loop(self):
        """
        健康检查循环
        """
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查错误: {e}")
                await asyncio.sleep(self._health_check_interval)
    
    async def _perform_health_check(self):
        """
        执行健康检查
        """
        try:
            # 检查缓存服务健康状态
            health_info = await cache_service.health_check()
            
            # 获取优化器状态
            optimizer_summary = cache_optimizer.get_optimization_summary()
            
            # 计算系统健康评分
            health_score = self._calculate_health_score(health_info, optimizer_summary)
            
            # 更新状态
            self._last_health_status = CacheSystemStatus(
                redis_connected=health_info.get('redis_connected', False),
                local_cache_size=health_info.get('local_cache_size', 0),
                total_strategies=len(get_all_cache_strategies()),
                active_optimizations=optimizer_summary.get('running_tasks', 0),
                system_health_score=health_score,
                last_check_time=datetime.now()
            )
            
            # 如果健康评分过低，记录警告
            if health_score < 70:
                logger.warning(f"缓存系统健康评分较低: {health_score:.1f}")
                
        except Exception as e:
            logger.error(f"健康检查执行失败: {e}")
    
    def _calculate_health_score(
        self, 
        health_info: Dict[str, Any], 
        optimizer_summary: Dict[str, Any]
    ) -> float:
        """
        计算系统健康评分
        
        Args:
            health_info: 缓存服务健康信息
            optimizer_summary: 优化器摘要信息
            
        Returns:
            健康评分 (0-100)
        """
        score = 0.0
        
        # Redis连接状态 (30分)
        if health_info.get('redis_connected', False):
            score += 30
        
        # 内存使用情况 (20分)
        memory_usage = health_info.get('memory_usage', 0)
        if memory_usage < 1024 * 1024 * 512:  # 小于512MB
            score += 20
        elif memory_usage < 1024 * 1024 * 1024:  # 小于1GB
            score += 15
        elif memory_usage < 2 * 1024 * 1024 * 1024:  # 小于2GB
            score += 10
        
        # 优化器成功率 (25分)
        success_rate = optimizer_summary.get('success_rate', 0)
        score += (success_rate / 100) * 25
        
        # 错误率 (25分)
        error_rate = health_info.get('error_rate', 0)
        if error_rate < 1:
            score += 25
        elif error_rate < 5:
            score += 20
        elif error_rate < 10:
            score += 15
        elif error_rate < 20:
            score += 10
        
        return min(score, 100.0)
    
    # 缓存操作接口
    async def set_cache(
        self, 
        key: str, 
        value: Any, 
        cache_type: str = "default",
        ttl: Optional[int] = None
    ) -> CacheOperationResult:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            cache_type: 缓存类型
            ttl: 过期时间（秒）
            
        Returns:
            操作结果
        """
        start_time = datetime.now()
        
        try:
            success = await cache_service.set(key, value, cache_type, ttl)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "set", success, execution_time
            )
            
            return CacheOperationResult(
                success=success,
                operation="set",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录错误指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "set", False, execution_time
            )
            
            return CacheOperationResult(
                success=False,
                operation="set",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def get_cache(
        self, 
        key: str, 
        cache_type: str = "default"
    ) -> CacheOperationResult:
        """
        获取缓存
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
            
        Returns:
            操作结果
        """
        start_time = datetime.now()
        
        try:
            value = await cache_service.get(key, cache_type)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            hit = value is not None
            
            # 记录指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "get", True, execution_time, hit
            )
            
            return CacheOperationResult(
                success=True,
                operation="get",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time,
                metadata={'value': value, 'hit': hit}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录错误指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "get", False, execution_time
            )
            
            return CacheOperationResult(
                success=False,
                operation="get",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def delete_cache(
        self, 
        key: str, 
        cache_type: str = "default"
    ) -> CacheOperationResult:
        """
        删除缓存
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
            
        Returns:
            操作结果
        """
        start_time = datetime.now()
        
        try:
            success = await cache_service.delete(key, cache_type)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "delete", success, execution_time
            )
            
            return CacheOperationResult(
                success=success,
                operation="delete",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录错误指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "delete", False, execution_time
            )
            
            return CacheOperationResult(
                success=False,
                operation="delete",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def exists_cache(
        self, 
        key: str, 
        cache_type: str = "default"
    ) -> CacheOperationResult:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
            
        Returns:
            操作结果
        """
        start_time = datetime.now()
        
        try:
            exists = await cache_service.exists(key, cache_type)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "exists", True, execution_time
            )
            
            return CacheOperationResult(
                success=True,
                operation="exists",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time,
                metadata={'exists': exists}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录错误指标
            monitor = get_cache_monitor()
            monitor.record_operation(
                cache_type, "exists", False, execution_time
            )
            
            return CacheOperationResult(
                success=False,
                operation="exists",
                cache_type=cache_type,
                key=key,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    # 批量操作接口
    async def batch_set(
        self, 
        items: Dict[str, Any], 
        cache_type: str = "default",
        ttl: Optional[int] = None
    ) -> List[CacheOperationResult]:
        """
        批量设置缓存
        
        Args:
            items: 键值对字典
            cache_type: 缓存类型
            ttl: 过期时间（秒）
            
        Returns:
            操作结果列表
        """
        results = []
        
        for key, value in items.items():
            result = await self.set_cache(key, value, cache_type, ttl)
            results.append(result)
        
        return results
    
    async def batch_get(
        self, 
        keys: List[str], 
        cache_type: str = "default"
    ) -> List[CacheOperationResult]:
        """
        批量获取缓存
        
        Args:
            keys: 缓存键列表
            cache_type: 缓存类型
            
        Returns:
            操作结果列表
        """
        results = []
        
        for key in keys:
            result = await self.get_cache(key, cache_type)
            results.append(result)
        
        return results
    
    async def batch_delete(
        self, 
        keys: List[str], 
        cache_type: str = "default"
    ) -> List[CacheOperationResult]:
        """
        批量删除缓存
        
        Args:
            keys: 缓存键列表
            cache_type: 缓存类型
            
        Returns:
            操作结果列表
        """
        results = []
        
        for key in keys:
            result = await self.delete_cache(key, cache_type)
            results.append(result)
        
        return results
    
    # 管理接口
    async def clear_cache(
        self, 
        pattern: str = "*", 
        cache_type: Optional[str] = None
    ) -> CacheOperationResult:
        """
        清理缓存
        
        Args:
            pattern: 匹配模式
            cache_type: 缓存类型
            
        Returns:
            操作结果
        """
        start_time = datetime.now()
        
        try:
            if cache_type:
                deleted_count = await cache_service.clear_pattern(pattern, cache_type)
            else:
                deleted_count = await cache_service.clear_all()
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return CacheOperationResult(
                success=True,
                operation="clear",
                cache_type=cache_type or "all",
                execution_time=execution_time,
                metadata={'deleted_count': deleted_count}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return CacheOperationResult(
                success=False,
                operation="clear",
                cache_type=cache_type or "all",
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def warmup_cache(
        self, 
        cache_type: str, 
        data: Dict[str, Any]
    ) -> CacheOperationResult:
        """
        预热缓存
        
        Args:
            cache_type: 缓存类型
            data: 预热数据
            
        Returns:
            操作结果
        """
        start_time = datetime.now()
        
        try:
            success = await cache_service.warmup_cache(cache_type, data)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return CacheOperationResult(
                success=success,
                operation="warmup",
                cache_type=cache_type,
                execution_time=execution_time,
                metadata={'data_count': len(data)}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return CacheOperationResult(
                success=False,
                operation="warmup",
                cache_type=cache_type,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    # 监控接口
    def get_cache_metrics(
        self, 
        cache_type: Optional[str] = None
    ) -> Optional[CacheMetrics]:
        """
        获取缓存指标
        
        Args:
            cache_type: 缓存类型
            
        Returns:
            缓存指标
        """
        if cache_type:
            return cache_monitor.get_current_metrics(cache_type)
        else:
            # 返回所有类型的聚合指标
            all_metrics = cache_monitor.get_all_current_metrics()
            if not all_metrics:
                return None
            
            # 计算聚合指标
            total_hits = sum(m.cache_hits for m in all_metrics.values())
            total_misses = sum(m.cache_misses for m in all_metrics.values())
            total_operations = total_hits + total_misses
            
            if total_operations == 0:
                return None
            
            avg_response_time = sum(
                m.avg_response_time * (m.cache_hits + m.cache_misses) 
                for m in all_metrics.values()
            ) / total_operations
            
            return CacheMetrics(
                cache_hits=total_hits,
                cache_misses=total_misses,
                hit_rate=(total_hits / total_operations) * 100,
                avg_response_time=avg_response_time,
                memory_usage=sum(m.memory_usage for m in all_metrics.values()),
                error_count=sum(m.error_count for m in all_metrics.values()),
                error_rate=sum(m.error_rate for m in all_metrics.values()) / len(all_metrics),
                last_access=max(m.last_access for m in all_metrics.values()),
                total_operations=total_operations,
                set_operations=sum(m.set_operations for m in all_metrics.values()),
                delete_operations=sum(m.delete_operations for m in all_metrics.values())
            )
    
    async def get_performance_report(
        self, 
        cache_type: Optional[str] = None,
        days: int = 7
    ) -> Optional[PerformanceReport]:
        """
        获取性能报告
        
        Args:
            cache_type: 缓存类型
            days: 报告天数
            
        Returns:
            性能报告
        """
        if cache_type:
            return await cache_monitor.generate_performance_report(cache_type, days)
        else:
            # 生成全局报告
            strategies = get_all_cache_strategies()
            if not strategies:
                return None
            
            # 选择第一个策略类型生成报告（示例）
            first_cache_type = list(strategies.keys())[0]
            return await cache_monitor.generate_performance_report(first_cache_type, days)
    
    def get_system_status(self) -> Optional[CacheSystemStatus]:
        """
        获取系统状态
        
        Returns:
            系统状态
        """
        return self._last_health_status
    
    # 优化接口
    async def trigger_optimization(
        self, 
        cache_type: str, 
        optimization_type: OptimizationType,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        触发优化任务
        
        Args:
            cache_type: 缓存类型
            optimization_type: 优化类型
            parameters: 优化参数
            
        Returns:
            任务ID
        """
        return await cache_optimizer.manual_optimize(
            cache_type, optimization_type, parameters
        )
    
    def get_optimization_tasks(
        self, 
        cache_type: Optional[str] = None,
        status: Optional[OptimizationTaskStatus] = None,
        limit: int = 50
    ) -> List[OptimizationTask]:
        """
        获取优化任务列表
        
        Args:
            cache_type: 缓存类型过滤
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        return cache_optimizer.get_tasks(cache_type, status, limit)
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        获取优化摘要
        
        Returns:
            优化摘要
        """
        return cache_optimizer.get_optimization_summary()
    
    # 策略管理接口
    def get_cache_strategy(self, cache_type: str) -> Optional[CacheStrategy]:
        """
        获取缓存策略
        
        Args:
            cache_type: 缓存类型
            
        Returns:
            缓存策略
        """
        return get_cache_strategy(cache_type)
    
    def get_all_cache_strategies(self) -> Dict[str, CacheStrategy]:
        """
        获取所有缓存策略
        
        Returns:
            策略字典
        """
        return get_all_cache_strategies()
    
    def update_cache_strategy(
        self, 
        cache_type: str, 
        strategy: CacheStrategy
    ) -> bool:
        """
        更新缓存策略
        
        Args:
            cache_type: 缓存类型
            strategy: 新策略
            
        Returns:
            是否更新成功
        """
        try:
            update_cache_strategy(cache_type, strategy)
            logger.info(f"缓存策略已更新: {cache_type}")
            return True
        except Exception as e:
            logger.error(f"更新缓存策略失败 {cache_type}: {e}")
            return False
    
    # 统计接口
    async def export_metrics(
        self, 
        cache_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        导出指标数据
        
        Args:
            cache_type: 缓存类型
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            指标数据
        """
        try:
            if not start_time:
                start_time = datetime.now() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.now()
            
            if cache_type:
                metrics_history = cache_monitor.get_metrics_history(
                    cache_type, start_time, end_time
                )
                return {
                    'cache_type': cache_type,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'metrics': [m.to_dict() for m in metrics_history]
                }
            else:
                # 导出所有类型的指标
                all_data = {}
                strategies = get_all_cache_strategies()
                
                for ct in strategies.keys():
                    metrics_history = cache_monitor.get_metrics_history(
                        ct, start_time, end_time
                    )
                    all_data[ct] = [m.to_dict() for m in metrics_history]
                
                return {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'all_metrics': all_data
                }
                
        except Exception as e:
            logger.error(f"导出指标失败: {e}")
            return {'error': str(e)}


# 全局缓存管理器实例
cache_manager = CacheManager()