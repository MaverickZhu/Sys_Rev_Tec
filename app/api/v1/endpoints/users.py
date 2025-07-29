from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.User],
    summary="获取用户列表",
    description="获取系统中所有用户的列表（需要超级用户权限）",
)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    获取用户列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **权限**: 需要超级用户权限
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post(
    "/",
    response_model=schemas.User,
    summary="创建新用户",
    description="创建一个新的系统用户账户（需要超级用户权限）",
)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    创建新用户

    - **user_in**: 用户注册信息（用户名、密码、邮箱等）
    - **返回**: 创建的用户信息（不包含密码）
    - **验证**: 检查用户名和邮箱唯一性
    - **权限**: 需要超级用户权限
    """
    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在",
        )
    
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="邮箱已被注册",
        )
    
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.get(
    "/me",
    response_model=schemas.User,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取当前用户信息
    
    - **返回**: 当前用户的详细信息
    - **权限**: 需要用户认证
    """
    return current_user


@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="根据ID获取用户",
    description="根据用户ID获取用户详细信息（需要超级用户权限）",
)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    根据ID获取用户
    
    - **user_id**: 用户ID
    - **返回**: 用户详细信息
    - **权限**: 需要超级用户权限
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=schemas.User,
    summary="更新用户信息",
    description="更新指定用户的信息（需要超级用户权限）",
)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    更新用户信息
    
    - **user_id**: 用户ID
    - **user_in**: 更新的用户信息
    - **返回**: 更新后的用户信息
    - **权限**: 需要超级用户权限
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    
    # 检查用户名唯一性（如果要更新用户名）
    if user_in.username and user_in.username != user.username:
        existing_user = crud.user.get_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="用户名已存在",
            )
    
    # 检查邮箱唯一性（如果要更新邮箱）
    if user_in.email and user_in.email != user.email:
        existing_user = crud.user.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="邮箱已被注册",
            )
    
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete(
    "/{user_id}",
    summary="删除用户",
    description="删除指定的用户（需要超级用户权限）",
)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    删除用户
    
    - **user_id**: 用户ID
    - **权限**: 需要超级用户权限
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    
    # 防止删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="不能删除自己的账户",
        )
    
    user = crud.user.remove(db, id=user_id)
    return {"message": "用户删除成功"}


@router.put(
    "/me",
    response_model=schemas.User,
    summary="更新当前用户信息",
    description="更新当前登录用户的个人信息",
)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新当前用户信息
    
    - **user_in**: 更新的用户信息
    - **返回**: 更新后的用户信息
    - **权限**: 需要用户认证
    """
    # 检查用户名唯一性（如果要更新用户名）
    if user_in.username and user_in.username != current_user.username:
        existing_user = crud.user.get_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="用户名已存在",
            )
    
    # 检查邮箱唯一性（如果要更新邮箱）
    if user_in.email and user_in.email != current_user.email:
        existing_user = crud.user.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="邮箱已被注册",
            )
    
    # 普通用户不能修改角色和超级用户状态
    if hasattr(user_in, 'role'):
        user_in.role = None
    if hasattr(user_in, 'is_superuser'):
        user_in.is_superuser = None
    
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user
