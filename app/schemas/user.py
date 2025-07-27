from pydantic import BaseModel

# Shared properties
class UserBase(BaseModel):
    username: str

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str
    is_superuser: bool = False
    is_active: bool = True

# Properties to receive on user update
class UserUpdate(UserBase):
    pass

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str