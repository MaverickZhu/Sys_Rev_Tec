from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.schemas import user as user_schemas
from app.api import deps
from app.models.user import User

router = APIRouter()

# 模拟用户数据
MOCK_USERS = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@gov.cn",
        "full_name": "张三",
        "is_active": True,
        "is_superuser": True,
        "department": "信息中心",
        "position": "系统管理员",
        "phone": "13800138001",
        "avatar": "/avatars/admin.jpg",
        "created_at": "2025-01-01T00:00:00Z",
        "last_login": "2025-08-05T08:00:00Z"
    },
    {
        "id": 2,
        "username": "reviewer",
        "email": "reviewer@gov.cn",
        "full_name": "李四",
        "is_active": True,
        "is_superuser": False,
        "department": "审查部",
        "position": "审查员",
        "phone": "13800138002",
        "avatar": "/avatars/reviewer.jpg",
        "created_at": "2025-01-15T00:00:00Z",
        "last_login": "2025-08-04T16:30:00Z"
    },
    {
        "id": 3,
        "username": "analyst",
        "email": "analyst@gov.cn",
        "full_name": "王五",
        "is_active": True,
        "is_superuser": False,
        "department": "分析部",
        "position": "分析师",
        "phone": "13800138003",
        "avatar": "/avatars/analyst.jpg",
        "created_at": "2025-02-01T00:00:00Z",
        "last_login": "2025-08-03T14:20:00Z"
    },
    {
        "id": 4,
        "username": "operator",
        "email": "operator@gov.cn",
        "full_name": "赵六",
        "is_active": False,
        "is_superuser": False,
        "department": "运营部",
        "position": "操作员",
        "phone": "13800138004",
        "avatar": "/avatars/operator.jpg",
        "created_at": "2025-03-01T00:00:00Z",
        "last_login": "2025-07-20T10:15:00Z"
    }
]


@router.get(
    "/",
    summary="获取用户列表",
    description="获取系统中所有用户的列表",
)
def read_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    department: str = None,
    is_active: bool = None,
) -> Any:
    """
    获取用户列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **search**: 搜索关键词（用户名、姓名、邮箱）
    - **department**: 部门过滤
    - **is_active**: 状态过滤
    """
    users = MOCK_USERS.copy()
    
    # 搜索过滤
    if search:
        users = [
            user for user in users
            if search.lower() in user["username"].lower() or
               search.lower() in user["full_name"].lower() or
               search.lower() in user["email"].lower()
        ]
    
    # 部门过滤
    if department:
        users = [user for user in users if user["department"] == department]
    
    # 状态过滤
    if is_active is not None:
        users = [user for user in users if user["is_active"] == is_active]
    
    # 分页
    total = len(users)
    users = users[skip:skip + limit]
    
    return {
        "users": users,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post(
    "/",
    summary="创建新用户",
    description="创建一个新的系统用户账户",
)
def create_user(
    user_in: user_schemas.UserCreate,
) -> Any:
    """
    创建新用户

    - **user_in**: 用户注册信息（用户名、密码、邮箱等）
    - **返回**: 创建的用户信息（不包含密码）
    - **验证**: 检查用户名和邮箱唯一性
    """
    # 检查用户名是否已存在
    for user in MOCK_USERS:
        if user["username"] == user_in.username:
            raise HTTPException(
                status_code=400,
                detail="用户名已存在",
            )
        if user["email"] == user_in.email:
            raise HTTPException(
                status_code=400,
                detail="邮箱已被注册",
            )
    
    # 创建新用户（模拟）
    new_user = {
        "id": max([u["id"] for u in MOCK_USERS]) + 1,
        "username": user_in.username,
        "email": user_in.email,
        "full_name": getattr(user_in, 'full_name', user_in.username),
        "is_active": True,
        "is_superuser": getattr(user_in, 'is_superuser', False),
        "department": getattr(user_in, 'department', '未分配'),
        "position": getattr(user_in, 'position', '员工'),
        "phone": getattr(user_in, 'phone', ''),
        "avatar": "/avatars/default.jpg",
        "created_at": "2025-08-05T08:30:00Z",
        "last_login": None
    }
    
    return {
        "message": "用户创建成功",
        "user": new_user
    }


@router.get(
    "/me",
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
def read_user_me() -> Any:
    """
    获取当前用户信息

    - **返回**: 当前用户的详细信息
    """
    # 返回默认管理员用户信息（模拟）
    return MOCK_USERS[0]


@router.get(
    "/{user_id}",
    summary="根据ID获取用户",
    description="根据用户ID获取用户详细信息",
)
def read_user_by_id(
    user_id: int,
) -> Any:
    """
    根据ID获取用户

    - **user_id**: 用户ID
    - **返回**: 用户详细信息
    """
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    return user


@router.put(
    "/{user_id}",
    summary="更新用户信息",
    description="更新指定用户的信息",
)
def update_user(
    user_id: int,
    user_in: user_schemas.UserUpdate,
) -> Any:
    """
    更新用户信息

    - **user_id**: 用户ID
    - **user_in**: 更新的用户信息
    - **返回**: 更新后的用户信息
    """
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    # 检查用户名唯一性（如果要更新用户名）
    if hasattr(user_in, 'username') and user_in.username and user_in.username != user["username"]:
        existing_user = next((u for u in MOCK_USERS if u["username"] == user_in.username), None)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="用户名已存在",
            )

    # 检查邮箱唯一性（如果要更新邮箱）
    if hasattr(user_in, 'email') and user_in.email and user_in.email != user["email"]:
        existing_user = next((u for u in MOCK_USERS if u["email"] == user_in.email), None)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="邮箱已被注册",
            )

    # 更新用户信息（模拟）
    updated_user = user.copy()
    update_data = user_in.dict(exclude_unset=True)
    updated_user.update(update_data)
    
    return {
        "message": "用户信息更新成功",
        "user": updated_user
    }


@router.delete(
    "/{user_id}",
    summary="删除用户",
    description="删除指定的用户",
)
def delete_user(
    user_id: int,
) -> Any:
    """
    删除用户

    - **user_id**: 用户ID
    """
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    # 防止删除管理员账户
    if user_id == 1:
        raise HTTPException(
            status_code=400,
            detail="不能删除管理员账户",
        )
    
    return {
        "message": f"用户 {user['full_name']} 删除成功"
    }
