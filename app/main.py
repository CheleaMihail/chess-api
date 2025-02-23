from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api import user, profile, room, auth, chess

# Initialize the database
Base.metadata.create_all(bind=engine)

# Create FastAPI instance
app = FastAPI(title="Chess API", version="1.0")


# CORS Middleware (Adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Routers
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(chess.router, prefix="/chess", tags=["Chess"])
app.include_router(auth.router, prefix="/auth", tags=["Authorization"])
app.include_router(profile.router, prefix="/profiles", tags=["Profiles"])
app.include_router(room.router, prefix="/rooms", tags=["Chess Rooms"])


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Chess Platform API!"}
