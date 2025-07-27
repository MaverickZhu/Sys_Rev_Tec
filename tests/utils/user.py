from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core.security import get_password_hash
from tests.utils.utils import random_lower_string, random_email


def create_random_user(db: Session) -> models.User:
    """创建随机测试用户"""
    email = random_email()
    password = random_lower_string()
    username = random_lower_string()
    full_name = f"{random_lower_string()} {random_lower_string()}"
    
    user_in = schemas.UserCreate(
        email=email,
        password=password,
        username=username,
        full_name=full_name
    )
    
    user = crud.user.create(db=db, obj_in=user_in)
    return user


def create_random_superuser(db: Session) -> models.User:
    """创建随机超级用户"""
    email = random_email()
    password = random_lower_string()
    username = random_lower_string()
    full_name = f"{random_lower_string()} {random_lower_string()}"
    
    user_in = schemas.UserCreate(
        email=email,
        password=password,
        username=username,
        full_name=full_name,
        is_superuser=True
    )
    
    user = crud.user.create(db=db, obj_in=user_in)
    return user


def create_user_with_role(db: Session, role: str = "user") -> models.User:
    """创建指定角色的用户"""
    email = random_email()
    password = random_lower_string()
    username = random_lower_string()
    full_name = f"{random_lower_string()} {random_lower_string()}"
    
    user_in = schemas.UserCreate(
        email=email,
        password=password,
        username=username,
        full_name=full_name,
        role=role
    )
    
    user = crud.user.create(db=db, obj_in=user_in)
    return user


def authentication_token_from_email(
    *, client, email: str, db: Session
) -> dict:
    """从邮箱获取认证令牌"""
    password = random_lower_string()
    user = crud.user.get_by_email(db, email=email)
    if not user:
        user_in_create = schemas.UserCreate(
            username=random_lower_string(),
            email=email,
            password=password
        )
        user = crud.user.create(db, obj_in=user_in_create)
    else:
        user_in_update = schemas.UserUpdate(password=password)
        user = crud.user.update(db, db_obj=user, obj_in=user_in_update)

    return user_authentication_headers(
        client=client, email=email, password=password
    )


def user_authentication_headers(*, client, email: str, password: str) -> dict:
    """获取用户认证头"""
    data = {"username": email, "password": password}
    r = client.post("/api/v1/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers