import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamped, UUIDPrimaryKey


class Strand(UUIDPrimaryKey, Timestamped, Base):
    """The mentoring relationship. One to one or a group.

    Members are a separate table rather than two columns, because a group
    strand is a first-class outcome: given representation numbers in senior
    technical roles, one-to-one for everyone is arithmetically impossible in
    most cohorts.
    """

    __tablename__ = "strand"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    origin_mode: Mapped[str] = mapped_column(String(16), nullable=False)

    # A partial explanation, not the explanation. In a global assignment the
    # real reason often involves a third person, so this is presented as such.
    match_rationale: Mapped[str | None] = mapped_column(Text)

    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_session_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # What the monitor reports. Sessions logged matter more than sessions
    # scheduled: logging is the engagement signal the health view reads.
    sessions_logged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    milestones_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    members: Mapped[list["StrandMember"]] = relationship(
        back_populates="strand", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="strand", cascade="all, delete-orphan"
    )


class StrandMember(UUIDPrimaryKey, Base):
    __tablename__ = "strand_member"
    __table_args__ = (UniqueConstraint("strand_id", "participation_id"),)

    strand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strand.id"), nullable=False, index=True
    )
    participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False, index=True
    )
    # Denormalised from the participation so a strand can be rendered without
    # joining out to find who was the mentor.
    role: Mapped[str] = mapped_column(String(16), nullable=False)

    strand: Mapped[Strand] = relationship(back_populates="members")


class Message(UUIDPrimaryKey, Base):
    __tablename__ = "message"

    strand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strand.id"), nullable=False, index=True
    )
    author_participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    delivery_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="sent"
    )
    # Echoed back so an optimistic send can be reconciled against the stored
    # row instead of duplicated.
    client_token: Mapped[str | None] = mapped_column(String(64))

    # Per member, so a group strand can tell who has read what.
    read_by: Mapped[list["MessageRead"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    strand: Mapped[Strand] = relationship(back_populates="messages")


class MessageRead(UUIDPrimaryKey, Base):
    __tablename__ = "message_read"
    __table_args__ = (UniqueConstraint("message_id", "participation_id"),)

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message.id"), nullable=False, index=True
    )
    participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message: Mapped[Message] = relationship(back_populates="read_by")
