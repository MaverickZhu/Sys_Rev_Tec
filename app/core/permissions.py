"""权限验证核心模块

提供权限检查装饰器和权限验证功能
"""

import json
import logging
from functools import wraps
from typing import List, Optional, Union, Callable, Any

from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.permission import Permission, ResourceType, OperationType, PermissionLevel
from app.crud.crud_user import user as user_crud
from app.crud.crud_permission import permission as permission_crud
from app.core.permission_cache import get_permission_cache_manager, cache_permission_check
from app.core.permission_query_optimizer import get_permission_query_optimizer

logger = logging.getLogger(__name__)


class PermissionChecker:
    """权限检查器
    
    提供各种权限检查方法，集成缓存和查询优化功能
    """
    
    def __init__(self, db: Session, use_cache: bool = True, use_optimization: bool = True):
        self.db = db
        self.use_cache = use_cache
        self.use_optimization = use_optimization
        self.cache_manager = get_permission_cache_manager() if use_cache else None
        self.query_optimizer = get_permission_query_optimizer(db, use_cache) if use_optimization else None
    
    @cache_permission_check
    def check_permission(self, user: User, permission_code: str) -> bool:
        """检查用户是否具有指定权限
        
        Args:
            user: 用户对象
            permission_code: 权限代码
            
        Returns:
            bool: 是否具有权限
        """
        try:
            # 优先使用优化查询
            if self.use_optimization and self.query_optimizer:
                return self.query_optimizer.optimize_permission_query(user.id, permission_code)
            
            # 其次使用缓存
            if self.use_cache and self.cache_manager:
                return self.cache_manager.check_user_permission(user.id, permission_code, self.db)
            
            # 降级到原始方法
            return user.has_permission(permission_code)
        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False
    
    @cache_permission_check
    def check_role(self, user: User, role_code: str) -> bool:
        """检查用户是否具有指定角色
        
        Args:
            user: 用户对象
            role_code: 角色代码
            
        Returns:
            bool: 是否具有角色
        """
        try:
            # 优先使用缓存
            if self.use_cache and self.cache_manager:
                return self.cache_manager.check_user_role(user.id, role_code, self.db)
            
            # 降级到原始方法
            # 检查基础角色
            if user.role.value == role_code:
                return True
            
            # 检查主要角色
            if user.primary_role and user.primary_role.code == role_code:
                return True
            
            return False
        except Exception as e:
            logger.error(f"角色检查失败: {e}")
            return False
    
    @cache_permission_check
    def check_resource_permission(
        self, 
        user: User, 
        resource_type: str, 
        resource_id: str, 
        operation: str
    ) -> bool:
        """检查用户是否对特定资源具有操作权限
        
        Args:
            user: 用户对象
            resource_type: 资源类型
            resource_id: 资源ID
            operation: 操作类型
            
        Returns:
            bool: 是否具有权限
        """
        try:
            # 优先使用缓存
            if self.use_cache and self.cache_manager:
                return self.cache_manager.check_user_resource_permission(
                    user.id, resource_type, resource_id, operation, self.db
                )
            
            # 降级到原始方法
            return user.has_resource_permission(resource_type, resource_id, operation)
        except Exception as e:
            logger.error(f"资源权限检查失败: {e}")
            return False
    
    def check_any_permission(self, user: User, permission_codes: List[str]) -> bool:
        """检查用户是否具有任一权限
        
        Args:
            user: 用户对象
            permission_codes: 权限代码列表
            
        Returns:
            bool: 是否具有任一权限
        """
        for permission_code in permission_codes:
            if self.check_permission(user, permission_code):
                return True
        return False
    
    def check_all_permissions(self, user: User, permission_codes: List[str]) -> bool:
        """检查用户是否具有所有权限
        
        Args:
            user: 用户对象
            permission_codes: 权限代码列表
            
        Returns:
            bool: 是否具有所有权限
        """
        for permission_code in permission_codes:
            if not self.check_permission(user, permission_code):
                return False
        return True


def require_permission(
    permission_code: str,
    error_message: Optional[str] = None,
    use_cache: bool = True,
    use_optimization: bool = True
):
    """权限检查装饰器
    
    Args:
        permission_code: 需要的权限代码
        error_message: 自定义错误消息
        use_cache: 是否使用缓存
        use_optimization: 是否使用查询优化
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取依赖
            db: Session = kwargs.get('db') or next(get_db())
            current_user: User = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败，请先登录"
                )
            
            # 检查权限（使用缓存和优化）
            checker = PermissionChecker(db, use_cache=use_cache, use_optimization=use_optimization)
            if not checker.check_permission(current_user, permission_code):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or f"权限不足，需要权限: {permission_code}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(
    role_name: str,
    error_message: Optional[str] = None,
    use_cache: bool = True,
    use_optimization: bool = True
):
    """角色检查装饰器
    
    Args:
        role_name: 需要的角色名称
        error_message: 自定义错误消息
        use_cache: 是否使用缓存
        use_optimization: 是否使用查询优化
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取依赖
            db: Session = kwargs.get('db') or next(get_db())
            current_user: User = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败，请先登录"
                )
            
            # 检查角色（使用缓存和优化）
            checker = PermissionChecker(db, use_cache=use_cache, use_optimization=use_optimization)
            if not checker.check_role(current_user, role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or f"权限不足，需要角色: {role_name}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(
    permission_codes: List[str],
    error_message: Optional[str] = None,
    use_cache: bool = True
):
    """任一权限检查装饰器
    
    Args:
        permission_codes: 权限代码列表
        error_message: 自定义错误消息
        use_cache: 是否使用缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取依赖
            db: Session = kwargs.get('db') or next(get_db())
            current_user: User = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败，请先登录"
                )
            
            # 检查权限（使用缓存）
            checker = PermissionChecker(db, use_cache=use_cache)
            if not checker.check_any_permission(current_user, permission_codes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or f"权限不足，需要以下任一权限: {', '.join(permission_codes)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(
    permission_codes: List[str],
    error_message: Optional[str] = None,
    use_cache: bool = True
):
    """所有权限检查装饰器
    
    Args:
        permission_codes: 权限代码列表
        error_message: 自定义错误消息
        use_cache: 是否使用缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取依赖
            db: Session = kwargs.get('db') or next(get_db())
            current_user: User = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败，请先登录"
                )
            
            # 检查权限（使用缓存）
            checker = PermissionChecker(db, use_cache=use_cache)
            if not checker.check_all_permissions(current_user, permission_codes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or f"权限不足，需要以下所有权限: {', '.join(permission_codes)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_resource_permission(
    resource_type: str,
    operation: str,
    resource_id_param: str = "id",
    error_message: Optional[str] = None,
    use_cache: bool = True
):
    """资源权限检查装饰器
    
    Args:
        resource_type: 资源类型
        operation: 操作类型
        resource_id_param: 资源ID参数名
        error_message: 自定义错误消息
        use_cache: 是否使用缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取依赖
            db: Session = kwargs.get('db') or next(get_db())
            current_user: User = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败，请先登录"
                )
            
            # 获取资源ID
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"缺少资源ID参数: {resource_id_param}"
                )
            
            # 检查资源权限（使用缓存）
            checker = PermissionChecker(db, use_cache=use_cache)
            if not checker.check_resource_permission(current_user, resource_type, str(resource_id), operation):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or f"权限不足，无法对资源 {resource_type}:{resource_id} 执行 {operation} 操作"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# FastAPI依赖函数
def get_permission_checker(db: Session = Depends(get_db), use_cache: bool = True) -> PermissionChecker:
    """获取权限检查器依赖
    
    Args:
        db: 数据库会话
        use_cache: 是否使用缓存
        
    Returns:
        PermissionChecker: 权限检查器实例
    """
    return PermissionChecker(db, use_cache=use_cache)


def check_user_permission(
    permission_code: str,
    current_user: User = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker)
) -> bool:
    """检查用户权限的依赖函数"""
    if not checker.check_permission(current_user, permission_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission_code}"
        )
    return True


def check_user_role(
    role_code: str,
    current_user: User = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker)
) -> bool:
    """检查用户角色的依赖函数"""
    if not checker.check_role(current_user, role_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要角色: {role_code}"
        )
    return True


# 权限常量定义
class Permissions:
    """权限常量类"""
    
    # 项目权限
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE = "project:manage"
    
    # 文档权限
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_DOWNLOAD = "document:download"
    
    # 报告权限
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_UPDATE = "report:update"
    REPORT_DELETE = "report:delete"
    REPORT_EXPORT = "report:export"
    REPORT_ANALYZE = "report:analyze"
    
    # 用户权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"
    
    # 系统权限
    SYSTEM_CONFIGURE = "system:configure"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_BACKUP = "system:backup"
    
    # 审计权限
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    AUDIT_ANALYZE = "audit:analyze"


class Roles:
    """角色常量类"""
    
    ADMIN = "admin"
    USER = "user"
    REVIEWER = "reviewer"
    MANAGER = "manager"
    AUDITOR = "auditor"
    ANALYST = "analyst"
    OPERATOR = "operator"