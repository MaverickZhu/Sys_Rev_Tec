from typing import Generator, Optional

from app.db.session import SessionLocal
from app.models.user import User

"""
API依赖模块

提供数据库会话和用户认证相关的依赖函数。
"""


def get_db() -> Generator:
    """获取数据库会话

    Returns:
        Generator: 数据库会话生成器
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user() -> Optional[User]:
    """单机版简化用户获取（返回None表示无需认证）"""
    return None
