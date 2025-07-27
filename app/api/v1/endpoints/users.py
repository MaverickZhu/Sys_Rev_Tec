from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.middleware import moderate_rate_limit

router = APIRouter()


@router.post(
    "/", 
    response_model=schemas.User,
    summary="创建新用户",
    description="注册一个新的系统用户账户"
)
@moderate_rate_limit
def create_user(
    request: Request,
    *, 
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    创建新用户
    
    - **user_in**: 用户注册信息（用户名、密码、邮箱等）
    - **返回**: 创建的用户信息（不包含密码）
    - **验证**: 检查用户名唯一性
    - **权限**: 公开接口，无需认证
    """
    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user