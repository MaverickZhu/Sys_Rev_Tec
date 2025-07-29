"""缓存定时任务模块

提供缓存的定时刷新、清理和优化功能。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.cache_monitor import get_cache_monitor
from app.core.cache_warmup import scheduled_cache_refresh
from app.core.config import settings
from app.core.permission_cache import get_permission_cache_manager

logger = logging.getLogger(__name__)


class CacheScheduler:
    """缓存定时任务调度器"""
    
    def __init__(self):
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}
        self.intervals = {
            "cache_refresh": 300,  # 5分钟刷新缓存
            "cache_cleanup": 3600,  # 1小时清理过期缓存
            "stats_cleanup": 86400,  # 24小时清理统计数据
            "health_check": 60,  # 1分钟健康检查
        }
    
    async def start(self):
        """启动定时任务"""
        if self.running:
            logger.warning("Cache scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting cache scheduler...")
        
        # 启动各种定时任务
        self.tasks["cache_refresh"] = asyncio.create_task(
            self._schedule_cache_refresh()
        )
        self.tasks["cache_cleanup"] = asyncio.create_task(
            self._schedule_cache_cleanup()
        )
        self.tasks["stats_cleanup"] = asyncio.create_task(
            self._schedule_stats_cleanup()
        )
        self.tasks["health_check"] = asyncio.create_task(
            self._schedule_health_check()
        )
        
        logger.info("Cache scheduler started successfully")
    
    async def stop(self):
        """停止定时任务"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping cache scheduler...")
        
        # 取消所有任务
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task {task_name} cancelled")
        
        self.tasks.clear()
        logger.info("Cache scheduler stopped")
    
    async def _schedule_cache_refresh(self):
        """定时刷新缓存"""
        while self.running:
            try:
                await asyncio.sleep(self.intervals["cache_refresh"])
                if not self.running:
                    break
                
                logger.debug("Starting scheduled cache refresh...")
                await scheduled_cache_refresh()
                logger.debug("Scheduled cache refresh completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache refresh task: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _schedule_cache_cleanup(self):
        """定时清理过期缓存"""
        while self.running:
            try:
                await asyncio.sleep(self.intervals["cache_cleanup"])
                if not self.running:
                    break
                
                logger.debug("Starting scheduled cache cleanup...")
                await self._cleanup_expired_cache()
                logger.debug("Scheduled cache cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(300)  # 出错后等待5分钟再重试
    
    async def _schedule_stats_cleanup(self):
        """定时清理统计数据"""
        while self.running:
            try:
                await asyncio.sleep(self.intervals["stats_cleanup"])
                if not self.running:
                    break
                
                logger.debug("Starting scheduled stats cleanup...")
                await self._cleanup_old_stats()
                logger.debug("Scheduled stats cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stats cleanup task: {e}")
                await asyncio.sleep(3600)  # 出错后等待1小时再重试
    
    async def _schedule_health_check(self):
        """定时健康检查"""
        while self.running:
            try:
                await asyncio.sleep(self.intervals["health_check"])
                if not self.running:
                    break
                
                await self._perform_health_check()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check task: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            cache_manager = get_permission_cache_manager()
            
            # 清理过期的用户权限缓存
            expired_count = 0
            
            # 这里可以添加具体的清理逻辑
            # 例如检查缓存项的TTL并删除过期项
            
            logger.info(f"Cleaned up {expired_count} expired cache entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
    
    async def _cleanup_old_stats(self):
        """清理旧的统计数据"""
        try:
            monitor = get_cache_monitor()
            
            # 清理7天前的统计数据
            cutoff_time = datetime.now() - timedelta(days=7)
            cleaned_count = await monitor.clear_old_data(cutoff_time)
            
            logger.info(f"Cleaned up {cleaned_count} old statistics records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old stats: {e}")
    
    async def _perform_health_check(self):
        """执行健康检查"""
        try:
            cache_manager = get_permission_cache_manager()
            monitor = get_cache_monitor()
            
            # 检查缓存连接状态
            cache_healthy = await self._check_cache_health(cache_manager)
            
            # 检查监控系统状态
            monitor_healthy = await self._check_monitor_health(monitor)
            
            if not cache_healthy:
                logger.warning("Cache system health check failed")
            
            if not monitor_healthy:
                logger.warning("Monitor system health check failed")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _check_cache_health(self, cache_manager) -> bool:
        """检查缓存系统健康状态"""
        try:
            # 执行简单的缓存操作测试
            test_key = "health_check_test"
            test_value = "test_value"
            
            # 测试设置和获取
            await cache_manager.set_cache(test_key, test_value, ttl=60)
            result = await cache_manager.get_cache(test_key)
            
            if result == test_value:
                # 清理测试数据
                await cache_manager.delete_cache(test_key)
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Cache health check error: {e}")
            return False
    
    async def _check_monitor_health(self, monitor) -> bool:
        """检查监控系统健康状态"""
        try:
            # 检查监控系统是否正常工作
            stats = monitor.get_stats()
            return stats is not None
            
        except Exception as e:
            logger.error(f"Monitor health check error: {e}")
            return False
    
    def update_interval(self, task_name: str, interval: int):
        """更新任务间隔"""
        if task_name in self.intervals:
            self.intervals[task_name] = interval
            logger.info(f"Updated {task_name} interval to {interval} seconds")
        else:
            logger.warning(f"Unknown task name: {task_name}")
    
    def get_task_status(self) -> Dict[str, Dict]:
        """获取任务状态"""
        status = {
            "running": self.running,
            "tasks": {},
            "intervals": self.intervals.copy()
        }
        
        for task_name, task in self.tasks.items():
            status["tasks"][task_name] = {
                "done": task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return status


# 全局调度器实例
_cache_scheduler: Optional[CacheScheduler] = None


def get_cache_scheduler() -> CacheScheduler:
    """获取缓存调度器实例"""
    global _cache_scheduler
    if _cache_scheduler is None:
        _cache_scheduler = CacheScheduler()
    return _cache_scheduler


async def start_cache_scheduler():
    """启动缓存调度器"""
    scheduler = get_cache_scheduler()
    await scheduler.start()


async def stop_cache_scheduler():
    """停止缓存调度器"""
    scheduler = get_cache_scheduler()
    await scheduler.stop()