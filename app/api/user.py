from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.services import auth
from app.schemas.auth import TokenData
from app.schemas.user import UserAuthResponse, UserResponse, UserCreate

router = APIRouter()


@router.post("/", response_model=UserAuthResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)

    user_data = crud.create_user(db=db, user=user, hashed_password=hashed_password)

    access_token = auth.create_access_token(
        {"username": user_data.username, "id": user_data.id}
    )
    refresh_token = auth.create_refresh_token(
        {"username": user_data.username, "id": user_data.id}
    )

    return {
        "id": user_data.id,
        "username": user_data.username,
        "email": user_data.email,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# Get user by ID endpoint
@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    user_data = crud.get_user_by_id(db, user_id=user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user_data.seeker = getattr(current_user, "username", None)
    return user_data


# Update user endpoint
@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    user_data = crud.get_user_by_id(db, user_id=user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = auth.hash_password(user.password)
    updated_user = crud.update_user(
        db, user_id=user_id, user=user, hashed_password=hashed_password
    )
    return updated_user
