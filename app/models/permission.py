"""权限模型

定义系统的权限资源、操作和权限组合模型
"""

from enum import Enum as PyEnum
from typing import List

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.models.associations import user_roles, role_permission_association, user_permission_association


class ResourceType(PyEnum):
    """资源类型枚举"""
    
    PROJECT = "project"  # 项目
    DOCUMENT = "document"  # 文档
    REPORT = "report"  # 报告
    USER = "user"  # 用户
    SYSTEM = "system"  # 系统
    AUDIT = "audit"  # 审计
    ANALYSIS = "analysis"  # 分析
    TEMPLATE = "template"  # 模板
    EXPORT = "export"  # 导出
    IMPORT = "import"  # 导入


class OperationType(PyEnum):
    """操作类型枚举"""
    
    # 基础CRUD操作
    CREATE = "create"  # 创建
    READ = "read"  # 读取
    UPDATE = "update"  # 更新
    DELETE = "delete"  # 删除
    
    # 业务操作
    APPROVE = "approve"  # 审批
    REJECT = "reject"  # 拒绝
    SUBMIT = "submit"  # 提交
    REVIEW = "review"  # 审查
    ANALYZE = "analyze"  # 分析
    EXPORT = "export"  # 导出
    IMPORT = "import"  # 导入
    ASSIGN = "assign"  # 分配
    MANAGE = "manage"  # 管理
    CONFIGURE = "configure"  # 配置
    MONITOR = "monitor"  # 监控
    AUDIT = "audit"  # 审计


class PermissionLevel(PyEnum):
    """权限级别枚举"""
    
    NONE = "none"  # 无权限
    READ = "read"  # 只读
    WRITE = "write"  # 读写
    ADMIN = "admin"  # 管理员
    OWNER = "owner"  # 所有者



class Permission(Base):
    """权限模型
    
    定义系统中的具体权限，包括资源类型、操作类型和权限级别
    """
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 权限标识
    code = Column(String(100), unique=True, index=True, nullable=False, comment="权限代码")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(Text, comment="权限描述")
    
    # 权限分类
    resource_type = Column(Enum(ResourceType), nullable=False, comment="资源类型")
    operation_type = Column(Enum(OperationType), nullable=False, comment="操作类型")
    permission_level = Column(Enum(PermissionLevel), default=PermissionLevel.READ, comment="权限级别")
    
    # 权限属性
    is_system = Column(Boolean, default=False, comment="是否为系统权限")
    is_active = Column(Boolean, default=True, comment="是否激活")
    priority = Column(Integer, default=0, comment="权限优先级")
    
    # 权限约束
    resource_pattern = Column(String(200), comment="资源匹配模式")
    conditions = Column(Text, comment="权限条件（JSON格式）")
    
    # 权限继承
    parent_id = Column(Integer, ForeignKey('permissions.id'), nullable=True, comment="父权限ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    parent = relationship("Permission", remote_side=[id], backref="children")
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions",
                       foreign_keys="[role_permissions.c.role_id, role_permissions.c.permission_id]")
    users = relationship("User", secondary="user_permissions", back_populates="direct_permissions",
                       foreign_keys="[user_permissions.c.user_id, user_permissions.c.permission_id]")
    
    def __repr__(self):
        return f"<Permission(code='{self.code}', name='{self.name}')>"
    
    @property
    def full_code(self) -> str:
        """获取完整权限代码"""
        return f"{self.resource_type.value}:{self.operation_type.value}"
    
    def has_child_permission(self, permission_code: str) -> bool:
        """检查是否包含子权限"""
        for child in self.children:
            if child.code == permission_code or child.has_child_permission(permission_code):
                return True
        return False
    
    def get_all_child_permissions(self) -> List['Permission']:
        """获取所有子权限（递归）"""
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_child_permissions())
        return all_children


class Role(Base):
    """角色模型（扩展原有角色模型）
    
    定义用户角色和权限组合
    """
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 角色信息
    code = Column(String(50), unique=True, index=True, nullable=False, comment="角色代码")
    name = Column(String(100), nullable=False, comment="角色名称")
    description = Column(Text, comment="角色描述")
    
    # 角色属性
    is_system = Column(Boolean, default=False, comment="是否为系统角色")
    is_active = Column(Boolean, default=True, comment="是否激活")
    priority = Column(Integer, default=0, comment="角色优先级")
    
    # 角色继承
    parent_id = Column(Integer, ForeignKey('roles.id'), nullable=True, comment="父角色ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    parent = relationship("Role", remote_side=[id], backref="children")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles",
                             foreign_keys="[role_permissions.c.role_id, role_permissions.c.permission_id]")
    users = relationship("User", secondary="user_roles", back_populates="roles",
                       foreign_keys="[user_roles.c.user_id, user_roles.c.role_id]")
    
    def __repr__(self):
        return f"<Role(code='{self.code}', name='{self.name}')>"
    
    def has_permission(self, permission_code: str) -> bool:
        """检查角色是否具有指定权限"""
        # 检查直接权限
        for permission in self.permissions:
            if permission.code == permission_code or permission.has_child_permission(permission_code):
                return True
        
        # 检查继承权限
        if self.parent:
            return self.parent.has_permission(permission_code)
        
        return False
    
    def get_all_permissions(self) -> List[Permission]:
        """获取角色的所有权限（包括继承）"""
        all_permissions = list(self.permissions)
        
        # 添加子权限
        for permission in self.permissions:
            all_permissions.extend(permission.get_all_child_permissions())
        
        # 添加继承权限
        if self.parent:
            all_permissions.extend(self.parent.get_all_permissions())
        
        # 去重
        unique_permissions = []
        seen_ids = set()
        for permission in all_permissions:
            if permission.id not in seen_ids:
                unique_permissions.append(permission)
                seen_ids.add(permission.id)
        
        return unique_permissions


class PermissionGroup(Base):
    """权限组模型
    
    用于组织和管理相关权限
    """
    
    __tablename__ = "permission_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 权限组信息
    code = Column(String(50), unique=True, index=True, nullable=False, comment="权限组代码")
    name = Column(String(100), nullable=False, comment="权限组名称")
    description = Column(Text, comment="权限组描述")
    
    # 权限组属性
    is_active = Column(Boolean, default=True, comment="是否激活")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    permissions = relationship("Permission", secondary="permission_group_permissions")
    
    def __repr__(self):
        return f"<PermissionGroup(code='{self.code}', name='{self.name}')>"


class ResourcePermission(Base):
    """资源权限模型
    
    定义特定资源实例的权限控制
    """
    
    __tablename__ = "resource_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 资源信息
    resource_type = Column(Enum(ResourceType), nullable=False, comment="资源类型")
    resource_id = Column(String(100), nullable=False, comment="资源ID")
    
    # 权限主体
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment="用户ID")
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True, comment="角色ID")
    
    # 权限信息
    permission_level = Column(Enum(PermissionLevel), nullable=False, comment="权限级别")
    operations = Column(String(500), comment="允许的操作列表（JSON格式）")
    
    # 权限约束
    conditions = Column(Text, comment="权限条件（JSON格式）")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    
    # 权限状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 授权信息
    granted_by = Column(Integer, ForeignKey('users.id'), comment="授权人")
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), comment="授权时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", foreign_keys=[role_id])
    grantor = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        subject = f"user:{self.user_id}" if self.user_id else f"role:{self.role_id}"
        return f"<ResourcePermission({subject} -> {self.resource_type.value}:{self.resource_id})>"
    
    @property
    def is_expired(self) -> bool:
        """检查权限是否已过期"""
        if self.expires_at is None:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)