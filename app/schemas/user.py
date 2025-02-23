from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class UserAuthResponse(UserResponse):
    id: int
    username: str
    email: EmailStr
    access_token: str
    refresh_token: str

    class Config:
        from_attributes = True
