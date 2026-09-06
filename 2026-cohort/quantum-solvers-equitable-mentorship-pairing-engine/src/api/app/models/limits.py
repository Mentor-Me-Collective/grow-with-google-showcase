from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RateLimitCounter(Base):
    """One counter per key per window.

    No surrogate id: the key and the window it belongs to *are* the identity,
    and making them the primary key is what lets the increment be a single
    `INSERT … ON CONFLICT DO UPDATE`. Reading a count and writing it back would
    be the same check-then-act race the limiter exists to bound.

    Rows are disposable. Nothing reads a window once it has passed, so an
    expired row is litter rather than history, and `app.limits` sweeps them.
    """

    __tablename__ = "rate_limit_counter"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
