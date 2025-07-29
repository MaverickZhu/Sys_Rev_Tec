"""权限管理API路由

提供权限、角色、权限组的管理接口
"""

import logging
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_superuser
from app.core.permissions import (
    require_permission, require_role, require_any_permission,
    PermissionChecker, Permissions, Roles
)
from app.crud.crud_permission import permission, role, permission_group, resource_permission
from app.crud.crud_user import user as user_crud
from app.models.user import User
from app.models.permission import Permission, Role, PermissionGroup, ResourcePermission
from app.schemas.permission import (
    # 权限相关
    PermissionCreate, PermissionUpdate, Permission as PermissionSchema,
    PermissionSearchRequest,
    # 角色相关
    RoleCreate, RoleUpdate, Role as RoleSchema,
    RoleSearchRequest, RolePermissionRequest,
    # 权限组相关
    PermissionGroupCreate, PermissionGroupUpdate, PermissionGroup as PermissionGroupSchema,
    PermissionGroupSearchRequest,
    # 资源权限相关
    ResourcePermissionCreate, ResourcePermissionUpdate, ResourcePermission as ResourcePermissionSchema,
    ResourcePermissionRequest,
    # 用户权限相关
    UserPermissionSummary, PermissionCheckRequest, PermissionCheckResponse,
    UserRoleRequest, UserPermissionRequest,
    # 统计相关
    PermissionStats
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# 权限管理接口
@router.get("/permissions", response_model=List[PermissionSchema])
@require_permission(Permissions.SYSTEM_CONFIGURE)
async def get_permissions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    operation: Optional[str] = Query(None, description="操作类型"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量")
):
    """获取权限列表"""
    try:
        permissions = permission.search(
            db,
            keyword=keyword,
            resource_type=resource_type,
            operation=operation,
            skip=skip,
            limit=limit
        )
        return permissions
    except Exception as e:
        logger.error(f"获取权限列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限列表失败"
        )


@router.post("/permissions", response_model=PermissionSchema)
@require_permission(Permissions.SYSTEM_CONFIGURE)
async def create_permission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_in: PermissionCreate
):
    """创建权限"""
    try:
        # 检查权限代码是否已存在
        existing = permission.get_by_code(db, code=permission_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限代码已存在"
            )
        
        new_permission = permission.create(db, obj_in=permission_in)
        logger.info(f"用户 {current_user.username} 创建了权限 {new_permission.code}")
        return new_permission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建权限失败"
        )


@router.get("/permissions/{permission_id}", response_model=PermissionSchema)
@require_permission(Permissions.SYSTEM_CONFIGURE)
async def get_permission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_id: int
):
    """获取权限详情"""
    try:
        perm = permission.get(db, id=permission_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        return perm
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取权限详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限详情失败"
        )


@router.put("/permissions/{permission_id}", response_model=PermissionSchema)
@require_permission(Permissions.SYSTEM_CONFIGURE)
async def update_permission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_id: int,
    permission_in: PermissionUpdate
):
    """更新权限"""
    try:
        perm = permission.get(db, id=permission_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        updated_permission = permission.update(db, db_obj=perm, obj_in=permission_in)
        logger.info(f"用户 {current_user.username} 更新了权限 {updated_permission.code}")
        return updated_permission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新权限失败"
        )


@router.delete("/permissions/{permission_id}")
@require_permission(Permissions.SYSTEM_CONFIGURE)
async def delete_permission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_id: int
):
    """删除权限"""
    try:
        perm = permission.get(db, id=permission_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        permission.remove(db, id=permission_id)
        logger.info(f"用户 {current_user.username} 删除了权限 {perm.code}")
        return {"message": "权限删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除权限失败"
        )


# 角色管理接口
@router.get("/roles", response_model=List[RoleSchema])
@require_permission(Permissions.USER_MANAGE)
async def get_roles(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量")
):
    """获取角色列表"""
    try:
        roles = role.search(
            db,
            keyword=keyword,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        return roles
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色列表失败"
        )


@router.post("/roles", response_model=RoleSchema)
@require_permission(Permissions.USER_MANAGE)
async def create_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_in: RoleCreate
):
    """创建角色"""
    try:
        # 检查角色代码是否已存在
        existing = role.get_by_code(db, code=role_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色代码已存在"
            )
        
        # 创建角色
        role_data = role_in.dict(exclude={"permission_ids"})
        new_role = role.create(db, obj_in=role_data)
        
        # 设置权限
        if role_in.permission_ids:
            permissions = [permission.get(db, id=pid) for pid in role_in.permission_ids]
            permissions = [p for p in permissions if p]  # 过滤不存在的权限
            role.set_permissions(db, role=new_role, permissions=permissions)
        
        logger.info(f"用户 {current_user.username} 创建了角色 {new_role.code}")
        return new_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建角色失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建角色失败"
        )


@router.get("/roles/{role_id}", response_model=RoleSchema)
@require_permission(Permissions.USER_MANAGE)
async def get_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_id: int
):
    """获取角色详情"""
    try:
        role_obj = role.get(db, id=role_id)
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色详情失败"
        )


@router.put("/roles/{role_id}", response_model=RoleSchema)
@require_permission(Permissions.USER_MANAGE)
async def update_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_id: int,
    role_in: RoleUpdate
):
    """更新角色"""
    try:
        role_obj = role.get(db, id=role_id)
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 更新角色基本信息
        role_data = role_in.dict(exclude={"permission_ids"}, exclude_unset=True)
        updated_role = role.update(db, db_obj=role_obj, obj_in=role_data)
        
        # 更新权限
        if role_in.permission_ids is not None:
            permissions = [permission.get(db, id=pid) for pid in role_in.permission_ids]
            permissions = [p for p in permissions if p]  # 过滤不存在的权限
            role.set_permissions(db, role=updated_role, permissions=permissions)
        
        logger.info(f"用户 {current_user.username} 更新了角色 {updated_role.code}")
        return updated_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新角色失败"
        )


@router.delete("/roles/{role_id}")
@require_permission(Permissions.USER_MANAGE)
async def delete_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_id: int
):
    """删除角色"""
    try:
        role_obj = role.get(db, id=role_id)
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        role.remove(db, id=role_id)
        logger.info(f"用户 {current_user.username} 删除了角色 {role_obj.code}")
        return {"message": "角色删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除角色失败"
        )


# 用户权限管理接口
@router.get("/users/{user_id}/permissions", response_model=UserPermissionSummary)
@require_any_permission([Permissions.USER_MANAGE, Permissions.USER_READ])
async def get_user_permissions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int
):
    """获取用户权限摘要"""
    try:
        user = user_crud.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 获取用户所有权限
        all_permissions = user.get_all_permissions()
        
        # 获取资源权限
        user_resource_permissions = resource_permission.get_user_permissions(db, user_id=user_id)
        
        return UserPermissionSummary(
            user_id=user.id,
            username=user.username,
            role=user.role.value,
            primary_role=user.primary_role,
            direct_permissions=user.direct_permissions,
            role_permissions=user.primary_role.permissions if user.primary_role else [],
            resource_permissions=user_resource_permissions,
            all_permissions=all_permissions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户权限摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户权限摘要失败"
        )


@router.post("/users/{user_id}/role")
@require_permission(Permissions.USER_MANAGE)
async def assign_user_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int,
    role_request: UserRoleRequest
):
    """为用户分配角色"""
    try:
        user = user_crud.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        role_obj = role.get(db, id=role_request.role_id)
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 更新用户主要角色
        user.primary_role_id = role_obj.id
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"用户 {current_user.username} 为用户 {user.username} 分配了角色 {role_obj.code}")
        return {"message": "角色分配成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配用户角色失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配用户角色失败"
        )


@router.post("/users/{user_id}/permissions")
@require_permission(Permissions.USER_MANAGE)
async def assign_user_permissions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int,
    permission_request: UserPermissionRequest
):
    """为用户分配直接权限"""
    try:
        user = user_crud.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 获取权限对象
        permissions = []
        for perm_id in permission_request.permission_ids:
            perm = permission.get(db, id=perm_id)
            if perm:
                permissions.append(perm)
        
        # 设置用户直接权限
        user.direct_permissions = permissions
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"用户 {current_user.username} 为用户 {user.username} 分配了 {len(permissions)} 个直接权限")
        return {"message": "权限分配成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配用户权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配用户权限失败"
        )


# 资源权限管理接口
@router.get("/resource-permissions")
@require_any_permission([Permissions.USER_MANAGE, Permissions.USER_READ])
async def get_resource_permissions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: Optional[int] = Query(None, description="用户ID"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量")
):
    """获取资源权限列表"""
    try:
        # 构建查询条件
        query = db.query(ResourcePermission)
        
        if user_id:
            query = query.filter(ResourcePermission.user_id == user_id)
        if resource_type:
            query = query.filter(ResourcePermission.resource_type == resource_type)
        if resource_id:
            query = query.filter(ResourcePermission.resource_id.contains(resource_id))
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        resource_permissions = query.offset(skip).limit(limit).all()
        
        # 格式化返回数据
        result = []
        for rp in resource_permissions:
            result.append({
                "id": rp.id,
                "user_id": rp.user_id,
                "user": {
                    "id": rp.user.id,
                    "username": rp.user.username,
                    "email": rp.user.email
                } if rp.user else None,
                "resource_type": rp.resource_type.value,
                "resource_id": rp.resource_id,
                "permission_level": rp.permission_level.value,
                "operations": [op.value for op in rp.operations] if rp.operations else [],
                "granted_at": rp.granted_at,
                "expires_at": rp.expires_at,
                "granted_by": rp.granted_by,
                "is_active": rp.is_active
            })
        
        return {
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"获取资源权限列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资源权限列表失败"
        )


@router.post("/resource-permissions")
@require_permission(Permissions.USER_MANAGE)
async def grant_resource_permission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_request: ResourcePermissionRequest
):
    """授予资源权限"""
    try:
        user = user_crud.get(db, id=permission_request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 授予权限
        resource_perm = resource_permission.grant_permission(
            db,
            user_id=permission_request.user_id,
            resource_type=permission_request.resource_type,
            resource_id=permission_request.resource_id,
            permission_level=permission_request.permission_level,
            granted_by=current_user.id
        )
        
        logger.info(
            f"用户 {current_user.username} 为用户 {user.username} 授予了资源权限: "
            f"{permission_request.resource_type}:{permission_request.resource_id} - {permission_request.permission_level.value}"
        )
        return {"message": "资源权限授予成功", "permission_id": resource_perm.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"授予资源权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="授予资源权限失败"
        )


@router.delete("/resource-permissions")
@require_permission(Permissions.USER_MANAGE)
async def revoke_resource_permission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int = Query(..., description="用户ID"),
    resource_type: str = Query(..., description="资源类型"),
    resource_id: str = Query(..., description="资源ID")
):
    """撤销资源权限"""
    try:
        user = user_crud.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 撤销权限
        success = resource_permission.revoke_permission(
            db,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源权限不存在"
            )
        
        logger.info(
            f"用户 {current_user.username} 撤销了用户 {user.username} 的资源权限: "
            f"{resource_type}:{resource_id}"
        )
        return {"message": "资源权限撤销成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"撤销资源权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="撤销资源权限失败"
        )


# 权限检查接口
@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission_api(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    check_request: PermissionCheckRequest
):
    """检查权限"""
    try:
        checker = PermissionChecker(db)
        
        if check_request.resource_type and check_request.resource_id and check_request.operation:
            # 检查资源权限
            has_permission = checker.check_resource_permission(
                current_user,
                check_request.resource_type,
                check_request.resource_id,
                check_request.operation
            )
            permission_source = "resource_permission"
        else:
            # 检查普通权限
            has_permission = checker.check_permission(current_user, check_request.permission_code)
            permission_source = "role_or_direct_permission"
        
        return PermissionCheckResponse(
            has_permission=has_permission,
            permission_source=permission_source if has_permission else None,
            message="权限检查完成"
        )
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="权限检查失败"
        )


# 权限统计接口
@router.get("/stats", response_model=PermissionStats)
@require_permission(Permissions.SYSTEM_MONITOR)
async def get_permission_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限统计信息"""
    try:
        # 统计权限
        total_permissions = db.query(Permission).count()
        active_permissions = db.query(Permission).filter(Permission.is_active == True).count()
        
        # 统计角色
        total_roles = db.query(Role).count()
        active_roles = db.query(Role).filter(Role.is_active == True).count()
        
        # 统计权限组
        total_permission_groups = db.query(PermissionGroup).count()
        active_permission_groups = db.query(PermissionGroup).filter(PermissionGroup.is_active == True).count()
        
        # 资源类型统计
        resource_type_stats = {}
        for resource_type in db.query(Permission.resource_type).distinct():
            count = db.query(Permission).filter(Permission.resource_type == resource_type[0]).count()
            resource_type_stats[resource_type[0].value] = count
        
        # 操作类型统计
        operation_type_stats = {}
        for operation_type in db.query(Permission.operation).distinct():
            count = db.query(Permission).filter(Permission.operation == operation_type[0]).count()
            operation_type_stats[operation_type[0].value] = count
        
        return PermissionStats(
            total_permissions=total_permissions,
            active_permissions=active_permissions,
            total_roles=total_roles,
            active_roles=active_roles,
            total_permission_groups=total_permission_groups,
            active_permission_groups=active_permission_groups,
            resource_type_stats=resource_type_stats,
            operation_type_stats=operation_type_stats
        )
    except Exception as e:
        logger.error(f"获取权限统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限统计失败"
        )


# 初始化默认数据接口
@router.post("/init-default-data")
@require_role(Roles.ADMIN)
async def init_default_permission_data(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """初始化默认权限数据"""
    try:
        # 创建默认权限
        created_permissions = permission.create_default_permissions(db)
        
        # 创建默认角色
        created_roles = role.create_default_roles(db)
        
        logger.info(
            f"用户 {current_user.username} 初始化了默认权限数据: "
            f"{len(created_permissions)} 个权限, {len(created_roles)} 个角色"
        )
        
        return {
            "message": "默认权限数据初始化成功",
            "created_permissions": len(created_permissions),
            "created_roles": len(created_roles)
        }
    except Exception as e:
        logger.error(f"初始化默认权限数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化默认权限数据失败"
        )