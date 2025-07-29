from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.auth import auth_manager
from app.models.user import UserRole as Role

router = APIRouter()


@router.post("/add", response_model=schemas.TokenBlacklist)
def add_token_to_blacklist(
    *,
    db: Session = Depends(deps.get_db),
    token_data: schemas.TokenBlacklistCreate,
    current_user: schemas.User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    添加token到黑名单（仅管理员）
    """
    # 检查权限
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    # 获取请求信息
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    blacklist_entry = crud.token_blacklist.add_to_blacklist(
        db=db,
        jti=token_data.jti,
        token=token_data.token_hash,  # 这里假设传入的是已经哈希的值
        user_id=token_data.user_id,
        token_type=token_data.token_type,
        expires_at=token_data.expires_at,
        reason=token_data.reason,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return blacklist_entry


@router.post("/validate", response_model=schemas.TokenValidationResponse)
def validate_token(
    *,
    db: Session = Depends(deps.get_db),
    validation_request: schemas.TokenValidationRequest,
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    验证token是否在黑名单中
    """
    try:
        # 解码token获取jti
        payload = auth_manager.verify_token(validation_request.token, "access")
        jti = payload.get("jti")
        
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token: missing jti"
            )
        
        # 检查黑名单
        blacklist_info = crud.token_blacklist.get_blacklist_info(
            db=db, jti=jti
        )
        
        if blacklist_info:
            return schemas.TokenValidationResponse(
                is_blacklisted=True,
                reason=blacklist_info.reason,
                blacklisted_at=blacklist_info.blacklisted_at,
            )
        else:
            return schemas.TokenValidationResponse(
                is_blacklisted=False,
                reason=None,
                blacklisted_at=None,
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token validation failed: {str(e)}"
        )


@router.get("/list", response_model=List[schemas.TokenBlacklist])
def get_blacklist(
    *,
    db: Session = Depends(deps.get_db),
    query_params: schemas.TokenBlacklistQuery = Depends(),
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取token黑名单列表
    
    - 普通用户只能查看自己的token
    - 管理员可以查看所有token
    """
    # 如果不是管理员，只能查看自己的token
    if current_user.role != Role.ADMIN:
        query_params.user_id = current_user.id
    
    blacklist_entries = crud.token_blacklist.get_blacklist_by_query(
        db=db, query_params=query_params
    )
    return blacklist_entries


@router.get("/count")
def get_blacklist_count(
    *,
    db: Session = Depends(deps.get_db),
    query_params: schemas.TokenBlacklistQuery = Depends(),
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取token黑名单总数
    """
    # 如果不是管理员，只能查看自己的token
    if current_user.role != Role.ADMIN:
        query_params.user_id = current_user.id
    
    count = crud.token_blacklist.get_blacklist_count(
        db=db, query_params=query_params
    )
    return {"count": count}


@router.get("/stats", response_model=schemas.TokenBlacklistStats)
def get_blacklist_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取token黑名单统计信息（仅管理员）
    """
    # 检查权限
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    stats = crud.token_blacklist.get_blacklist_stats(db=db)
    return stats


@router.delete("/remove/{jti}")
def remove_from_blacklist(
    *,
    db: Session = Depends(deps.get_db),
    jti: str,
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    从黑名单中移除token（仅管理员）
    """
    # 检查权限
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    success = crud.token_blacklist.remove_from_blacklist(db=db, jti=jti)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found in blacklist"
        )
    
    return {"message": "Token removed from blacklist successfully"}


@router.post("/cleanup")
def cleanup_expired_tokens(
    *,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    清理已过期的黑名单token（仅管理员）
    """
    # 检查权限
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    removed_count = crud.token_blacklist.cleanup_expired_tokens(db=db)
    return {"message": f"Removed {removed_count} expired tokens from blacklist"}


@router.post("/blacklist-user/{user_id}")
def blacklist_user_tokens(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    reason: str = "管理员操作",
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    将指定用户的所有token加入黑名单（仅管理员）
    
    注意：这个操作主要用于紧急情况，实际的token失效需要配合JWT验证逻辑
    """
    # 检查权限
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    # 检查目标用户是否存在
    target_user = crud.user.get(db=db, id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 防止超级用户误操作自己
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot blacklist your own tokens"
        )
    
    affected_count = crud.token_blacklist.blacklist_user_tokens(
        db=db, user_id=user_id, reason=reason
    )
    
    return {
        "message": f"Blacklisted tokens for user {target_user.username}",
        "affected_count": affected_count,
        "user_id": user_id,
        "reason": reason,
    }