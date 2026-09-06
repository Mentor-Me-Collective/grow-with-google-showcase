import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamped, UUIDPrimaryKey


class MatchingRecipe(UUIDPrimaryKey, Timestamped, Base):
    """The weights, constraints and fairness rules a run is scored against.

    Coupled to the published form: a weight can only refer to a question that is
    actually asked. Versioned on every save so a published run can say which
    recipe produced it.
    """

    __tablename__ = "matching_recipe"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    hard_constraints: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    weights: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    fairness: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    updated_by: Mapped[str | None] = mapped_column(String(200))


class Run(UUIDPrimaryKey, Base):
    """A matching run as a stored object with a lifecycle, not a function call.

    queued -> running -> drafted -> published | discarded. The frontend polls
    this row and expects `progress` to climb from 0 to 1 with `fairness_summary`
    null until it reaches drafted.

    Nothing here is visible to a participant until `published_at` is set.
    """

    __tablename__ = "run"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recipe_version: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(200), nullable=False)

    # Set when the background task picks the run up, which is the only thing
    # that distinguishes a task that died mid-run from one that was never
    # scheduled at all. Both leave the row looking identical otherwise, and they
    # are different faults.
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[str | None] = mapped_column(String(200))

    drafted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_rate: Mapped[float | None] = mapped_column(Float)

    # Stored as computed rather than recalculated on read: the summary describes
    # the roster as it stood when the run happened, and recomputing it later
    # would quietly rewrite the record a coordinator published against.
    fairness_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    pairs: Mapped[list["DraftPair"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    unmatched: Mapped[list["RunUnmatched"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class DraftPair(UUIDPrimaryKey, Base):
    """One proposed pairing, before anybody has been told anything."""

    __tablename__ = "draft_pair"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("run.id"), nullable=False, index=True
    )
    mentee_participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False
    )
    mentor_participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    priority_band: Mapped[str] = mapped_column(String(16), nullable=False)

    # What contributed to this pair's score, kept for the per-pair view. Labelled
    # a partial explanation wherever it is shown, because in a global assignment
    # the true reason often involves a third person.
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    run: Mapped[Run] = relationship(back_populates="pairs")


class RunUnmatched(UUIDPrimaryKey, Base):
    """Somebody a run could not place, with a reason a coordinator can act on.

    A reason code rather than a sentence, because each one has a different
    remedy: no capacity needs a mentor, no overlap needs a different pool or a
    group, an incomplete profile needs the participant.
    """

    __tablename__ = "run_unmatched"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("run.id"), nullable=False, index=True
    )
    participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(32), nullable=False)

    run: Mapped[Run] = relationship(back_populates="unmatched")


class ParticipantAttribute(UUIDPrimaryKey, Base):
    """One flagged answer, projected into a fixed typed shape.

    This is the boundary architecture 3.1 describes: the application form is
    unknown at compile time, but everything downstream — matching, reporting,
    export — reads this table, which always has the same columns. The unknown
    schema stops here and nowhere else.

    Rebuilt rather than maintained. It is a projection of the answers, so it can
    be thrown away and recomputed at any time, which is what makes a change to
    the flags on a question safe.
    """

    __tablename__ = "participant_attribute"
    __table_args__ = (UniqueConstraint("participation_id", "field_id"),)

    participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participation.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("program.id"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    #: The flags that put it here. A question may feed both scores.
    matching: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    equity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    field_type: Mapped[str] = mapped_column(String(32), nullable=False)
    #: Exactly one of these carries the value, chosen by field_type.
    text_value: Mapped[str | None] = mapped_column(Text)
    number_value: Mapped[float | None] = mapped_column(Float)
    option_values: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
