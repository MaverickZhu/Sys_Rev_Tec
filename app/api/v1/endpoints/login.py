from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()


@router.post(
    "/login/access-token", 
    response_model=schemas.Token,
    summary="用户登录获取访问令牌",
    description="使用用户名和密码登录，获取JWT访问令牌用于后续API调用"
)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录获取访问令牌
    
    - **form_data**: OAuth2表单数据（用户名和密码）
    - **返回**: JWT访问令牌和令牌类型
    - **验证**: 检查用户凭据和账户状态
    - **令牌**: Bearer类型，用于Authorization头
    - **有效期**: 根据系统配置设定
    """
    user = crud.user.authenticate(
        db,
        username=form_data.username,
        password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }