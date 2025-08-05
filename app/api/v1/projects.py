#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理API模块

功能:
1. 项目创建
2. 项目查询
3. 项目更新
4. 项目删除
5. 项目状态管理
6. 项目成员管理
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectList,
    ProjectMember,
    ProjectResponse,
    ProjectStats,
    ProjectStatus,
    ProjectUpdate,
)
from app.services.audit_service import AuditService
from app.services.file_service import FileService
from app.services.project_service import ProjectService
from app.utils.cache import cache_manager
from app.utils.permissions import check_project_permission
from app.utils.response import success_response

router = APIRouter()
project_service = ProjectService()
audit_service = AuditService()
file_service = FileService()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建新项目

    Args:
        project_data: 项目创建数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        ProjectResponse: 创建的项目信息
    """
    try:
        # 检查项目名称是否已存在
        existing_project = (
            db.query(Project)
            .filter(
                and_(
                    Project.name == project_data.name,
                    Project.owner_id == current_user.id,
                    Project.is_deleted == False,
                )
            )
            .first()
        )

        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="项目名称已存在"
            )

        # 创建项目
        project = await project_service.create_project(
            db, project_data, current_user.id
        )

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_CREATE",
            resource_type="project",
            resource_id=str(project.id),
            details={
                "project_name": project.name,
                "project_type": project.project_type,
                "description": project.description,
            },
        )

        return success_response(
            data=ProjectResponse.from_orm(project), message="项目创建成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}",
        )


@router.get("/", response_model=ProjectList)
async def get_projects(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    project_type: Optional[str] = Query(None, description="项目类型"),
    status: Optional[str] = Query(None, description="项目状态"),
    owner_only: bool = Query(False, description="仅显示我创建的项目"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取项目列表

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        search: 搜索关键词
        project_type: 项目类型
        status: 项目状态
        owner_only: 仅显示我创建的项目
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        ProjectList: 项目列表和分页信息
    """
    try:
        # 构建查询
        query = db.query(Project).filter(Project.is_deleted == False)

        # 权限过滤：普通用户只能看到自己参与的项目
        if not current_user.is_superuser:
            if owner_only:
                query = query.filter(Project.owner_id == current_user.id)
            else:
                # 用户可以看到自己创建的或参与的项目
                query = query.filter(
                    or_(
                        Project.owner_id == current_user.id,
                        Project.members.any(id=current_user.id),
                    )
                )
        elif owner_only:
            query = query.filter(Project.owner_id == current_user.id)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%"),
                )
            )

        # 项目类型过滤
        if project_type:
            query = query.filter(Project.project_type == project_type)

        # 状态过滤
        if status:
            query = query.filter(Project.status == status)

        # 按更新时间倒序
        query = query.order_by(desc(Project.updated_at))

        # 分页
        total = query.count()
        projects = query.offset(skip).limit(limit).all()

        return {
            "projects": [ProjectResponse.from_orm(project) for project in projects],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}",
        )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取项目详情

    Args:
        project_id: 项目ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        ProjectDetail: 项目详细信息
    """
    try:
        # 尝试从缓存获取
        cache_key = f"project:{project_id}:detail"
        cached_project = await cache_manager.get(cache_key)
        if cached_project:
            project_detail = ProjectDetail.parse_raw(cached_project)
            # 检查权限
            if not await check_project_permission(
                db, current_user.id, project_id, "read"
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="没有权限访问该项目"
                )
            return project_detail

        # 从数据库获取
        project = (
            db.query(Project)
            .filter(and_(Project.id == project_id, Project.is_deleted == False))
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在"
            )

        # 检查权限
        if not await check_project_permission(db, current_user.id, project_id, "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限访问该项目"
            )

        # 获取项目详细信息
        project_detail = await project_service.get_project_detail(db, project_id)

        # 缓存项目信息
        await cache_manager.set(cache_key, project_detail.json(), expire=1800)  # 30分钟

        # 记录访问日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_VIEW",
            resource_type="project",
            resource_id=str(project_id),
        )

        return project_detail

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目详情失败: {str(e)}",
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新项目信息

    Args:
        project_id: 项目ID
        project_update: 项目更新数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        ProjectResponse: 更新后的项目信息
    """
    try:
        # 检查项目是否存在
        project = (
            db.query(Project)
            .filter(and_(Project.id == project_id, Project.is_deleted == False))
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在"
            )

        # 检查权限
        if not await check_project_permission(db, current_user.id, project_id, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限修改该项目"
            )

        # 检查项目名称是否已存在（排除当前项目）
        if project_update.name and project_update.name != project.name:
            existing_project = (
                db.query(Project)
                .filter(
                    and_(
                        Project.name == project_update.name,
                        Project.owner_id == project.owner_id,
                        Project.id != project_id,
                        Project.is_deleted == False,
                    )
                )
                .first()
            )

            if existing_project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="项目名称已存在"
                )

        # 更新项目
        updated_project = await project_service.update_project(
            db, project_id, project_update
        )

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_UPDATE",
            resource_type="project",
            resource_id=str(project_id),
            details=project_update.dict(exclude_unset=True),
        )

        # 清除缓存
        await cache_manager.delete(f"project:{project_id}:detail")

        return success_response(
            data=ProjectResponse.from_orm(updated_project), message="项目更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新项目失败: {str(e)}",
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    删除项目（软删除）

    Args:
        project_id: 项目ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 操作结果
    """
    try:
        # 检查项目是否存在
        project = (
            db.query(Project)
            .filter(and_(Project.id == project_id, Project.is_deleted == False))
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在"
            )

        # 检查权限（只有项目所有者或管理员可以删除）
        if project.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有项目所有者或管理员可以删除项目",
            )

        # 软删除项目
        await project_service.delete_project(db, project_id)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_DELETE",
            resource_type="project",
            resource_id=str(project_id),
            details={"project_name": project.name},
        )

        # 清除缓存
        await cache_manager.delete(f"project:{project_id}:detail")

        return success_response(message="项目删除成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除项目失败: {str(e)}",
        )


@router.post("/{project_id}/status", response_model=ProjectResponse)
async def update_project_status(
    project_id: int,
    status_data: ProjectStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新项目状态

    Args:
        project_id: 项目ID
        status_data: 状态数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        ProjectResponse: 更新后的项目信息
    """
    try:
        # 检查项目是否存在
        project = (
            db.query(Project)
            .filter(and_(Project.id == project_id, Project.is_deleted == False))
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在"
            )

        # 检查权限
        if not await check_project_permission(db, current_user.id, project_id, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限修改项目状态"
            )

        # 更新状态
        updated_project = await project_service.update_project_status(
            db, project_id, status_data.status, status_data.reason
        )

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_STATUS_UPDATE",
            resource_type="project",
            resource_id=str(project_id),
            details={
                "old_status": project.status,
                "new_status": status_data.status,
                "reason": status_data.reason,
            },
        )

        # 清除缓存
        await cache_manager.delete(f"project:{project_id}:detail")

        return success_response(
            data=ProjectResponse.from_orm(updated_project), message="项目状态更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新项目状态失败: {str(e)}",
        )


@router.get("/{project_id}/members", response_model=List[ProjectMember])
async def get_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取项目成员列表

    Args:
        project_id: 项目ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        List[ProjectMember]: 项目成员列表
    """
    try:
        # 检查权限
        if not await check_project_permission(db, current_user.id, project_id, "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限查看项目成员"
            )

        # 获取项目成员
        members = await project_service.get_project_members(db, project_id)

        return [ProjectMember.from_orm(member) for member in members]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目成员失败: {str(e)}",
        )


@router.post("/{project_id}/members/{user_id}")
async def add_project_member(
    project_id: int,
    user_id: int,
    role: str = Query("member", description="成员角色"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    添加项目成员

    Args:
        project_id: 项目ID
        user_id: 用户ID
        role: 成员角色
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 操作结果
    """
    try:
        # 检查权限（只有项目所有者或管理员可以添加成员）
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在"
            )

        if project.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有项目所有者或管理员可以添加成员",
            )

        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 添加成员
        await project_service.add_project_member(db, project_id, user_id, role)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_MEMBER_ADD",
            resource_type="project",
            resource_id=str(project_id),
            details={
                "added_user_id": user_id,
                "added_username": user.username,
                "role": role,
            },
        )

        # 清除缓存
        await cache_manager.delete(f"project:{project_id}:detail")

        return success_response(message="项目成员添加成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加项目成员失败: {str(e)}",
        )


@router.delete("/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    移除项目成员

    Args:
        project_id: 项目ID
        user_id: 用户ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 操作结果
    """
    try:
        # 检查权限
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在"
            )

        # 项目所有者、管理员或用户自己可以移除
        if (
            project.owner_id != current_user.id
            and not current_user.is_superuser
            and user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限移除该成员"
            )

        # 不能移除项目所有者
        if user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除项目所有者"
            )

        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()

        # 移除成员
        await project_service.remove_project_member(db, project_id, user_id)

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_MEMBER_REMOVE",
            resource_type="project",
            resource_id=str(project_id),
            details={
                "removed_user_id": user_id,
                "removed_username": user.username if user else "unknown",
            },
        )

        # 清除缓存
        await cache_manager.delete(f"project:{project_id}:detail")

        return success_response(message="项目成员移除成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除项目成员失败: {str(e)}",
        )


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取项目统计信息

    Args:
        project_id: 项目ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        ProjectStats: 项目统计信息
    """
    try:
        # 检查权限
        if not await check_project_permission(db, current_user.id, project_id, "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限查看项目统计"
            )

        # 尝试从缓存获取
        cache_key = f"project:{project_id}:stats"
        cached_stats = await cache_manager.get(cache_key)
        if cached_stats:
            return ProjectStats.parse_raw(cached_stats)

        # 获取统计信息
        stats = await project_service.get_project_stats(db, project_id)

        # 缓存统计信息
        await cache_manager.set(cache_key, stats.json(), expire=300)  # 5分钟

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目统计失败: {str(e)}",
        )


@router.post("/{project_id}/files", response_model=dict)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传项目文件

    Args:
        project_id: 项目ID
        file: 上传的文件
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 上传结果
    """
    try:
        # 检查权限
        if not await check_project_permission(db, current_user.id, project_id, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有权限上传文件到该项目"
            )

        # 上传文件
        file_info = await file_service.upload_project_file(
            db, project_id, file, current_user.id
        )

        # 记录审计日志
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_FILE_UPLOAD",
            resource_type="project",
            resource_id=str(project_id),
            details={
                "filename": file.filename,
                "file_size": file_info["size"],
                "file_id": file_info["id"],
            },
        )

        # 清除缓存
        await cache_manager.delete(f"project:{project_id}:detail")
        await cache_manager.delete(f"project:{project_id}:stats")

        return success_response(data=file_info, message="文件上传成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}",
        )
