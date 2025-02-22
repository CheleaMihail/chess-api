from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.services import auth
from app.schemas.user import UserResponse, UserCreate

router = APIRouter()


# Get user by ID endpoint
@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user_data = [{id: user_id}]
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return user_data
