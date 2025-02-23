from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    stats_ultra = Column(Integer, default=0)
    stats_bullet = Column(Integer, default=0)
    stats_rapid = Column(Integer, default=0)
    stats_blitz = Column(Integer, default=0)
    stats_classic = Column(Integer, default=0)
    # Relationship with the Profile model (one-to-one)
    # profile = relationship("Profile", back_populates="user", uselist=False)


# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from database import Base

# # User Table
# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     hashed_password = Column(String, nullable=False)

#     # Relationship to Profile
#     profile = relationship("Profile", back_populates="user", uselist=False)

# # Profile Table
# class Profile(Base):
#     __tablename__ = "profiles"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     bio = Column(String, nullable=True)
#     avatar_url = Column(String, nullable=True)

#     # Relationship to User
#     user = relationship("User", back_populates="profile")

# # Room Table
# class Room(Base):
#     __tablename__ = "rooms"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, nullable=False)
