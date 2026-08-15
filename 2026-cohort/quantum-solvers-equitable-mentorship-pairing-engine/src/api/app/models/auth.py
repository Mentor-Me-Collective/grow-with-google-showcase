import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import Timestamped, UUIDPrimaryKey


class SessionToken(UUIDPrimaryKey, Base):
    """An opaque session, not a JWT.

    The contract declares the scheme as an apiKey in a cookie, and an opaque
    token in a table can be revoked the moment somebody signs out — a signed
    token cannot, without building the revocation list that the table already is.
    """

    __tablename__ = "session_token"

    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MagicLinkToken(UUIDPrimaryKey, Base):
    """Single use, short lived.

    `used_at` rather than deletion on consumption: a second click on the same
    link should be able to say "that link has been used" instead of "no such
    link", which is what a person needs to be told.
    """

    __tablename__ = "magic_link_token"

    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationPreference(UUIDPrimaryKey, Timestamped, Base):
    """Per kind, not one switch.

    Somebody who wants to know when their mentor writes but not when the
    programme sends a newsletter should not have to choose between both and
    neither.
    """

    __tablename__ = "notification_preference"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id"), unique=True, nullable=False
    )
    new_message: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    match_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    milestone_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    broadcasts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    digest: Mapped[str] = mapped_column(String(16), nullable=False, default="weekly")


class Invite(UUIDPrimaryKey, Timestamped, Base):
    """For participants a coordinator adds directly rather than by application."""

    __tablename__ = "invite"

    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    invited_by_name: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApplicationResumeToken(UUIDPrimaryKey, Base):
    """Lets somebody pick up a half-finished application on another device.

    The same mechanism as the sign-in link, scoped to one draft instead of an
    account — which is why architecture 3.2 could describe it before it existed.
    """

    __tablename__ = "application_resume_token"

    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_draft.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
