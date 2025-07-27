#!/usr/bin/env python3

import logging
from app.db.session import SessionLocal
from app.core.config import settings
from app.crud import user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_superuser() -> None:
    """修复超级用户状态"""
    db = SessionLocal()
    
    try:
        # 获取超级用户
        superuser = user.get_by_username(db, username=settings.FIRST_SUPERUSER)
        if superuser:
            logger.info(f"Found superuser: {superuser.username}")
            logger.info(f"Current status - is_active: {superuser.is_active}, is_superuser: {superuser.is_superuser}")
            
            # 更新用户状态
            if not superuser.is_active or not superuser.is_superuser:
                update_data = {
                    "is_active": True,
                    "is_superuser": True
                }
                updated_user = user.update(db, db_obj=superuser, obj_in=update_data)
                logger.info(f"Updated superuser status - is_active: {updated_user.is_active}, is_superuser: {updated_user.is_superuser}")
            else:
                logger.info("Superuser status is already correct")
        else:
            logger.error("Superuser not found")
    except Exception as e:
        logger.error(f"Error fixing superuser: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Fixing superuser status")
    fix_superuser()
    logger.info("Superuser fix completed")