import uuid
from datetime import datetime
from typing import Any

from app.enums import PriorityBand, RunState, UnmatchedReason
from app.schemas.common import Wire


class PersonRefOut(Wire):
    participation_id: uuid.UUID
    name: str
    photo_url: str | None = None


class RunOut(Wire):
    id: uuid.UUID
    program_id: uuid.UUID
    state: RunState
    progress: float
    recipe_version: int | None = None
    created_at: datetime
    created_by: str
    published_at: datetime | None = None
    published_by: str | None = None
    drafted_count: int = 0
    published_count: int = 0
    coverage_rate: float | None = None


class ScoreContributionOut(Wire):
    field_id: uuid.UUID
    label: str
    weight: int
    direction: str
    contribution: float
    #: Both sides' answers, because a number on its own does not tell a
    #: coordinator what was compared.
    mentee_answer: str | None = None
    mentor_answer: str | None = None


class PriorityContributionOut(Wire):
    field_id: uuid.UUID
    label: str
    weight: int
    #: Already inverted where the question is a scale, so higher always means
    #: less existing access.
    value: float
    answer: str | None = None


class DraftPairOut(Wire):
    id: uuid.UUID
    mentee: PersonRefOut
    mentor: PersonRefOut
    score: float
    priority_band: PriorityBand
    score_breakdown: list[ScoreContributionOut] = []
    #: Questions the recipe scores that this pair could not be compared on.
    unscored: list[str] = []
    priority_score: float | None = None
    priority_breakdown: list[PriorityContributionOut] = []


class RunDetailOut(RunOut):
    #: Null until the run reaches `drafted`. The review screen shows progress
    #: instead while it is absent.
    fairness_summary: dict[str, Any] | None = None
    pairs: list[DraftPairOut] = []
    unmatched_count: int = 0


class RunPageOut(Wire):
    items: list[RunOut]
    page: int
    page_size: int
    total: int


class UnmatchedEntryOut(Wire):
    participation_id: uuid.UUID
    name: str
    email: str | None = None
    role: str
    reason: UnmatchedReason
    profile_completeness: float
    timezone: str | None = None
    skills: list[str] = []
    joined_at: datetime | None = None
    last_run_id: uuid.UUID | None = None


class AvailableMentorOut(Wire):
    participation_id: uuid.UUID
    name: str
    load: int
    capacity: int
    skills: list[str] = []
    timezone: str | None = None


class UnmatchedPageOut(Wire):
    items: list[UnmatchedEntryOut]
    page: int
    page_size: int
    total: int
    #: Mentors with room to spare, so a pairing can be made without leaving the
    #: queue to go and find one.
    available_mentors: list[AvailableMentorOut] = []


class StrandCreateIn(Wire):
    mentee_participation_id: uuid.UUID
    mentor_participation_id: uuid.UUID
