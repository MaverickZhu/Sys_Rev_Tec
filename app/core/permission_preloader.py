"""权限预加载机制

实现智能的权限数据预加载策略，提升权限查询性能
"""

import logging
import asyncio
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock, Thread
import time

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.permission import Permission, Role
from app.core.permission_cache import get_permission_cache_manager
from app.core.permission_query_optimizer import get_permission_query_optimizer

logger = logging.getLogger(__name__)


@dataclass
class PreloadRequest:
    """预加载请求"""
    user_ids: List[int]
    permission_codes: Optional[List[str]] = None
    priority: int = 1  # 1-5, 5为最高优先级
    requested_at: datetime = field(default_factory=datetime.utcnow)
    requester: str = "system"
    
    def __hash__(self):
        return hash((tuple(sorted(self.user_ids)), tuple(sorted(self.permission_codes or []))))


@dataclass
class PreloadStats:
    """预加载统计信息"""
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_preload_time: float = 0.0
    last_preload_time: Optional[datetime] = None
    
    def update_timing(self, duration: float):
        """更新时间统计"""
        if self.completed_requests == 0:
            self.avg_preload_time = duration
        else:
            self.avg_preload_time = (self.avg_preload_time * self.completed_requests + duration) / (self.completed_requests + 1)
        self.last_preload_time = datetime.utcnow()


class PermissionPreloader:
    """权限预加载器
    
    智能预加载用户权限数据，提升查询性能
    """
    
    def __init__(self, db: Session, max_queue_size: int = 1000):
        self.db = db
        self.max_queue_size = max_queue_size
        
        # 组件
        self.cache_manager = get_permission_cache_manager()
        self.query_optimizer = get_permission_query_optimizer(db)
        
        # 预加载队列和统计
        self.preload_queue = deque(maxlen=max_queue_size)
        self.processing_queue = set()
        self.stats = PreloadStats()
        self.lock = Lock()
        
        # 用户访问模式分析
        self.user_access_patterns = defaultdict(list)  # user_id -> [access_time, ...]
        self.permission_access_patterns = defaultdict(list)  # permission_code -> [access_time, ...]
        self.user_permission_correlations = defaultdict(set)  # user_id -> {permission_codes}
        
        # 预加载策略配置
        self.config = {
            'enable_pattern_analysis': True,
            'pattern_analysis_window': 3600,  # 1小时
            'min_access_frequency': 3,  # 最小访问频率
            'preload_batch_size': 50,
            'max_preload_age': 1800,  # 30分钟
            'enable_predictive_preload': True,
            'correlation_threshold': 0.3
        }
        
        # 启动后台处理线程
        self.running = True
        self.worker_thread = Thread(target=self._process_preload_queue, daemon=True)
        self.worker_thread.start()
        
        logger.info("权限预加载器已启动")
    
    def request_preload(self, user_ids: List[int], permission_codes: Optional[List[str]] = None, 
                       priority: int = 1, requester: str = "system") -> bool:
        """请求预加载权限数据
        
        Args:
            user_ids: 用户ID列表
            permission_codes: 权限代码列表（可选）
            priority: 优先级（1-5）
            requester: 请求者标识
            
        Returns:
            bool: 是否成功添加到队列
        """
        if not user_ids:
            return False
        
        request = PreloadRequest(
            user_ids=user_ids,
            permission_codes=permission_codes,
            priority=priority,
            requester=requester
        )
        
        with self.lock:
            # 检查是否已在处理中
            if request in self.processing_queue:
                return True
            
            # 添加到队列（按优先级排序）
            inserted = False
            for i, existing_request in enumerate(self.preload_queue):
                if request.priority > existing_request.priority:
                    self.preload_queue.insert(i, request)
                    inserted = True
                    break
            
            if not inserted:
                if len(self.preload_queue) < self.max_queue_size:
                    self.preload_queue.append(request)
                else:
                    logger.warning("预加载队列已满，丢弃低优先级请求")
                    return False
            
            self.stats.total_requests += 1
            
        logger.debug(f"添加预加载请求: {len(user_ids)} 用户, 优先级 {priority}")
        return True
    
    def _process_preload_queue(self):
        """处理预加载队列（后台线程）"""
        while self.running:
            try:
                request = None
                with self.lock:
                    if self.preload_queue:
                        request = self.preload_queue.popleft()
                        self.processing_queue.add(request)
                
                if request:
                    self._execute_preload(request)
                    with self.lock:
                        self.processing_queue.discard(request)
                else:
                    time.sleep(0.1)  # 队列为空时短暂休眠
                    
            except Exception as e:
                logger.error(f"预加载队列处理错误: {e}")
                time.sleep(1)
    
    def _execute_preload(self, request: PreloadRequest):
        """执行预加载请求"""
        start_time = time.time()
        
        try:
            # 检查缓存中已有的数据
            cache_hits = 0
            cache_misses = []
            
            for user_id in request.user_ids:
                if self.cache_manager.has_user_permissions(user_id):
                    cache_hits += 1
                else:
                    cache_misses.append(user_id)
            
            # 只预加载缓存中没有的数据
            if cache_misses:
                user_permissions = self.query_optimizer.preload_user_permissions(cache_misses)
                
                # 将数据存入缓存
                for user_id, permissions_data in user_permissions.items():
                    self.cache_manager.cache_user_permissions(user_id, permissions_data)
                
                logger.info(f"预加载完成: {len(cache_misses)} 用户, 缓存命中: {cache_hits}")
            
            # 更新统计
            duration = time.time() - start_time
            with self.lock:
                self.stats.completed_requests += 1
                self.stats.cache_hits += cache_hits
                self.stats.cache_misses += len(cache_misses)
                self.stats.update_timing(duration)
            
            # 记录访问模式
            if self.config['enable_pattern_analysis']:
                self._record_access_pattern(request)
                
        except Exception as e:
            logger.error(f"预加载执行失败: {e}")
            with self.lock:
                self.stats.failed_requests += 1
    
    def _record_access_pattern(self, request: PreloadRequest):
        """记录用户访问模式"""
        current_time = datetime.utcnow()
        
        # 记录用户访问时间
        for user_id in request.user_ids:
            self.user_access_patterns[user_id].append(current_time)
            
            # 保持窗口大小
            cutoff_time = current_time - timedelta(seconds=self.config['pattern_analysis_window'])
            self.user_access_patterns[user_id] = [
                t for t in self.user_access_patterns[user_id] if t > cutoff_time
            ]
        
        # 记录权限访问模式
        if request.permission_codes:
            for permission_code in request.permission_codes:
                self.permission_access_patterns[permission_code].append(current_time)
                
                # 保持窗口大小
                cutoff_time = current_time - timedelta(seconds=self.config['pattern_analysis_window'])
                self.permission_access_patterns[permission_code] = [
                    t for t in self.permission_access_patterns[permission_code] if t > cutoff_time
                ]
            
            # 记录用户-权限关联
            for user_id in request.user_ids:
                self.user_permission_correlations[user_id].update(request.permission_codes)
    
    def analyze_access_patterns(self) -> Dict[str, Any]:
        """分析访问模式
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(seconds=self.config['pattern_analysis_window'])
        
        # 分析高频访问用户
        frequent_users = []
        for user_id, access_times in self.user_access_patterns.items():
            recent_accesses = [t for t in access_times if t > cutoff_time]
            if len(recent_accesses) >= self.config['min_access_frequency']:
                frequent_users.append({
                    'user_id': user_id,
                    'access_count': len(recent_accesses),
                    'avg_interval': self._calculate_avg_interval(recent_accesses)
                })
        
        # 分析高频访问权限
        frequent_permissions = []
        for permission_code, access_times in self.permission_access_patterns.items():
            recent_accesses = [t for t in access_times if t > cutoff_time]
            if len(recent_accesses) >= self.config['min_access_frequency']:
                frequent_permissions.append({
                    'permission_code': permission_code,
                    'access_count': len(recent_accesses),
                    'avg_interval': self._calculate_avg_interval(recent_accesses)
                })
        
        # 分析用户-权限关联度
        correlations = []
        for user_id, permissions in self.user_permission_correlations.items():
            if len(permissions) > 1:
                correlations.append({
                    'user_id': user_id,
                    'permission_count': len(permissions),
                    'permissions': list(permissions)
                })
        
        return {
            'analysis_time': current_time.isoformat(),
            'window_seconds': self.config['pattern_analysis_window'],
            'frequent_users': sorted(frequent_users, key=lambda x: x['access_count'], reverse=True)[:20],
            'frequent_permissions': sorted(frequent_permissions, key=lambda x: x['access_count'], reverse=True)[:20],
            'user_permission_correlations': sorted(correlations, key=lambda x: x['permission_count'], reverse=True)[:20],
            'total_users_tracked': len(self.user_access_patterns),
            'total_permissions_tracked': len(self.permission_access_patterns)
        }
    
    def _calculate_avg_interval(self, access_times: List[datetime]) -> float:
        """计算平均访问间隔（秒）"""
        if len(access_times) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(access_times)):
            interval = (access_times[i] - access_times[i-1]).total_seconds()
            intervals.append(interval)
        
        return sum(intervals) / len(intervals)
    
    def predict_preload_candidates(self) -> List[Tuple[int, float]]:
        """预测需要预加载的用户
        
        Returns:
            List[Tuple[int, float]]: [(user_id, prediction_score), ...]
        """
        if not self.config['enable_predictive_preload']:
            return []
        
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(seconds=self.config['pattern_analysis_window'])
        
        candidates = []
        
        for user_id, access_times in self.user_access_patterns.items():
            recent_accesses = [t for t in access_times if t > cutoff_time]
            
            if len(recent_accesses) >= 2:
                # 计算访问频率
                frequency = len(recent_accesses) / self.config['pattern_analysis_window']
                
                # 计算访问规律性（间隔标准差的倒数）
                intervals = []
                for i in range(1, len(recent_accesses)):
                    interval = (recent_accesses[i] - recent_accesses[i-1]).total_seconds()
                    intervals.append(interval)
                
                if intervals:
                    import statistics
                    regularity = 1.0 / (statistics.stdev(intervals) + 1.0)
                else:
                    regularity = 0.0
                
                # 计算最后访问时间的新近度
                last_access = max(recent_accesses)
                recency = 1.0 / ((current_time - last_access).total_seconds() + 1.0)
                
                # 综合评分
                score = frequency * 0.4 + regularity * 0.3 + recency * 0.3
                
                if score > self.config['correlation_threshold']:
                    candidates.append((user_id, score))
        
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:50]
    
    def auto_preload_by_patterns(self) -> Dict[str, Any]:
        """基于访问模式自动预加载
        
        Returns:
            Dict[str, Any]: 预加载结果
        """
        candidates = self.predict_preload_candidates()
        
        if not candidates:
            return {'message': '没有发现需要预加载的候选用户', 'candidates_count': 0}
        
        # 分批预加载
        batch_size = self.config['preload_batch_size']
        preloaded_count = 0
        
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            user_ids = [user_id for user_id, score in batch]
            
            # 请求预加载
            success = self.request_preload(
                user_ids=user_ids,
                priority=3,  # 中等优先级
                requester="auto_pattern"
            )
            
            if success:
                preloaded_count += len(user_ids)
        
        return {
            'message': f'基于访问模式自动预加载 {preloaded_count} 个用户',
            'candidates_count': len(candidates),
            'preloaded_count': preloaded_count,
            'top_candidates': candidates[:10]
        }
    
    def get_preload_stats(self) -> Dict[str, Any]:
        """获取预加载统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.lock:
            stats_dict = {
                'total_requests': self.stats.total_requests,
                'completed_requests': self.stats.completed_requests,
                'failed_requests': self.stats.failed_requests,
                'success_rate': self.stats.completed_requests / max(self.stats.total_requests, 1),
                'cache_hits': self.stats.cache_hits,
                'cache_misses': self.stats.cache_misses,
                'cache_hit_rate': self.stats.cache_hits / max(self.stats.cache_hits + self.stats.cache_misses, 1),
                'avg_preload_time': self.stats.avg_preload_time,
                'last_preload_time': self.stats.last_preload_time.isoformat() if self.stats.last_preload_time else None,
                'queue_size': len(self.preload_queue),
                'processing_count': len(self.processing_queue),
                'config': self.config.copy()
            }
        
        return stats_dict
    
    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新预加载配置
        
        Args:
            config_updates: 配置更新
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        updated_keys = []
        
        for key, value in config_updates.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                updated_keys.append(f"{key}: {old_value} -> {value}")
        
        logger.info(f"预加载配置已更新: {updated_keys}")
        
        return {
            'message': '配置更新成功',
            'updated_keys': updated_keys,
            'current_config': self.config.copy()
        }
    
    def clear_patterns(self) -> Dict[str, Any]:
        """清除访问模式数据
        
        Returns:
            Dict[str, Any]: 清除结果
        """
        with self.lock:
            user_count = len(self.user_access_patterns)
            permission_count = len(self.permission_access_patterns)
            correlation_count = len(self.user_permission_correlations)
            
            self.user_access_patterns.clear()
            self.permission_access_patterns.clear()
            self.user_permission_correlations.clear()
        
        logger.info("访问模式数据已清除")
        
        return {
            'message': '访问模式数据已清除',
            'cleared_users': user_count,
            'cleared_permissions': permission_count,
            'cleared_correlations': correlation_count
        }
    
    def shutdown(self):
        """关闭预加载器"""
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        logger.info("权限预加载器已关闭")


# 全局实例
_permission_preloader = None


def get_permission_preloader(db: Session = None) -> PermissionPreloader:
    """获取权限预加载器实例
    
    Args:
        db: 数据库会话
        
    Returns:
        PermissionPreloader: 预加载器实例
    """
    if db:
        return PermissionPreloader(db)
    
    global _permission_preloader
    if _permission_preloader is None:
        from app.api.deps import get_db
        db_session = next(get_db())
        _permission_preloader = PermissionPreloader(db_session)
    
    return _permission_preloader


# 便捷函数
def request_user_preload(user_ids: List[int], priority: int = 1, db: Session = None) -> bool:
    """请求用户权限预加载的便捷函数"""
    preloader = get_permission_preloader(db)
    return preloader.request_preload(user_ids, priority=priority)


def auto_preload_frequent_users(db: Session = None) -> Dict[str, Any]:
    """自动预加载频繁访问用户的便捷函数"""
    preloader = get_permission_preloader(db)
    return preloader.auto_preload_by_patterns()


def get_preload_statistics(db: Session = None) -> Dict[str, Any]:
    """获取预加载统计信息的便捷函数"""
    preloader = get_permission_preloader(db)
    return preloader.get_preload_stats()