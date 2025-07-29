"""数据库初始化数据

创建默认权限、角色和系统配置
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.permission import (
    Permission, Role, PermissionGroup,
    ResourceType, OperationType, PermissionLevel
)
from app.models.user import User, UserRole
from app.crud.crud_permission import (
    permission as permission_crud,
    role as role_crud,
    permission_group as permission_group_crud
)

logger = logging.getLogger(__name__)


def create_default_permissions(db: Session) -> None:
    """创建默认权限"""
    logger.info("创建默认权限...")
    
    # 定义默认权限
    default_permissions = [
        # 用户管理权限
        {
            "name": "用户查看",
            "code": "USER_READ",
            "description": "查看用户信息",
            "resource_type": ResourceType.USER,
            "operation_type": OperationType.READ
        },
        {
            "name": "用户管理",
            "code": "USER_MANAGE",
            "description": "创建、编辑、删除用户",
            "resource_type": ResourceType.USER,
            "operation_type": OperationType.MANAGE
        },
        {
            "name": "用户创建",
            "code": "USER_CREATE",
            "description": "创建新用户",
            "resource_type": ResourceType.USER,
            "operation_type": OperationType.CREATE
        },
        {
            "name": "用户编辑",
            "code": "USER_UPDATE",
            "description": "编辑用户信息",
            "resource_type": ResourceType.USER,
            "operation_type": OperationType.UPDATE
        },
        {
            "name": "用户删除",
            "code": "USER_DELETE",
            "description": "删除用户",
            "resource_type": ResourceType.USER,
            "operation_type": OperationType.DELETE
        },
        
        # 角色管理权限
        {
            "name": "角色查看",
            "code": "ROLE_READ",
            "description": "查看角色信息",
            "resource_type": ResourceType.ROLE,
            "operation_type": OperationType.READ
        },
        {
            "name": "角色管理",
            "code": "ROLE_MANAGE",
            "description": "创建、编辑、删除角色",
            "resource_type": ResourceType.ROLE,
            "operation_type": OperationType.MANAGE
        },
        {
            "name": "角色创建",
            "code": "ROLE_CREATE",
            "description": "创建新角色",
            "resource_type": ResourceType.ROLE,
            "operation_type": OperationType.CREATE
        },
        {
            "name": "角色编辑",
            "code": "ROLE_UPDATE",
            "description": "编辑角色信息",
            "resource_type": ResourceType.ROLE,
            "operation_type": OperationType.UPDATE
        },
        {
            "name": "角色删除",
            "code": "ROLE_DELETE",
            "description": "删除角色",
            "resource_type": ResourceType.ROLE,
            "operation_type": OperationType.DELETE
        },
        
        # 权限管理权限
        {
            "name": "权限查看",
            "code": "PERMISSION_READ",
            "description": "查看权限信息",
            "resource_type": ResourceType.PERMISSION,
            "operation_type": OperationType.READ
        },
        {
            "name": "权限管理",
            "code": "PERMISSION_MANAGE",
            "description": "创建、编辑、删除权限",
            "resource_type": ResourceType.PERMISSION,
            "operation_type": OperationType.MANAGE
        },
        
        # 报表权限
        {
            "name": "报表查看",
            "code": "REPORT_READ",
            "description": "查看报表",
            "resource_type": ResourceType.REPORT,
            "operation_type": OperationType.READ
        },
        {
            "name": "报表管理",
            "code": "REPORT_MANAGE",
            "description": "创建、编辑、删除报表",
            "resource_type": ResourceType.REPORT,
            "operation_type": OperationType.MANAGE
        },
        {
            "name": "报表导出",
            "code": "REPORT_EXPORT",
            "description": "导出报表数据",
            "resource_type": ResourceType.REPORT,
            "operation_type": OperationType.EXECUTE
        },
        
        # 系统管理权限
        {
            "name": "系统配置",
            "code": "SYSTEM_CONFIGURE",
            "description": "系统配置管理",
            "resource_type": ResourceType.SYSTEM,
            "operation_type": OperationType.MANAGE
        },
        {
            "name": "系统监控",
            "code": "SYSTEM_MONITOR",
            "description": "系统监控和状态查看",
            "resource_type": ResourceType.SYSTEM,
            "operation_type": OperationType.READ
        },
        {
            "name": "系统维护",
            "code": "SYSTEM_MAINTAIN",
            "description": "系统维护操作",
            "resource_type": ResourceType.SYSTEM,
            "operation_type": OperationType.EXECUTE
        },
        
        # 审计权限
        {
            "name": "审计查看",
            "code": "AUDIT_READ",
            "description": "查看审计日志",
            "resource_type": ResourceType.AUDIT,
            "operation_type": OperationType.READ
        },
        {
            "name": "审计管理",
            "code": "AUDIT_MANAGE",
            "description": "审计日志管理",
            "resource_type": ResourceType.AUDIT,
            "operation_type": OperationType.MANAGE
        },
        {
            "name": "审计导出",
            "code": "AUDIT_EXPORT",
            "description": "导出审计数据",
            "resource_type": ResourceType.AUDIT,
            "operation_type": OperationType.EXECUTE
        },
        
        # 数据权限
        {
            "name": "数据查看",
            "code": "DATA_READ",
            "description": "查看数据",
            "resource_type": ResourceType.DATA,
            "operation_type": OperationType.READ
        },
        {
            "name": "数据编辑",
            "code": "DATA_UPDATE",
            "description": "编辑数据",
            "resource_type": ResourceType.DATA,
            "operation_type": OperationType.UPDATE
        },
        {
            "name": "数据删除",
            "code": "DATA_DELETE",
            "description": "删除数据",
            "resource_type": ResourceType.DATA,
            "operation_type": OperationType.DELETE
        },
        {
            "name": "数据导出",
            "code": "DATA_EXPORT",
            "description": "导出数据",
            "resource_type": ResourceType.DATA,
            "operation_type": OperationType.EXECUTE
        },
        {
            "name": "数据导入",
            "code": "DATA_IMPORT",
            "description": "导入数据",
            "resource_type": ResourceType.DATA,
            "operation_type": OperationType.CREATE
        }
    ]
    
    # 创建权限
    created_permissions = {}
    for perm_data in default_permissions:
        # 检查权限是否已存在
        existing_perm = db.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()
        
        if not existing_perm:
            permission = permission_crud.create(
                db,
                name=perm_data["name"],
                code=perm_data["code"],
                description=perm_data["description"],
                resource_type=perm_data["resource_type"],
                operation_type=perm_data["operation_type"],
                is_system=True,
                is_active=True
            )
            created_permissions[perm_data["code"]] = permission
            logger.info(f"创建权限: {perm_data['name']} ({perm_data['code']})")
        else:
            created_permissions[perm_data["code"]] = existing_perm
            logger.info(f"权限已存在: {perm_data['name']} ({perm_data['code']})")
    
    return created_permissions


def create_default_roles(db: Session, permissions: dict) -> None:
    """创建默认角色"""
    logger.info("创建默认角色...")
    
    # 定义默认角色及其权限
    default_roles = [
        {
            "name": "超级管理员",
            "code": "SUPER_ADMIN",
            "description": "系统超级管理员，拥有所有权限",
            "level": 1,
            "permissions": list(permissions.keys())  # 所有权限
        },
        {
            "name": "系统管理员",
            "code": "SYSTEM_ADMIN",
            "description": "系统管理员，负责系统配置和用户管理",
            "level": 2,
            "permissions": [
                "USER_READ", "USER_MANAGE", "USER_CREATE", "USER_UPDATE", "USER_DELETE",
                "ROLE_READ", "ROLE_MANAGE", "ROLE_CREATE", "ROLE_UPDATE", "ROLE_DELETE",
                "PERMISSION_READ", "PERMISSION_MANAGE",
                "SYSTEM_CONFIGURE", "SYSTEM_MONITOR", "SYSTEM_MAINTAIN",
                "AUDIT_READ", "AUDIT_MANAGE", "AUDIT_EXPORT"
            ]
        },
        {
            "name": "审计员",
            "code": "AUDITOR",
            "description": "审计员，负责审计和监控",
            "level": 3,
            "permissions": [
                "USER_READ", "ROLE_READ", "PERMISSION_READ",
                "REPORT_READ", "REPORT_EXPORT",
                "SYSTEM_MONITOR",
                "AUDIT_READ", "AUDIT_EXPORT",
                "DATA_READ", "DATA_EXPORT"
            ]
        },
        {
            "name": "部门经理",
            "code": "MANAGER",
            "description": "部门经理，管理部门用户和数据",
            "level": 4,
            "permissions": [
                "USER_READ", "USER_CREATE", "USER_UPDATE",
                "ROLE_READ",
                "REPORT_READ", "REPORT_MANAGE", "REPORT_EXPORT",
                "DATA_READ", "DATA_UPDATE", "DATA_EXPORT", "DATA_IMPORT"
            ]
        },
        {
            "name": "审查员",
            "code": "REVIEWER",
            "description": "审查员，负责数据审查和报表查看",
            "level": 5,
            "permissions": [
                "USER_READ",
                "REPORT_READ", "REPORT_EXPORT",
                "DATA_READ", "DATA_EXPORT"
            ]
        },
        {
            "name": "普通用户",
            "code": "USER",
            "description": "普通用户，基本查看权限",
            "level": 6,
            "permissions": [
                "DATA_READ",
                "REPORT_READ"
            ]
        }
    ]
    
    # 创建角色
    created_roles = {}
    for role_data in default_roles:
        # 检查角色是否已存在
        existing_role = db.query(Role).filter(
            Role.code == role_data["code"]
        ).first()
        
        if not existing_role:
            # 获取角色权限
            role_permissions = []
            for perm_code in role_data["permissions"]:
                if perm_code in permissions:
                    role_permissions.append(permissions[perm_code])
            
            role = role_crud.create(
                db,
                name=role_data["name"],
                code=role_data["code"],
                description=role_data["description"],
                level=role_data["level"],
                permissions=role_permissions,
                is_system=True,
                is_active=True
            )
            created_roles[role_data["code"]] = role
            logger.info(f"创建角色: {role_data['name']} ({role_data['code']})，权限数: {len(role_permissions)}")
        else:
            created_roles[role_data["code"]] = existing_role
            logger.info(f"角色已存在: {role_data['name']} ({role_data['code']})")
    
    return created_roles


def create_default_permission_groups(db: Session, permissions: dict) -> None:
    """创建默认权限组"""
    logger.info("创建默认权限组...")
    
    # 定义权限组
    permission_groups = [
        {
            "name": "用户管理组",
            "description": "用户相关的所有权限",
            "permissions": ["USER_READ", "USER_MANAGE", "USER_CREATE", "USER_UPDATE", "USER_DELETE"]
        },
        {
            "name": "角色管理组",
            "description": "角色相关的所有权限",
            "permissions": ["ROLE_READ", "ROLE_MANAGE", "ROLE_CREATE", "ROLE_UPDATE", "ROLE_DELETE"]
        },
        {
            "name": "权限管理组",
            "description": "权限相关的所有权限",
            "permissions": ["PERMISSION_READ", "PERMISSION_MANAGE"]
        },
        {
            "name": "报表管理组",
            "description": "报表相关的所有权限",
            "permissions": ["REPORT_READ", "REPORT_MANAGE", "REPORT_EXPORT"]
        },
        {
            "name": "系统管理组",
            "description": "系统相关的所有权限",
            "permissions": ["SYSTEM_CONFIGURE", "SYSTEM_MONITOR", "SYSTEM_MAINTAIN"]
        },
        {
            "name": "审计管理组",
            "description": "审计相关的所有权限",
            "permissions": ["AUDIT_READ", "AUDIT_MANAGE", "AUDIT_EXPORT"]
        },
        {
            "name": "数据管理组",
            "description": "数据相关的所有权限",
            "permissions": ["DATA_READ", "DATA_UPDATE", "DATA_DELETE", "DATA_EXPORT", "DATA_IMPORT"]
        }
    ]
    
    # 创建权限组
    for group_data in permission_groups:
        # 检查权限组是否已存在
        existing_group = db.query(PermissionGroup).filter(
            PermissionGroup.name == group_data["name"]
        ).first()
        
        if not existing_group:
            # 获取权限组权限
            group_permissions = []
            for perm_code in group_data["permissions"]:
                if perm_code in permissions:
                    group_permissions.append(permissions[perm_code])
            
            group = permission_group_crud.create(
                db,
                name=group_data["name"],
                description=group_data["description"],
                permissions=group_permissions,
                is_active=True
            )
            logger.info(f"创建权限组: {group_data['name']}，权限数: {len(group_permissions)}")
        else:
            logger.info(f"权限组已存在: {group_data['name']}")


def update_existing_users(db: Session, roles: dict) -> None:
    """更新现有用户的角色"""
    logger.info("更新现有用户角色...")
    
    # 获取所有用户
    users = db.query(User).all()
    
    for user in users:
        # 根据用户的旧角色设置新的主要角色
        if user.is_superuser:
            # 超级用户设置为超级管理员
            if "SUPER_ADMIN" in roles:
                user.primary_role_id = roles["SUPER_ADMIN"].id
                logger.info(f"用户 {user.username} 设置为超级管理员")
        elif hasattr(user, 'role') and user.role:
            # 根据旧的角色枚举设置新角色
            role_mapping = {
                UserRole.ADMIN: "SYSTEM_ADMIN",
                UserRole.MANAGER: "MANAGER",
                UserRole.REVIEWER: "REVIEWER",
                UserRole.AUDITOR: "AUDITOR",
                UserRole.USER: "USER"
            }
            
            new_role_code = role_mapping.get(user.role)
            if new_role_code and new_role_code in roles:
                user.primary_role_id = roles[new_role_code].id
                logger.info(f"用户 {user.username} 从 {user.role.value} 更新为 {new_role_code}")
        else:
            # 默认设置为普通用户
            if "USER" in roles:
                user.primary_role_id = roles["USER"].id
                logger.info(f"用户 {user.username} 设置为默认用户角色")
    
    db.commit()


def init_default_data(db: Session) -> None:
    """初始化默认数据"""
    logger.info("开始初始化默认数据...")
    
    try:
        # 1. 创建默认权限
        permissions = create_default_permissions(db)
        
        # 2. 创建默认角色
        roles = create_default_roles(db, permissions)
        
        # 3. 创建默认权限组
        create_default_permission_groups(db, permissions)
        
        # 4. 更新现有用户角色
        update_existing_users(db, roles)
        
        logger.info("默认数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化默认数据失败: {str(e)}")
        db.rollback()
        raise


def create_test_data(db: Session) -> None:
    """创建测试数据（仅在开发环境使用）"""
    logger.info("创建测试数据...")
    
    try:
        # 这里可以添加测试用户、测试数据等
        # 注意：仅在开发环境使用
        pass
        
    except Exception as e:
        logger.error(f"创建测试数据失败: {str(e)}")
        db.rollback()
        raise


if __name__ == "__main__":
    # 可以单独运行此脚本进行数据初始化
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        init_default_data(db)
    finally:
        db.close()