from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user, get_db
from app.core.auth import auth_manager
from app.core.config import settings
from app.crud.crud_token_blacklist import token_blacklist
from app.crud.crud_user import user as user_crud
from app.models.user import User
from app.schemas.user import (
    LoginResponse,
    PasswordChange,
    TokenRefresh,
    TokenResponse,
)
from app.schemas.user import User as UserSchema
from app.schemas.user import (
    UserCreate,
    UserLogin,
)

router = APIRouter()


@router.post("/login")
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2兼容的令牌登录，获取访问令牌以供将来请求使用
    """
    # 模拟用户认证
    if form_data.username == "admin" and form_data.password == "admin123":
        user_data = {
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
            "last_login": "2025-08-05T08:30:00Z"
        }
    elif form_data.username == "reviewer" and form_data.password == "reviewer123":
        user_data = {
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
            "last_login": "2025-08-05T08:30:00Z"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 模拟生成令牌
    access_token = "mock_access_token_" + form_data.username
    refresh_token = "mock_refresh_token_" + form_data.username

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": user_data
    }


@router.post("/login/json")
def login_json(user_in: UserLogin) -> Any:
    """
    JSON格式登录接口
    """
    # 模拟用户认证
    if user_in.username == "admin" and user_in.password == "admin123":
        user_data = {
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
            "last_login": "2025-08-05T08:30:00Z"
        }
    elif user_in.username == "reviewer" and user_in.password == "reviewer123":
        user_data = {
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
            "last_login": "2025-08-05T08:30:00Z"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 模拟生成令牌
    access_token = "mock_access_token_" + user_in.username
    refresh_token = "mock_refresh_token_" + user_in.username

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": user_data
    }


@router.post("/refresh")
def refresh_token(token_data: TokenRefresh) -> Any:
    """
    刷新访问令牌
    """
    # 模拟刷新令牌验证
    if token_data.refresh_token.startswith("mock_refresh_token_"):
        username = token_data.refresh_token.replace("mock_refresh_token_", "")
        new_access_token = "mock_access_token_" + username + "_refreshed"
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 3600
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
        )


@router.post("/register")
def register(user_in: UserCreate) -> Any:
    """
    用户注册
    """
    # 模拟检查用户名是否已存在
    existing_usernames = ["admin", "reviewer", "analyst", "operator"]
    if user_in.username in existing_usernames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )

    # 模拟检查邮箱是否已存在
    existing_emails = ["admin@gov.cn", "reviewer@gov.cn", "analyst@gov.cn", "operator@gov.cn"]
    if user_in.email in existing_emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在"
        )

    # 模拟创建用户
    new_user = {
        "id": 5,  # 新用户ID
        "username": user_in.username,
        "email": user_in.email,
        "full_name": user_in.full_name or user_in.username,
        "is_active": True,
        "is_superuser": False,
        "department": "新用户部门",
        "position": "新用户",
        "phone": "",
        "avatar": "/avatars/default.jpg",
        "created_at": "2025-01-20T10:00:00Z",
        "last_login": None
    }
    
    return {
        "message": "注册成功",
        "user": new_user
    }


@router.get("/me")
def read_users_me() -> Any:
    """
    获取当前用户信息
    """
    # 返回模拟的当前用户信息（管理员）
    return {
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
        "last_login": "2025-08-05T08:30:00Z"
    }


@router.post("/change-password")
def change_password(password_data: PasswordChange) -> Any:
    """
    修改密码
    """
    # 模拟验证当前密码（假设当前密码是admin123）
    if password_data.current_password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误"
        )

    # 模拟密码修改成功
    return {"message": "密码修改成功"}


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    用户登出 - 将当前token加入黑名单
    """
    try:
        # 从请求头中提取token
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="未找到认证令牌"
            )

        scheme, token = get_authorization_scheme_param(authorization)
        if not token or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的认证令牌格式"
            )

        # 解码token获取信息
        payload = auth_manager.verify_token(token, "access")
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="令牌缺少必要信息"
            )

        # 将token加入黑名单
        from datetime import datetime

        expires_at = datetime.fromtimestamp(exp)

        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None

        token_blacklist.add_to_blacklist(
            db=db,
            jti=jti,
            token=token,
            user_id=current_user.id,
            token_type="access",
            expires_at=expires_at,
            reason="用户主动登出",
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return {"message": "登出成功，令牌已失效"}

    except HTTPException:
        raise
    except Exception:
        # 即使加入黑名单失败，也返回成功（客户端仍应删除令牌）
        return {"message": "登出成功"}


@router.get("/verify", response_model=UserSchema)
def verify_token(current_user: User = Depends(get_current_user)) -> Any:
    """
    验证访问令牌
    """
    return current_user


@router.get("/test-token", response_model=UserSchema)
def test_token(current_user: User = Depends(get_current_user)) -> Any:
    """
    测试访问令牌
    """
    return current_user
