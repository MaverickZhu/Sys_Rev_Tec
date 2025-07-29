"""权限查询性能优化模块

提供高性能的权限查询方法，包括SQL优化、预加载、批量检查等功能
"""

import logging
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, text, func
from sqlalchemy.sql import select

from app.models.user import User
from app.models.permission import Permission, Role, ResourcePermission, PermissionLevel
from app.core.permission_cache import get_permission_cache_manager

logger = logging.getLogger(__name__)


class PermissionQueryOptimizer:
    """权限查询优化器
    
    提供高性能的权限查询方法
    """
    
    def __init__(self, db: Session, use_cache: bool = True):
        self.db = db
        self.use_cache = use_cache
        self.cache_manager = get_permission_cache_manager() if use_cache else None
        
        # 查询统计
        self.query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'db_queries': 0,
            'batch_queries': 0
        }
    
    def preload_user_permissions(self, user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """预加载用户权限数据
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            Dict[int, Dict]: 用户权限数据映射
        """
        try:
            # 使用优化的SQL查询预加载所有相关数据
            users_query = (
                self.db.query(User)
                .options(
                    joinedload(User.primary_role).joinedload(Role.permissions),
                    selectinload(User.direct_permissions),
                    selectinload(User.resource_permissions)
                )
                .filter(User.id.in_(user_ids))
            )
            
            users = users_query.all()
            
            result = {}
            for user in users:
                # 收集用户的所有权限
                permissions = set()
                
                # 直接权限
                for perm in user.direct_permissions:
                    permissions.add(perm.code)
                    # 添加子权限
                    for child in perm.get_all_child_permissions():
                        permissions.add(child.code)
                
                # 角色权限
                if user.primary_role:
                    role_permissions = self._get_role_permissions_recursive(user.primary_role)
                    permissions.update(role_permissions)
                
                # 资源权限
                resource_permissions = {}
                for res_perm in user.resource_permissions:
                    if res_perm.is_active and not res_perm.is_expired:
                        key = f"{res_perm.resource_type.value}:{res_perm.resource_id}"
                        resource_permissions[key] = {
                            'level': res_perm.permission_level,
                            'operations': res_perm.operations
                        }
                
                result[user.id] = {
                    'permissions': list(permissions),
                    'resource_permissions': resource_permissions,
                    'is_superuser': user.is_superuser,
                    'role_code': user.primary_role.code if user.primary_role else None
                }
            
            logger.info(f"预加载了 {len(users)} 个用户的权限数据")
            return result
            
        except Exception as e:
            logger.error(f"预加载用户权限失败: {e}")
            return {}
    
    def _get_role_permissions_recursive(self, role: Role, visited: Set[int] = None) -> Set[str]:
        """递归获取角色权限（防止循环引用）
        
        Args:
            role: 角色对象
            visited: 已访问的角色ID集合
            
        Returns:
            Set[str]: 权限代码集合
        """
        if visited is None:
            visited = set()
        
        if role.id in visited:
            return set()
        
        visited.add(role.id)
        permissions = set()
        
        # 直接权限
        for perm in role.permissions:
            permissions.add(perm.code)
            # 添加子权限
            for child in perm.get_all_child_permissions():
                permissions.add(child.code)
        
        # 继承权限
        if role.parent:
            parent_permissions = self._get_role_permissions_recursive(role.parent, visited)
            permissions.update(parent_permissions)
        
        return permissions
    
    def batch_check_permissions(
        self, 
        user_ids: List[int], 
        permission_codes: List[str]
    ) -> Dict[int, Dict[str, bool]]:
        """批量检查用户权限
        
        Args:
            user_ids: 用户ID列表
            permission_codes: 权限代码列表
            
        Returns:
            Dict[int, Dict[str, bool]]: 用户权限检查结果
        """
        self.query_stats['batch_queries'] += 1
        
        try:
            # 预加载用户权限数据
            user_permissions = self.preload_user_permissions(user_ids)
            
            result = {}
            for user_id in user_ids:
                user_data = user_permissions.get(user_id, {})
                user_result = {}
                
                for permission_code in permission_codes:
                    # 超级用户拥有所有权限
                    if user_data.get('is_superuser', False):
                        user_result[permission_code] = True
                    else:
                        user_result[permission_code] = permission_code in user_data.get('permissions', [])
                
                result[user_id] = user_result
            
            return result
            
        except Exception as e:
            logger.error(f"批量权限检查失败: {e}")
            return {user_id: {code: False for code in permission_codes} for user_id in user_ids}
    
    def batch_check_resource_permissions(
        self, 
        user_ids: List[int], 
        resource_checks: List[Tuple[str, str, str]]  # (resource_type, resource_id, operation)
    ) -> Dict[int, Dict[str, bool]]:
        """批量检查资源权限
        
        Args:
            user_ids: 用户ID列表
            resource_checks: 资源检查列表 [(resource_type, resource_id, operation), ...]
            
        Returns:
            Dict[int, Dict[str, bool]]: 用户资源权限检查结果
        """
        self.query_stats['batch_queries'] += 1
        
        try:
            # 预加载用户权限数据
            user_permissions = self.preload_user_permissions(user_ids)
            
            result = {}
            for user_id in user_ids:
                user_data = user_permissions.get(user_id, {})
                user_result = {}
                
                for resource_type, resource_id, operation in resource_checks:
                    check_key = f"{resource_type}:{resource_id}:{operation}"
                    
                    # 超级用户拥有所有权限
                    if user_data.get('is_superuser', False):
                        user_result[check_key] = True
                        continue
                    
                    # 检查资源权限
                    resource_key = f"{resource_type}:{resource_id}"
                    resource_perm = user_data.get('resource_permissions', {}).get(resource_key)
                    
                    if resource_perm:
                        user_result[check_key] = self._check_operation_allowed(
                            resource_perm['level'], 
                            resource_perm['operations'], 
                            operation
                        )
                    else:
                        user_result[check_key] = False
                
                result[user_id] = user_result
            
            return result
            
        except Exception as e:
            logger.error(f"批量资源权限检查失败: {e}")
            return {user_id: {f"{rt}:{ri}:{op}": False for rt, ri, op in resource_checks} for user_id in user_ids}
    
    def _check_operation_allowed(self, permission_level: PermissionLevel, operations: str, operation: str) -> bool:
        """检查操作是否被允许
        
        Args:
            permission_level: 权限级别
            operations: 允许的操作列表（JSON字符串）
            operation: 要检查的操作
            
        Returns:
            bool: 是否允许操作
        """
        try:
            # 检查具体操作列表
            if operations:
                import json
                allowed_operations = json.loads(operations)
                if operation in allowed_operations:
                    return True
            
            # 根据权限级别判断
            if permission_level == PermissionLevel.OWNER:
                return True
            elif permission_level == PermissionLevel.ADMIN:
                return operation in ['create', 'read', 'update', 'delete', 'manage']
            elif permission_level == PermissionLevel.WRITE:
                return operation in ['create', 'read', 'update']
            elif permission_level == PermissionLevel.READ:
                return operation == 'read'
            
            return False
            
        except Exception:
            return False
    
    def optimize_permission_query(self, user_id: int, permission_code: str) -> bool:
        """优化的单个权限查询
        
        Args:
            user_id: 用户ID
            permission_code: 权限代码
            
        Returns:
            bool: 是否具有权限
        """
        self.query_stats['total_queries'] += 1
        
        try:
            # 优先使用缓存
            if self.use_cache and self.cache_manager:
                result = self.cache_manager.check_user_permission(user_id, permission_code, self.db)
                if result is not None:
                    self.query_stats['cache_hits'] += 1
                    return result
            
            # 使用优化的数据库查询
            self.query_stats['db_queries'] += 1
            
            # 使用单次查询获取用户及其权限信息
            user_query = (
                self.db.query(User)
                .options(
                    joinedload(User.primary_role).joinedload(Role.permissions),
                    selectinload(User.direct_permissions)
                )
                .filter(User.id == user_id)
            )
            
            user = user_query.first()
            if not user:
                return False
            
            # 超级用户拥有所有权限
            if user.is_superuser:
                return True
            
            # 检查直接权限
            for perm in user.direct_permissions:
                if perm.code == permission_code or perm.has_child_permission(permission_code):
                    return True
            
            # 检查角色权限
            if user.primary_role:
                role_permissions = self._get_role_permissions_recursive(user.primary_role)
                if permission_code in role_permissions:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"优化权限查询失败: {e}")
            return False
    
    def get_user_permission_summary(self, user_id: int) -> Dict[str, Any]:
        """获取用户权限摘要
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 权限摘要
        """
        try:
            user_data = self.preload_user_permissions([user_id]).get(user_id, {})
            
            return {
                'user_id': user_id,
                'is_superuser': user_data.get('is_superuser', False),
                'role_code': user_data.get('role_code'),
                'permission_count': len(user_data.get('permissions', [])),
                'resource_permission_count': len(user_data.get('resource_permissions', {})),
                'permissions': user_data.get('permissions', []),
                'resource_permissions': user_data.get('resource_permissions', {})
            }
            
        except Exception as e:
            logger.error(f"获取用户权限摘要失败: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    def analyze_permission_usage(self, days: int = 30) -> Dict[str, Any]:
        """分析权限使用情况
        
        Args:
            days: 分析天数
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 统计权限使用频率
            permission_usage = (
                self.db.query(
                    Permission.code,
                    Permission.name,
                    func.count().label('usage_count')
                )
                .join(Permission.users)
                .group_by(Permission.id, Permission.code, Permission.name)
                .order_by(func.count().desc())
                .limit(50)
                .all()
            )
            
            # 统计角色使用情况
            role_usage = (
                self.db.query(
                    Role.code,
                    Role.name,
                    func.count(User.id).label('user_count')
                )
                .join(User, User.primary_role_id == Role.id)
                .group_by(Role.id, Role.code, Role.name)
                .order_by(func.count(User.id).desc())
                .all()
            )
            
            return {
                'permission_usage': [
                    {'code': code, 'name': name, 'usage_count': count}
                    for code, name, count in permission_usage
                ],
                'role_usage': [
                    {'code': code, 'name': name, 'user_count': count}
                    for code, name, count in role_usage
                ],
                'query_stats': self.query_stats.copy(),
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"权限使用分析失败: {e}")
            return {'error': str(e)}
    
    def suggest_index_optimizations(self) -> List[str]:
        """建议数据库索引优化
        
        Returns:
            List[str]: 索引优化建议
        """
        suggestions = [
            # 用户表索引
            "CREATE INDEX IF NOT EXISTS idx_users_primary_role_id ON users(primary_role_id);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_superuser ON users(is_superuser);",
            
            # 权限表索引
            "CREATE INDEX IF NOT EXISTS idx_permissions_resource_operation ON permissions(resource_type, operation_type);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_parent_id ON permissions(parent_id);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_is_active ON permissions(is_active);",
            
            # 角色表索引
            "CREATE INDEX IF NOT EXISTS idx_roles_parent_id ON roles(parent_id);",
            "CREATE INDEX IF NOT EXISTS idx_roles_is_active ON roles(is_active);",
            
            # 资源权限表索引
            "CREATE INDEX IF NOT EXISTS idx_resource_permissions_user_resource ON resource_permissions(user_id, resource_type, resource_id);",
            "CREATE INDEX IF NOT EXISTS idx_resource_permissions_expires_at ON resource_permissions(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_resource_permissions_is_active ON resource_permissions(is_active);",
            
            # 关联表索引
            "CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_permissions_permission_id ON user_permissions(permission_id);",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);",
        ]
        
        return suggestions
    
    def apply_index_optimizations(self) -> Dict[str, Any]:
        """应用索引优化
        
        Returns:
            Dict[str, Any]: 应用结果
        """
        suggestions = self.suggest_index_optimizations()
        results = {'success': [], 'failed': []}
        
        for sql in suggestions:
            try:
                self.db.execute(text(sql))
                results['success'].append(sql)
                logger.info(f"成功执行索引优化: {sql}")
            except Exception as e:
                results['failed'].append({'sql': sql, 'error': str(e)})
                logger.error(f"索引优化失败: {sql}, 错误: {e}")
        
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"提交索引优化失败: {e}")
            return {'error': str(e)}
        
        return results


# 全局实例
_permission_query_optimizer = None


def get_permission_query_optimizer(db: Session = None, use_cache: bool = True) -> PermissionQueryOptimizer:
    """获取权限查询优化器实例
    
    Args:
        db: 数据库会话
        use_cache: 是否使用缓存
        
    Returns:
        PermissionQueryOptimizer: 优化器实例
    """
    if db:
        return PermissionQueryOptimizer(db, use_cache)
    
    global _permission_query_optimizer
    if _permission_query_optimizer is None:
        from app.api.deps import get_db
        db_session = next(get_db())
        _permission_query_optimizer = PermissionQueryOptimizer(db_session, use_cache)
    
    return _permission_query_optimizer


# 便捷函数
def batch_check_user_permissions(
    user_ids: List[int], 
    permission_codes: List[str], 
    db: Session
) -> Dict[int, Dict[str, bool]]:
    """批量检查用户权限的便捷函数"""
    optimizer = get_permission_query_optimizer(db)
    return optimizer.batch_check_permissions(user_ids, permission_codes)


def preload_user_permissions_data(user_ids: List[int], db: Session) -> Dict[int, Dict[str, Any]]:
    """预加载用户权限数据的便捷函数"""
    optimizer = get_permission_query_optimizer(db)
    return optimizer.preload_user_permissions(user_ids)


def optimize_single_permission_check(user_id: int, permission_code: str, db: Session) -> bool:
    """优化的单个权限检查便捷函数"""
    optimizer = get_permission_query_optimizer(db)
    return optimizer.optimize_permission_query(user_id, permission_code)