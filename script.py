from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:joracrinj@localhost:5432/chess"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("✅ Database connected successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
