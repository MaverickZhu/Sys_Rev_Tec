from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.auth import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):

    def is_active(self, user: User) -> bool:
        """检查用户是否激活"""
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """检查用户是否为超级用户"""
        return user.is_superuser

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """用户认证
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            User: 认证成功返回用户对象，失败返回None
        """
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """创建用户"""
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            full_name=obj_in.full_name,
            employee_id=obj_in.employee_id,
            department=obj_in.department,
            position=obj_in.position,
            phone=obj_in.phone,
            hashed_password=get_password_hash(obj_in.password),
            role=obj_in.role,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """更新用户密码"""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def update_login_info(self, db: Session, *, user: User) -> User:
        """更新用户登录信息"""
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def create_superuser(self, db: Session, *, obj_in: UserCreate) -> User:
        """创建超级用户"""
        obj_in.is_superuser = True
        obj_in.is_active = True
        return self.create(db, obj_in=obj_in)


user = CRUDUser(User)
