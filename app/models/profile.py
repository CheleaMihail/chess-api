from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bio = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Relationship to User model
    user = relationship("User", back_populates="profile")
