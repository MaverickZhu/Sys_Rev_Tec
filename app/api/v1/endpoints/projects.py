# 移除限流中间件导入


from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.project import Project
from app.utils.cache_decorator import fastapi_cache_medium

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Project,
    summary="创建新项目",
    description="创建一个新的政府采购项目审查项目",
)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
) -> Any:
    """
    创建新项目

    - **project_in**: 项目创建信息（名称、描述等）
    - **返回**: 创建的项目详细信息
    - **权限**: 需要用户登录认证
    """
    project = crud.project.create_with_owner(db=db, obj_in=project_in, owner_id=1)
    return project


@router.get(
    "/",
    response_model=List[schemas.Project],
    summary="获取项目列表",
    description="分页获取当前用户的项目列表",
)
@fastapi_cache_medium
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取项目列表

    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数（默认100）
    - **返回**: 当前用户的项目列表
    - **权限**: 需要用户登录认证
    """
    projects = crud.project.get_multi(db, skip=skip, limit=limit)
    return projects


@router.get(
    "/{project_id}",
    response_model=schemas.Project,
    summary="获取项目详情",
    description="根据项目ID获取项目详细信息",
)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
) -> Any:
    """
    获取项目详情

    - **project_id**: 项目ID
    - **返回**: 项目详细信息
    - **权限**: 需要用户登录认证
    """
    # 直接从数据库查询，避免缓存问题
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project
