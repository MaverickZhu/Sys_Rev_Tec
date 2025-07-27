import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app import crud, models, schemas
from app.core.security import get_password_hash, verify_password
from tests.utils.utils import random_lower_string, random_email
from tests.utils.user import create_random_user


class TestCRUDUserCoverage:
    """CRUDUser覆盖率测试"""

    def test_authenticate_success(self, db: Session) -> None:
        """测试用户认证成功"""
        username = random_lower_string()
        password = random_lower_string()
        user_in = schemas.UserCreate(
            username=username,
            password=password
        )
        user = crud.user.create(db=db, obj_in=user_in)
        
        authenticated_user = crud.user.authenticate(
            db=db, username=username, password=password
        )
        assert authenticated_user
        assert authenticated_user.username == username
        assert authenticated_user.id == user.id

    def test_authenticate_wrong_password(self, db: Session) -> None:
        """测试用户认证密码错误"""
        username = random_lower_string()
        password = random_lower_string()
        user_in = schemas.UserCreate(
            username=username,
            password=password
        )
        crud.user.create(db=db, obj_in=user_in)
        
        authenticated_user = crud.user.authenticate(
            db=db, username=username, password="wrong_password"
        )
        assert authenticated_user is None

    def test_authenticate_user_not_found(self, db: Session) -> None:
        """测试用户认证用户不存在"""
        authenticated_user = crud.user.authenticate(
            db=db, username="nonexistent_user", password="any_password"
        )
        assert authenticated_user is None

    def test_is_active_true(self, db: Session) -> None:
        """测试用户活跃状态为真"""
        user = create_random_user(db)
        user.is_active = True
        assert crud.user.is_active(user) is True

    def test_is_active_false(self, db: Session) -> None:
        """测试用户活跃状态为假"""
        user = create_random_user(db)
        user.is_active = False
        assert crud.user.is_active(user) is False

    def test_get_by_username_exists(self, db: Session) -> None:
        """测试按用户名获取存在的用户"""
        user = create_random_user(db)
        found_user = crud.user.get_by_username(db=db, username=user.username)
        assert found_user
        assert found_user.id == user.id
        assert found_user.username == user.username

    def test_get_by_username_not_exists(self, db: Session) -> None:
        """测试按用户名获取不存在的用户"""
        found_user = crud.user.get_by_username(db=db, username="nonexistent_user")
        assert found_user is None

    def test_create_user_basic(self, db: Session) -> None:
        """测试创建基本用户"""
        username = random_lower_string()
        password = random_lower_string()
        user_in = schemas.UserCreate(
            username=username,
            password=password
        )
        user = crud.user.create(db=db, obj_in=user_in)
        assert user.username == username
        assert user.is_active is True
        assert user.is_superuser is False
        assert verify_password(password, user.hashed_password)

    def test_create_user_with_superuser(self, db: Session) -> None:
        """测试创建超级用户"""
        username = random_lower_string()
        password = random_lower_string()
        user_in = schemas.UserCreate(
            username=username,
            password=password,
            is_superuser=True
        )
        user = crud.user.create(db=db, obj_in=user_in)
        assert user.username == username
        assert user.is_superuser is True
        assert user.is_active is True

    def test_create_user_inactive(self, db: Session) -> None:
        """测试创建非活跃用户"""
        username = random_lower_string()
        password = random_lower_string()
        user_in = schemas.UserCreate(
            username=username,
            password=password,
            is_active=False
        )
        user = crud.user.create(db=db, obj_in=user_in)
        assert user.username == username
        assert user.is_active is False
        assert user.is_superuser is False

    def test_update_user_with_dict(self, db: Session) -> None:
        """测试使用字典更新用户"""
        user = create_random_user(db)
        new_username = random_lower_string()
        update_data = {"username": new_username}
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in=update_data)
        assert updated_user.username == new_username
        assert updated_user.id == user.id

    def test_update_user_with_schema(self, db: Session) -> None:
        """测试使用schema更新用户"""
        user = create_random_user(db)
        new_username = random_lower_string()
        user_update = schemas.UserUpdate(username=new_username)
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in=user_update)
        assert updated_user.username == new_username
        assert updated_user.id == user.id

    def test_update_user_password(self, db: Session) -> None:
        """测试更新用户密码"""
        user = create_random_user(db)
        new_password = random_lower_string()
        update_data = {"password": new_password}
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in=update_data)
        assert verify_password(new_password, updated_user.hashed_password)
        assert updated_user.id == user.id

    def test_update_user_password_with_dict(self, db: Session) -> None:
        """测试使用字典更新用户密码"""
        user = create_random_user(db)
        new_password = random_lower_string()
        update_data = {"password": new_password}
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in=update_data)
        assert verify_password(new_password, updated_user.hashed_password)
        assert updated_user.id == user.id

    def test_update_user_multiple_fields(self, db: Session) -> None:
        """测试更新用户多个字段"""
        user = create_random_user(db)
        new_username = random_lower_string()
        new_password = random_lower_string()
        update_data = {
            "username": new_username,
            "password": new_password,
            "is_active": False
        }
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in=update_data)
        assert updated_user.username == new_username
        assert updated_user.is_active is False
        assert verify_password(new_password, updated_user.hashed_password)
        assert updated_user.id == user.id


class TestCRUDUserEdgeCases:
    """CRUDUser边界情况测试"""

    def test_authenticate_empty_username(self, db: Session) -> None:
        """测试空用户名认证"""
        authenticated_user = crud.user.authenticate(
            db=db, username="", password="any_password"
        )
        assert authenticated_user is None

    def test_authenticate_empty_password(self, db: Session) -> None:
        """测试空密码认证"""
        user = create_random_user(db)
        authenticated_user = crud.user.authenticate(
            db=db, username=user.username, password=""
        )
        assert authenticated_user is None

    def test_get_by_username_empty_string(self, db: Session) -> None:
        """测试空字符串用户名查询"""
        found_user = crud.user.get_by_username(db=db, username="")
        assert found_user is None

    def test_create_user_with_all_fields(self, db: Session) -> None:
        """测试创建包含所有字段的用户"""
        username = random_lower_string()
        password = random_lower_string()
        user_in = schemas.UserCreate(
            username=username,
            password=password,
            is_superuser=True,
            is_active=False
        )
        user = crud.user.create(db=db, obj_in=user_in)
        assert user.username == username
        assert user.is_superuser is True
        assert user.is_active is False
        assert verify_password(password, user.hashed_password)

    def test_update_user_empty_dict(self, db: Session) -> None:
        """测试使用空字典更新用户"""
        user = create_random_user(db)
        original_username = user.username
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in={})
        assert updated_user.username == original_username
        assert updated_user.id == user.id

    def test_update_user_schema_only_username(self, db: Session) -> None:
        """测试使用schema只更新用户名"""
        user = create_random_user(db)
        new_username = random_lower_string()
        
        # UserUpdate只有username字段
        user_update = schemas.UserUpdate(username=new_username)
        
        updated_user = crud.user.update(db=db, db_obj=user, obj_in=user_update)
        assert updated_user.username == new_username
        assert updated_user.id == user.id