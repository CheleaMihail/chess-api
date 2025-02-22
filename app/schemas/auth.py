from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenData(BaseModel):
    id: int
    username: str


class RefershToken(BaseModel):
    access_token: str

    class Config:
        from_attributes = True
