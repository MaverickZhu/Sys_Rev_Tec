# Shared properties

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    employee_id: Optional[str] = Field(None, max_length=50, description="工号")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    phone: Optional[str] = Field(None, max_length=20, description="电话")


# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="密码")
    is_active: bool = True


# Properties to receive on user update
class UserUpdate(UserBase):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, description="新密码")
    is_active: Optional[bool] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    is_active: bool
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Properties to return to client
class User(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# 登录请求模型
class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    remember_me: Optional[bool] = Field(False, description="记住我")


# 登录响应模型
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


# 令牌刷新请求模型
class TokenRefresh(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


# 令牌响应模型
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# 密码修改模型
class PasswordChange(BaseModel):
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
