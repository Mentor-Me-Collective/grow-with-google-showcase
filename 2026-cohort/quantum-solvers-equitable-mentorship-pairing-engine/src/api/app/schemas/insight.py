import uuid
from datetime import date, datetime

from pydantic import Field

from app.enums import AuditAction
from app.schemas.common import Wire
from app.schemas.matching import PersonRefOut
from app.schemas.setup import PriorityBandStatOut


class TimePointOut(Wire):
    date: date
    value: float


class MentorLoadOut(Wire):
    mentor: PersonRefOut
    load: int
    capacity: int


class CountPointOut(Wire):
    label: str
    count: int


class MilestoneCompletionOut(Wire):
    title: str
    completed: int
    total: int


class DropOffStageOut(Wire):
    """The funnel from applying to still meeting.

    Counts at each stage rather than one retention figure, because where a
    programme loses people is the part it can act on.
    """

    stage: str
    count: int


class DemographicBreakdownOut(Wire):
    """Buckets smaller than the suppression threshold are withheld rather than
    rounded: in a cohort of twenty, "one person" plus any other column is an
    identification."""

    field_id: uuid.UUID
    label: str
    buckets: list[CountPointOut] = []
    suppressed_buckets: int = 0


class ProgramReportOut(Wire):
    program_name: str
    #: `from` is a keyword, so the field is named around it and the wire name is
    #: pinned by hand — the camelCase generator would emit `from_`.
    from_: date = Field(alias="from")
    to: date
    coverage_over_time: list[TimePointOut] = []
    mentor_load: list[MentorLoadOut] = []
    quality_by_band: list[PriorityBandStatOut] = []
    sessions_by_week: list[CountPointOut] = []
    check_in_sentiment: list[CountPointOut] = []
    check_in_response_rate: float | None = None
    milestone_completion: list[MilestoneCompletionOut] = []
    drop_off: list[DropOffStageOut] = []
    demographics: list[DemographicBreakdownOut] = []
    suppression_threshold: int = 3


class AuditEventOut(Wire):
    id: uuid.UUID
    at: datetime
    actor_name: str
    action: AuditAction
    #: Plain words. A log that needs the reader to know the schema is not
    #: inspectable by the people it exists for.
    summary: str
    subject_label: str | None = None


class AuditPageOut(Wire):
    items: list[AuditEventOut]
    page: int
    page_size: int
    total: int
    #: Everybody who appears in the whole log, not just this page — otherwise
    #: the filter loses the option that produced the current view.
    actors: list[str] = []
