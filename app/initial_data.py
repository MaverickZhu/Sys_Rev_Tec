import logging

from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
from app.crud import user
from app.schemas import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    # Tables should be created with Alembic, so we don't need this
    # Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create superuser
    superuser = user.get_by_username(db, username=settings.FIRST_SUPERUSER)
    if not superuser:
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        superuser = user.create(db, obj_in=user_in)
        logger.info("Superuser created")
    else:
        logger.info("Superuser already exists")


if __name__ == "__main__":
    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")