import logging

from app.core.config import settings
from app.crud import user
from app.db.session import SessionLocal
from app.schemas import UserCreate

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def init_db() -> None:

    # Tables should be created with Alembic, so we don't need this
    # Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create initial user
    initial_user = user.get_by_username(db, username=settings.FIRST_USER)
    if not initial_user:
        user_in = UserCreate(
            username=settings.FIRST_USER,
            email=settings.FIRST_USER_EMAIL,
            full_name="系统管理员",
        )
        initial_user = user.create(db, obj_in=user_in)
        logger.info("Initial user created")
    else:
        logger.info("Initial user already exists")


if __name__ == "__main__":

    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")
