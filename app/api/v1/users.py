#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理API模块

功能:
1. 用户注册
2. 用户登录
3. 用户信息管理
4. 权限控制
5. 密码管理
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_superuser, get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    Token,
    UserCreate,
    UserList,
    UserPermission,
    UserProfile,
    UserResponse,
    UserUpdate,
)
from app.services.audit_service import AuditService
from app.services.user_service import UserService
from app.utils.cache import cache_manager
from app.utils.response import success_response

router = APIRouter()
user_service = UserService()
audit_service = AuditService()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    Args:
        user_data: 用户注册数据
        db: 数据库会话

    Returns:
        UserResponse: 注册成功的用户信息

    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    try:
        # 检查用户名是否已存在
        existing_user = (
            db.query(User)
            .filter(
                or_(User.username == user_data.username, User.email == user_data.email)
            )
            .first()
        )

        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在"
                )

        # 创建新用户
        user = await user_service.create_user(db, user_data)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=user.id,
            action="USER_REGISTER",
            resource_type="user",
            resource_id=str(user.id),
            details={"username": user.username, "email": user.email},
        )

        return success_response(
            data=UserResponse.from_orm(user), message="用户注册成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}",
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    用户登录

    Args:
        form_data: 登录表单数据
        db: 数据库会话

    Returns:
        Token: 访问令牌和用户信息

    Raises:
        HTTPException: 用户名或密码错误
    """
    try:
        # 验证用户凭据
        user = await user_service.authenticate_user(
            db, form_data.username, form_data.password
        )

        if not user:
            # 记录登录失败
            await audit_service.log_action(
                db=db,
                user_id=None,
                action="LOGIN_FAILED",
                resource_type="auth",
                details={
                    "username": form_data.username,
                    "reason": "invalid_credentials",
                },
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户账户已被禁用"
            )

        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )

        # 更新最后登录时间
        await user_service.update_last_login(db, user.id)

        # 记录登录成功
        await audit_service.log_action(
            db=db,
            user_id=user.id,
            action="LOGIN_SUCCESS",
            resource_type="auth",
            details={"username": user.username},
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}",
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    Args:
        current_user: 当前登录用户

    Returns:
        UserProfile: 用户详细信息
    """
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新当前用户信息

    Args:
        user_update: 用户更新数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        UserResponse: 更新后的用户信息
    """
    try:
        # 检查邮箱是否已被其他用户使用
        if user_update.email and user_update.email != current_user.email:
            existing_user = (
                db.query(User)
                .filter(
                    and_(User.email == user_update.email, User.id != current_user.id)
                )
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被其他用户使用",
                )

        # 更新用户信息
        updated_user = await user_service.update_user(db, current_user.id, user_update)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="USER_UPDATE",
            resource_type="user",
            resource_id=str(current_user.id),
            details=user_update.dict(exclude_unset=True),
        )

        # 清除用户缓存
        await cache_manager.delete(f"user:{current_user.id}")

        return success_response(
            data=UserResponse.from_orm(updated_user), message="用户信息更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}",
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    修改密码

    Args:
        password_data: 密码修改数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 操作结果
    """
    try:
        # 验证当前密码
        if not verify_password(
            password_data.current_password, current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误"
            )

        # 更新密码
        new_hashed_password = get_password_hash(password_data.new_password)
        await user_service.update_password(db, current_user.id, new_hashed_password)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PASSWORD_CHANGE",
            resource_type="user",
            resource_id=str(current_user.id),
        )

        return success_response(message="密码修改成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}",
        )


@router.get("/", response_model=UserList)
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    role: Optional[str] = Query(None, description="用户角色"),
    db: Session = Depends(get_db),
):
    """
    获取用户列表（仅管理员）

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        search: 搜索关键词
        is_active: 是否激活
        role: 用户角色
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        UserList: 用户列表和分页信息
    """
    try:
        # 构建查询
        query = db.query(User)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

        # 状态过滤
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # 角色过滤
        if role:
            query = query.filter(User.role == role)

        # 分页
        total = query.count()
        users = query.offset(skip).limit(limit).all()

        return {
            "users": [UserResponse.from_orm(user) for user in users],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    获取指定用户信息（仅管理员）

    Args:
        user_id: 用户ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        UserProfile: 用户详细信息
    """
    try:
        # 尝试从缓存获取
        cached_user = await cache_manager.get(f"user:{user_id}")
        if cached_user:
            return UserProfile.parse_raw(cached_user)

        # 从数据库获取
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        user_profile = UserProfile.from_orm(user)

        # 缓存用户信息
        await cache_manager.set(
            f"user:{user_id}", user_profile.json(), expire=3600  # 1小时
        )

        return user_profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}",
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    更新指定用户信息（仅管理员）

    Args:
        user_id: 用户ID
        user_update: 用户更新数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        UserResponse: 更新后的用户信息
    """
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 检查邮箱是否已被其他用户使用
        if user_update.email and user_update.email != user.email:
            existing_user = (
                db.query(User)
                .filter(and_(User.email == user_update.email, User.id != user_id))
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被其他用户使用",
                )

        # 更新用户信息
        updated_user = await user_service.update_user(db, user_id, user_update)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="USER_UPDATE_ADMIN",
            resource_type="user",
            resource_id=str(user_id),
            details=user_update.dict(exclude_unset=True),
        )

        # 清除用户缓存
        await cache_manager.delete(f"user:{user_id}")

        return success_response(
            data=UserResponse.from_orm(updated_user), message="用户信息更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}",
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    删除用户（仅管理员）

    Args:
        user_id: 用户ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 操作结果
    """
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 不能删除自己
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账户"
            )

        # 软删除用户
        await user_service.delete_user(db, user_id)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="USER_DELETE",
            resource_type="user",
            resource_id=str(user_id),
            details={"deleted_username": user.username},
        )

        # 清除用户缓存
        await cache_manager.delete(f"user:{user_id}")

        return success_response(message="用户删除成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}",
        )


@router.post("/{user_id}/permissions", response_model=UserPermission)
async def update_user_permissions(
    user_id: int,
    permissions: UserPermission,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    更新用户权限（仅管理员）

    Args:
        user_id: 用户ID
        permissions: 权限数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        UserPermission: 更新后的权限信息
    """
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 更新权限
        updated_permissions = await user_service.update_user_permissions(
            db, user_id, permissions
        )

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="USER_PERMISSION_UPDATE",
            resource_type="user",
            resource_id=str(user_id),
            details=permissions.dict(),
        )

        # 清除用户缓存
        await cache_manager.delete(f"user:{user_id}")

        return success_response(data=updated_permissions, message="用户权限更新成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新权限失败: {str(e)}",
        )
