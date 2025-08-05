from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# 创建PostgreSQL生产环境数据库引擎
# 使用配置文件中的数据库URL
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DATABASE_ECHO,
    # PostgreSQL生产环境优化参数
    connect_args={
        "connect_timeout": 30,
        "application_name": "sys_rev_tech_app",
        "client_encoding": "utf8",
        "options": "-c timezone=UTC",
        "sslmode": "disable",     # 禁用SSL以简化连接
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """获取数据库会话"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
