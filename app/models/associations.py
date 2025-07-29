"""关联表定义

定义用户、角色、权限之间的多对多关联表
"""

from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, func
from app.db.base_class import Base

# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', Integer, ForeignKey('users.id')),
    Column('expires_at', DateTime(timezone=True), nullable=True),
)

# 角色权限关联表
role_permission_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('granted_by', Integer, ForeignKey('users.id')),
)

# 用户权限关联表（直接授权）
user_permission_association = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('granted_by', Integer, ForeignKey('users.id')),
    Column('expires_at', DateTime(timezone=True), nullable=True),
)

# 权限组权限关联表
permission_group_permissions = Table(
    'permission_group_permissions',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('permission_groups.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now()),
    Column('added_by', Integer, ForeignKey('users.id')),
)