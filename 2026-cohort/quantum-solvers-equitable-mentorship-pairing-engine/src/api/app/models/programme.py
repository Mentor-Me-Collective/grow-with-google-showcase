import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import Timestamped, UUIDPrimaryKey


class ProgramMilestone(UUIDPrimaryKey, Timestamped, Base):
    """A point in the programme arc, in weeks from the cohort start.

    Weeks rather than dates: a cohort gets re-run with new dates and the arc is
    the part that stays the same.
    """

    __tablename__ = "program_milestone"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    week_offset: Mapped[int] = mapped_column(Integer, nullable=False)

    # Shown inside every strand when this point is reached. Without one, the
    # milestone only exists for the coordinator.
    strand_prompt: Mapped[str | None] = mapped_column(Text)
    reminder_days_before: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class MessageTemplate(UUIDPrimaryKey, Timestamped, Base):
    """Wording the programme sends on a coordinator's behalf.

    Ships with defaults, so a programme that never opens the templates screen
    still sends something that reads like a person wrote it.
    """

    __tablename__ = "message_template"
    __table_args__ = (UniqueConstraint("program_id", "kind"),)

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # True while the programme has not overridden the wording, so the screen can
    # show what was written from what was inherited.
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_by: Mapped[str | None] = mapped_column(String(200))


class Broadcast(UUIDPrimaryKey, Base):
    """One message sent to a segment at once."""

    __tablename__ = "broadcast"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    segment: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Counted when it was sent, not recomputed on read. A segment's size
    # changes, and a history that recalculated it would rewrite what happened.
    recipient_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    state: Mapped[str] = mapped_column(String(16), nullable=False, default="sent")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Resource(UUIDPrimaryKey, Timestamped, Base):
    """Static reading a coordinator publishes for participants."""

    __tablename__ = "resource"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    url: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)


class AuditEvent(UUIDPrimaryKey, Base):
    """Who changed what, and when.

    The fairness claim is only inspectable if the deviations from the algorithm
    are on the record, so this is where they go. Summaries are written in plain
    words: a log that needs the reader to know the schema is not inspectable by
    the people it exists for.
    """

    __tablename__ = "audit_event"

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=False, index=True
    )
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    actor_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    subject_label: Mapped[str | None] = mapped_column(Text)
