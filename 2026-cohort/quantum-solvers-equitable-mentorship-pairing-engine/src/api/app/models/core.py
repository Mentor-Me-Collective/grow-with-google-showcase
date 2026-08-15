import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import true as sa_true
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamped, UUIDPrimaryKey


class Organisation(UUIDPrimaryKey, Timestamped, Base):
    """The tenant. Owns programmes, coordinators, taxonomy and the audit log."""

    __tablename__ = "organisation"

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text)

    programs: Mapped[list["Program"]] = relationship(back_populates="organisation")


class Program(UUIDPrimaryKey, Timestamped, Base):
    """A cohort. Owns its form schema, matching recipe, roster and reports."""

    __tablename__ = "program"
    __table_args__ = (UniqueConstraint("organisation_id", "slug"),)

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="open")

    cohort_start: Mapped[date | None] = mapped_column(Date)
    cohort_end: Mapped[date | None] = mapped_column(Date)
    applications_close_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    matching_opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    time_commitment: Mapped[str | None] = mapped_column(Text)
    eligibility: Mapped[str | None] = mapped_column(Text)
    open_roles: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    recruitment_goal: Mapped[int | None] = mapped_column(Integer)
    # Architecture 4.9: the directory only exists when this is on. False is a
    # real state, not an error.
    self_matching_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    organisation: Mapped[Organisation] = relationship(back_populates="programs")
    participations: Mapped[list["Participation"]] = relationship(
        back_populates="program"
    )


class Account(UUIDPrimaryKey, Timestamped, Base):
    """One person, one login, one email. Exists above organisations.

    Carries no role. Role lives on Participation, because the same person is a
    mentee in one programme and a mentor in another, simultaneously.
    """

    __tablename__ = "account"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    photo_url: Mapped[str | None] = mapped_column(Text)

    # One switch per kind of mail, as columns rather than a JSON blob: these are
    # read on the way out of every send, and a fixed set of five is exactly the
    # shape that rots when it is stored as free-form. Defaults are on, except
    # the digest, because somebody who never opens settings should still hear
    # that they have been matched.
    notify_new_message: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa_true()
    )
    notify_match_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa_true()
    )
    notify_milestone_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa_true()
    )
    notify_broadcasts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa_true()
    )
    digest_frequency: Mapped[str] = mapped_column(
        String(16), nullable=False, default="weekly", server_default="weekly"
    )

    participations: Mapped[list["Participation"]] = relationship(
        back_populates="account"
    )


class Participation(UUIDPrimaryKey, Timestamped, Base):
    """Account × programme. Where role, status and the profile actually live.

    Every participant-facing query is scoped by program_id, and every admin
    query by organisation_id and usually also program_id.
    """

    __tablename__ = "participation"
    __table_args__ = (UniqueConstraint("account_id", "program_id"),)

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )

    role: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="applied")
    is_coordinator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Mentors only. Load may exceed capacity — a mentor over capacity is
    # precisely what the fairness summary has to be able to report.
    capacity: Mapped[int | None] = mapped_column(Integer)
    load: Mapped[int | None] = mapped_column(Integer)

    profile_completeness: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    timezone: Mapped[str | None] = mapped_column(String(64))
    headline: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    # Denormalised for the roster and the directory, which read it far more
    # often than strands change. Maintained when a strand is created or ended.
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped[Account] = relationship(back_populates="participations")
    program: Mapped[Program] = relationship(back_populates="participations")
