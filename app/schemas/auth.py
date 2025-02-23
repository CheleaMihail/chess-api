from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class RefershToken(BaseModel):
    id: int
    access_token: str

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str
