from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Role(PyEnum):
    """用户角色枚举"""

    ADMIN = "admin"
    USER = "user"
    REVIEWER = "reviewer"
    MANAGER = "manager"


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    username = Column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )
    email = Column(String(100), unique=True, index=True, comment="邮箱")
    full_name = Column(String(100), comment="姓名")

    # 用户详细信息
    employee_id = Column(String(50), unique=True, comment="工号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    phone = Column(String(20), comment="电话")

    # 用户状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    # projects = relationship("Project", back_populates="owner")
