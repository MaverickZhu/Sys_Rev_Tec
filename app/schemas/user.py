# Shared properties


from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None


# Properties to receive on user creation


class UserCreate(UserBase):

    is_active: bool = True


# Properties to receive on user update


class UserUpdate(UserBase):

    username: Optional[str] = None


# Properties shared by models stored in DB


class UserInDBBase(UserBase):

    id: int
    is_active: bool

    model_config = {"from_attributes": True}


# Properties to return to client


class User(UserInDBBase):

    pass


# Properties stored in DB


class UserInDB(UserInDBBase):

    pass
