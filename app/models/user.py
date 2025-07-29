from enum import Enum as PyEnum
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.models.associations import user_roles


class UserRole(PyEnum):
    """用户基础角色枚举（保持向后兼容）"""

    ADMIN = "admin"
    USER = "user"
    REVIEWER = "reviewer"
    MANAGER = "manager"
    AUDITOR = "auditor"  # 审计员


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    username = Column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )
    email = Column(String(100), unique=True, index=True, comment="邮箱")
    full_name = Column(String(100), comment="姓名")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    role = Column(Enum(UserRole), default=UserRole.USER, comment="用户基础角色")
    
    # 权限系统关联
    primary_role_id = Column(Integer, ForeignKey('roles.id'), nullable=True, comment="主要角色ID")

    # 用户详细信息
    employee_id = Column(String(50), unique=True, comment="工号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    phone = Column(String(20), comment="电话")

    # 用户状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")

    # 认证相关
    last_login = Column(DateTime(timezone=True), comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    # projects = relationship("Project", back_populates="owner")
    
    # 权限系统关联关系
    primary_role = relationship("Role", foreign_keys=[primary_role_id])
    roles = relationship("Role", secondary="user_roles", back_populates="users",
                       foreign_keys="[user_roles.c.user_id, user_roles.c.role_id]")
    direct_permissions = relationship("Permission", secondary="user_permissions", back_populates="users",
                                    foreign_keys="[user_permissions.c.user_id, user_permissions.c.permission_id]")
    resource_permissions = relationship("ResourcePermission", foreign_keys="ResourcePermission.user_id")
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否具有指定权限
        
        Args:
            permission_code: 权限代码
            
        Returns:
            bool: 是否具有权限
        """
        # 超级用户拥有所有权限
        if self.is_superuser:
            return True
        
        # 检查直接权限
        for permission in self.direct_permissions:
            if permission.code == permission_code or permission.has_child_permission(permission_code):
                return True
        
        # 检查角色权限
        if self.primary_role:
            return self.primary_role.has_permission(permission_code)
        
        return False
    
    def get_all_permissions(self) -> List['Permission']:
        """获取用户的所有权限
        
        Returns:
            List[Permission]: 权限列表
        """
        if self.is_superuser:
            # 超级用户返回所有权限（这里可以优化为从数据库查询）
            return []
        
        all_permissions = list(self.direct_permissions)
        
        # 添加角色权限
        if self.primary_role:
            all_permissions.extend(self.primary_role.get_all_permissions())
        
        # 去重
        unique_permissions = []
        seen_ids = set()
        for permission in all_permissions:
            if permission.id not in seen_ids:
                unique_permissions.append(permission)
                seen_ids.add(permission.id)
        
        return unique_permissions
    
    def has_resource_permission(self, resource_type: str, resource_id: str, operation: str) -> bool:
        """检查用户是否对特定资源具有操作权限
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            operation: 操作类型
            
        Returns:
            bool: 是否具有权限
        """
        # 超级用户拥有所有权限
        if self.is_superuser:
            return True
        
        # 检查资源权限
        for res_perm in self.resource_permissions:
            if (res_perm.resource_type.value == resource_type and 
                res_perm.resource_id == resource_id and 
                res_perm.is_active and 
                not res_perm.is_expired):
                
                # 检查操作权限
                if res_perm.operations:
                    import json
                    try:
                        allowed_operations = json.loads(res_perm.operations)
                        return operation in allowed_operations
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # 根据权限级别判断
                from app.models.permission import PermissionLevel
                if res_perm.permission_level == PermissionLevel.OWNER:
                    return True
                elif res_perm.permission_level == PermissionLevel.ADMIN:
                    return operation in ['create', 'read', 'update', 'delete', 'manage']
                elif res_perm.permission_level == PermissionLevel.WRITE:
                    return operation in ['create', 'read', 'update']
                elif res_perm.permission_level == PermissionLevel.READ:
                    return operation == 'read'
        
        return False
