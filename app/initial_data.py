import logging

from app.core.config import settings
from app.crud.crud_user import user
from app.db.session import SessionLocal
from app.schemas.user import UserCreate
from app.models.user import UserRole as Role

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def init_db() -> None:
    """初始化数据库数据"""
    # Tables should be created with Alembic, so we don't need this
    # Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 创建默认超级用户
        superuser = user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
        if not superuser:
            logger.info("创建默认超级用户...")
            user_in = UserCreate(
                username=settings.FIRST_SUPERUSER_USERNAME,
                email=settings.FIRST_SUPERUSER_EMAIL,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name="系统管理员",
                role=Role.ADMIN,
                is_superuser=True,
                is_active=True
            )
            superuser = user.create(db, obj_in=user_in)
            logger.info(f"超级用户创建成功: {superuser.username}")
        else:
            logger.info(f"超级用户已存在: {superuser.username}")
        
        # 创建默认普通用户（如果配置了的话）
        if hasattr(settings, 'FIRST_USER') and settings.FIRST_USER:
            initial_user = user.get_by_username(db, username=settings.FIRST_USER)
            if not initial_user:
                logger.info("创建默认普通用户...")
                user_in = UserCreate(
                    username=settings.FIRST_USER,
                    email=getattr(settings, 'FIRST_USER_EMAIL', f"{settings.FIRST_USER}@example.com"),
                    password=getattr(settings, 'FIRST_USER_PASSWORD', 'defaultpassword'),
                    full_name="默认用户",
                    role=Role.USER,
                    is_superuser=False,
                    is_active=True
                )
                initial_user = user.create(db, obj_in=user_in)
                logger.info(f"普通用户创建成功: {initial_user.username}")
            else:
                logger.info(f"普通用户已存在: {initial_user.username}")
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":

    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")
