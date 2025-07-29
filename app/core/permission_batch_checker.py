"""权限批量检查器

实现高效的批量权限验证功能，支持多种检查模式和优化策略
"""

import logging
from typing import List, Dict, Set, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import time

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.models.user import User
from app.models.permission import Permission, Role, ResourcePermission, PermissionLevel
from app.core.permission_cache import get_permission_cache_manager
from app.core.permission_query_optimizer import get_permission_query_optimizer
from app.core.permission_preloader import get_permission_preloader

logger = logging.getLogger(__name__)


class CheckMode(Enum):
    """检查模式"""
    FAST = "fast"  # 快速模式，优先使用缓存
    ACCURATE = "accurate"  # 精确模式，确保数据准确性
    BALANCED = "balanced"  # 平衡模式，缓存+数据库验证


class CheckStrategy(Enum):
    """检查策略"""
    PARALLEL = "parallel"  # 并行检查
    SEQUENTIAL = "sequential"  # 顺序检查
    BATCH_OPTIMIZED = "batch_optimized"  # 批量优化


@dataclass
class BatchCheckRequest:
    """批量检查请求"""
    user_ids: List[int]
    permission_codes: List[str]
    resource_checks: Optional[List[Tuple[str, str, str]]] = None  # (resource_type, resource_id, operation)
    mode: CheckMode = CheckMode.BALANCED
    strategy: CheckStrategy = CheckStrategy.BATCH_OPTIMIZED
    use_cache: bool = True
    preload_missing: bool = True
    timeout_seconds: int = 30


@dataclass
class BatchCheckResult:
    """批量检查结果"""
    user_permissions: Dict[int, Dict[str, bool]]  # user_id -> {permission_code: has_permission}
    resource_permissions: Dict[int, Dict[str, bool]]  # user_id -> {"type:id:op": has_permission}
    execution_time: float
    cache_hit_rate: float
    total_checks: int
    successful_checks: int
    failed_checks: int
    errors: List[str]
    metadata: Dict[str, Any]


class PermissionBatchChecker:
    """权限批量检查器
    
    提供高效的批量权限验证功能
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # 组件
        self.cache_manager = get_permission_cache_manager()
        self.query_optimizer = get_permission_query_optimizer(db)
        self.preloader = get_permission_preloader(db)
        
        # 统计信息
        self.stats = {
            'total_batch_checks': 0,
            'total_individual_checks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_batch_size': 0.0,
            'avg_execution_time': 0.0,
            'error_count': 0
        }
        
        # 配置
        self.config = {
            'max_batch_size': 1000,
            'max_users_per_batch': 100,
            'max_permissions_per_batch': 50,
            'cache_ttl': 3600,  # 1小时
            'enable_preloading': True,
            'parallel_threshold': 20,  # 超过此数量使用并行处理
            'optimization_level': 2  # 1-3, 3为最高优化
        }
    
    def batch_check(self, request: BatchCheckRequest) -> BatchCheckResult:
        """执行批量权限检查
        
        Args:
            request: 批量检查请求
            
        Returns:
            BatchCheckResult: 检查结果
        """
        start_time = time.time()
        
        try:
            # 验证请求参数
            self._validate_request(request)
            
            # 预加载缺失的权限数据
            if request.preload_missing and self.config['enable_preloading']:
                self._preload_missing_data(request)
            
            # 执行权限检查
            user_permissions = self._check_user_permissions(request)
            resource_permissions = self._check_resource_permissions(request)
            
            # 计算统计信息
            execution_time = time.time() - start_time
            total_checks = len(request.user_ids) * len(request.permission_codes)
            if request.resource_checks:
                total_checks += len(request.user_ids) * len(request.resource_checks)
            
            cache_hits = self.stats['cache_hits']
            cache_misses = self.stats['cache_misses']
            cache_hit_rate = cache_hits / max(cache_hits + cache_misses, 1)
            
            # 更新全局统计
            self._update_stats(execution_time, total_checks)
            
            return BatchCheckResult(
                user_permissions=user_permissions,
                resource_permissions=resource_permissions,
                execution_time=execution_time,
                cache_hit_rate=cache_hit_rate,
                total_checks=total_checks,
                successful_checks=total_checks,
                failed_checks=0,
                errors=[],
                metadata={
                    'mode': request.mode.value,
                    'strategy': request.strategy.value,
                    'users_count': len(request.user_ids),
                    'permissions_count': len(request.permission_codes),
                    'resource_checks_count': len(request.resource_checks) if request.resource_checks else 0
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"批量权限检查失败: {e}")
            
            return BatchCheckResult(
                user_permissions={},
                resource_permissions={},
                execution_time=execution_time,
                cache_hit_rate=0.0,
                total_checks=0,
                successful_checks=0,
                failed_checks=1,
                errors=[str(e)],
                metadata={'error': True}
            )
    
    def _validate_request(self, request: BatchCheckRequest):
        """验证请求参数"""
        if not request.user_ids:
            raise ValueError("用户ID列表不能为空")
        
        if not request.permission_codes and not request.resource_checks:
            raise ValueError("必须指定权限代码或资源检查")
        
        if len(request.user_ids) > self.config['max_users_per_batch']:
            raise ValueError(f"用户数量超过限制: {len(request.user_ids)} > {self.config['max_users_per_batch']}")
        
        if len(request.permission_codes) > self.config['max_permissions_per_batch']:
            raise ValueError(f"权限数量超过限制: {len(request.permission_codes)} > {self.config['max_permissions_per_batch']}")
    
    def _preload_missing_data(self, request: BatchCheckRequest):
        """预加载缺失的权限数据"""
        try:
            # 检查哪些用户的权限数据不在缓存中
            missing_users = []
            for user_id in request.user_ids:
                if not self.cache_manager.has_user_permissions(user_id):
                    missing_users.append(user_id)
            
            if missing_users:
                # 请求预加载
                self.preloader.request_preload(
                    user_ids=missing_users,
                    permission_codes=request.permission_codes,
                    priority=4,  # 高优先级
                    requester="batch_checker"
                )
                
                # 等待预加载完成（最多等待5秒）
                max_wait = 5.0
                wait_interval = 0.1
                waited = 0.0
                
                while waited < max_wait:
                    all_loaded = True
                    for user_id in missing_users:
                        if not self.cache_manager.has_user_permissions(user_id):
                            all_loaded = False
                            break
                    
                    if all_loaded:
                        break
                    
                    time.sleep(wait_interval)
                    waited += wait_interval
                
                logger.debug(f"预加载了 {len(missing_users)} 个用户的权限数据")
                
        except Exception as e:
            logger.warning(f"预加载权限数据失败: {e}")
    
    def _check_user_permissions(self, request: BatchCheckRequest) -> Dict[int, Dict[str, bool]]:
        """检查用户权限"""
        if not request.permission_codes:
            return {}
        
        if request.strategy == CheckStrategy.BATCH_OPTIMIZED:
            return self._batch_optimized_check(request.user_ids, request.permission_codes, request.mode)
        elif request.strategy == CheckStrategy.PARALLEL:
            return self._parallel_check(request.user_ids, request.permission_codes, request.mode)
        else:
            return self._sequential_check(request.user_ids, request.permission_codes, request.mode)
    
    def _batch_optimized_check(self, user_ids: List[int], permission_codes: List[str], mode: CheckMode) -> Dict[int, Dict[str, bool]]:
        """批量优化检查"""
        if mode == CheckMode.FAST:
            # 快速模式：优先使用缓存
            return self._fast_cache_check(user_ids, permission_codes)
        elif mode == CheckMode.ACCURATE:
            # 精确模式：直接查询数据库
            return self.query_optimizer.batch_check_permissions(user_ids, permission_codes)
        else:
            # 平衡模式：缓存+数据库验证
            return self._balanced_check(user_ids, permission_codes)
    
    def _fast_cache_check(self, user_ids: List[int], permission_codes: List[str]) -> Dict[int, Dict[str, bool]]:
        """快速缓存检查"""
        result = {}
        cache_hits = 0
        cache_misses = 0
        
        for user_id in user_ids:
            user_result = {}
            
            for permission_code in permission_codes:
                cached_result = self.cache_manager.check_user_permission(user_id, permission_code, self.db)
                
                if cached_result is not None:
                    user_result[permission_code] = cached_result
                    cache_hits += 1
                else:
                    # 缓存未命中，使用优化查询
                    user_result[permission_code] = self.query_optimizer.optimize_permission_query(user_id, permission_code)
                    cache_misses += 1
            
            result[user_id] = user_result
        
        self.stats['cache_hits'] += cache_hits
        self.stats['cache_misses'] += cache_misses
        
        return result
    
    def _balanced_check(self, user_ids: List[int], permission_codes: List[str]) -> Dict[int, Dict[str, bool]]:
        """平衡检查（缓存+数据库验证）"""
        # 首先尝试缓存
        cache_result = self._fast_cache_check(user_ids, permission_codes)
        
        # 对于关键权限，进行数据库验证
        critical_permissions = self._get_critical_permissions(permission_codes)
        
        if critical_permissions:
            db_result = self.query_optimizer.batch_check_permissions(user_ids, critical_permissions)
            
            # 合并结果，数据库结果优先
            for user_id in user_ids:
                if user_id in db_result:
                    cache_result[user_id].update(db_result[user_id])
        
        return cache_result
    
    def _get_critical_permissions(self, permission_codes: List[str]) -> List[str]:
        """获取关键权限列表"""
        # 定义关键权限模式
        critical_patterns = [
            'admin:', 'system:', 'security:', 'user:delete', 'data:delete'
        ]
        
        critical_permissions = []
        for code in permission_codes:
            for pattern in critical_patterns:
                if code.startswith(pattern):
                    critical_permissions.append(code)
                    break
        
        return critical_permissions
    
    def _parallel_check(self, user_ids: List[int], permission_codes: List[str], mode: CheckMode) -> Dict[int, Dict[str, bool]]:
        """并行检查（简化版，实际可使用线程池）"""
        # 这里简化为批量检查，实际实现可以使用ThreadPoolExecutor
        return self.query_optimizer.batch_check_permissions(user_ids, permission_codes)
    
    def _sequential_check(self, user_ids: List[int], permission_codes: List[str], mode: CheckMode) -> Dict[int, Dict[str, bool]]:
        """顺序检查"""
        result = {}
        
        for user_id in user_ids:
            user_result = {}
            for permission_code in permission_codes:
                user_result[permission_code] = self.query_optimizer.optimize_permission_query(user_id, permission_code)
            result[user_id] = user_result
        
        return result
    
    def _check_resource_permissions(self, request: BatchCheckRequest) -> Dict[int, Dict[str, bool]]:
        """检查资源权限"""
        if not request.resource_checks:
            return {}
        
        return self.query_optimizer.batch_check_resource_permissions(request.user_ids, request.resource_checks)
    
    def _update_stats(self, execution_time: float, total_checks: int):
        """更新统计信息"""
        self.stats['total_batch_checks'] += 1
        self.stats['total_individual_checks'] += total_checks
        
        # 更新平均执行时间
        if self.stats['total_batch_checks'] == 1:
            self.stats['avg_execution_time'] = execution_time
        else:
            self.stats['avg_execution_time'] = (
                self.stats['avg_execution_time'] * (self.stats['total_batch_checks'] - 1) + execution_time
            ) / self.stats['total_batch_checks']
        
        # 更新平均批量大小
        self.stats['avg_batch_size'] = self.stats['total_individual_checks'] / self.stats['total_batch_checks']
    
    def check_single_user_multiple_permissions(self, user_id: int, permission_codes: List[str], 
                                             mode: CheckMode = CheckMode.BALANCED) -> Dict[str, bool]:
        """检查单个用户的多个权限
        
        Args:
            user_id: 用户ID
            permission_codes: 权限代码列表
            mode: 检查模式
            
        Returns:
            Dict[str, bool]: 权限检查结果
        """
        request = BatchCheckRequest(
            user_ids=[user_id],
            permission_codes=permission_codes,
            mode=mode
        )
        
        result = self.batch_check(request)
        return result.user_permissions.get(user_id, {})
    
    def check_multiple_users_single_permission(self, user_ids: List[int], permission_code: str, 
                                             mode: CheckMode = CheckMode.BALANCED) -> Dict[int, bool]:
        """检查多个用户的单个权限
        
        Args:
            user_ids: 用户ID列表
            permission_code: 权限代码
            mode: 检查模式
            
        Returns:
            Dict[int, bool]: 用户权限检查结果
        """
        request = BatchCheckRequest(
            user_ids=user_ids,
            permission_codes=[permission_code],
            mode=mode
        )
        
        result = self.batch_check(request)
        return {user_id: perms.get(permission_code, False) for user_id, perms in result.user_permissions.items()}
    
    def check_user_resource_access(self, user_id: int, resource_type: str, resource_id: str, 
                                 operations: List[str], mode: CheckMode = CheckMode.BALANCED) -> Dict[str, bool]:
        """检查用户对资源的访问权限
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            operations: 操作列表
            mode: 检查模式
            
        Returns:
            Dict[str, bool]: 操作权限检查结果
        """
        resource_checks = [(resource_type, resource_id, op) for op in operations]
        
        request = BatchCheckRequest(
            user_ids=[user_id],
            permission_codes=[],
            resource_checks=resource_checks,
            mode=mode
        )
        
        result = self.batch_check(request)
        user_resource_perms = result.resource_permissions.get(user_id, {})
        
        return {
            op: user_resource_perms.get(f"{resource_type}:{resource_id}:{op}", False)
            for op in operations
        }
    
    def optimize_batch_size(self, user_count: int, permission_count: int) -> Tuple[int, int]:
        """优化批量大小
        
        Args:
            user_count: 用户数量
            permission_count: 权限数量
            
        Returns:
            Tuple[int, int]: (优化后的用户批量大小, 优化后的权限批量大小)
        """
        total_checks = user_count * permission_count
        
        if total_checks <= 100:
            return user_count, permission_count
        elif total_checks <= 1000:
            # 中等规模，适当分批
            user_batch_size = min(user_count, 50)
            permission_batch_size = min(permission_count, 20)
        else:
            # 大规模，需要分批处理
            user_batch_size = min(user_count, 25)
            permission_batch_size = min(permission_count, 10)
        
        return user_batch_size, permission_batch_size
    
    def get_batch_check_stats(self) -> Dict[str, Any]:
        """获取批量检查统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        cache_total = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = self.stats['cache_hits'] / max(cache_total, 1)
        
        return {
            'total_batch_checks': self.stats['total_batch_checks'],
            'total_individual_checks': self.stats['total_individual_checks'],
            'avg_batch_size': round(self.stats['avg_batch_size'], 2),
            'avg_execution_time': round(self.stats['avg_execution_time'], 4),
            'cache_hit_rate': round(cache_hit_rate, 4),
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'error_count': self.stats['error_count'],
            'config': self.config.copy()
        }
    
    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置
        
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
        
        logger.info(f"批量检查器配置已更新: {updated_keys}")
        
        return {
            'message': '配置更新成功',
            'updated_keys': updated_keys,
            'current_config': self.config.copy()
        }
    
    def reset_stats(self) -> Dict[str, Any]:
        """重置统计信息
        
        Returns:
            Dict[str, Any]: 重置结果
        """
        old_stats = self.stats.copy()
        
        self.stats = {
            'total_batch_checks': 0,
            'total_individual_checks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_batch_size': 0.0,
            'avg_execution_time': 0.0,
            'error_count': 0
        }
        
        logger.info("批量检查器统计信息已重置")
        
        return {
            'message': '统计信息已重置',
            'previous_stats': old_stats,
            'reset_time': datetime.utcnow().isoformat()
        }


# 全局实例
_permission_batch_checker = None


def get_permission_batch_checker(db: Session = None) -> PermissionBatchChecker:
    """获取权限批量检查器实例
    
    Args:
        db: 数据库会话
        
    Returns:
        PermissionBatchChecker: 批量检查器实例
    """
    if db:
        return PermissionBatchChecker(db)
    
    global _permission_batch_checker
    if _permission_batch_checker is None:
        from app.api.deps import get_db
        db_session = next(get_db())
        _permission_batch_checker = PermissionBatchChecker(db_session)
    
    return _permission_batch_checker


# 便捷函数
def batch_check_permissions(user_ids: List[int], permission_codes: List[str], 
                          mode: CheckMode = CheckMode.BALANCED, db: Session = None) -> Dict[int, Dict[str, bool]]:
    """批量检查权限的便捷函数"""
    checker = get_permission_batch_checker(db)
    request = BatchCheckRequest(user_ids=user_ids, permission_codes=permission_codes, mode=mode)
    result = checker.batch_check(request)
    return result.user_permissions


def check_user_permissions(user_id: int, permission_codes: List[str], 
                         mode: CheckMode = CheckMode.BALANCED, db: Session = None) -> Dict[str, bool]:
    """检查单个用户多个权限的便捷函数"""
    checker = get_permission_batch_checker(db)
    return checker.check_single_user_multiple_permissions(user_id, permission_codes, mode)


def check_users_permission(user_ids: List[int], permission_code: str, 
                         mode: CheckMode = CheckMode.BALANCED, db: Session = None) -> Dict[int, bool]:
    """检查多个用户单个权限的便捷函数"""
    checker = get_permission_batch_checker(db)
    return checker.check_multiple_users_single_permission(user_ids, permission_code, mode)