from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.post(
    "/", 
    response_model=schemas.Project,
    summary="创建新项目",
    description="创建一个新的政府采购项目审查项目"
)
def create_project(
    *, 
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    创建新项目
    
    - **project_in**: 项目创建信息（名称、描述等）
    - **返回**: 创建的项目详细信息
    - **权限**: 需要用户登录认证
    """
    project = crud.project.create_with_owner(db=db, obj_in=project_in, owner_id=current_user.id)
    return project


@router.get(
    "/", 
    response_model=List[schemas.Project],
    summary="获取项目列表",
    description="分页获取所有项目列表"
)
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    获取项目列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数（默认100）
    - **返回**: 项目列表
    - **权限**: 需要用户登录认证
    """
    projects = crud.project.get_multi(db, skip=skip, limit=limit)
    return projects