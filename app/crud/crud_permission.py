"""权限管理CRUD操作

提供权限、角色、权限组的增删改查操作
"""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import CRUDBase
from app.models.permission import (
    Permission, Role, PermissionGroup, ResourcePermission,
    ResourceType, OperationType, PermissionLevel
)
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate, PermissionUpdate,
    RoleCreate, RoleUpdate,
    PermissionGroupCreate, PermissionGroupUpdate,
    ResourcePermissionCreate, ResourcePermissionUpdate
)

logger = logging.getLogger(__name__)


class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    """权限CRUD操作"""
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[Permission]:
        """根据权限代码获取权限"""
        return db.query(Permission).filter(Permission.code == code).first()
    
    def get_by_resource_and_operation(
        self, 
        db: Session, 
        *, 
        resource_type: ResourceType, 
        operation: OperationType
    ) -> Optional[Permission]:
        """根据资源类型和操作类型获取权限"""
        return db.query(Permission).filter(
            and_(
                Permission.resource_type == resource_type,
                Permission.operation == operation
            )
        ).first()
    
    def get_by_resource_type(
        self, 
        db: Session, 
        *, 
        resource_type: ResourceType
    ) -> List[Permission]:
        """根据资源类型获取所有权限"""
        return db.query(Permission).filter(
            Permission.resource_type == resource_type
        ).all()
    
    def search(
        self, 
        db: Session, 
        *, 
        keyword: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        operation: Optional[OperationType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Permission]:
        """搜索权限"""
        query = db.query(Permission)
        
        if keyword:
            query = query.filter(
                or_(
                    Permission.name.contains(keyword),
                    Permission.code.contains(keyword),
                    Permission.description.contains(keyword)
                )
            )
        
        if resource_type:
            query = query.filter(Permission.resource_type == resource_type)
        
        if operation:
            query = query.filter(Permission.operation == operation)
        
        return query.offset(skip).limit(limit).all()
    
    def create_default_permissions(self, db: Session) -> List[Permission]:
        """创建默认权限"""
        default_permissions = [
            # 项目权限
            {"code": "project:create", "name": "创建项目", "resource_type": ResourceType.PROJECT, "operation": OperationType.CREATE},
            {"code": "project:read", "name": "查看项目", "resource_type": ResourceType.PROJECT, "operation": OperationType.READ},
            {"code": "project:update", "name": "更新项目", "resource_type": ResourceType.PROJECT, "operation": OperationType.UPDATE},
            {"code": "project:delete", "name": "删除项目", "resource_type": ResourceType.PROJECT, "operation": OperationType.DELETE},
            {"code": "project:manage", "name": "管理项目", "resource_type": ResourceType.PROJECT, "operation": OperationType.MANAGE},
            
            # 文档权限
            {"code": "document:create", "name": "创建文档", "resource_type": ResourceType.DOCUMENT, "operation": OperationType.CREATE},
            {"code": "document:read", "name": "查看文档", "resource_type": ResourceType.DOCUMENT, "operation": OperationType.READ},
            {"code": "document:update", "name": "更新文档", "resource_type": ResourceType.DOCUMENT, "operation": OperationType.UPDATE},
            {"code": "document:delete", "name": "删除文档", "resource_type": ResourceType.DOCUMENT, "operation": OperationType.DELETE},
            {"code": "document:upload", "name": "上传文档", "resource_type": ResourceType.DOCUMENT, "operation": OperationType.UPLOAD},
            {"code": "document:download", "name": "下载文档", "resource_type": ResourceType.DOCUMENT, "operation": OperationType.DOWNLOAD},
            
            # 报告权限
            {"code": "report:create", "name": "创建报告", "resource_type": ResourceType.REPORT, "operation": OperationType.CREATE},
            {"code": "report:read", "name": "查看报告", "resource_type": ResourceType.REPORT, "operation": OperationType.READ},
            {"code": "report:update", "name": "更新报告", "resource_type": ResourceType.REPORT, "operation": OperationType.UPDATE},
            {"code": "report:delete", "name": "删除报告", "resource_type": ResourceType.REPORT, "operation": OperationType.DELETE},
            {"code": "report:export", "name": "导出报告", "resource_type": ResourceType.REPORT, "operation": OperationType.EXPORT},
            {"code": "report:analyze", "name": "分析报告", "resource_type": ResourceType.REPORT, "operation": OperationType.ANALYZE},
            
            # 用户权限
            {"code": "user:create", "name": "创建用户", "resource_type": ResourceType.USER, "operation": OperationType.CREATE},
            {"code": "user:read", "name": "查看用户", "resource_type": ResourceType.USER, "operation": OperationType.READ},
            {"code": "user:update", "name": "更新用户", "resource_type": ResourceType.USER, "operation": OperationType.UPDATE},
            {"code": "user:delete", "name": "删除用户", "resource_type": ResourceType.USER, "operation": OperationType.DELETE},
            {"code": "user:manage", "name": "管理用户", "resource_type": ResourceType.USER, "operation": OperationType.MANAGE},
            
            # 系统权限
            {"code": "system:configure", "name": "系统配置", "resource_type": ResourceType.SYSTEM, "operation": OperationType.CONFIGURE},
            {"code": "system:monitor", "name": "系统监控", "resource_type": ResourceType.SYSTEM, "operation": OperationType.MONITOR},
            {"code": "system:audit", "name": "系统审计", "resource_type": ResourceType.SYSTEM, "operation": OperationType.AUDIT},
            {"code": "system:backup", "name": "系统备份", "resource_type": ResourceType.SYSTEM, "operation": OperationType.BACKUP},
            
            # 审计权限
            {"code": "audit:read", "name": "查看审计", "resource_type": ResourceType.AUDIT, "operation": OperationType.READ},
            {"code": "audit:export", "name": "导出审计", "resource_type": ResourceType.AUDIT, "operation": OperationType.EXPORT},
            {"code": "audit:analyze", "name": "分析审计", "resource_type": ResourceType.AUDIT, "operation": OperationType.ANALYZE},
        ]
        
        created_permissions = []
        for perm_data in default_permissions:
            existing = self.get_by_code(db, code=perm_data["code"])
            if not existing:
                permission = Permission(**perm_data)
                db.add(permission)
                created_permissions.append(permission)
        
        db.commit()
        return created_permissions


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """角色CRUD操作"""
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[Role]:
        """根据角色代码获取角色"""
        return db.query(Role).filter(Role.code == code).first()
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        """根据角色名称获取角色"""
        return db.query(Role).filter(Role.name == name).first()
    
    def search(
        self, 
        db: Session, 
        *, 
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """搜索角色"""
        query = db.query(Role)
        
        if keyword:
            query = query.filter(
                or_(
                    Role.name.contains(keyword),
                    Role.code.contains(keyword),
                    Role.description.contains(keyword)
                )
            )
        
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def add_permission(self, db: Session, *, role: Role, permission: Permission) -> Role:
        """为角色添加权限"""
        if permission not in role.permissions:
            role.permissions.append(permission)
            db.add(role)
            db.commit()
            db.refresh(role)
        return role
    
    def remove_permission(self, db: Session, *, role: Role, permission: Permission) -> Role:
        """从角色移除权限"""
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.add(role)
            db.commit()
            db.refresh(role)
        return role
    
    def set_permissions(self, db: Session, *, role: Role, permissions: List[Permission]) -> Role:
        """设置角色权限"""
        role.permissions = permissions
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    def create_default_roles(self, db: Session) -> List[Role]:
        """创建默认角色"""
        default_roles = [
            {"code": "admin", "name": "系统管理员", "description": "拥有所有权限的系统管理员", "level": 1},
            {"code": "manager", "name": "项目经理", "description": "负责项目管理的角色", "level": 2},
            {"code": "reviewer", "name": "审查员", "description": "负责审查工作的角色", "level": 3},
            {"code": "auditor", "name": "审计员", "description": "负责审计工作的角色", "level": 3},
            {"code": "analyst", "name": "分析员", "description": "负责数据分析的角色", "level": 4},
            {"code": "operator", "name": "操作员", "description": "负责日常操作的角色", "level": 5},
            {"code": "user", "name": "普通用户", "description": "基础用户角色", "level": 6},
        ]
        
        created_roles = []
        for role_data in default_roles:
            existing = self.get_by_code(db, code=role_data["code"])
            if not existing:
                role = Role(**role_data)
                db.add(role)
                created_roles.append(role)
        
        db.commit()
        return created_roles


class CRUDPermissionGroup(CRUDBase[PermissionGroup, PermissionGroupCreate, PermissionGroupUpdate]):
    """权限组CRUD操作"""
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[PermissionGroup]:
        """根据权限组代码获取权限组"""
        return db.query(PermissionGroup).filter(PermissionGroup.code == code).first()
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[PermissionGroup]:
        """根据权限组名称获取权限组"""
        return db.query(PermissionGroup).filter(PermissionGroup.name == name).first()
    
    def search(
        self, 
        db: Session, 
        *, 
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PermissionGroup]:
        """搜索权限组"""
        query = db.query(PermissionGroup)
        
        if keyword:
            query = query.filter(
                or_(
                    PermissionGroup.name.contains(keyword),
                    PermissionGroup.code.contains(keyword),
                    PermissionGroup.description.contains(keyword)
                )
            )
        
        if is_active is not None:
            query = query.filter(PermissionGroup.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def add_permission(self, db: Session, *, group: PermissionGroup, permission: Permission) -> PermissionGroup:
        """为权限组添加权限"""
        if permission not in group.permissions:
            group.permissions.append(permission)
            db.add(group)
            db.commit()
            db.refresh(group)
        return group
    
    def remove_permission(self, db: Session, *, group: PermissionGroup, permission: Permission) -> PermissionGroup:
        """从权限组移除权限"""
        if permission in group.permissions:
            group.permissions.remove(permission)
            db.add(group)
            db.commit()
            db.refresh(group)
        return group
    
    def set_permissions(self, db: Session, *, group: PermissionGroup, permissions: List[Permission]) -> PermissionGroup:
        """设置权限组权限"""
        group.permissions = permissions
        db.add(group)
        db.commit()
        db.refresh(group)
        return group


class CRUDResourcePermission(CRUDBase[ResourcePermission, ResourcePermissionCreate, ResourcePermissionUpdate]):
    """资源权限CRUD操作"""
    
    def get_by_resource(
        self, 
        db: Session, 
        *, 
        resource_type: str, 
        resource_id: str
    ) -> List[ResourcePermission]:
        """根据资源获取所有权限"""
        return db.query(ResourcePermission).filter(
            and_(
                ResourcePermission.resource_type == resource_type,
                ResourcePermission.resource_id == resource_id
            )
        ).all()
    
    def get_user_resource_permission(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        resource_type: str, 
        resource_id: str
    ) -> Optional[ResourcePermission]:
        """获取用户对特定资源的权限"""
        return db.query(ResourcePermission).filter(
            and_(
                ResourcePermission.user_id == user_id,
                ResourcePermission.resource_type == resource_type,
                ResourcePermission.resource_id == resource_id
            )
        ).first()
    
    def get_user_permissions(
        self, 
        db: Session, 
        *, 
        user_id: int,
        resource_type: Optional[str] = None
    ) -> List[ResourcePermission]:
        """获取用户的所有资源权限"""
        query = db.query(ResourcePermission).filter(ResourcePermission.user_id == user_id)
        
        if resource_type:
            query = query.filter(ResourcePermission.resource_type == resource_type)
        
        return query.all()
    
    def grant_permission(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        resource_type: str, 
        resource_id: str, 
        permission_level: PermissionLevel,
        granted_by: int
    ) -> ResourcePermission:
        """授予用户资源权限"""
        # 检查是否已存在
        existing = self.get_user_resource_permission(
            db, user_id=user_id, resource_type=resource_type, resource_id=resource_id
        )
        
        if existing:
            # 更新权限级别
            existing.permission_level = permission_level
            existing.granted_by = granted_by
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # 创建新权限
            permission = ResourcePermission(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission_level=permission_level,
                granted_by=granted_by
            )
            db.add(permission)
            db.commit()
            db.refresh(permission)
            return permission
    
    def revoke_permission(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        resource_type: str, 
        resource_id: str
    ) -> bool:
        """撤销用户资源权限"""
        permission = self.get_user_resource_permission(
            db, user_id=user_id, resource_type=resource_type, resource_id=resource_id
        )
        
        if permission:
            db.delete(permission)
            db.commit()
            return True
        return False


# 创建CRUD实例
permission = CRUDPermission(Permission)
role = CRUDRole(Role)
permission_group = CRUDPermissionGroup(PermissionGroup)
resource_permission = CRUDResourcePermission(ResourcePermission)