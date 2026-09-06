import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class UUIDPrimaryKey:
    """UUID primary keys, generated in Python rather than by the database.

    The contract types every id as `format: uuid`, and generating client-side
    means an object knows its own id before it is flushed — which matters when
    building a graph of related rows in one transaction, as the seed does.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class Timestamped:
    """Rows that want to know when they appeared and last changed.

    Server-side defaults, so a row inserted by a migration or by psql gets the
    same treatment as one inserted by the API.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
