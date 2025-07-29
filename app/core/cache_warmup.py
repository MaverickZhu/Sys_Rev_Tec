"""缓存预热模块

在系统启动时预加载常用的权限数据到缓存中
"""

import asyncio
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.permission_cache import get_permission_cache_manager
from app.crud.crud_user import user as user_crud
from app.crud.crud_permission import permission as permission_crud
from app.models.user import User
from app.models.permission import Permission, Role
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class CacheWarmupManager:
    """缓存预热管理器"""
    
    def __init__(self):
        self.cache_manager = get_permission_cache_manager()
    
    async def warmup_all(self, db: Session) -> None:
        """执行完整的缓存预热
        
        Args:
            db: 数据库会话
        """
        logger.info("开始缓存预热...")
        
        try:
            # 预热用户权限
            await self.warmup_user_permissions(db)
            
            # 预热角色权限
            await self.warmup_role_permissions(db)
            
            # 预热活跃用户数据
            await self.warmup_active_users(db)
            
            logger.info("缓存预热完成")
            
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
            raise
    
    async def warmup_user_permissions(self, db: Session, limit: int = 100) -> None:
        """预热用户权限缓存
        
        Args:
            db: 数据库会话
            limit: 预热用户数量限制
        """
        logger.info(f"预热用户权限缓存，限制 {limit} 个用户")
        
        try:
            # 获取活跃用户列表
            users = user_crud.get_active_users(db, limit=limit)
            
            for user in users:
                # 预热用户权限
                user_permissions = user_crud.get_user_permissions(db, user.id)
                for permission in user_permissions:
                    self.cache_manager.cache_user_permission(
                        user.id, permission.code, True
                    )
                
                # 预热用户角色
                if user.role:
                    self.cache_manager.cache_user_role(
                        user.id, user.role.value, True
                    )
                
                logger.debug(f"预热用户 {user.id} 的权限缓存")
            
            logger.info(f"成功预热 {len(users)} 个用户的权限缓存")
            
        except Exception as e:
            logger.error(f"预热用户权限缓存失败: {e}")
            raise
    
    async def warmup_role_permissions(self, db: Session) -> None:
        """预热角色权限缓存
        
        Args:
            db: 数据库会话
        """
        logger.info("预热角色权限缓存")
        
        try:
            # 获取所有角色
            roles = permission_crud.get_all_roles(db)
            
            for role in roles:
                # 获取角色权限
                role_permissions = permission_crud.get_role_permissions(db, role.id)
                
                for permission in role_permissions:
                    self.cache_manager.cache_role_permission(
                        role.value, permission.code, True
                    )
                
                logger.debug(f"预热角色 {role.value} 的权限缓存")
            
            logger.info(f"成功预热 {len(roles)} 个角色的权限缓存")
            
        except Exception as e:
            logger.error(f"预热角色权限缓存失败: {e}")
            raise
    
    async def warmup_active_users(self, db: Session, days: int = 7) -> None:
        """预热活跃用户数据
        
        Args:
            db: 数据库会话
            days: 活跃天数
        """
        logger.info(f"预热最近 {days} 天的活跃用户数据")
        
        try:
            # 获取活跃用户
            active_users = user_crud.get_recently_active_users(db, days=days)
            
            for user in active_users:
                # 缓存用户基本信息
                self.cache_manager.cache_user_info(user.id, {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role.value if user.role else None,
                    'is_active': user.is_active,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                })
                
                logger.debug(f"预热活跃用户 {user.id} 的基本信息")
            
            logger.info(f"成功预热 {len(active_users)} 个活跃用户的基本信息")
            
        except Exception as e:
            logger.error(f"预热活跃用户数据失败: {e}")
            raise
    
    async def warmup_critical_permissions(self, db: Session) -> None:
        """预热关键权限数据
        
        Args:
            db: 数据库会话
        """
        logger.info("预热关键权限数据")
        
        # 关键权限列表
        critical_permissions = [
            'USER_MANAGE',
            'ROLE_MANAGE', 
            'PERMISSION_MANAGE',
            'AUDIT_READ',
            'SYSTEM_CONFIG',
            'PROJECT_CREATE',
            'PROJECT_DELETE'
        ]
        
        try:
            # 获取所有用户
            users = user_crud.get_all_users(db)
            
            for user in users:
                for permission_code in critical_permissions:
                    # 检查并缓存关键权限
                    has_permission = user.has_permission(permission_code)
                    self.cache_manager.cache_user_permission(
                        user.id, permission_code, has_permission
                    )
            
            logger.info(f"成功预热 {len(critical_permissions)} 个关键权限")
            
        except Exception as e:
            logger.error(f"预热关键权限数据失败: {e}")
            raise


def get_cache_warmup_manager() -> CacheWarmupManager:
    """获取缓存预热管理器实例
    
    Returns:
        CacheWarmupManager: 缓存预热管理器
    """
    return CacheWarmupManager()


async def startup_cache_warmup() -> None:
    """启动时执行缓存预热
    
    在应用启动时调用此函数来预热缓存
    """
    logger.info("执行启动缓存预热")
    
    db = SessionLocal()
    try:
        warmup_manager = get_cache_warmup_manager()
        await warmup_manager.warmup_all(db)
        
    except Exception as e:
        logger.error(f"启动缓存预热失败: {e}")
        # 不抛出异常，避免影响应用启动
        
    finally:
        db.close()


async def scheduled_cache_refresh() -> None:
    """定期缓存刷新
    
    可以通过定时任务调用此函数来定期刷新缓存
    """
    logger.info("执行定期缓存刷新")
    
    db = SessionLocal()
    try:
        # 清理过期缓存
        cache_manager = get_permission_cache_manager()
        cache_manager.clear_expired_cache()
        
        # 重新预热关键数据
        warmup_manager = get_cache_warmup_manager()
        await warmup_manager.warmup_critical_permissions(db)
        
        logger.info("定期缓存刷新完成")
        
    except Exception as e:
        logger.error(f"定期缓存刷新失败: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    # 测试缓存预热
    asyncio.run(startup_cache_warmup())