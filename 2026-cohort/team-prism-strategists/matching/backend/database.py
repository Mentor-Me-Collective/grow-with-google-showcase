import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_env_db = os.getenv("DATABASE_URL")
if _env_db and _env_db != "sqlite:///./mentor_me.db":
    DATABASE_URL = _env_db
    # SQLAlchemy 2.0 requires postgresql:// instead of postgres://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    _matching_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _db_path = os.path.join(_matching_dir, "mentor_me.db").replace("\\", "/")
    DATABASE_URL = f"sqlite:///{_db_path}"

# connect_args={"check_same_thread": False} is required only for SQLite
_connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
