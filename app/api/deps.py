from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.core.auth import auth_manager, security
from app.crud.crud_user import user as user_crud

"""
API依赖模块

提供数据库会话和用户认证相关的依赖函数。
"""


def get_db() -> Generator:
    """获取数据库会话

    Returns:
        Generator: 数据库会话生成器
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前认证用户
    
    Args:
        db: 数据库会话
        credentials: HTTP认证凭据
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    # 提取并验证token
    token = auth_manager.extract_token_from_credentials(credentials)
    payload = auth_manager.verify_token(token, "access")
    
    # 获取用户ID
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户
    user = user_crud.get(db, id=int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查用户状态
    if not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 活跃用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出异常
    """
    if not user_crud.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 超级用户对象
        
    Raises:
        HTTPException: 用户不是超级用户时抛出异常
    """
    if not user_crud.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取可选的当前用户（用于可选认证的接口）
    
    Args:
        db: 数据库会话
        credentials: HTTP认证凭据（可选）
        
    Returns:
        Optional[User]: 用户对象或None
    """
    if not credentials:
        return None
    
    try:
        token = auth_manager.extract_token_from_credentials(credentials)
        payload = auth_manager.verify_token(token, "access")
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
            
        user = user_crud.get(db, id=int(user_id))
        if user and user_crud.is_active(user):
            return user
    except Exception:
        pass
    
    return None
