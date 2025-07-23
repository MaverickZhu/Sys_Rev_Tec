from enum import Enum
from typing import List, Set
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.api.deps import get_current_user, get_db


class Permission(str, Enum):
    """权限枚举"""
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # 角色管理权限
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_LIST = "role:list"
    
    # 项目管理权限
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_LIST = "project:list"
    PROJECT_ASSIGN = "project:assign"
    
    # 文档管理权限
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_LIST = "document:list"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_DOWNLOAD = "document:download"
    
    # 审查权限
    REVIEW_CREATE = "review:create"
    REVIEW_READ = "review:read"
    REVIEW_UPDATE = "review:update"
    REVIEW_DELETE = "review:delete"
    REVIEW_LIST = "review:list"
    REVIEW_ASSIGN = "review:assign"
    REVIEW_APPROVE = "review:approve"
    REVIEW_REJECT = "review:reject"
    
    # OCR权限
    OCR_PROCESS = "ocr:process"
    OCR_RESULT_READ = "ocr:result:read"
    
    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_MONITOR = "system:monitor"


class RolePermissions:
    """角色权限配置"""
    
    # 超级管理员 - 拥有所有权限
    SUPER_ADMIN = [perm.value for perm in Permission]
    
    # 系统管理员
    ADMIN = [
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_LIST,
        Permission.ROLE_CREATE,
        Permission.ROLE_READ,
        Permission.ROLE_UPDATE,
        Permission.ROLE_LIST,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_LIST,
        Permission.PROJECT_ASSIGN,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_LIST,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.REVIEW_CREATE,
        Permission.REVIEW_READ,
        Permission.REVIEW_UPDATE,
        Permission.REVIEW_LIST,
        Permission.REVIEW_ASSIGN,
        Permission.OCR_PROCESS,
        Permission.OCR_RESULT_READ,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_AUDIT,
        Permission.SYSTEM_MONITOR,
    ]
    
    # 项目经理
    PROJECT_MANAGER = [
        Permission.USER_READ,
        Permission.USER_LIST,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_LIST,
        Permission.PROJECT_ASSIGN,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_LIST,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.REVIEW_CREATE,
        Permission.REVIEW_READ,
        Permission.REVIEW_UPDATE,
        Permission.REVIEW_LIST,
        Permission.REVIEW_ASSIGN,
        Permission.OCR_PROCESS,
        Permission.OCR_RESULT_READ,
    ]
    
    # 高级审查员
    SENIOR_REVIEWER = [
        Permission.USER_READ,
        Permission.PROJECT_READ,
        Permission.PROJECT_LIST,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_LIST,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.REVIEW_CREATE,
        Permission.REVIEW_READ,
        Permission.REVIEW_UPDATE,
        Permission.REVIEW_LIST,
        Permission.REVIEW_APPROVE,
        Permission.REVIEW_REJECT,
        Permission.OCR_PROCESS,
        Permission.OCR_RESULT_READ,
    ]
    
    # 普通审查员
    REVIEWER = [
        Permission.PROJECT_READ,
        Permission.PROJECT_LIST,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_LIST,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.REVIEW_CREATE,
        Permission.REVIEW_READ,
        Permission.REVIEW_UPDATE,
        Permission.REVIEW_LIST,
        Permission.OCR_PROCESS,
        Permission.OCR_RESULT_READ,
    ]
    
    # 普通用户
    USER = [
        Permission.PROJECT_READ,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_LIST,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.REVIEW_READ,
        Permission.OCR_RESULT_READ,
    ]


def get_user_permissions(user: User) -> Set[str]:
    """获取用户权限集合"""
    permissions = set()
    
    # 超级用户拥有所有权限
    if user.is_superuser:
        return set(RolePermissions.SUPER_ADMIN)
    
    # 从角色获取权限
    if user.role and user.role.permissions:
        import json
        try:
            role_permissions = json.loads(user.role.permissions)
            if isinstance(role_permissions, list):
                permissions.update(role_permissions)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 从用户额外权限获取
    if user.permissions:
        import json
        try:
            user_permissions = json.loads(user.permissions)
            if isinstance(user_permissions, list):
                permissions.update(user_permissions)
        except (json.JSONDecodeError, TypeError):
            pass
    
    return permissions


def has_permission(user: User, required_permission: str) -> bool:
    """检查用户是否拥有指定权限"""
    user_permissions = get_user_permissions(user)
    return required_permission in user_permissions


def has_any_permission(user: User, required_permissions: List[str]) -> bool:
    """检查用户是否拥有任意一个指定权限"""
    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in required_permissions)


def has_all_permissions(user: User, required_permissions: List[str]) -> bool:
    """检查用户是否拥有所有指定权限"""
    user_permissions = get_user_permissions(user)
    return all(perm in user_permissions for perm in required_permissions)


def require_permission(permission: str):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从依赖注入中获取当前用户
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """任意权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: one of {permissions} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(permissions: List[str]):
    """全部权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_all_permissions(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: all of {permissions} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 权限依赖注入函数
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_permissions(*permissions: str):
    """权限依赖注入函数"""
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        for permission in permissions:
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )
        return current_user
    return permission_checker