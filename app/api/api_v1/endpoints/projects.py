from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.permissions import (
    Permission, require_permissions, get_current_active_user,
    has_permission, get_user_permissions
)
from app.db.session import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Project])
def read_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="项目状态筛选"),
    review_status: Optional[str] = Query(None, description="审查状态筛选"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    department: Optional[str] = Query(None, description="部门筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: models.User = Depends(require_permissions(Permission.PROJECT_LIST)),
) -> Any:
    """
    获取项目列表
    """
    # 构建筛选条件
    filters = {}
    if status:
        filters["status"] = status
    if review_status:
        filters["review_status"] = review_status
    if project_type:
        filters["project_type"] = project_type
    if department:
        filters["department"] = department
    if priority:
        filters["priority"] = priority
    if risk_level:
        filters["risk_level"] = risk_level
    
    # 如果不是超级用户或管理员，只能查看自己的项目
    user_permissions = get_user_permissions(current_user)
    if not (current_user.is_superuser or Permission.PROJECT_READ in user_permissions):
        filters["owner_id"] = current_user.id
    
    if search:
        # 使用搜索功能
        projects = crud.project.search_projects(
            db, query=search, skip=skip, limit=limit
        )
    elif filters:
        # 使用筛选功能
        projects = crud.project.get_projects_by_filters(
            db, filters=filters, skip=skip, limit=limit
        )
    else:
        # 获取所有项目
        if current_user.is_superuser or Permission.PROJECT_READ in user_permissions:
            projects = crud.project.get_multi(db, skip=skip, limit=limit)
        else:
            projects = crud.project.get_by_owner(
                db, owner_id=current_user.id, skip=skip, limit=limit
            )
    
    return projects


@router.post("/", response_model=schemas.Project)
def create_project(
    *,
    db: Session = Depends(get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(require_permissions(Permission.PROJECT_CREATE)),
) -> Any:
    """
    创建新项目
    """
    # 检查项目编号是否已存在
    if crud.project.get_by_code(db, project_code=project_in.project_code):
        raise HTTPException(
            status_code=400,
            detail="项目编号已存在"
        )
    
    project = crud.project.create_with_owner(
        db=db, obj_in=project_in, owner_id=current_user.id
    )
    return project


@router.get("/statistics", response_model=Dict[str, Any])
def get_project_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.PROJECT_LIST)),
) -> Any:
    """
    获取项目统计信息
    """
    # 如果不是超级用户或管理员，只统计自己的项目
    user_permissions = get_user_permissions(current_user)
    owner_id = None if (current_user.is_superuser or Permission.PROJECT_READ in user_permissions) else current_user.id
    
    statistics = crud.project.get_project_statistics(db, owner_id=owner_id)
    return statistics


@router.get("/my", response_model=List[schemas.Project])
def read_my_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    获取当前用户的项目列表
    """
    projects = crud.project.get_by_owner(
        db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return projects


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    根据ID获取项目详情
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：超级用户、项目负责人或有读取权限的用户可以查看
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or project.owner_id == current_user.id
        or Permission.PROJECT_READ in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限访问此项目")
    
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    更新项目信息
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：超级用户、项目负责人或有更新权限的用户可以修改
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or project.owner_id == current_user.id
        or Permission.PROJECT_UPDATE in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限修改此项目")
    
    # 如果更新项目编号，检查是否已存在
    if project_in.project_code and project_in.project_code != project.project_code:
        existing_project = crud.project.get_by_code(db, project_code=project_in.project_code)
        if existing_project:
            raise HTTPException(
                status_code=400,
                detail="项目编号已存在"
            )
    
    project = crud.project.update(db=db, db_obj=project, obj_in=project_in)
    return project


@router.delete("/{project_id}")
def delete_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    current_user: models.User = Depends(require_permissions(Permission.PROJECT_DELETE)),
) -> Any:
    """
    删除项目
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：超级用户、项目负责人或有删除权限的用户可以删除
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or project.owner_id == current_user.id
        or Permission.PROJECT_DELETE in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限删除此项目")
    
    project = crud.project.remove(db=db, id=project_id)
    return {"message": "项目删除成功"}


@router.put("/{project_id}/review-status")
def update_project_review_status(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    review_status: str,
    review_progress: Optional[int] = None,
    current_user: models.User = Depends(require_permissions(Permission.REVIEW_UPDATE)),
) -> Any:
    """
    更新项目审查状态
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证审查状态值
    valid_statuses = ["pending", "in_progress", "completed", "rejected"]
    if review_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效的审查状态，必须是: {', '.join(valid_statuses)}"
        )
    
    project = crud.project.update_review_status(
        db=db,
        project_id=project_id,
        review_status=review_status,
        review_progress=review_progress
    )
    
    return {"message": "项目审查状态更新成功", "project": project}


# 问题跟踪相关端点
@router.get("/{project_id}/issues", response_model=List[schemas.Issue])
def read_project_issues(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    获取项目的问题列表
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or project.owner_id == current_user.id
        or Permission.PROJECT_READ in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限访问此项目")
    
    issues = crud.issue.get_by_project(
        db, project_id=project_id, skip=skip, limit=limit
    )
    return issues


@router.post("/{project_id}/issues", response_model=schemas.Issue)
def create_project_issue(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    issue_in: schemas.IssueCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    为项目创建问题
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or project.owner_id == current_user.id
        or Permission.PROJECT_UPDATE in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限为此项目创建问题")
    
    issue = crud.issue.create_with_project(
        db=db, obj_in=issue_in, project_id=project_id, reporter_id=current_user.id
    )
    return issue


# 项目比对相关端点
@router.get("/{project_id}/comparisons", response_model=List[schemas.ProjectComparison])
def read_project_comparisons(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    current_user: models.User = Depends(require_permissions(Permission.PROJECT_READ)),
) -> Any:
    """
    获取项目的比对记录
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    comparisons = crud.project_comparison.get_by_project(db, project_id=project_id)
    return comparisons


@router.post("/{project_id}/comparisons", response_model=schemas.ProjectComparison)
def create_project_comparison(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    compared_project_id: int,
    comparison_type: str,
    current_user: models.User = Depends(require_permissions(Permission.PROJECT_UPDATE)),
) -> Any:
    """
    创建项目比对
    """
    # 检查两个项目是否存在
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    compared_project = crud.project.get(db=db, id=compared_project_id)
    if not compared_project:
        raise HTTPException(status_code=404, detail="比对项目不存在")
    
    if project_id == compared_project_id:
        raise HTTPException(status_code=400, detail="不能与自己比对")
    
    comparison = crud.project_comparison.create_comparison(
        db=db,
        project_id=project_id,
        compared_project_id=compared_project_id,
        comparison_type=comparison_type,
        analyst_id=current_user.id
    )
    return comparison