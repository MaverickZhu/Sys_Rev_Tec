import os
import sys

# 确保在正确的目录中
os.chdir(r'C:\Users\Zz-20240101\Desktop\Sys_Rev_Tec')
sys.path.insert(0, os.getcwd())

try:
    from app.db.session import SessionLocal
    from app.crud import user as user_crud
    from app.crud.crud_permission import resource_permission
    from app.schemas.permission import UserPermissionSummary
    
    print("导入成功")
    
    # 测试数据库连接
    db = SessionLocal()
    print("数据库连接成功")
    
    # 获取用户
    user = user_crud.get(db, id=1)
    if user:
        print(f"用户: {user.username}")
        print(f"角色: {user.role}")
        print(f"主要角色: {user.primary_role}")
        
        # 测试primary_role.permissions访问
        if user.primary_role:
            try:
                role_permissions = user.primary_role.permissions
                print(f"主要角色权限数量: {len(role_permissions)}")
                for perm in role_permissions:
                    print(f"  - {perm.code}: {perm.name}")
            except Exception as e:
                print(f"访问主要角色权限时出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 获取所有权限
        try:
            all_permissions = user.get_all_permissions()
            print(f"所有权限数量: {len(all_permissions)}")
        except Exception as e:
            print(f"获取所有权限时出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 获取资源权限
        try:
            user_resource_permissions = resource_permission.get_user_permissions(db, user_id=1)
            print(f"资源权限数量: {len(user_resource_permissions)}")
        except Exception as e:
            print(f"获取资源权限时出错: {e}")
            import traceback
            traceback.print_exc()
            
        # 尝试创建UserPermissionSummary
        try:
            summary = UserPermissionSummary(
                user_id=user.id,
                username=user.username,
                role=user.role.value if user.role else "user",
                primary_role=user.primary_role,
                direct_permissions=user.direct_permissions or [],
                role_permissions=user.primary_role.permissions if user.primary_role else [],
                resource_permissions=[],
                all_permissions=[]
            )
            print("UserPermissionSummary创建成功")
        except Exception as e:
            print(f"创建UserPermissionSummary时出错: {e}")
            import traceback
            traceback.print_exc()
            
    else:
        print("用户不存在")
    
    db.close()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()