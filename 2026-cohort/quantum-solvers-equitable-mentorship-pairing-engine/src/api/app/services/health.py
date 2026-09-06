"""How a strand is going, worked out rather than stored.

A quiet strand is one nobody has written in — not one somebody flagged as quiet
and forgot about. Deriving it on every read means the signal cannot go stale,
and it is what lets the dashboard and the monitor agree without either of them
owning the definition.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums import StrandState
from app.models import Message, ProgramMilestone, Strand

#: Design direction 8.3 puts the threshold at a fortnight. One definition, used
#: by the monitor, the dashboard and the participant's own strand card.
QUIET_AFTER_DAYS = 14


def days_since(when: datetime | None) -> int | None:
    if when is None:
        return None
    return (datetime.now(UTC) - when).days


def health_of(
    strand: Strand,
    days: int | None,
    has_messages: bool,
    milestones_completed: int,
    milestones_total: int,
) -> str:
    if strand.state == StrandState.ENDED:
        return "ended"
    # Never begun is its own state. A pair who never started needs an
    # introduction; a pair who stopped after eight sessions needs a different
    # conversation entirely, and calling both "quiet" hides that.
    if not has_messages:
        return "not_started"
    if days is not None and days >= QUIET_AFTER_DAYS:
        return "quiet"
    # Talking, but the arc has moved on without them.
    if milestones_total > 0 and milestones_completed == 0:
        return "slow"
    return "on_track"


def milestone_total(db: Session, program_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ProgramMilestone)
            .where(ProgramMilestone.program_id == program_id)
        )
        or 0
    )


def has_messages(db: Session, strand_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.strand_id == strand_id)
        )
        or 0
    ) > 0
