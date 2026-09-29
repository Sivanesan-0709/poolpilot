import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Check for environment variables (PostgreSQL on Neon/Supabase or serverless /tmp)
DATABASE_URL = os.getenv("DATABASE_URL")
IS_SERVERLESS = os.getenv("POOLPILOT_SERVERLESS", "0") in ("1", "true", "True") or os.getenv("VERCEL") == "1"

if DATABASE_URL:
    # Handle postgres:// vs postgresql:// for SQLAlchemy compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # Use /tmp for serverless Vercel runtime or local data dir
    if IS_SERVERLESS:
        DB_PATH = "/tmp/poolpilot.db"
    else:
        DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "poolpilot.db")
    
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
