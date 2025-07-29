from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_active_user
from app.core.auth import auth_manager
from app.core.config import settings
from app.crud.crud_user import user as user_crud
from app.crud.crud_token_blacklist import token_blacklist
from app.models.user import User
from app.schemas.user import (
    UserLogin,
    LoginResponse,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    User as UserSchema,
    PasswordChange
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2兼容的令牌登录，获取访问令牌以供将来请求使用
    """
    user = user_crud.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    elif not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 更新登录信息
    user_crud.update_login_info(db, user=user)
    
    # 生成令牌对
    tokens = auth_manager.create_token_pair(user.id)
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSchema.from_orm(user)
    )


@router.post("/login/json", response_model=LoginResponse)
def login_json(
    user_in: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    JSON格式登录接口
    """
    user = user_crud.authenticate(
        db, username=user_in.username, password=user_in.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    elif not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 更新登录信息
    user_crud.update_login_info(db, user=user)
    
    # 生成令牌对
    tokens = auth_manager.create_token_pair(user.id)
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSchema.from_orm(user)
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> Any:
    """
    刷新访问令牌
    """
    try:
        # 验证刷新令牌
        payload = auth_manager.verify_token(token_data.refresh_token, "refresh")
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 检查刷新令牌是否在黑名单中
        if jti and token_blacklist.is_token_blacklisted(db, jti=jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌已失效"
            )
        
        # 检查用户是否存在且活跃
        user = user_crud.get(db, id=int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        if not user_crud.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )
        
        # 生成新的访问令牌
        access_token = auth_manager.create_access_token(
            data={"sub": str(user.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )


@router.post("/register", response_model=UserSchema)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户注册
    """
    # 检查用户名是否已存在
    user = user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    user = user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    user = user_crud.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取当前用户信息
    """
    return current_user


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    修改密码
    """
    # 验证当前密码
    if not auth_manager.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    user_crud.update_password(db, user=current_user, new_password=password_data.new_password)
    
    return {"message": "密码修改成功"}


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    用户登出 - 将当前token加入黑名单
    """
    try:
        # 从请求头中提取token
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未找到认证令牌"
            )
        
        scheme, token = get_authorization_scheme_param(authorization)
        if not token or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的认证令牌格式"
            )
        
        # 解码token获取信息
        payload = auth_manager.verify_token(token, "access")
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if not jti or not exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="令牌缺少必要信息"
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
    except Exception as e:
        # 即使加入黑名单失败，也返回成功（客户端仍应删除令牌）
        return {"message": "登出成功"}


@router.get("/test-token", response_model=UserSchema)
def test_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    测试访问令牌
    """
    return current_user