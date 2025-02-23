from sqlalchemy.orm import Session
from app.schemas.user import UserCreate
from app.models.user import User


def create_user(db: Session, user: UserCreate, hashed_password: str):
    db_user = User(
        username=user.username, email=user.email, hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_users_by_username(db: Session, username_substr: str, current_user_id: int):
    return (
        db.query(User)
        .filter(User.username.ilike(f"%{username_substr}%"))
        .filter(User.id != current_user_id)
        .all()
    )


def update_user(db: Session, user_id: int, user: UserCreate, hashed_password: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.username = user.username
        db_user.email = user.email
        db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)
    return db_user
