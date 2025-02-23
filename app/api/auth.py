from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.services import auth
from app.schemas.auth import RefreshTokenRequest, UserLogin, RefershToken
from app.schemas.user import UserAuthResponse

router = APIRouter()


@router.post("/login/", response_model=UserAuthResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=login_data.email)

    if user is None or not auth.verify_password(
        login_data.password, user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = auth.create_access_token({"username": user.username, "id": user.id})
    refresh_token = auth.create_refresh_token(
        {"username": user.username, "id": user.id}
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/refresh/", response_model=RefershToken)
async def refresh_token(request: RefreshTokenRequest):
    token_data = auth.verify_refresh_token(request.refresh_token)

    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = auth.create_access_token(
        {"username": token_data.username, "id": token_data.id}
    )

    return {"access_token": new_access_token, "id": token_data.id}
