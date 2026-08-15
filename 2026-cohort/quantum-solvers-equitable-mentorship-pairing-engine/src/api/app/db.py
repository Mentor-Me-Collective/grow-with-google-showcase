from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base. Alembic reads its metadata to autogenerate migrations."""


settings = get_settings()

# Synchronous on purpose. At cohort scale — hundreds of rows, not millions —
# async buys nothing measurable, and it costs real correctness risk: greenlet
# errors and lazy-load surprises. FastAPI runs sync endpoints in a threadpool.
engine = create_engine(
    settings.database_url,
    # Recycle before a managed database's idle timeout can close a pooled
    # connection under us, which otherwise surfaces as a random 500.
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """One session per request, closed whatever happens."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
