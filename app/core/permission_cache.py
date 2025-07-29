"""权限缓存系统

提供用户权限、角色权限的缓存机制，提高权限检查性能
"""

import json
import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from functools import wraps
import hashlib

from sqlalchemy.orm import Session

from app.core.cache_config import get_default_cache_config, CacheStrategyConfig
from app.core.cache_monitor import get_cache_monitor, record_cache_operation
from app.services.cache_service import cache_service
from app.models.user import User
from app.models.permission import Permission, Role
from app.crud.crud_user import user as user_crud
from app.crud.crud_permission import permission as permission_crud

logger = logging.getLogger(__name__)


class PermissionCacheManager:
    """权限缓存管理器
    
    管理用户权限、角色权限的缓存
    """
    
    def __init__(self):
        self.cache_config = get_default_cache_config()
        # 使用全局缓存服务
        self.cache_service = cache_service
    
    def _setup_cache_strategies(self):
        """设置缓存策略"""
        # 缓存策略已在全局配置中设置，这里不需要额外配置
        logger.info("权限缓存策略已就绪")
    
    def _generate_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 键参数
            
        Returns:
            str: 缓存键
        """
        key_parts = [str(arg) for arg in args]
        key_content = ":".join(key_parts)
        
        # 对长键进行哈希处理
        if len(key_content) > 100:
            key_hash = hashlib.md5(key_content.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return f"{prefix}:{key_content}"
    
    async def get_user_permissions(self, user_id: int, db: Session) -> Optional[List[str]]:
        """获取用户权限列表（带缓存）
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            Optional[List[str]]: 权限代码列表
        """
        cache_key = self._generate_cache_key("user_perm", user_id)
        start_time = datetime.now()
        
        try:
            # 尝试从缓存获取
            cached_permissions = await self.cache_service.get(cache_key)
            response_time = (datetime.now() - start_time).total_seconds()
            
            if cached_permissions is not None:
                logger.debug(f"从缓存获取用户 {user_id} 权限")
                record_cache_operation(
                    operation_type='get',
                    cache_type='user_permissions',
                    key=cache_key,
                    hit=True,
                    response_time=response_time,
                    user_id=user_id
                )
                return json.loads(cached_permissions) if isinstance(cached_permissions, str) else cached_permissions
            
            # 从数据库获取
            user = user_crud.get(db, id=user_id)
            if not user:
                record_cache_operation(
                    operation_type='get',
                    cache_type='user_permissions',
                    key=cache_key,
                    hit=False,
                    response_time=response_time,
                    user_id=user_id
                )
                return None
            
            permissions = user.get_all_permissions()
            permission_codes = [perm.code for perm in permissions]
            
            # 存入缓存
            await self.cache_service.set(
                cache_key, 
                json.dumps(permission_codes),
                ttl=900  # 15分钟
            )
            
            record_cache_operation(
                operation_type='set',
                cache_type='user_permissions',
                key=cache_key,
                hit=False,
                response_time=response_time,
                user_id=user_id
            )
            
            logger.debug(f"从数据库获取并缓存用户 {user_id} 权限")
            return permission_codes
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"获取用户权限失败: {e}")
            record_cache_operation(
                operation_type='get',
                cache_type='user_permissions',
                key=cache_key,
                hit=False,
                response_time=response_time,
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_role_permissions(self, role_id: int, db: Session) -> Optional[List[str]]:
        """获取角色权限列表（带缓存）
        
        Args:
            role_id: 角色ID
            db: 数据库会话
            
        Returns:
            Optional[List[str]]: 权限代码列表
        """
        cache_key = self._generate_cache_key("role_perm", role_id)
        
        try:
            # 尝试从缓存获取
            cached_permissions = await self.cache_service.get(cache_key)
            if cached_permissions is not None:
                logger.debug(f"从缓存获取角色 {role_id} 权限")
                return json.loads(cached_permissions) if isinstance(cached_permissions, str) else cached_permissions
            
            # 从数据库获取
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return None
            
            permissions = role.get_all_permissions()
            permission_codes = [perm.code for perm in permissions]
            
            # 存入缓存
            await self.cache_service.set(
                cache_key, 
                json.dumps(permission_codes),
                ttl=1800  # 30分钟
            )
            
            logger.debug(f"从数据库获取并缓存角色 {role_id} 权限")
            return permission_codes
            
        except Exception as e:
            logger.error(f"获取角色权限失败: {e}")
            return None
    
    async def get_user_resource_permissions(
        self, 
        user_id: int, 
        resource_type: str, 
        resource_id: str, 
        db: Session
    ) -> Optional[List[str]]:
        """获取用户对特定资源的权限（带缓存）
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            db: 数据库会话
            
        Returns:
            Optional[List[str]]: 操作权限列表
        """
        cache_key = self._generate_cache_key("res_perm", user_id, resource_type, resource_id)
        
        try:
            # 尝试从缓存获取
            cached_permissions = await self.cache_service.get(cache_key)
            if cached_permissions is not None:
                logger.debug(f"从缓存获取用户 {user_id} 对资源 {resource_type}:{resource_id} 的权限")
                return json.loads(cached_permissions) if isinstance(cached_permissions, str) else cached_permissions
            
            # 从数据库获取
            user = user_crud.get(db, id=user_id)
            if not user:
                return None
            
            # 获取资源权限
            resource_permissions = user.get_resource_permissions(resource_type, resource_id)
            operation_codes = [rp.operation.value for rp in resource_permissions]
            
            # 存入缓存
            await self.cache_service.set(
                cache_key, 
                json.dumps(operation_codes),
                ttl=600  # 10分钟
            )
            
            logger.debug(f"从数据库获取并缓存用户 {user_id} 对资源 {resource_type}:{resource_id} 的权限")
            return operation_codes
            
        except Exception as e:
            logger.error(f"获取用户资源权限失败: {e}")
            return None
    
    async def check_user_permission(self, user_id: int, permission_code: str, db: Session) -> bool:
        """检查用户是否具有指定权限（带缓存）
        
        Args:
            user_id: 用户ID
            permission_code: 权限代码
            db: 数据库会话
            
        Returns:
            bool: 是否具有权限
        """
        try:
            permissions = await self.get_user_permissions(user_id, db)
            if permissions is None:
                return False
            
            return permission_code in permissions
            
        except Exception as e:
            logger.error(f"检查用户权限失败: {e}")
            return False
    
    async def check_user_resource_permission(
        self, 
        user_id: int, 
        resource_type: str, 
        resource_id: str, 
        operation: str, 
        db: Session
    ) -> bool:
        """检查用户是否对特定资源具有操作权限（带缓存）
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            operation: 操作类型
            db: 数据库会话
            
        Returns:
            bool: 是否具有权限
        """
        try:
            permissions = await self.get_user_resource_permissions(user_id, resource_type, resource_id, db)
            if permissions is None:
                return False
            
            return operation in permissions
            
        except Exception as e:
            logger.error(f"检查用户资源权限失败: {e}")
            return False
    
    async def invalidate_user_cache(self, user_id: int):
        """清除用户相关缓存
        
        Args:
            user_id: 用户ID
        """
        try:
            # 清除用户权限缓存
            user_perm_key = self._generate_cache_key("user_perm", user_id)
            await self.cache_service.delete(user_perm_key)
            
            # 清除用户资源权限缓存（通过模式匹配）
            res_perm_pattern = self._generate_cache_key("res_perm", user_id, "*")
            await self.cache_service.delete_pattern(res_perm_pattern)
            
            logger.info(f"清除用户 {user_id} 相关缓存")
            
        except Exception as e:
            logger.error(f"清除用户缓存失败: {e}")
    
    async def invalidate_role_cache(self, role_id: int):
        """清除角色相关缓存
        
        Args:
            role_id: 角色ID
        """
        try:
            # 清除角色权限缓存
            role_perm_key = self._generate_cache_key("role_perm", role_id)
            await self.cache_service.delete(role_perm_key)
            
            logger.info(f"清除角色 {role_id} 相关缓存")
            
        except Exception as e:
            logger.error(f"清除角色缓存失败: {e}")
    
    async def invalidate_all_permission_cache(self):
        """清除所有权限缓存"""
        try:
            await self.cache_service.clear()
            
            logger.info("清除所有权限缓存")
            
        except Exception as e:
            logger.error(f"清除所有权限缓存失败: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        try:
            stats = await self.cache_service.get_stats()
            return stats
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    async def warm_up_cache(self, db: Session, user_ids: Optional[List[int]] = None):
        """预热缓存
        
        Args:
            db: 数据库会话
            user_ids: 要预热的用户ID列表，None表示所有活跃用户
        """
        try:
            if user_ids is None:
                # 获取所有活跃用户
                users = db.query(User).filter(User.is_active == True).all()
                user_ids = [user.id for user in users]
            
            logger.info(f"开始预热 {len(user_ids)} 个用户的权限缓存")
            
            for user_id in user_ids:
                # 预热用户权限
                await self.get_user_permissions(user_id, db)
                
                # 预热用户角色权限
                user = user_crud.get(db, id=user_id)
                if user and user.primary_role:
                    await self.get_role_permissions(user.primary_role.id, db)
            
            logger.info("权限缓存预热完成")
            
        except Exception as e:
            logger.error(f"权限缓存预热失败: {e}")


# 全局权限缓存管理器实例
permission_cache_manager = PermissionCacheManager()


def cache_permission_check(func):
    """权限检查缓存装饰器
    
    自动缓存权限检查结果并记录监控数据
    """
    import time
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # 提取参数
        if len(args) >= 3:
            self, user, permission_code = args[0], args[1], args[2]
        else:
            return func(*args, **kwargs)
        
        # 生成缓存键
        cache_key = f"perm_check:{user.id}:{permission_code}"
        
        try:
            # 尝试从缓存获取
            cache_manager = get_permission_cache_manager()
            cached_result = await cache_manager.check_user_permission(user.id, permission_code, kwargs.get('db'))
            
            if cached_result is not None:
                response_time = time.time() - start_time
                logger.debug(f"权限检查缓存命中: {cache_key}")
                record_cache_operation(
                    operation_type='get',
                    cache_type='permission_check',
                    key=cache_key,
                    hit=True,
                    response_time=response_time,
                    user_id=user.id
                )
                return cached_result
            
            # 执行原始函数
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            response_time = time.time() - start_time
            
            # 记录缓存未命中
            record_cache_operation(
                operation_type='get',
                cache_type='permission_check',
                key=cache_key,
                hit=False,
                response_time=response_time,
                user_id=user.id
            )
            
            logger.debug(f"权限检查结果已缓存: {cache_key} = {result}")
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"权限检查缓存装饰器失败: {e}")
            
            # 记录错误
            record_cache_operation(
                operation_type='get',
                cache_type='permission_check',
                key=cache_key,
                hit=False,
                response_time=response_time,
                user_id=getattr(user, 'id', None),
                error=str(e)
            )
            
            # 降级到原始函数
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
    
    return wrapper


def get_permission_cache_manager() -> PermissionCacheManager:
    """获取权限缓存管理器
    
    Returns:
        PermissionCacheManager: 权限缓存管理器实例
    """
    return permission_cache_manager